#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko
import time
from typing import Optional, Tuple
from .logger import AutoTestLogger


class RemoteExecutor:
    """远程命令执行器"""
    
    def __init__(self, logger: AutoTestLogger):
        self.logger = logger
        self.ssh_client = None
        self.is_root = False
        self.root_password = None
    
    def connect(self, host: str, port: int, username: str, password: str) -> bool:
        """连接到远程服务器"""
        try:
            self.logger.step_start("Connecting to remote server for command execution")
            
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 设置连接超时
            self.ssh_client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=30
            )
            
            self.logger.info(f"Remote executor connected to {host}:{port}")
            self.logger.step_complete("Connecting to remote server for command execution")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to remote server: {str(e)}")
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            
            self.logger.info("Remote executor disconnected")
            
        except Exception as e:
            self.logger.warning(f"Error during remote executor disconnection: {str(e)}")
    
    def switch_to_root(self, root_switch_command: str, root_password: str) -> bool:
        """切换到root用户"""
        try:
            self.logger.step_start("Switching to root user")
            
            # 创建交互式会话
            channel = self.ssh_client.invoke_shell()
            time.sleep(1)
            
            # 清空初始输出
            if channel.recv_ready():
                channel.recv(1024)
            
            # 执行切换命令
            channel.send(f"{root_switch_command}\n")
            time.sleep(2)
            
            # 输入root密码
            if root_password:
                channel.send(f"{root_password}\n")
                time.sleep(2)
            
            # 检查是否成功切换
            channel.send("whoami\n")
            time.sleep(1)
            
            output = ""
            while channel.recv_ready():
                data = channel.recv(1024).decode('utf-8')
                output += data
            
            if "root" in output:
                self.logger.info("Successfully switched to root user")
                self.logger.step_complete("Switching to root user")
                self.is_root = True
                self.root_password = root_password
                channel.close()
                return True
            else:
                self.logger.error("Failed to switch to root user")
                channel.close()
                return False
                
        except Exception as e:
            self.logger.error(f"Error switching to root: {str(e)}")
            return False
    
    def execute_command(self, command: str, timeout: int = 60) -> Tuple[bool, str, str]:
        """执行远程命令"""
        try:
            if not self.ssh_client:
                self.logger.error("SSH client not connected")
                return False, "", "SSH client not connected"
            
            self.logger.info(f"Executing command: {command}")
            
            # 如果已切换到root，需要在root环境下执行
            if self.is_root:
                # 创建新的SSH会话执行命令
                stdin, stdout, stderr = self.ssh_client.exec_command(
                    command, 
                    timeout=timeout,
                    get_pty=True
                )
            else:
                stdin, stdout, stderr = self.ssh_client.exec_command(
                    command, 
                    timeout=timeout
                )
            
            # 等待命令完成
            exit_status = stdout.channel.recv_exit_status()
            stdout_content = stdout.read().decode('utf-8')
            stderr_content = stderr.read().decode('utf-8')
            
            # 记录命令输出
            self.logger.command_output(command, stdout_content)
            
            if exit_status == 0:
                self.logger.info(f"Command executed successfully")
                return True, stdout_content, stderr_content
            else:
                self.logger.error(f"Command failed with exit code {exit_status}")
                if stderr_content:
                    self.logger.error(f"Error output: {stderr_content}")
                return False, stdout_content, stderr_content
                
        except Exception as e:
            self.logger.error(f"Failed to execute command '{command}': {str(e)}")
            return False, "", str(e)
    
    def restart_service(self, restart_command: str) -> bool:
        """重启服务"""
        try:
            self.logger.step_start("Restarting service")
            
            success, stdout, stderr = self.execute_command(restart_command, timeout=120)
            
            if success:
                self.logger.info("Service restart completed successfully")
                self.logger.step_complete("Restarting service")
                return True
            else:
                self.logger.error("Service restart failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during service restart: {str(e)}")
            return False
    
    def enter_container(self, namespace: str, container_filter: str) -> bool:
        """进入容器（用于交互式操作）"""
        try:
            self.logger.step_start("Entering container")
            
            # 构建进入容器的命令
            get_pod_cmd = f"kubectl -n {namespace} get pods --no-headers | grep \"{container_filter}\" | head -n1 | awk '{{print $1}}'"
            enter_cmd = f"kubectl -n {namespace} exec -it $({get_pod_cmd}) -- sh"
            
            self.logger.info(f"Container entry command: {enter_cmd}")
            self.logger.step_complete("Entering container")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enter container: {str(e)}")
            return False
    
    def execute_in_container(self, command: str, namespace: str, container_filter: str, timeout: int = 60) -> Tuple[bool, str, str]:
        """在容器内执行命令"""
        try:
            self.logger.info(f"Executing command in container: {command}")
            
            # 构建在容器内执行命令的kubectl命令
            get_pod_cmd = f"kubectl -n {namespace} get pods --no-headers | grep \"{container_filter}\" | head -n1 | awk '{{print $1}}'"
            exec_cmd = f"kubectl -n {namespace} exec $({get_pod_cmd}) -- {command}"
            
            return self.execute_command(exec_cmd, timeout)
            
        except Exception as e:
            self.logger.error(f"Failed to execute command in container: {str(e)}")
            return False, "", str(e)
    
    def get_container_info(self, namespace: str, container_filter: str) -> Tuple[bool, str]:
        """获取容器信息"""
        try:
            self.logger.info("Getting container information")
            
            get_pods_cmd = f"kubectl -n {namespace} get pods | grep \"{container_filter}\""
            success, stdout, stderr = self.execute_command(get_pods_cmd)
            
            if success and stdout.strip():
                self.logger.info(f"Found containers: {stdout}")
                return True, stdout
            else:
                self.logger.warning(f"No containers found with filter: {container_filter}")
                return False, ""
                
        except Exception as e:
            self.logger.error(f"Failed to get container info: {str(e)}")
            return False, ""