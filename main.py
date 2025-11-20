"""
歌词文本处理工具 - 主程序
使用 PyQt6 构建图形界面
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QCheckBox, QProgressBar, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from lyric_processor import batch_process


class DropLineEdit(QLineEdit):
    """支持拖拽的文本框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            self.setText(files[0])


class ProcessThread(QThread):
    """处理线程"""
    
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(int, int)  # success_count, total_count
    error = pyqtSignal(str)
    
    def __init__(self, input_path, output_dir, include_header, single_line, encoding):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.include_header = include_header
        self.single_line = single_line
        self.encoding = encoding
    
    def run(self):
        try:
            def progress_callback(current, total):
                self.progress.emit(current, total)
            
            success_count, total_count = batch_process(
                self.input_path,
                self.output_dir,
                self.include_header,
                self.single_line,
                self.encoding,
                progress_callback
            )
            self.finished.emit(success_count, total_count)
        except Exception as e:
            self.error.emit(str(e))


class LyricProcessorGUI(QMainWindow):
    """歌词处理工具主窗口"""
    
    def __init__(self):
        super().__init__()
        self.process_thread = None
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('歌词文本处理工具')
        self.setGeometry(100, 100, 600, 250)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 设置紧凑间距
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        central_widget.setLayout(main_layout)
        
        # 输入文件/目录路径
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        input_label = QLabel('歌词文件/目录:')
        input_label.setMinimumWidth(90)
        input_layout.addWidget(input_label)
        self.input_path_edit = DropLineEdit()
        self.input_path_edit.setPlaceholderText('拖拽文件或文件夹到这里，或点击浏览...')
        input_layout.addWidget(self.input_path_edit)
        self.input_browse_btn = QPushButton('浏览')
        self.input_browse_btn.setMinimumWidth(60)
        self.input_browse_btn.clicked.connect(self.browse_input)
        input_layout.addWidget(self.input_browse_btn)
        main_layout.addLayout(input_layout)
        
        # 输出目录路径
        output_layout = QHBoxLayout()
        output_layout.setSpacing(5)
        output_label = QLabel('导出目录:')
        output_label.setMinimumWidth(90)
        output_layout.addWidget(output_label)
        self.output_path_edit = DropLineEdit()
        self.output_path_edit.setPlaceholderText('拖拽输出目录到这里，或点击浏览...')
        output_layout.addWidget(self.output_path_edit)
        self.output_browse_btn = QPushButton('浏览')
        self.output_browse_btn.setMinimumWidth(60)
        self.output_browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_browse_btn)
        main_layout.addLayout(output_layout)
        
        # 选项复选框 - 水平排列
        options_layout = QHBoxLayout()
        options_layout.setSpacing(15)
        self.include_header_check = QCheckBox('保留歌名/歌手')
        self.include_header_check.setChecked(True)
        options_layout.addWidget(self.include_header_check)
        
        self.single_line_check = QCheckBox('单行歌词输出')
        self.single_line_check.setChecked(False)
        options_layout.addWidget(self.single_line_check)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)
        
        # 开始按钮和进度条
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        self.start_btn = QPushButton('开始处理')
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)
        main_layout.addLayout(button_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(20)
        main_layout.addWidget(self.progress_bar)
    
    def browse_input(self):
        """浏览输入文件或目录"""
        # 先尝试选择文件
        path, _ = QFileDialog.getOpenFileName(
            self, '选择歌词文件或文件夹', '', '文本文件 (*.txt);;所有文件 (*.*)'
        )
        if not path:
            # 如果取消文件选择，尝试选择目录
            path = QFileDialog.getExistingDirectory(self, '选择歌词文件夹')
        if path:
            self.input_path_edit.setText(path)
    
    def browse_output(self):
        """浏览输出目录"""
        path = QFileDialog.getExistingDirectory(self, '选择导出目录')
        if path:
            self.output_path_edit.setText(path)
    
    def start_processing(self):
        """开始处理"""
        input_path = self.input_path_edit.text().strip()
        output_dir = self.output_path_edit.text().strip()
        
        # 验证输入
        if not input_path:
            QMessageBox.warning(self, '警告', '请选择输入文件或目录！')
            return
        
        if not os.path.exists(input_path):
            QMessageBox.warning(self, '警告', '输入路径不存在！')
            return
        
        if not output_dir:
            QMessageBox.warning(self, '警告', '请选择输出目录！')
            return
        
        # 禁用开始按钮
        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # 创建并启动处理线程
        self.process_thread = ProcessThread(
            input_path,
            output_dir,
            self.include_header_check.isChecked(),
            self.single_line_check.isChecked(),
            'utf-8'
        )
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.finished.connect(self.on_finished)
        self.process_thread.error.connect(self.on_error)
        self.process_thread.start()
    
    def update_progress(self, current, total):
        """更新进度条"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
    
    def on_finished(self, success_count, total_count):
        """处理完成"""
        self.start_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        
        QMessageBox.information(
            self, 
            '处理完成', 
            f'成功处理 {success_count}/{total_count} 个文件！\n'
            f'输出目录: {self.output_path_edit.text()}'
        )
    
    def on_error(self, error_msg):
        """处理错误"""
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, '错误', f'处理过程中发生错误:\n{error_msg}')


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = LyricProcessorGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

