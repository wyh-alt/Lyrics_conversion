# 歌词文本处理工具

一个用于将 karaoke.add(...) 格式歌词文件转换为纯文本格式的 Python 工具。

## 功能特性

- ✅ 支持单个或多个歌词文件处理
- ✅ 支持文件夹批量处理
- ✅ 自动去除中括号 `[]`
- ✅ 可选择性保留歌名和歌手信息
- ✅ 支持多行或单行输出格式
- ✅ 图形化界面，支持拖拽操作
- ✅ 实时进度显示
- ✅ 支持多种编码格式（UTF-8/GBK）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 图形界面

运行主程序：

```bash
python main.py
```

界面操作：
1. 选择或拖拽歌词文件/文件夹到"歌词文件/目录"输入框
2. 选择或拖拽输出目录到"导出目录"输入框
3. 选择处理选项：
   - ☑ 保留歌名/歌手：在输出文件开头添加歌名和歌手信息
   - ☑ 单行歌词输出：将所有歌词合并为一行（空格分隔）
4. 点击"开始处理"按钮
5. 等待处理完成，查看结果通知

### 命令行使用（可选）

也可以直接使用 `lyric_processor.py` 模块：

```python
from lyric_processor import LyricProcessor

processor = LyricProcessor()
processor.process_file(
    input_path='input.txt',
    output_path='output.txt',
    include_header=True,
    single_line=False
)
```

## 输入格式示例

```
karaoke := CreateKaraokeObject;
karaoke.rows := 2;
karaoke.clear;

karaoke.songname := '有你在 (《Whatever》官方中文版)';
karaoke.singer := '赵露思';

karaoke.add('00:01.148', '00:03.906', '[Baby ][you ][are ][my ][light]', '594,467,384,642,671');
karaoke.add('00:04.349', '00:07.628', '[你][点][亮][我][的][爱]', '309,379,581,398,777,835');
```

## 输出格式示例

### 多行输出（保留歌名/歌手）

```
# 有你在 (《Whatever》官方中文版) - 赵露思
Baby you are my light
你点亮我的爱
```

### 单行输出（保留歌名/歌手）

```
# 有你在 (《Whatever》官方中文版) - 赵露思 Baby you are my light 你点亮我的爱
```

### 多行输出（不保留歌名/歌手）

```
Baby you are my light
你点亮我的爱
```

## 文件说明

- `main.py` - 主程序入口，包含 GUI 界面
- `lyric_processor.py` - 核心处理逻辑
- `requirements.txt` - Python 依赖包列表
- `README.md` - 项目说明文档

## 技术栈

- Python 3.7+
- PyQt6 - 图形界面框架

## 打包为可执行文件

### Windows平台

1. 安装PyInstaller：
```bash
pip install pyinstaller
```

2. 运行打包脚本：
```bash
build.bat
```

或者手动打包：
```bash
pyinstaller build_exe.spec
```

打包完成后，可执行文件位于 `dist/歌词处理工具.exe`，可以在任意Windows平台直接运行。

## 注意事项

- 输出文件默认使用 UTF-8 编码
- 输出文件名保留原文件名，统一使用 .txt 扩展名
- 如果输出目录不存在，程序会自动创建
- 支持日文、韩文、中文等多种字符编码

## 许可证

MIT License

