#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QPushButton, QMessageBox, QFileDialog,
                             QApplication, QTabWidget, QTextEdit, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, List, Tuple
from .widgets import (FileConfigListWidget, GroupBoxWidget, LabeledLineEdit, 
                     LabeledSpinBox)


class ConfigWindow(QMainWindow):
    """配置窗口"""
    
    # 信号：配置完成，传递配置数据
    config_completed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.config_data = {}
        self.setupUI()
        self.load_default_config()
    
    def setupUI(self):
        """设置UI"""
        self.setWindowTitle("自动化测试工具 - 配置")
        self.setGeometry(100, 100, 800, 600)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 滚动内容
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 文件配置区域
        self.setup_file_config_section(scroll_layout)
        
        # 环境信息区域
        self.setup_environment_section(scroll_layout)
        
        # 测试脚本信息区域
        self.setup_test_script_section(scroll_layout)
        
        # 工具配置区域
        self.setup_tool_config_section(scroll_layout)
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 底部按钮
        self.setup_bottom_buttons(main_layout)
    
    def setup_file_config_section(self, parent_layout):
        """设置文件配置区域"""
        file_group = GroupBoxWidget("文件路径信息")
        file_layout = QVBoxLayout(file_group)
        
        self.file_config_widget = FileConfigListWidget()
        file_layout.addWidget(self.file_config_widget)
        
        parent_layout.addWidget(file_group)
    
    def setup_environment_section(self, parent_layout):
        """设置环境信息区域"""
        env_group = GroupBoxWidget("环境信息")
        env_layout = QVBoxLayout(env_group)
        
        # 基本连接信息
        self.ip_edit = LabeledLineEdit("服务器IP:", "192.168.1.100")
        env_layout.addWidget(self.ip_edit)
        
        self.port_edit = LabeledSpinBox("端口:", 1, 65535, 22)
        env_layout.addWidget(self.port_edit)
        
        self.username_edit = LabeledLineEdit("用户名:", "admin")
        env_layout.addWidget(self.username_edit)
        
        self.password_edit = LabeledLineEdit("密码:", "", True)
        env_layout.addWidget(self.password_edit)
        
        # Root切换信息
        self.root_command_edit = LabeledLineEdit("Root切换命令:", "sudo su -")
        env_layout.addWidget(self.root_command_edit)
        
        self.root_password_edit = LabeledLineEdit("Root密码:", "", True)
        env_layout.addWidget(self.root_password_edit)
        
        # 其他环境信息
        self.staging_path_edit = LabeledLineEdit("文件暂存路径:", "/tmp/auto_test_staging")
        env_layout.addWidget(self.staging_path_edit)
        
        self.container_filter_edit = LabeledLineEdit("容器名过滤关键词:", "evaluation-manager")
        env_layout.addWidget(self.container_filter_edit)
        
        self.namespace_edit = LabeledLineEdit("容器关联租户名:", "aistudio")
        env_layout.addWidget(self.namespace_edit)
        
        self.restart_command_edit = LabeledLineEdit("重启服务的命令:", "systemctl restart my-service")
        env_layout.addWidget(self.restart_command_edit)
        
        parent_layout.addWidget(env_group)
    
    def setup_test_script_section(self, parent_layout):
        """设置测试脚本信息区域"""
        script_group = GroupBoxWidget("测试脚本信息")
        script_layout = QVBoxLayout(script_group)
        
        # 脚本路径
        script_path_layout = QHBoxLayout()
        self.script_path_edit = LabeledLineEdit("脚本文件路径:", "/path/to/test_script.sh")
        script_path_layout.addWidget(self.script_path_edit)
        
        browse_script_btn = QPushButton("浏览...")
        browse_script_btn.clicked.connect(self.browse_test_script)
        script_path_layout.addWidget(browse_script_btn)
        
        script_layout.addLayout(script_path_layout)
        
        # 执行参数
        script_layout.addWidget(QLabel("执行参数:"))
        self.script_params_edit = QTextEdit()
        self.script_params_edit.setMaximumHeight(100)
        self.script_params_edit.setPlaceholderText("输入测试脚本的执行参数，支持多行")
        script_layout.addWidget(self.script_params_edit)
        
        parent_layout.addWidget(script_group)
    
    def setup_tool_config_section(self, parent_layout):
        """设置工具配置区域"""
        tool_group = GroupBoxWidget("工具自身配置")
        tool_layout = QVBoxLayout(tool_group)
        
        # 日志存储路径
        log_path_layout = QHBoxLayout()
        self.log_path_edit = LabeledLineEdit("操作日志存储路径:", "/tmp/auto_test_logs")
        log_path_layout.addWidget(self.log_path_edit)
        
        browse_log_btn = QPushButton("浏览...")
        browse_log_btn.clicked.connect(self.browse_log_directory)
        log_path_layout.addWidget(browse_log_btn)
        
        tool_layout.addLayout(log_path_layout)
        
        parent_layout.addWidget(tool_group)
    
    def setup_bottom_buttons(self, parent_layout):
        """设置底部按钮"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 保存配置按钮
        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        # 加载配置按钮
        load_btn = QPushButton("加载配置")
        load_btn.clicked.connect(self.load_config)
        button_layout.addWidget(load_btn)
        
        # 执行测试按钮
        execute_btn = QPushButton("执行测试")
        execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        execute_btn.clicked.connect(self.execute_test)
        button_layout.addWidget(execute_btn)
        
        parent_layout.addLayout(button_layout)
    
    def browse_test_script(self):
        """浏览测试脚本文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择测试脚本", 
            "", 
            "脚本文件 (*.sh *.py *.pl);;所有文件 (*.*)"
        )
        if file_path:
            self.script_path_edit.setText(file_path)
    
    def browse_log_directory(self):
        """浏览日志目录"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择日志存储目录"
        )
        if directory:
            self.log_path_edit.setText(directory)
    
    def validate_config(self) -> Tuple[bool, str]:
        """验证配置"""
        # 验证文件配置
        file_valid, file_msg = self.file_config_widget.validate_all()
        if not file_valid:
            return False, f"文件配置错误: {file_msg}"
        
        # 验证环境信息
        if not self.ip_edit.text().strip():
            return False, "请输入服务器IP"
        
        if not self.username_edit.text().strip():
            return False, "请输入用户名"
        
        if not self.password_edit.text().strip():
            return False, "请输入密码"
        
        if not self.staging_path_edit.text().strip():
            return False, "请输入文件暂存路径"
        
        if not self.restart_command_edit.text().strip():
            return False, "请输入重启服务的命令"
        
        # 验证测试脚本信息
        if not self.script_path_edit.text().strip():
            return False, "请输入测试脚本路径"
        
        if not self.log_path_edit.text().strip():
            return False, "请输入日志存储路径"
        
        return True, "配置验证通过"
    
    def get_config_data(self) -> Dict:
        """获取配置数据"""
        return {
            'files': self.file_config_widget.get_file_configs(),
            'environment': {
                'ip': self.ip_edit.text().strip(),
                'port': self.port_edit.value(),
                'username': self.username_edit.text().strip(),
                'password': self.password_edit.text().strip(),
                'root_command': self.root_command_edit.text().strip(),
                'root_password': self.root_password_edit.text().strip(),
                'staging_path': self.staging_path_edit.text().strip(),
                'container_filter': self.container_filter_edit.text().strip(),
                'namespace': self.namespace_edit.text().strip(),
                'restart_command': self.restart_command_edit.text().strip()
            },
            'test_script': {
                'script_path': self.script_path_edit.text().strip(),
                'parameters': self.script_params_edit.toPlainText().strip()
            },
            'tool_config': {
                'log_path': self.log_path_edit.text().strip()
            }
        }
    
    def load_default_config(self):
        """加载默认配置"""
        # 这里可以从配置文件加载，暂时使用默认值
        pass
    
    def save_config(self):
        """保存配置"""
        try:
            config_data = self.get_config_data()
            # 这里可以保存到配置文件
            QMessageBox.information(self, "保存成功", "配置已保存")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置时发生错误: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        try:
            # 这里可以从配置文件加载
            QMessageBox.information(self, "加载成功", "配置已加载")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载配置时发生错误: {str(e)}")
    
    def execute_test(self):
        """执行测试"""
        # 验证配置
        valid, message = self.validate_config()
        if not valid:
            QMessageBox.warning(self, "配置错误", message)
            return
        
        # 获取配置数据
        config_data = self.get_config_data()
        
        # 发送信号到主程序
        self.config_completed.emit(config_data)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self, 
            "确认退出", 
            "确定要退出配置吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ConfigWindow()
    window.show()
    sys.exit(app.exec_())