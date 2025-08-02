import sys
import os
import re

# เพิ่ม path เพื่อ import จาก main_gui.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import classes จาก main_gui.py
from main_gui import TwitchChatWorker, Trie

def test_f1uck_detection():
    """ทดสอบการตรวจจับ f1uck"""
    print("🔍 ทดสอบการตรวจจับ f1uck")
    print("=" * 50)
    
    # สร้าง worker สำหรับทดสอบ
    worker = TwitchChatWorker("test_channel")
    
    # ทดสอบข้อความ
    test_message = "f1uck"
    print(f"ข้อความทดสอบ: '{test_message}'")
    
    # ทดสอบขั้นตอนที่ 1: Preprocessing
    print("\n📝 ขั้นตอนที่ 1: Preprocessing")
    message_lower = test_message.lower()
    message_no_space = message_lower.replace(' ', '')
    print(f"message_lower: '{message_lower}'")
    print(f"message_no_space: '{message_no_space}'")
    
    # ทดสอบขั้นตอนที่ 2: Whitelist Check
    print("\n🛡️ ขั้นตอนที่ 2: Whitelist Check")
    whitelist_check = any(whitelist_word in message_lower for whitelist_word in worker.whitelist)
    print(f"Whitelist check: {whitelist_check}")
    print(f"Whitelist words: {worker.whitelist}")
    
    # ทดสอบขั้นตอนที่ 3: Direct Matching
    print("\n🎯 ขั้นตอนที่ 3: Direct Matching")
    words_in_message = message_lower.split()
    print(f"words_in_message: {words_in_message}")
    
    found_words = set()
    for word in words_in_message:
        trie_result = worker.trie.search(word)
        whitelist_result = word not in worker.whitelist
        print(f"  '{word}': trie.search() = {trie_result}, not in whitelist = {whitelist_result}")
        if trie_result and whitelist_result:
            found_words.add(word)
    
    print(f"Found words (step 3): {found_words}")
    
    # ทดสอบขั้นตอนที่ 4: No-Space Detection
    print("\n🔍 ขั้นตอนที่ 4: No-Space Detection")
    print(f"message_no_space: '{message_no_space}'")
    print(f"badwords_en: {list(worker.badwords_en)[:10]}...")  # แสดง 10 คำแรก
    
    # สร้าง substrings
    substrings = set([message_no_space[i:i+len(w)] for w in worker.badwords_en for i in range(len(message_no_space)-len(w)+1)])
    print(f"Generated substrings: {substrings}")
    
    no_space_matches_en = worker.badwords_en.intersection(substrings)
    print(f"No-space matches (EN): {no_space_matches_en}")
    
    # ทดสอบขั้นตอนที่ 5: Symbol Removal
    print("\n🧹 ขั้นตอนที่ 5: Symbol Removal")
    message_clean = re.sub(r'[^\w\sก-๙]', '', message_lower)
    print(f"message_clean: '{message_clean}'")
    
    words_clean = message_clean.split()
    print(f"words_clean: {words_clean}")
    
    for word in words_clean:
        trie_result = worker.trie.search(word)
        whitelist_result = word not in worker.whitelist
        print(f"  '{word}': trie.search() = {trie_result}, not in whitelist = {whitelist_result}")
        if trie_result and whitelist_result:
            found_words.add(word)
    
    print(f"Found words (step 5): {found_words}")
    
    # ทดสอบการตรวจจับทั้งหมด
    print("\n🎯 ผลลัพธ์สุดท้าย")
    final_result = worker.optimized_detect_bad_words(test_message)
    print(f"optimized_detect_bad_words('{test_message}'): {final_result}")
    
    return final_result

def test_variations():
    """ทดสอบรูปแบบต่างๆ ของ fuck"""
    print("\n" + "=" * 60)
    print("🧪 ทดสอบรูปแบบต่างๆ ของ fuck")
    print("=" * 60)
    
    worker = TwitchChatWorker("test_channel")
    
    test_cases = [
        "fuck",      # ปกติ
        "f1uck",     # ใช้ตัวเลข 1
        "f0ck",      # ใช้ตัวเลข 0
        "f@ck",      # ใช้สัญลักษณ์ @
        "f#ck",      # ใช้สัญลักษณ์ #
        "fu#k",      # ใช้สัญลักษณ์ #
        "f!ck",      # ใช้สัญลักษณ์ !
        "f_ck",      # ใช้ underscore
        "f-ck",      # ใช้ dash
    ]
    
    for test_case in test_cases:
        result = worker.optimized_detect_bad_words(test_case)
        print(f"'{test_case}' → {result}")

def analyze_regex():
    """วิเคราะห์ regex pattern"""
    print("\n" + "=" * 60)
    print("🔍 วิเคราะห์ Regex Pattern")
    print("=" * 60)
    
    test_cases = [
        "f1uck",
        "f0ck", 
        "f@ck",
        "f#ck",
        "fu#k",
        "f!ck",
        "f_ck",
        "f-ck"
    ]
    
    for test_case in test_cases:
        # ทดสอบ regex pattern ที่ใช้ในขั้นตอนที่ 5
        message_lower = test_case.lower()
        message_clean = re.sub(r'[^\w\sก-๙]', '', message_lower)
        
        print(f"'{test_case}' → regex → '{message_clean}'")
        
        # วิเคราะห์แต่ละตัวอักษร
        print(f"  Characters: {[c for c in test_case]}")
        print(f"  After regex: {[c for c in message_clean]}")
        print()

if __name__ == "__main__":
    print("🚀 เริ่มการทดสอบการตรวจจับ f1uck")
    
    # ทดสอบ f1uck
    test_f1uck_detection()
    
    # ทดสอบรูปแบบต่างๆ
    test_variations()
    
    # วิเคราะห์ regex
    analyze_regex()
    
    print("\n✅ การทดสอบเสร็จสิ้น") 