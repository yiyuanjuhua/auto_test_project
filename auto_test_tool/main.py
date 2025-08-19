#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动化测试工具
用于自动上传文件到测试环境并触发自动化测试

作者: AutoTestTool
版本: 1.0.0
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QStackedWidget
from PyQt5.QtCore import Qt
from typing import Dict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.config_window import ConfigWindow
from ui.monitor_window import MonitorWindow


class AutoTestToolApp:
    """自动化测试工具主应用"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_app()
        
        # 窗口组件
        self.stacked_widget = QStackedWidget()
        self.config_window = None
        self.monitor_window = None
        
        self.setup_windows()
    
    def setup_app(self):
        """设置应用程序"""
        self.app.setApplicationName("AutoTestTool")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("AutoTestTool")
        
        # 设置应用程序样式
        self.app.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
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
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
            }
            QPushButton:hover {
                background-color: #e9e9e9;
            }
            QPushButton:pressed {
                background-color: #d4edda;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
    
    def setup_windows(self):
        """设置窗口"""
        # 创建配置窗口
        self.config_window = ConfigWindow()
        self.config_window.config_completed.connect(self.on_config_completed)
        
        # 将配置窗口添加到堆栈
        self.stacked_widget.addWidget(self.config_window)
        self.stacked_widget.setCurrentWidget(self.config_window)
        
        # 设置主窗口属性
        self.stacked_widget.setWindowTitle("自动化测试工具")
        self.stacked_widget.setGeometry(100, 100, 800, 600)
    
    def on_config_completed(self, config_data: Dict):
        """配置完成处理"""
        try:
            # 创建监控窗口
            self.monitor_window = MonitorWindow(config_data)
            self.monitor_window.back_to_config.connect(self.on_back_to_config)
            
            # 切换到监控窗口
            self.stacked_widget.addWidget(self.monitor_window)
            self.stacked_widget.setCurrentWidget(self.monitor_window)
            
        except Exception as e:
            QMessageBox.critical(
                self.config_window, 
                "错误", 
                f"启动监控窗口失败: {str(e)}"
            )
    
    def on_back_to_config(self):
        """返回配置页面"""
        try:
            # 移除监控窗口
            if self.monitor_window:
                self.stacked_widget.removeWidget(self.monitor_window)
                self.monitor_window.deleteLater()
                self.monitor_window = None
            
            # 切换到配置窗口
            self.stacked_widget.setCurrentWidget(self.config_window)
            
        except Exception as e:
            QMessageBox.critical(
                None, 
                "错误", 
                f"返回配置页面失败: {str(e)}"
            )
    
    def run(self):
        """运行应用程序"""
        try:
            self.stacked_widget.show()
            return self.app.exec_()
        except Exception as e:
            QMessageBox.critical(
                None, 
                "致命错误", 
                f"应用程序运行失败: {str(e)}"
            )
            return 1


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import PyQt5
        import paramiko
        return True
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Please install required packages:")
        print("pip install PyQt5 paramiko")
        return False


def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 检查操作系统
    if not sys.platform.startswith('linux'):
        print("Warning: This tool is designed for Linux systems")
        print("Some features may not work properly on other platforms")
    
    try:
        # 创建并运行应用
        app = AutoTestToolApp()
        return app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())