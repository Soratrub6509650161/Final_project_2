from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image
import os
import mss
import numpy as np
import cv2
import time
import winsound

app = Flask(__name__)

# ตั้งค่า path ของ tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ตัวแปรสำหรับเก็บพื้นที่ที่เลือก
selected_region = None
sct = mss.mss()

def load_bad_words():
    try:
        with open('badwords.txt', 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def capture_and_process_screen():
    if selected_region is None:
        return None, "กรุณาเลือกพื้นที่ที่ต้องการตรวจจับก่อน"
    
    try:
        # จับภาพหน้าจอตามพื้นที่ที่เลือก
        screenshot = sct.grab(selected_region)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        
        # ประมวลผลภาพ
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # OCR
        text = pytesseract.image_to_string(thresh, lang='tha+eng')
        text_no_space = text.replace(' ', '')
        
        # ตรวจจับคำหยาบ
        bad_words = load_bad_words()
        found_words = [w for w in bad_words if w in text_no_space]
        
        if found_words:
            winsound.Beep(1000, 500)
            
        return text.strip(), found_words
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_region', methods=['POST'])
def select_region():
    global selected_region
    data = request.json
    selected_region = {
        'top': data['top'],
        'left': data['left'],
        'width': data['width'],
        'height': data['height']
    }
    return jsonify({'status': 'success'})

@app.route('/detect', methods=['GET'])
def detect():
    text, found_words = capture_and_process_screen()
    if text is None:
        return jsonify({'error': found_words})
    return jsonify({
        'text': text,
        'found_words': found_words
    })

if __name__ == '__main__':
    app.run(debug=True, port=5050) 