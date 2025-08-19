#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import paramiko
import subprocess
from typing import Dict, List, Tuple
from .logger import AutoTestLogger


class FileTransferManager:
    """文件传输管理器"""
    
    def __init__(self, logger: AutoTestLogger):
        self.logger = logger
        self.ssh_client = None
        self.sftp_client = None
    
    def connect_to_server(self, host: str, port: int, username: str, password: str) -> bool:
        """连接到远程服务器"""
        try:
            self.logger.step_start("Connecting to remote server")
            
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
            
            self.sftp_client = self.ssh_client.open_sftp()
            
            self.logger.info(f"Successfully connected to {host}:{port}")
            self.logger.step_complete("Connecting to remote server")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {str(e)}")
            return False
    
    def disconnect(self):
        """断开服务器连接"""
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None
            
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            
            self.logger.info("Disconnected from remote server")
            
        except Exception as e:
            self.logger.warning(f"Error during disconnection: {str(e)}")
    
    def upload_file_to_staging(self, local_path: str, remote_staging_path: str) -> bool:
        """上传文件到远程暂存路径"""
        try:
            if not self.sftp_client:
                self.logger.error("SFTP client not connected")
                return False
            
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_staging_path)
            self._ensure_remote_directory(remote_dir)
            
            self.logger.step_start(f"Uploading file: {local_path} -> {remote_staging_path}")
            
            # 分块上传大文件，避免内存溢出
            self._upload_file_chunked(local_path, remote_staging_path)
            
            self.logger.info(f"Successfully uploaded: {os.path.basename(local_path)}")
            self.logger.step_complete(f"Uploading file: {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload file {local_path}: {str(e)}")
            return False
    
    def _upload_file_chunked(self, local_path: str, remote_path: str, chunk_size: int = 1024*1024):
        """分块上传文件"""
        with open(local_path, 'rb') as local_file:
            with self.sftp_client.open(remote_path, 'wb') as remote_file:
                while True:
                    chunk = local_file.read(chunk_size)
                    if not chunk:
                        break
                    remote_file.write(chunk)
    
    def _ensure_remote_directory(self, remote_dir: str):
        """确保远程目录存在"""
        try:
            self.sftp_client.stat(remote_dir)
        except FileNotFoundError:
            # 目录不存在，创建它
            try:
                self.sftp_client.mkdir(remote_dir)
                self.logger.info(f"Created remote directory: {remote_dir}")
            except Exception as e:
                # 可能是父目录不存在，递归创建
                parent_dir = os.path.dirname(remote_dir)
                if parent_dir != remote_dir:
                    self._ensure_remote_directory(parent_dir)
                    self.sftp_client.mkdir(remote_dir)
                    self.logger.info(f"Created remote directory: {remote_dir}")
                else:
                    raise e
    
    def copy_to_container(self, staging_path: str, container_path: str, 
                         namespace: str, container_filter: str) -> bool:
        """使用kubectl命令将文件复制到容器"""
        try:
            self.logger.step_start(f"Copying file to container: {staging_path} -> {container_path}")
            
            # 构建kubectl命令
            get_pod_cmd = f"kubectl -n {namespace} get pods --no-headers | grep \"{container_filter}\" | head -n1 | awk '{{print $1}}'"
            kubectl_cp_cmd = f"kubectl -n {namespace} cp {staging_path} $({get_pod_cmd}):{container_path}"
            
            self.logger.info(f"Executing kubectl copy command")
            self.logger.command_output("kubectl command", kubectl_cp_cmd)
            
            # 通过SSH执行kubectl命令
            stdin, stdout, stderr = self.ssh_client.exec_command(kubectl_cp_cmd)
            
            # 等待命令完成
            exit_status = stdout.channel.recv_exit_status()
            stdout_content = stdout.read().decode('utf-8')
            stderr_content = stderr.read().decode('utf-8')
            
            if exit_status == 0:
                self.logger.info(f"Successfully copied file to container")
                if stdout_content:
                    self.logger.command_output("kubectl copy stdout", stdout_content)
                self.logger.step_complete(f"Copying file to container: {staging_path}")
                return True
            else:
                self.logger.error(f"kubectl copy failed with exit code {exit_status}")
                if stderr_content:
                    self.logger.error(f"Error output: {stderr_content}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to copy file to container: {str(e)}")
            return False
    
    def set_file_permissions(self, container_path: str, permissions: str,
                           namespace: str, container_filter: str) -> bool:
        """设置容器内文件权限"""
        try:
            self.logger.step_start(f"Setting file permissions: {container_path} -> {permissions}")
            
            # 构建kubectl exec命令
            get_pod_cmd = f"kubectl -n {namespace} get pods --no-headers | grep \"{container_filter}\" | head -n1 | awk '{{print $1}}'"
            chmod_cmd = f"kubectl -n {namespace} exec -it $({get_pod_cmd}) -- chmod -R {permissions} {container_path}"
            
            self.logger.info(f"Executing chmod command")
            self.logger.command_output("chmod command", chmod_cmd)
            
            # 通过SSH执行chmod命令
            stdin, stdout, stderr = self.ssh_client.exec_command(chmod_cmd)
            
            # 等待命令完成
            exit_status = stdout.channel.recv_exit_status()
            stdout_content = stdout.read().decode('utf-8')
            stderr_content = stderr.read().decode('utf-8')
            
            if exit_status == 0:
                self.logger.info(f"Successfully set file permissions to {permissions}")
                if stdout_content:
                    self.logger.command_output("chmod stdout", stdout_content)
                self.logger.step_complete(f"Setting file permissions: {container_path}")
                return True
            else:
                self.logger.error(f"chmod failed with exit code {exit_status}")
                if stderr_content:
                    self.logger.error(f"Error output: {stderr_content}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set file permissions: {str(e)}")
            return False
    
    def batch_upload_files(self, file_configs: List[Dict[str, str]], 
                          staging_base_path: str, namespace: str, 
                          container_filter: str) -> bool:
        """批量上传文件到容器"""
        try:
            self.logger.info(f"Starting batch upload of {len(file_configs)} files")
            
            for i, config in enumerate(file_configs, 1):
                local_path = config['local_path']
                container_path = config['container_path']
                permissions = config['permissions']
                
                self.logger.info(f"Processing file {i}/{len(file_configs)}: {os.path.basename(local_path)}")
                
                # 生成暂存路径
                filename = os.path.basename(local_path)
                staging_path = os.path.join(staging_base_path, filename)
                
                # 1. 上传到暂存路径
                if not self.upload_file_to_staging(local_path, staging_path):
                    return False
                
                # 2. 复制到容器
                if not self.copy_to_container(staging_path, container_path, namespace, container_filter):
                    return False
                
                # 3. 设置权限
                if not self.set_file_permissions(container_path, permissions, namespace, container_filter):
                    return False
            
            self.logger.info("All files uploaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Batch upload failed: {str(e)}")
            return False