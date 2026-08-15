#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class PowerMenu(QWidget):
    def __init__(self):
        super().__init__()
        # Set flags for a floating, borderless, always-on-top window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("PowerMenu")
        self.setFixedSize(400, 100)
        
        # Simulating an island/bubble effect by adjusting border radius and padding
        self.setStyleSheet("""
            QWidget#PowerMenu { 
                background-color: #1d2021; 
                border: 1px solid #767b7e; 
                border-top-left-radius: 12px; 
                border-top-right-radius: 12px; 
                border-bottom-left-radius: 0px; 
                border-bottom-right-radius: 0px;
                padding-bottom: 10px;
            }
        """)
        
        layout = QHBoxLayout(self)
        actions = [
            ("󰐥", "systemctl poweroff"),
            ("󰑐", "systemctl reboot"),
            ("󰤄", "systemctl suspend"),
            ("󰈆", "hyprshutdown --vt 2")
        ]
        
        # Colors for the icons (rgba format)
        colors = [
            "rgba(251, 73, 52, 1.0)",  # #fb4934
            "rgba(254, 128, 25, 1.0)", # #fe8019
            "rgba(250, 189, 47, 1.0)", # #fabd2f
            "rgba(131, 165, 152, 1.0)" # #83a598
        ]
        
        for i, (icon, cmd) in enumerate(actions):
            btn = QPushButton(icon)
            btn.setFixedSize(70, 70)
            btn.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: rgba(29, 32, 33, 0.6); 
                    border: 1px solid rgba(118, 123, 126, 1.0); 
                    color: {colors[i]}; 
                    font-family: 'JetBrains Mono'; 
                    font-size: 30px; 
                    border-radius: 4px; 
                }}
                QPushButton:hover {{ 
                    background-color: rgba(34, 34, 34, 1.0); 
                    border-color: {colors[i]}; 
                }}
            """)
            btn.clicked.connect(lambda chk, c=cmd: self.execute_and_close(c))
            layout.addWidget(btn)

    def execute_and_close(self, cmd):
        os.system(cmd)
        self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PowerMenu()
    window.show()
    sys.exit(app.exec())
