
# 标准库导入
import os
import json
import threading
import time
import tempfile
from datetime import datetime, date

# 第三方库导入
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import Calendar
from plyer import notification
import markdown
import webbrowser

class DailyPlanner:
    """每日计划管理应用主类"""
    
    def __init__(self, root):
        """初始化应用界面和数据结构"""
        self.root = root
        self.root.title("每日计划管理器")
        self.root.geometry("1000x700")
        
        # 初始化分类管理
        self.default_categories = ["工作", "学习", "生活", "其他"]
        self.current_category = tk.StringVar(value=self.default_categories[0])
        
        # 初始化数据目录路径
        self.data_dir = os.path.join(os.path.expanduser('~'), 'DailyPlannerData')
        self.template_dir = os.path.join(self.data_dir, 'templates')
        
        # 设置默认标签
        self.default_tags =self.default_categories
        
        # 初始化数据目录
        self._init_data_dirs()
        self.create_widgets()
        self.setup_reminder()
    def update_tags(self,tag):
        self.default_tags.append(tag)
        return
        
        
    def _init_data_dirs(self):
        """初始化应用所需的数据目录结构"""
        try:
            # 确保主数据目录存在
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            
            # 确保模板目录存在
            if not os.path.exists(self.template_dir):
                os.makedirs(self.template_dir)
            
            # 确保备份目录存在
            backup_dir = os.path.join(self.data_dir, 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 初始化标签文件（如果不存在）
            tags_file = os.path.join(self.data_dir, 'tags.json')
            if not os.path.exists(tags_file):
                with open(tags_file, 'w', encoding='utf-8') as f:
                    json.dump({'tags': self.default_tags}, f, ensure_ascii=False)
                    
        except OSError as e:
            messagebox.showerror("初始化错误", f"无法创建数据目录: {str(e)}")
            raise

    def create_widgets(self):
        # 日期选择
        self.date_frame = tk.Frame(self.root)
        self.date_frame.pack(pady=10)
        
        tk.Label(self.date_frame, text="选择日期:").pack(side=tk.LEFT)
        # 日期选择按钮
        self.date_str = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        tk.Entry(self.date_frame, textvariable=self.date_str, width=10).pack(side=tk.LEFT, padx=5)
        
        # 日历弹出按钮
        def open_calendar():
            top = tk.Toplevel(self.root)
            cal = Calendar(top, selectmode='day', date_pattern='y-mm-dd')
            cal.pack(padx=10, pady=10)
            def set_date():
                self.date_str.set(cal.get_date())
                top.destroy()
            tk.Button(top, text="选择", command=set_date).pack(pady=5)
            
        tk.Button(self.date_frame, text="📅", command=open_calendar).pack(side=tk.LEFT)
        
        tk.Button(self.date_frame, text="加载", command=self.load_plan).pack(side=tk.LEFT)
        
        # 分类标签
        self.tag_frame = tk.Frame(self.root)
        self.tag_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.tag_frame, text="分类:").pack(side=tk.LEFT)
        self.tag_var = tk.StringVar(value="工作")
        
        # 预设分类
        #self.default_tags = ["工作", "学习", "生活", "其他"]
        self.default_tags = self.load_tags()
        self.tag_combobox = ttk.Combobox(self.tag_frame, 
                                      textvariable=self.tag_var,
                                      values=self.default_tags)
        self.tag_combobox.pack(side=tk.LEFT, padx=5)
        self.tag_combobox.config(postcommand=lambda: self.tag_combobox.config(values=self.load_tags()))
        
        # 添加新分类按钮
        tk.Button(self.tag_frame, text="+", command=self.add_new_tag).pack(side=tk.LEFT, padx=5)
        
        # 计划内容编辑
        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(self.text_frame, text="计划内容(Markdown格式):").pack(anchor=tk.W)
        self.text = tk.Text(self.text_frame, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # Markdown测试和预览按钮
        btn_frame = tk.Frame(self.text_frame)
        btn_frame.pack(anchor=tk.E, pady=5)
        
        tk.Button(btn_frame, text="测试Markdown", 
                command=self.insert_markdown_test).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="预览Markdown", 
                command=self.preview_markdown).pack(side=tk.LEFT)
        
        # 完成状态
        self.done_var = tk.BooleanVar()
        tk.Checkbutton(self.root, text="已完成", variable=self.done_var).pack(anchor=tk.W, padx=10)
        
        # 操作按钮
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(pady=10)
        
        tk.Button(self.btn_frame, text="保存计划", command=self.save_plan).pack(side=tk.LEFT, padx=5)
        tk.Button(self.btn_frame, text="备份数据", command=self.backup_data).pack(side=tk.LEFT, padx=5)
        tk.Button(self.btn_frame, text="导入内容到模板库", command=self.import_to_template).pack(side=tk.LEFT, padx=5)
        tk.Button(self.btn_frame, text="模板库", command=self.manage_templates).pack(side=tk.LEFT, padx=5)
        
    def get_plan_file(self, selected_date):
        return os.path.join(self.data_dir, f"{selected_date}.json")
        
    def load_plan(self):
        selected_date = self.date_str.get()
        try:
            datetime.strptime(selected_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，请使用YYYY-MM-DD格式")
            return
            
        file_path = self.get_plan_file(selected_date)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, data.get('content', ''))
                self.tag_var.set(data.get('tag', '工作'))
                self.done_var.set(data.get('done', False))
        else:
            self.text.delete(1.0, tk.END)
            self.tag_var.set("工作")
            self.done_var.set(False)
            messagebox.showinfo("提示", f"{selected_date} 还没有计划，可以开始创建")
            
    def save_plan(self):
        selected_date = self.date_str.get()
        try:
            datetime.strptime(selected_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，请使用YYYY-MM-DD格式")
            return
            
        content = self.text.get(1.0, tk.END).strip()
        data = {
            'date': selected_date,
            'content': content,
            'tag': self.tag_var.get(),
            'done': self.done_var.get(),
            'last_modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        file_path = self.get_plan_file(selected_date)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        messagebox.showinfo("成功", f"{selected_date} 的计划已保存")
        
    def setup_reminder(self):
        """设置每日提醒，确保只创建一个线程"""
        if not hasattr(self, '_reminder_thread'):
            def reminder_thread():
                while True:
                    now = datetime.now()
                    if now.hour == 9 and now.minute == 0:
                        self.check_and_remind()
                    time.sleep(60)
                    
            self._reminder_thread = threading.Thread(target=reminder_thread, daemon=True)
            self._reminder_thread.start()
        
    def check_and_remind(self):
        today = date.today().strftime('%Y-%m-%d')
        file_path = self.get_plan_file(today)
        
        if not os.path.exists(file_path):
            notification.notify(
                title="每日计划提醒",
                message="今天是新的一天！请填写今天的计划",
                timeout=10
            )
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('content', '').strip():
                    notification.notify(
                        title="今日计划提醒",
                        message="您今天有以下计划:\n" + data['content'],
                        timeout=10
                    )
                else:
                    notification.notify(
                        title="每日计划提醒",
                        message="今天的计划是空的，请补充",
                        timeout=10
                    )

    def backup_data(self):
        backup_dir = os.path.join(self.data_dir, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        
        import zipfile
        with zipfile.ZipFile(backup_file, 'w') as zipf:
            for root, _, files in os.walk(self.data_dir):
                for file in files:
                    if not file.startswith('backup_'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.data_dir)
                        zipf.write(file_path, arcname)
                        
        messagebox.showinfo("成功", f"数据已备份到: {backup_file}")

    def load_tags(self):
        """加载所有可用标签"""
        tags_file = os.path.join(self.data_dir, 'tags.json')
        if os.path.exists(tags_file):
            with open(tags_file, 'r', encoding='utf-8') as f:
                return json.load(f).get('tags', self.default_tags)
        return self.default_tags
        
    def save_tags(self, tags):
        """保存标签列表"""
        tags_file = os.path.join(self.data_dir, 'tags.json')
        with open(tags_file, 'w', encoding='utf-8') as f:
            json.dump({'tags': tags}, f, ensure_ascii=False, indent=2)
            
    def add_new_tag(self):
        """添加新分类标签"""
        from tkinter import simpledialog
        new_tag = simpledialog.askstring("新分类", "输入新分类名称:")
        if new_tag and new_tag.strip():
            current_tags = list(self.load_tags())
            if new_tag not in current_tags:
                current_tags.append(new_tag)
                self.save_tags(current_tags)
                self.tag_combobox.config(values=current_tags)
                self.tag_var.set(new_tag)
                
    def insert_markdown_test(self):
        """插入Markdown测试内容"""
        test_content = """# 每日计划测试案例
        

## 今日重点
- [x] 完成项目设计文档
- [ ] 代码评审
- [ ] 团队会议

## 任务详情
1. **核心功能开发**
   - 用户认证模块
   - 数据可视化组件
   - `API`接口调试

2. *次要任务*
   - 回复客户邮件
   - 更新项目进度表

## 代码示例
```python
def hello_world():
    print("Hello, Markdown!")
```

## 注意事项
> 重要提示：明天上午10点有客户演示

[项目文档链接](https://example.com)"""
        
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, test_content)
        
    def preview_markdown(self):
        """预览Markdown格式内容"""
        content = self.text.get(1.0, tk.END)
        html = markdown.markdown(content)
        
        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
            f.write(f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial; margin: 20px; }}
                    h1 {{ color: #333; }}
                    ul, ol {{ margin-left: 20px; }}
                    code {{ background: #f0f0f0; padding: 2px 5px; }}
                    pre {{ background: #f0f0f0; padding: 10px; }}
                </style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """)
            temp_path = f.name
            
        # 在浏览器中打开
        webbrowser.open(f'file://{temp_path}')
    def import_to_template(self):
        content = self.text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "当前内容为空，无法创建模板")
            return
        
        template_name = simpledialog.askstring("创建模板", "输入模板名称:")
        if not template_name:
            return
        
        category = simpledialog.askstring("选择分类", "输入模板分类:", 
                 initialvalue="工作")
        if not category:
            return
        
        template_dir = os.path.join(self.template_dir, category)
        os.makedirs(template_dir, exist_ok=True)
        
        template_path = os.path.join(template_dir, f"{template_name}.md")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        messagebox.showinfo("成功", f"模板'{template_name}'已创建")
    def get_categories(self):
        """获取所有可用分类"""
        return self.load_tags() # 可以改为从配置文件读取

    def validate_category(self, category):
        """验证分类是否有效"""
        return category in self.get_categories()

    def manage_templates(self):
        """模板管理窗口"""
        # 防止重复创建窗口
        if hasattr(self, '_template_win') and self._template_win.winfo_exists():
            self._template_win.lift()
            return

        self._template_win = tk.Toplevel(self.root)
        self._template_win.title("模板库管理")
        self._template_win.geometry("800x600")
        
        # 使用统一分类管理
        categories = self.load_tags()
        current_category = self.tag_var.get() if self.validate_category(self.tag_var.get()) \
                         else self.get_categories()[0]
        self.template_category = tk.StringVar(value=current_category)
        
        # 分类选择区域
        category_frame = tk.Frame(self._template_win)
        category_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(category_frame, text="分类:").pack(side=tk.LEFT)
        
        for cat in categories:
            tk.Radiobutton(
                category_frame,
                text=cat,
                variable=self.template_category,
                value=cat,
                command=self.refresh_template_list
            ).pack(side=tk.LEFT, padx=5)
        
        # 模板列表区域
        list_frame = tk.Frame(self._template_win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        self.template_list = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        scrollbar.config(command=self.template_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_list.pack(fill=tk.BOTH, expand=True)
        
        # 添加右键菜单
        #self.template_menu = tk.Menu(self.template_list, tearoff=0)
        #self.template_menu.add_command(label="预览", command=self.preview_selected_template)
        #self.template_list.bind("<Button-3>", self.show_template_menu)
        
        # 操作按钮区域
        btn_frame = tk.Frame(self._template_win)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="导出到计划", command=self.load_template).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除模板", command=self.delete_template).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=self._template_win.destroy).pack(side=tk.LEFT, padx=5)
        
        # 初始刷新模板列表
        self.refresh_template_list()
    def refresh_template_list(self):
        """刷新模板列表，支持搜索功能"""
        if not hasattr(self, 'template_list'):
            return
            
        self.template_list.delete(0, tk.END)
        category = self.template_category.get()
        search_term = getattr(self, 'template_search', tk.StringVar()).get().lower()
        
        if not self.validate_category(category):
            category = self.get_categories()[0]
            self.template_category.set(category)
        
        template_dir = os.path.join(self.template_dir, category)
        
        if os.path.exists(template_dir):
            try:
                templates = []
                for f in os.listdir(template_dir):
                    if f.endswith('.md') and os.path.isfile(os.path.join(template_dir, f)):
                        template_name = f[:-3]
                        if not search_term or search_term in template_name.lower():
                            templates.append(template_name)
                
                for template in sorted(templates):
                    self.template_list.insert(tk.END, template)
            except OSError as e:
                print(f"加载模板错误: {e}")
        
        if self.template_list.size() == 0:
            self.template_list.insert(tk.END, "该分类下暂无模板")
            
    def show_template_preview(self, event=None):
        """显示选中模板的预览"""
        if not hasattr(self, 'template_preview'):
            return
            
        selection = self.template_list.curselection()
        if not selection:
            return
            
        template_name = self.template_list.get(selection[0])
        category = self.template_category.get()
        template_path = os.path.join(self.template_dir, category, f"{template_name}.md")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # 限制预览长度
                self.template_preview.delete(1.0, tk.END)
                self.template_preview.insert(tk.END, content)
        except Exception as e:
            self.template_preview.delete(1.0, tk.END)
            self.template_preview.insert(tk.END, f"预览错误: {str(e)}")
            
    def preview_selected_template(self):
        """预览选中的完整模板"""
        selection = self.template_list.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模板")
            return
            
        template_name = self.template_list.get(selection[0])
        category = self.template_category.get()
        template_path = os.path.join(self.template_dir, category, f"{template_name}.md")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 创建临时HTML文件
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
                html = markdown.markdown(content)
                f.write(f"""
                <html>
                <head>
                    <title>{template_name} 模板预览</title>
                    <style>
                        body {{ font-family: Arial; margin: 20px; }}
                        h1 {{ color: #333; }}
                        ul, ol {{ margin-left: 20px; }}
                        code {{ background: #f0f0f0; padding: 2px 5px; }}
                        pre {{ background: #f0f0f0; padding: 10px; }}
                    </style>
                </head>
                <body>
                    <h1>{template_name}</h1>
                    {html}
                </body>
                </html>
                """)
                temp_path = f.name
                
            # 在浏览器中打开
            webbrowser.open(f'file://{temp_path}')
        except Exception as e:
            messagebox.showerror("错误", f"预览模板失败: {str(e)}")
    
    def save_as_template(self, content):
        """保存当前内容为模板"""
        template_name = simpledialog.askstring("新建模板", "输入模板名称:")
        if not template_name:
            return
            
        category = self.template_category.get()
        template_dir = os.path.join(self.template_dir, category)
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
            
        template_path = os.path.join(template_dir, f"{template_name}.md")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        self.refresh_template_list()
        messagebox.showinfo("成功", "模板保存成功")
    
    def load_template(self):
        """加载模板到当前编辑器"""
        selection = self.template_list.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模板")
            return
            
        template_name = self.template_list.get(selection[0])
        category = self.template_category.get()
        template_path = os.path.join(self.template_dir, category, f"{template_name}.md")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, content)
    
    def delete_template(self):
        """删除选中的模板"""
        selection = self.template_list.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模板")
            return
            
        template_name = self.template_list.get(selection[0])
        category = self.template_category.get()
        template_path = os.path.join(self.template_dir, category, f"{template_name}.md")
        
        if os.path.exists(template_path):
            os.remove(template_path)
            self.refresh_template_list()
            messagebox.showinfo("成功", "模板已删除")

def main():
    from tkinter import simpledialog
    root = tk.Tk()
    app = DailyPlanner(root)
    root.mainloop()

if __name__ == "__main__":
    main()
