import sys
import os
import time
import threading
import numpy as np
import pytesseract
import mss
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
    QFileDialog, QDoubleSpinBox, QGroupBox, QGridLayout, QMessageBox, QFrame, QComboBox, QDialog, QListWidget, QLineEdit, QSystemTrayIcon, QStyle, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
import winsound
import tkinter as tk
import csv
from datetime import datetime
from datetime import timedelta
import re
import pandas as pd
# เตรียม import สำหรับตัดคำไทย
try:
    from pythainlp.tokenize import word_tokenize
except ImportError:
    word_tokenize = None

class AreaSelector:
    def __init__(self, delay=5):
        self.region = None
        self.delay = delay

    def select_area(self):
        print(f"\nกรุณาสลับไปยังหน้าต่างที่ต้องการเลือกพื้นที่ตรวจจับ (เช่น Twitch chat)")
        for i in range(self.delay, 0, -1):
            print(f"เริ่มเลือกพื้นที่ในอีก {i} วินาที...")
            time.sleep(1)
        print("\nโปรดลากเมาส์เลือกพื้นที่ที่ต้องการตรวจจับบนหน้าจอ")
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)
        root.title('ลากเมาส์เลือกพื้นที่ที่ต้องการตรวจจับ')
        start_x = start_y = end_x = end_y = 0
        rect = None
        def on_mouse_down(event):
            nonlocal start_x, start_y
            start_x, start_y = event.x, event.y
        def on_mouse_drag(event):
            nonlocal rect
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(start_x, start_y, event.x, event.y, outline='red', width=2)
        def on_mouse_up(event):
            nonlocal end_x, end_y
            end_x, end_y = event.x, event.y
            root.quit()
        canvas = tk.Canvas(root, cursor="cross")
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        root.mainloop()
        root.destroy()
        x1, y1 = min(start_x, end_x), min(start_y, end_y)
        x2, y2 = max(start_x, end_x), max(start_y, end_y)
        self.region = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        return self.region

class BadWordManagerDialog(QDialog):
    def __init__(self, badwords_file, parent=None):
        super().__init__(parent)
        self.setWindowTitle('จัดการคำหยาบ')
        self.badwords_file = badwords_file
        self.setMinimumWidth(400)
        self.list_widget = QListWidget()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText('เพิ่มคำหยาบใหม่...')
        add_btn = QPushButton('เพิ่ม')
        del_btn = QPushButton('ลบที่เลือก')
        save_btn = QPushButton('บันทึก')
        close_btn = QPushButton('ปิด')
        add_btn.clicked.connect(self.add_word)
        del_btn.clicked.connect(self.delete_selected)
        save_btn.clicked.connect(self.save_words)
        close_btn.clicked.connect(self.close)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout = QVBoxLayout()
        layout.addWidget(QLabel('คำหยาบทั้งหมด:'))
        layout.addWidget(self.list_widget)
        layout.addWidget(self.input_line)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.load_words()
    def load_words(self):
        self.list_widget.clear()
        try:
            with open(self.badwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        self.list_widget.addItem(word)
        except FileNotFoundError:
            pass
    def add_word(self):
        word = self.input_line.text().strip()
        if word and not self.list_widget.findItems(word, Qt.MatchExactly):
            self.list_widget.addItem(word)
            self.input_line.clear()
    def delete_selected(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
    def save_words(self):
        words = [self.list_widget.item(i).text().strip() for i in range(self.list_widget.count()) if self.list_widget.item(i).text().strip()]
        try:
            with open(self.badwords_file, 'w', encoding='utf-8') as f:
                for w in words:
                    f.write(w + '\n')
            QMessageBox.information(self, 'บันทึกสำเร็จ', 'บันทึกคำหยาบเรียบร้อยแล้ว')
        except Exception as e:
            QMessageBox.warning(self, 'ผิดพลาด', f'ไม่สามารถบันทึกได้: {e}')

class DashboardWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Dashboard สถิติ - Bad Word Detector')
        self.setGeometry(300, 300, 600, 400)
        self.setFont(QFont('Tahoma', 10))
        self.init_ui()
        
        # Timer สำหรับอัพเดทข้อมูล
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # อัพเดททุก 1 วินาที

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # หัวข้อ
        title_label = QLabel('📊 Dashboard สถิติการตรวจจับ')
        title_label.setStyleSheet('font-size: 20px; font-weight: bold; color: #2196F3; text-align: center;')
        layout.addWidget(title_label)

        # สถิติการตรวจจับ
        stats_group = QGroupBox('📈 สถิติการทำงาน')
        stats_layout = QGridLayout()
        
        # จำนวนคำหยาบที่พบวันนี้
        detection_count_label = QLabel('จำนวนคำหยาบที่พบวันนี้:')
        detection_count_label.setStyleSheet('font-weight: bold; color: #d32f2f; font-size: 14px;')
        self.detection_count_label = QLabel('0')
        self.detection_count_label.setStyleSheet('font-size: 24px; font-weight: bold; color: #d32f2f;')
        stats_layout.addWidget(detection_count_label, 0, 0)
        stats_layout.addWidget(self.detection_count_label, 0, 1)
        
        # จำนวน Screenshot
        screenshot_count_label = QLabel('จำนวน Screenshot:')
        screenshot_count_label.setStyleSheet('font-weight: bold; color: #2196F3; font-size: 14px;')
        self.screenshot_count_label = QLabel('0')
        self.screenshot_count_label.setStyleSheet('font-size: 24px; font-weight: bold; color: #2196F3;')
        stats_layout.addWidget(screenshot_count_label, 1, 0)
        stats_layout.addWidget(self.screenshot_count_label, 1, 1)
        
        # เวลาการทำงาน
        working_time_label = QLabel('เวลาการทำงาน:')
        working_time_label.setStyleSheet('font-weight: bold; color: #4CAF50; font-size: 14px;')
        self.working_time_label = QLabel('00:00:00')
        self.working_time_label.setStyleSheet('font-size: 24px; font-weight: bold; color: #4CAF50;')
        stats_layout.addWidget(working_time_label, 2, 0)
        stats_layout.addWidget(self.working_time_label, 2, 1)
        
        # ความถี่การตรวจจับ
        detection_freq_label = QLabel('ความถี่การตรวจจับ:')
        detection_freq_label.setStyleSheet('font-weight: bold; color: #FF9800; font-size: 14px;')
        self.detection_freq_label = QLabel('0 ครั้ง/นาที')
        self.detection_freq_label.setStyleSheet('font-size: 24px; font-weight: bold; color: #FF9800;')
        stats_layout.addWidget(detection_freq_label, 3, 0)
        stats_layout.addWidget(self.detection_freq_label, 3, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # ปุ่มปิด
        close_btn = QPushButton('ปิด Dashboard')
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet('background-color: #FF5722; font-size: 14px; padding: 10px;')
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def update_stats(self):
        """อัพเดทสถิติจากหน้าหลัก"""
        if self.parent:
            # อัพเดทจำนวนคำหยาบที่พบวันนี้
            self.detection_count_label.setText(str(self.parent.detection_count))
            
            # อัพเดทจำนวน Screenshot
            self.screenshot_count_label.setText(str(self.parent.screenshot_count))
            
            # อัพเดทเวลาการทำงาน
            if self.parent.start_time:
                elapsed = datetime.now() - self.parent.start_time
                hours = elapsed.seconds // 3600
                minutes = (elapsed.seconds % 3600) // 60
                seconds = elapsed.seconds % 60
                self.working_time_label.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')
            
            # อัพเดทความถี่การตรวจจับ (คำนวณจาก 1 นาทีล่าสุด)
            now = datetime.now()
            recent_detections = [t for t in self.parent.detection_times if (now - t).seconds <= 60]
            freq = len(recent_detections)
            self.detection_freq_label.setText(f'{freq} ครั้ง/นาที')

class BadWordDetectorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bad Word Detector (PyQt5) - Enhanced Version')
        self.setGeometry(200, 200, 700, 600)
        self.setFont(QFont('Tahoma', 10))
        self.sct = mss.mss()
        self.region = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.detect_badwords)
        self.detecting = False
        self.bad_words = self.load_all_bad_words()
        self.sound_file = None
        self.detect_interval = 1
        
        # เพิ่มตัวแปรสำหรับการตรวจสอบข้อความซ้ำ
        self.last_detected_text = ''
        self.last_text_hash = None
        self.processed_count = 0
        self.skipped_count = 0
        
        # เพิ่มตัวแปรสำหรับ Dashboard
        self.detection_count = 0
        self.screenshot_count = 0
        self.start_time = None
        self.detection_times = []  # เก็บเวลาที่เจอคำหยาบ
        
        # กำหนด log_dir ก่อน
        self.log_dir = "logs"
        
        # สร้างโฟลเดอร์ screenshots
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.tray_icon = QSystemTrayIcon(self)
        style = self.style()
        icon = style.standardIcon(QStyle.SP_MessageBoxWarning)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setVisible(True)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QGroupBox {
                border: 2px solid #4CAF50;
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QLabel {
                color: #333333;
            }
            QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QCheckBox {
                color: #333333;
                font-weight: bold;
            }
        """)
        self.logs = []
        self.current_log = None  # เพิ่มตัวแปรเก็บ log ของรอบปัจจุบัน
        self.last_detected_text = None  # เพิ่มตัวแปรเก็บข้อความล่าสุด
        self.last_log_time = 0
        self.log_cooldown = 5.0  # default 5 วินาที
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Status
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QHBoxLayout()
        self.status_label = QLabel('สถานะ: พร้อมใช้งาน')
        self.status_label.setStyleSheet('color: #4CAF50; font-weight: bold; font-size: 12px;')
        status_layout.addWidget(self.status_label)
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)

        # ตรวจจับคำหยาบทุกภาษา
        lang_info = QLabel('ตรวจจับคำหยาบ: ไทย + อังกฤษ')
        lang_info.setStyleSheet('font-weight: bold; color: #2196F3;')
        layout.addWidget(lang_info)

        # Badword manager button
        badword_mgr_btn = QPushButton('จัดการคำหยาบ (ไทย)')
        badword_mgr_btn.clicked.connect(lambda: self.open_badword_manager('badwords.txt'))
        badword_mgr_en_btn = QPushButton('จัดการคำหยาบ (อังกฤษ)')
        badword_mgr_en_btn.clicked.connect(lambda: self.open_badword_manager('badwords_en.txt'))
        btn_mgr_layout = QHBoxLayout()
        btn_mgr_layout.addWidget(badword_mgr_btn)
        btn_mgr_layout.addWidget(badword_mgr_en_btn)
        layout.addLayout(btn_mgr_layout)

        # Area selection
        area_group = QGroupBox('เลือกพื้นที่ตรวจจับ')
        area_layout = QVBoxLayout()
        self.select_area_btn = QPushButton('เลือกพื้นที่ตรวจจับ')
        self.select_area_btn.clicked.connect(self.select_area)
        area_layout.addWidget(self.select_area_btn)
        area_group.setLayout(area_layout)
        layout.addWidget(area_group)

        # Control buttons
        control_group = QGroupBox('ควบคุมการตรวจจับ')
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton('เริ่มตรวจจับ')
        self.stop_btn = QPushButton('หยุดตรวจจับ')
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Performance settings
        performance_group = QGroupBox('การตั้งค่าประสิทธิภาพ')
        performance_layout = QGridLayout()
        
        # Checkbox สำหรับข้ามข้อความซ้ำ
        self.skip_duplicate_checkbox = QCheckBox('ข้ามข้อความซ้ำ (ประหยัด CPU)')
        self.skip_duplicate_checkbox.setChecked(True)
        self.skip_duplicate_checkbox.setToolTip('ข้ามการประมวลผลเมื่อข้อความเหมือนเดิม')
        performance_layout.addWidget(self.skip_duplicate_checkbox, 0, 0, 1, 2)
        
        # แสดงสถานะการตรวจสอบ
        self.duplicate_status_label = QLabel('สถานะ: ตรวจสอบข้อความซ้ำ')
        self.duplicate_status_label.setStyleSheet('color: #4CAF50; font-size: 10px;')
        performance_layout.addWidget(self.duplicate_status_label, 1, 0, 1, 2)
        
        # ปุ่ม reset
        reset_btn = QPushButton('รีเซ็ตการตรวจสอบ')
        reset_btn.clicked.connect(self.reset_duplicate_check)
        reset_btn.setStyleSheet('background-color: #FF9800;')
        performance_layout.addWidget(reset_btn, 2, 0, 1, 2)
        
        # Dashboard Button
        dashboard_btn = QPushButton('📊 เปิด Dashboard')
        dashboard_btn.clicked.connect(self.open_dashboard)
        dashboard_btn.setStyleSheet('background-color: #2196F3; font-size: 14px; padding: 10px;')
        performance_layout.addWidget(dashboard_btn, 3, 0, 1, 2)
        
        # Settings
        settings_group = QGroupBox('การตั้งค่า')
        settings_layout = QGridLayout()
        settings_layout.setSpacing(15)
        
        interval_label = QLabel('ความถี่การตรวจจับ (วินาที):')
        interval_label.setStyleSheet('font-weight: bold;')
        settings_layout.addWidget(interval_label, 0, 0)
        
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setMinimum(0.1)
        self.interval_spin.setMaximum(10)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(1.0)
        self.interval_spin.valueChanged.connect(self.update_interval)
        settings_layout.addWidget(self.interval_spin, 0, 1)
        
        sound_label = QLabel('เสียงเตือน:')
        sound_label.setStyleSheet('font-weight: bold;')
        settings_layout.addWidget(sound_label, 1, 0)
        
        self.sound_btn = QPushButton('เลือกไฟล์เสียง (.wav)')
        self.sound_btn.clicked.connect(self.select_sound)
        settings_layout.addWidget(self.sound_btn, 1, 1)
        
        # --- เพิ่มตั้งค่าความถี่แคป log ---
        logcap_label = QLabel('ความถี่แคปภาพ/เก็บ log (วินาที):')
        logcap_label.setStyleSheet('font-weight: bold;')
        settings_layout.addWidget(logcap_label, 2, 0)
        self.logcap_spin = QDoubleSpinBox()
        self.logcap_spin.setMinimum(1)
        self.logcap_spin.setMaximum(60)
        self.logcap_spin.setSingleStep(1)
        self.logcap_spin.setValue(self.log_cooldown)
        self.logcap_spin.valueChanged.connect(self.update_logcap_interval)
        settings_layout.addWidget(self.logcap_spin, 2, 1)
        
        # --- เพิ่มปุ่มตั้งค่าอัตโนมัติ ---
        preset_label = QLabel('ตั้งค่าอัตโนมัติ:')
        preset_label.setStyleSheet('font-weight: bold;')
        settings_layout.addWidget(preset_label, 3, 0)
        
        preset_layout = QHBoxLayout()
        slow_chat_btn = QPushButton('แชทไหลช้า (30s)')
        medium_chat_btn = QPushButton('แชทปานกลาง (10s)')
        fast_chat_btn = QPushButton('แชทไหลเร็ว (5s)')
        very_fast_chat_btn = QPushButton('แชทไหลเร็วมาก (2s)')
        
        slow_chat_btn.clicked.connect(lambda: self.logcap_spin.setValue(30))
        medium_chat_btn.clicked.connect(lambda: self.logcap_spin.setValue(10))
        fast_chat_btn.clicked.connect(lambda: self.logcap_spin.setValue(5))
        very_fast_chat_btn.clicked.connect(lambda: self.logcap_spin.setValue(2))
        
        preset_layout.addWidget(slow_chat_btn)
        preset_layout.addWidget(medium_chat_btn)
        preset_layout.addWidget(fast_chat_btn)
        preset_layout.addWidget(very_fast_chat_btn)
        settings_layout.addLayout(preset_layout, 3, 1)
        
        # --- เพิ่มการจัดการไฟล์ ---
        file_mgmt_label = QLabel('การจัดการไฟล์:')
        file_mgmt_label.setStyleSheet('font-weight: bold;')
        settings_layout.addWidget(file_mgmt_label, 4, 0)
        
        file_mgmt_layout = QHBoxLayout()
        self.select_folder_btn = QPushButton('เลือกโฟลเดอร์บันทึก')
        self.select_folder_btn.clicked.connect(self.select_save_folder)
        self.folder_label = QLabel(f'โฟลเดอร์ปัจจุบัน: {self.log_dir}')
        self.folder_label.setStyleSheet('font-size: 10px; color: #666;')
        
        file_mgmt_layout.addWidget(self.select_folder_btn)
        file_mgmt_layout.addWidget(self.folder_label)
        settings_layout.addLayout(file_mgmt_layout, 4, 1)
        
        # ปุ่มจัดการไฟล์
        file_actions_layout = QHBoxLayout()
        self.open_folder_btn = QPushButton('เปิดโฟลเดอร์')
        self.open_folder_btn.clicked.connect(self.open_save_folder)
        self.cleanup_btn = QPushButton('ลบไฟล์เก่า (7 วัน)')
        self.cleanup_btn.clicked.connect(self.cleanup_old_files)
        
        file_actions_layout.addWidget(self.open_folder_btn)
        file_actions_layout.addWidget(self.cleanup_btn)
        settings_layout.addLayout(file_actions_layout, 5, 0, 1, 2)
        # --- จบเพิ่ม ---

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Results - แสดงเฉพาะคำหยาบที่พบ
        results_group = QGroupBox('ผลการตรวจจับ')
        results_layout = QVBoxLayout()
        
        badword_label = QLabel('คำหยาบที่พบ:')
        badword_label.setStyleSheet('font-weight: bold; color: #d32f2f;')
        results_layout.addWidget(badword_label)
        
        self.badword_text = QTextEdit()
        self.badword_text.setMaximumHeight(60)
        self.badword_text.setPlaceholderText('คำหยาบที่พบจะแสดงที่นี่...')
        results_layout.addWidget(self.badword_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        export_btn = QPushButton('Export Log (CSV)')
        export_btn.clicked.connect(self.export_log)
        layout.addWidget(export_btn)

        # --- เพิ่ม UI/UX ปรับปรุง ---
        # Dark Mode Toggle
        dark_mode_layout = QHBoxLayout()
        self.dark_mode_checkbox = QCheckBox('Dark Mode')
        self.dark_mode_checkbox.clicked.connect(self.toggle_dark_mode)
        dark_mode_layout.addWidget(self.dark_mode_checkbox)
        
        # Keyboard Shortcuts Info
        shortcuts_info = QLabel('Keyboard Shortcuts:\nCtrl+S: เริ่ม/หยุดตรวจจับ | Ctrl+A: เลือกพื้นที่ | Ctrl+D: Dark Mode')
        shortcuts_info.setStyleSheet('font-size: 10px; color: #666; background-color: #f9f9f9; padding: 5px; border-radius: 3px;')
        dark_mode_layout.addWidget(shortcuts_info)
        
        layout.addLayout(dark_mode_layout)
        # --- จบเพิ่ม ---

        self.setLayout(layout)

    def reset_duplicate_check(self):
        """Reset การตรวจสอบข้อความซ้ำ"""
        self.last_detected_text = ''
        self.last_text_hash = None
        self.processed_count = 0
        self.skipped_count = 0
        self.duplicate_status_label.setText('สถานะ: รีเซ็ตการตรวจสอบ')
        self.duplicate_status_label.setStyleSheet('color: #2196F3; font-size: 10px;')

    def select_area(self):
        self.status_label.setText('สถานะ: กำลังเลือกพื้นที่...')
        self.status_label.setStyleSheet('color: #FFA500; font-weight: bold; font-size: 12px;')
        
        # สร้าง QTimer สำหรับนับถอยหลัง
        countdown_timer = QTimer()
        countdown = 5
        
        def update_countdown():
            nonlocal countdown
            if countdown > 0:
                self.status_label.setText(f'สถานะ: เริ่มเลือกพื้นที่ในอีก {countdown} วินาที...')
                countdown -= 1
            else:
                countdown_timer.stop()
                selector = AreaSelector(delay=0)  # ตั้งค่า delay เป็น 0 เพราะเราทำการนับถอยหลังเองแล้ว
                region = selector.select_area()
                if region['width'] > 0 and region['height'] > 0:
                    self.region = region
                    self.status_label.setText('สถานะ: เลือกพื้นที่แล้ว')
                    self.status_label.setStyleSheet('color: #4CAF50; font-weight: bold; font-size: 12px;')
                else:
                    self.status_label.setText('สถานะ: เลือกพื้นที่ไม่สำเร็จ')
                    self.status_label.setStyleSheet('color: #FF0000; font-weight: bold; font-size: 12px;')
        
        countdown_timer.timeout.connect(update_countdown)
        countdown_timer.start(1000)  # เริ่มนับถอยหลังทุก 1 วินาที

    def start_detection(self):
        if not self.region:
            QMessageBox.warning(self, 'แจ้งเตือน', 'กรุณาเลือกพื้นที่ก่อนเริ่มตรวจจับ')
            return
        self.detecting = True
        self.timer.start(int(self.detect_interval * 1000))
        self.status_label.setText('สถานะ: กำลังตรวจจับ...')
        self.status_label.setStyleSheet('color: #2196F3; font-weight: bold; font-size: 12px;')
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # เริ่ม Dashboard
        self.start_time = datetime.now()
        self.detection_count = 0
        self.screenshot_count = 0
        self.detection_times = []
        
        # Timer สำหรับอัพเดทเวลาการทำงาน
        self.working_timer = QTimer()
        self.working_timer.timeout.connect(self.update_working_time)
        self.working_timer.start(1000)  # อัพเดททุก 1 วินาที
        
        # --- เริ่ม log รอบใหม่ ---
        self.current_log = {
            'datetime_start': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'badwords': set(),
            'screenshots': []
        }
        # Reset การตรวจสอบข้อความซ้ำเมื่อเริ่มใหม่
        self.reset_duplicate_check()

    def stop_detection(self):
        self.detecting = False
        self.timer.stop()
        if hasattr(self, 'working_timer'):
            self.working_timer.stop()
        self.status_label.setText('สถานะ: หยุดตรวจจับ')
        self.status_label.setStyleSheet('color: #FFA500; font-weight: bold; font-size: 12px;')
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        # --- บันทึก log รอบนี้ ---
        if self.current_log and self.current_log['badwords']:
            self.logs.append({
                'datetime_start': self.current_log['datetime_start'],
                'datetime_end': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'badwords': ', '.join(sorted(self.current_log['badwords'])),
                'screenshots': ', '.join(self.current_log['screenshots'])
            })
        self.current_log = None

    def update_interval(self):
        self.detect_interval = self.interval_spin.value()
        if self.detecting:
            self.timer.stop()
            self.timer.start(int(self.detect_interval * 1000))

    def select_sound(self):
        file, _ = QFileDialog.getOpenFileName(self, 'เลือกไฟล์เสียง', '', 'WAV Files (*.wav)')
        if file:
            self.sound_file = file
            self.sound_btn.setText(os.path.basename(file))
        else:
            self.sound_file = None
            self.sound_btn.setText('เลือกไฟล์เสียง (.wav)')

    def load_all_bad_words(self):
        badwords = []
        for filename in ['badwords.txt', 'badwords_en.txt']:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    badwords += [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                continue
        return badwords

    def update_logcap_interval(self):
        self.log_cooldown = self.logcap_spin.value()

    def update_dashboard(self):
        """อัพเดท Dashboard สถิติ"""
        # อัพเดทจำนวนคำหยาบที่พบวันนี้
        self.detection_count_label.setText(str(self.detection_count))
        
        # อัพเดทจำนวน Screenshot
        self.screenshot_count_label.setText(str(self.screenshot_count))
        
        # อัพเดทเวลาการทำงาน
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.working_time_label.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')
        
        # อัพเดทความถี่การตรวจจับ (คำนวณจาก 1 นาทีล่าสุด)
        now = datetime.now()
        recent_detections = [t for t in self.detection_times if (now - t).seconds <= 60]
        freq = len(recent_detections)
        self.detection_freq_label.setText(f'{freq} ครั้ง/นาที')

    def update_working_time(self):
        """อัพเดทเวลาการทำงานทุกวินาที"""
        self.update_dashboard()

    def detect_badwords(self):
        if not self.region:
            return
        
        try:
            # 1. จับภาพและประมวลผลภาพ
            screenshot = self.sct.grab(self.region)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 2. OCR
            text = pytesseract.image_to_string(thresh, lang='tha+eng')
            text_now = text.strip()
            
            # 3. ตรวจสอบข้อความซ้ำ
            if self.skip_duplicate_checkbox.isChecked():
                # สร้าง hash ของข้อความเพื่อเปรียบเทียบ
                text_hash = hash(text_now)
                
                if text_hash == self.last_text_hash:
                    # ข้อความเหมือนเดิม ไม่ต้องประมวลผล
                    self.skipped_count += 1
                    self.duplicate_status_label.setText('สถานะ: ข้ามข้อความซ้ำ')
                    self.duplicate_status_label.setStyleSheet('color: #FFA500; font-size: 10px;')
                    return
                
                # ข้อความเปลี่ยน อัพเดท hash
                self.last_text_hash = text_hash
                self.processed_count += 1
                self.duplicate_status_label.setText('สถานะ: ข้อความใหม่')
                self.duplicate_status_label.setStyleSheet('color: #4CAF50; font-size: 10px;')
            
            # 4. ตรวจจับคำหยาบ
            badwords_th = []
            badwords_en = []
            for w in self.bad_words:
                if re.search(r'[ก-๙]', w):
                    badwords_th.append(w)
                else:
                    badwords_en.append(w)
            
            found_words = set()
            text_no_space = text.replace(' ', '')
            text_lower = text.lower()
            text_no_space_lower = text_no_space.lower()
            
            for w in badwords_th + badwords_en:
                w_lower = w.lower()
                safe_chars = [re.escape(c) for c in w_lower]
                pattern = r'[\s\.\-\_]*'.join(safe_chars)
                try:
                    if re.search(pattern, text_lower):
                        found_words.add(w)
                except re.error as e:
                    print(f'Regex error for word {w}: {e}')
                if w_lower in text_no_space_lower:
                    found_words.add(w)
            
            if word_tokenize is not None:
                try:
                    words_th = word_tokenize(text, engine='newmm')
                    found_words.update([w for w in badwords_th if w in words_th])
                except Exception as e:
                    print(f"Pythainlp Error: {e}")
            
            final_found_words = sorted(list(found_words))
            
            # 6. จัดการผลลัพธ์
            if final_found_words:
                self.badword_text.setPlainText(', '.join(final_found_words))
                self.play_alert()
                self.show_popup_alert(final_found_words)
                
                # อัพเดท Dashboard
                self.detection_count += 1
                self.detection_times.append(datetime.now())
                
                # บันทึก log
                now = time.time()
                if now - self.last_log_time > self.log_cooldown:
                    self.last_log_time = now
                    screenshot_filename = os.path.join(
                        self.log_dir, 
                        f'screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                    )
                    cv2.imwrite(screenshot_filename, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                    
                    # อัพเดท Dashboard Screenshot
                    self.screenshot_count += 1
                    
                    if self.current_log is not None:
                        self.current_log['badwords'].update(final_found_words)
                        self.current_log['screenshots'].append(screenshot_filename)
            else:
                self.badword_text.setPlainText('')
            
            # 7. อัพเดทข้อความล่าสุด
            self.last_detected_text = text_now
            
        except Exception as e:
            self.status_label.setText(f'ข้อผิดพลาด: {str(e)}')
            self.status_label.setStyleSheet('color: red')

    def play_alert(self):
        if self.sound_file:
            try:
                winsound.PlaySound(self.sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f'ไม่สามารถเล่นเสียง: {e}')
        else:
            winsound.Beep(1000, 500)

    def open_badword_manager(self, filename):
        dlg = BadWordManagerDialog(filename, self)
        if dlg.exec_():
            # reload badwords after editing
            self.bad_words = self.load_all_bad_words()

    def show_popup_alert(self, found_words):
        # แสดง notification มุมขวาล่าง ไม่ต้องกด OK
        self.tray_icon.showMessage(
            'พบคำหยาบ',
            f'ตรวจพบคำหยาบ: {', '.join(found_words)}',
            QSystemTrayIcon.Warning,
            4000  # 4 วินาที
        )

    def export_log(self):
        if not self.logs:
            QMessageBox.information(self, 'Export Log', 'ยังไม่มีข้อมูลประวัติการตรวจจับ')
            return
        file, _ = QFileDialog.getSaveFileName(self, 'บันทึกไฟล์ CSV', '', 'CSV Files (*.csv)')
        if file:
            # เพิ่มข้อมูลสถิติใน CSV
            export_data = []
            for log in self.logs:
                # คำนวณระยะเวลาการตรวจจับ
                start_time = datetime.strptime(log['datetime_start'], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(log['datetime_end'], '%Y-%m-%d %H:%M:%S')
                duration = (end_time - start_time).total_seconds()
                
                # นับจำนวนคำหยาบที่พบ
                badword_count = len(log['badwords'].split(', ')) if log['badwords'] else 0
                
                # นับจำนวน screenshot
                screenshot_count = len(log['screenshots'].split(', ')) if log['screenshots'] else 0
                
                export_data.append({
                    'วันที่เริ่ม': log['datetime_start'],
                    'วันที่สิ้นสุด': log['datetime_end'],
                    'ระยะเวลา (วินาที)': round(duration, 1),
                    'คำหยาบที่พบ': log['badwords'],
                    'จำนวนคำหยาบ': badword_count,
                    'จำนวน Screenshot': screenshot_count,
                    'ไฟล์ Screenshot': log['screenshots']
                })
            
            df = pd.DataFrame(export_data)
            df.to_csv(file, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, 'Export Log', f'บันทึกไฟล์ CSV สำเร็จแล้ว\nพบข้อมูล {len(export_data)} รายการ')

    def select_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'เลือกโฟลเดอร์บันทึก')
        if folder:
            self.log_dir = folder
            self.folder_label.setText(f'โฟลเดอร์ปัจจุบัน: {self.log_dir}')

    def open_save_folder(self):
        os.startfile(self.log_dir)

    def cleanup_old_files(self):
        # ตรวจสอบและลบไฟล์เก่าในโฟลเดอร์
        for filename in os.listdir(self.log_dir):
            if filename.startswith('screenshot_') and filename.endswith('.png'):
                file_path = os.path.join(self.log_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if datetime.now() - file_time > timedelta(days=7):
                    os.remove(file_path)
        QMessageBox.information(self, 'ลบไฟล์เรียบร้อย', 'ลบไฟล์เก่าเรียบร้อยแล้ว')

    def toggle_dark_mode(self):
        """สลับ Dark Mode"""
        if self.dark_mode_checkbox.isChecked():
            self.setStyleSheet("""
                QWidget {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QGroupBox {
                    border: 2px solid #4CAF50;
                    border-radius: 6px;
                    margin-top: 12px;
                    font-weight: bold;
                    padding-top: 10px;
                    background-color: #3d3d3d;
                }
                QTextEdit {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 5px;
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QDoubleSpinBox {
                    padding: 5px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QCheckBox {
                    color: #ffffff;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QGroupBox {
                    border: 2px solid #4CAF50;
                    border-radius: 6px;
                    margin-top: 12px;
                    font-weight: bold;
                    padding-top: 10px;
                }
                QTextEdit {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 5px;
                    background-color: white;
                }
                QLabel {
                    color: #333333;
                }
                QDoubleSpinBox {
                    padding: 5px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                }
                QCheckBox {
                    color: #333333;
                    font-weight: bold;
                }
            """)

    def keyPressEvent(self, event):
        """จัดการ Keyboard Shortcuts"""
        if event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            # Ctrl+S: เริ่ม/หยุดตรวจจับ
            if self.detecting:
                self.stop_detection()
            else:
                self.start_detection()
        elif event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            # Ctrl+A: เลือกพื้นที่
            self.select_area()
        elif event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            # Ctrl+D: Dark Mode
            self.dark_mode_checkbox.setChecked(not self.dark_mode_checkbox.isChecked())
            self.toggle_dark_mode()
        else:
            super().keyPressEvent(event)

    def open_dashboard(self):
        """เปิดหน้า Dashboard"""
        self.dashboard_window = DashboardWindow(self)
        self.dashboard_window.show()

if __name__ == '__main__':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    app = QApplication(sys.argv)
    window = BadWordDetectorApp()
    window.show()
    sys.exit(app.exec_()) 