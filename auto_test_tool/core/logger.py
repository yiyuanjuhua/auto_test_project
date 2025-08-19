#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
from typing import Callable, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class AutoTestLogger(QObject):
    """自动化测试工具日志管理器"""
    
    # 定义信号，用于向GUI发送日志消息
    log_signal = pyqtSignal(str)
    
    def __init__(self, log_file_path: str = None):
        super().__init__()
        self.log_file_path = log_file_path
        self.logger = None
        self.gui_callback: Optional[Callable[[str], None]] = None
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger('AutoTestTool')
        self.logger.setLevel(logging.INFO)
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 如果指定了日志文件路径，添加文件处理器
        if self.log_file_path:
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def set_log_file(self, log_file_path: str):
        """设置日志文件路径"""
        self.log_file_path = log_file_path
        self._setup_logger()
    
    def set_gui_callback(self, callback: Callable[[str], None]):
        """设置GUI回调函数，用于向界面发送日志"""
        self.gui_callback = callback
    
    def info(self, message: str):
        """记录信息级别日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] INFO: {message}"
        
        if self.logger:
            self.logger.info(message)
        
        # 发送到GUI
        if self.gui_callback:
            self.gui_callback(formatted_msg)
        
        # 发送信号
        self.log_signal.emit(formatted_msg)
    
    def error(self, message: str):
        """记录错误级别日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] ERROR: {message}"
        
        if self.logger:
            self.logger.error(message)
        
        # 发送到GUI
        if self.gui_callback:
            self.gui_callback(formatted_msg)
        
        # 发送信号
        self.log_signal.emit(formatted_msg)
    
    def warning(self, message: str):
        """记录警告级别日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] WARNING: {message}"
        
        if self.logger:
            self.logger.warning(message)
        
        # 发送到GUI
        if self.gui_callback:
            self.gui_callback(formatted_msg)
        
        # 发送信号
        self.log_signal.emit(formatted_msg)
    
    def command_output(self, command: str, output: str):
        """记录命令执行输出"""
        message = f"Command: {command}\nOutput:\n{output}"
        self.info(message)
    
    def step_start(self, step_name: str):
        """记录步骤开始"""
        self.info(f"Starting step: {step_name}")
    
    def step_complete(self, step_name: str):
        """记录步骤完成"""
        self.info(f"Completed step: {step_name}")
    
    def save_session_log(self, save_path: str) -> bool:
        """保存当前会话日志到指定路径"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_filename = f"auto_test_{timestamp}.log"
            final_path = os.path.join(save_path, log_filename)
            
            os.makedirs(save_path, exist_ok=True)
            
            # 如果当前有日志文件，复制内容到新位置
            if self.log_file_path and os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r', encoding='utf-8') as src:
                    with open(final_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            self.info(f"Session log saved to: {final_path}")
            return True
        except Exception as e:
            self.error(f"Failed to save session log: {str(e)}")
            return False
    
    @staticmethod
    def create_temp_log_path() -> str:
        """创建临时日志文件路径"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        temp_dir = "/tmp/auto_test_tool"
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, f"auto_test_temp_{timestamp}.log")