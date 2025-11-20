@echo off
chcp 65001 >nul
echo 正在打包程序为exe...
echo.

REM 检查PyInstaller是否安装
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)

REM 清理旧的构建文件
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 使用spec文件打包
pyinstaller build_exe.spec

if exist dist\歌词处理工具.exe (
    echo.
    echo ========================================
    echo 打包成功！
    echo 可执行文件位置: dist\歌词处理工具.exe
    echo ========================================
) else (
    echo.
    echo 打包失败，请检查错误信息
)

pause

