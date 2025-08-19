#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QGroupBox,
                             QScrollArea, QFrame, QFileDialog, QSpinBox,
                             QCheckBox, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from typing import Dict, List, Tuple


class FileConfigWidget(QFrame):
    """文件配置组件"""
    
    remove_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setupUI()
    
    def setupUI(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        
        # 本地文件路径
        local_layout = QHBoxLayout()
        local_layout.addWidget(QLabel("本地文件路径:"))
        self.local_path_edit = QLineEdit()
        local_layout.addWidget(self.local_path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_local_file)
        local_layout.addWidget(browse_btn)
        layout.addLayout(local_layout)
        
        # 容器目标路径
        container_layout = QHBoxLayout()
        container_layout.addWidget(QLabel("容器目标路径:"))
        self.container_path_edit = QLineEdit()
        container_layout.addWidget(self.container_path_edit)
        layout.addLayout(container_layout)
        
        # 文件权限
        permission_layout = QHBoxLayout()
        permission_layout.addWidget(QLabel("文件权限:"))
        self.permission_edit = QLineEdit("755")
        permission_layout.addWidget(self.permission_edit)
        
        # 删除按钮
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self.remove_requested.emit)
        permission_layout.addWidget(remove_btn)
        layout.addLayout(permission_layout)
        
        self.setLayout(layout)
    
    def browse_local_file(self):
        """浏览本地文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择文件", 
            "", 
            "所有文件 (*.*)"
        )
        if file_path:
            self.local_path_edit.setText(file_path)
    
    def get_config(self) -> Dict[str, str]:
        """获取配置信息"""
        return {
            'local_path': self.local_path_edit.text().strip(),
            'container_path': self.container_path_edit.text().strip(),
            'permissions': self.permission_edit.text().strip() or '755'
        }
    
    def set_config(self, config: Dict[str, str]):
        """设置配置信息"""
        self.local_path_edit.setText(config.get('local_path', ''))
        self.container_path_edit.setText(config.get('container_path', ''))
        self.permission_edit.setText(config.get('permissions', '755'))
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        config = self.get_config()
        return bool(config['local_path'] and config['container_path'])


class FileConfigListWidget(QWidget):
    """文件配置列表组件"""
    
    def __init__(self):
        super().__init__()
        self.file_widgets: List[FileConfigWidget] = []
        self.setupUI()
        self.add_file_config()  # 默认添加一个
    
    def setupUI(self):
        """设置UI"""
        main_layout = QVBoxLayout()
        
        # 标题和添加按钮
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("文件配置信息:"))
        header_layout.addStretch()
        
        add_btn = QPushButton("添加文件")
        add_btn.clicked.connect(self.add_file_config)
        header_layout.addWidget(add_btn)
        main_layout.addLayout(header_layout)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        scroll_area.setWidget(self.scroll_widget)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def add_file_config(self):
        """添加文件配置组件"""
        widget = FileConfigWidget()
        widget.remove_requested.connect(lambda: self.remove_file_config(widget))
        
        self.file_widgets.append(widget)
        self.scroll_layout.addWidget(widget)
    
    def remove_file_config(self, widget: FileConfigWidget):
        """删除文件配置组件"""
        if len(self.file_widgets) > 1:  # 至少保留一个
            self.file_widgets.remove(widget)
            widget.setParent(None)
            widget.deleteLater()
    
    def get_file_configs(self) -> List[Dict[str, str]]:
        """获取所有文件配置"""
        configs = []
        for widget in self.file_widgets:
            if widget.is_valid():
                configs.append(widget.get_config())
        return configs
    
    def set_file_configs(self, configs: List[Dict[str, str]]):
        """设置文件配置"""
        # 清除现有配置
        for widget in self.file_widgets[:]:
            self.remove_file_config(widget)
        
        # 添加新配置
        for config in configs:
            self.add_file_config()
            self.file_widgets[-1].set_config(config)
    
    def validate_all(self) -> Tuple[bool, str]:
        """验证所有配置"""
        if not self.file_widgets:
            return False, "至少需要配置一个文件"
        
        valid_configs = self.get_file_configs()
        if not valid_configs:
            return False, "所有文件配置都无效，请检查必填项"
        
        if len(valid_configs) != len(self.file_widgets):
            return False, "部分文件配置无效，请检查必填项"
        
        return True, "文件配置验证通过"


class LogDisplayWidget(QTextEdit):
    """日志显示组件"""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.max_lines = 1000  # 最大显示行数，避免内存溢出
        self.line_count = 0
    
    def setupUI(self):
        """设置UI"""
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                color: #333;
            }
        """)
    
    def append_log(self, message: str):
        """添加日志消息"""
        # 移动光标到末尾
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        
        # 添加消息
        self.append(message)
        
        # 控制显示行数，避免内存溢出
        self.line_count += 1
        if self.line_count > self.max_lines:
            self._trim_lines()
    
    def _trim_lines(self):
        """裁剪多余行数"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        # 删除前面的行
        lines_to_remove = self.line_count - self.max_lines
        for _ in range(lines_to_remove):
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # 删除换行符
        
        self.line_count = self.max_lines
    
    def clear_log(self):
        """清空日志"""
        self.clear()
        self.line_count = 0
    
    def get_all_log(self) -> str:
        """获取所有日志内容"""
        return self.toPlainText()


class GroupBoxWidget(QGroupBox):
    """分组框组件"""
    
    def __init__(self, title: str):
        super().__init__(title)
        self.setupUI()
    
    def setupUI(self):
        """设置UI样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)


class LabeledLineEdit(QWidget):
    """带标签的输入框组件"""
    
    def __init__(self, label_text: str, placeholder: str = "", is_password: bool = False):
        super().__init__()
        self.label_text = label_text
        self.setupUI(placeholder, is_password)
    
    def setupUI(self, placeholder: str, is_password: bool):
        """设置UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(self.label_text)
        label.setMinimumWidth(120)
        layout.addWidget(label)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        if is_password:
            self.line_edit.setEchoMode(QLineEdit.Password)
        
        layout.addWidget(self.line_edit)
        self.setLayout(layout)
    
    def text(self) -> str:
        """获取文本"""
        return self.line_edit.text()
    
    def setText(self, text: str):
        """设置文本"""
        self.line_edit.setText(text)
    
    def clear(self):
        """清空文本"""
        self.line_edit.clear()


class LabeledSpinBox(QWidget):
    """带标签的数字输入框组件"""
    
    def __init__(self, label_text: str, min_value: int = 0, max_value: int = 99999, default_value: int = 0):
        super().__init__()
        self.label_text = label_text
        self.setupUI(min_value, max_value, default_value)
    
    def setupUI(self, min_value: int, max_value: int, default_value: int):
        """设置UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(self.label_text)
        label.setMinimumWidth(120)
        layout.addWidget(label)
        
        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(min_value)
        self.spin_box.setMaximum(max_value)
        self.spin_box.setValue(default_value)
        
        layout.addWidget(self.spin_box)
        layout.addStretch()
        self.setLayout(layout)
    
    def value(self) -> int:
        """获取值"""
        return self.spin_box.value()
    
    def setValue(self, value: int):
        """设置值"""
        self.spin_box.setValue(value)


# FileConfigListWidget已在上面定义，这里不需要别名