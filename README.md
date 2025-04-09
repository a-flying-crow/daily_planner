# daily_planner
记录每天生活。领导时不时来问我工作，用这个保存下工作痕迹

# 每日计划管理器

## 功能特性
- 按日期记录每日工作计划
- 每天上午9点自动提醒填写计划
- 支持提前多天编写计划
- 自动保存计划到本地

## 安装步骤

1. 安装Python 3.x (推荐3.8+)
2. 安装依赖库：
   ```powershell
   pip install plyer
   ```
3. 下载本项目文件

## 使用方法

1. 直接运行：
   ```powershell
   python daily_planner.py
   ```
   或双击`start_planner.bat`

2. 设置开机自启动：
   - 按`Win+R`打开运行对话框
   - 输入`shell:startup`回车
   - 将`start_planner.bat`的快捷方式复制到此文件夹

## 程序界面说明
- 顶部日期选择框：选择要查看/编辑的日期
- 中间文本框：编辑当日计划内容
- 保存按钮：保存当前日期的计划

## 注意事项
- 程序会在每天上午9点弹出提醒
- 所有计划数据保存在用户目录下的`DailyPlannerData`文件夹
