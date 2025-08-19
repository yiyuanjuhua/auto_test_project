#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtCore import pyqtSignal  
from typing import Dict

class MonitorWindow(QMainWindow):
    back_to_config = pyqtSignal()
    
    def __init__(self, config_data: Dict):
        super().__init__()
        self.config_data = config_data
        print("MonitorWindow initialized")

