# 项目 README 说明
## 项目名称
四种类别 D{0-1}KP 实例求解系统

## 环境依赖
本项目基于 Python 开发，核心依赖库如下：
- Python 3.11+
- matplotlib >= 3.10
- ttkbootstrap >= 1.20
- numpy >= 1.26
- pandas >= 3.0
- scipy >= 1.17
- torch >= 2.0
- 其他依赖：seaborn、sympy、tqdm、pyyaml 等

## 项目结构
```
Four kinds of D{0-1}KP instances/
├─ main.py              # 项目主入口文件
├─ main_window.py       # 主界面逻辑
├─ algorithms/          # 算法模块
├─ experiment/          # 实验模块
├─ *.txt                # 数据文件
├─ *.csv                # 结果文件
└─ dist/
   └─ main.exe          # 打包后的可执行文件
```

## 运行方式
### 方式 1：直接运行源码
1. 安装依赖：`pip install -r requirements.txt`
2. 执行命令：`python main.py`
3. 打包后的exe文件：

### 方式 2：运行打包好的 exe 文件
1. 进入 `dist` 文件夹
2. 双击 `main.exe` 即可启动程序
3. 无需安装 Python 环境，直接运行

## 打包命令（用于重新生成 exe）
```bash
pyinstaller -F -w --hidden-import=ttkbootstrap --hidden-import=matplotlib --add-data "algorithms;algorithms" --add-data "experiment;experiment" --add-data "*.*;." main.py
```

## 打包工具
- 使用 **PyInstaller** 进行打包
- 打包命令已集成所有模块、数据文件、界面依赖
- 生成单文件 exe，便携可直接分发

## 注意事项
1. exe 文件运行时请勿删除同级数据文件
2. 首次运行可能需要短暂加载时间
3. 若运行异常，可检查数据文件是否完整
4. 打包环境：Windows 10/11，Python 3.11，Conda 虚拟环境
5. 通过网盘分享的文件：Four kinds of D{0-1}KP instances
链接: https://pan.baidu.com/s/1-igPA-M-FifMnULjR9FVyw?pwd=3p4u 提取码: 3p4u 
