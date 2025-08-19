#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import threading
from typing import Optional, Callable, Tuple
from .logger import AutoTestLogger


class TestRunner:
    """本地测试脚本执行器"""
    
    def __init__(self, logger: AutoTestLogger):
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.output_callback: Optional[Callable[[str], None]] = None
    
    def set_output_callback(self, callback: Callable[[str], None]):
        """设置实时输出回调函数"""
        self.output_callback = callback
    
    def execute_test_script(self, script_path: str, parameters: str = "") -> bool:
        """执行测试脚本"""
        try:
            self.logger.step_start("Executing local test script")
            
            # 检查脚本文件是否存在
            if not os.path.exists(script_path):
                self.logger.error(f"Test script not found: {script_path}")
                return False
            
            # 确保脚本有执行权限
            os.chmod(script_path, 0o755)
            
            # 构建完整命令
            if parameters.strip():
                command = f"{script_path} {parameters}"
            else:
                command = script_path
            
            self.logger.info(f"Executing test script: {command}")
            
            # 启动进程
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.is_running = True
            
            # 实时读取输出
            output_lines = []
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    output_lines.append(output.strip())
                    self.logger.info(f"Test Output: {output.strip()}")
                    
                    # 如果有回调函数，实时发送输出
                    if self.output_callback:
                        self.output_callback(output.strip())
            
            # 等待进程结束
            return_code = self.process.wait()
            self.is_running = False
            
            # 记录完整输出
            full_output = '\n'.join(output_lines)
            self.logger.command_output(command, full_output)
            
            if return_code == 0:
                self.logger.info("Test script executed successfully")
                self.logger.step_complete("Executing local test script")
                return True
            else:
                self.logger.error(f"Test script failed with return code: {return_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to execute test script: {str(e)}")
            self.is_running = False
            return False
    
    def execute_test_script_async(self, script_path: str, parameters: str = "", 
                                 completion_callback: Optional[Callable[[bool], None]] = None):
        """异步执行测试脚本"""
        def run_script():
            success = self.execute_test_script(script_path, parameters)
            if completion_callback:
                completion_callback(success)
        
        # 在新线程中执行脚本
        thread = threading.Thread(target=run_script)
        thread.daemon = True
        thread.start()
    
    def stop_test(self) -> bool:
        """停止正在运行的测试"""
        try:
            if self.process and self.is_running:
                self.logger.warning("Stopping test script execution")
                self.process.terminate()
                
                # 等待进程结束，如果超时则强制杀死
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Force killing test process")
                    self.process.kill()
                    self.process.wait()
                
                self.is_running = False
                self.logger.info("Test script execution stopped")
                return True
            else:
                self.logger.warning("No test script is currently running")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping test script: {str(e)}")
            return False
    
    def is_script_running(self) -> bool:
        """检查脚本是否正在运行"""
        return self.is_running and self.process and self.process.poll() is None
    
    def validate_script(self, script_path: str) -> Tuple[bool, str]:
        """验证测试脚本是否有效"""
        try:
            if not script_path:
                return False, "Script path is empty"
            
            if not os.path.exists(script_path):
                return False, f"Script file does not exist: {script_path}"
            
            if not os.path.isfile(script_path):
                return False, f"Path is not a file: {script_path}"
            
            # 检查文件是否可读
            if not os.access(script_path, os.R_OK):
                return False, f"Script file is not readable: {script_path}"
            
            # 尝试检查文件头（简单验证）
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#!'):
                        return True, "Script validation passed"
                    else:
                        return True, "Script validation passed (no shebang found, but file is readable)"
            except UnicodeDecodeError:
                # 可能是二进制文件
                return True, "Script validation passed (binary executable)"
            
        except Exception as e:
            return False, f"Script validation error: {str(e)}"