#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test file สำหรับทดสอบ wordsegment library
ทดสอบการแยกคำที่ติดกัน เช่น "hellofuck" -> "hello fuck"
"""

import sys
import re

def test_wordsegment_installation():
    """ทดสอบการติดตั้ง wordsegment"""
    try:
        from wordsegment import load, segment # type: ignore
        print("✅ wordsegment imported successfully")
        return True
    except ImportError:
        print("❌ wordsegment not installed")
        print("💡 Install with: pip install wordsegment")
        return False

def test_basic_segmentation():
    """ทดสอบการแยกคำพื้นฐาน"""
    try:
        from wordsegment import load, segment
        
        print("📚 Loading wordsegment dictionary...")
        load()  # โหลด dictionary ครั้งแรก
        print("✅ Dictionary loaded successfully")
        
        test_cases = [
            "hellofuck",
            "youarebitch", 
            "thisshit",
            "goddamn",
            "holyshit",
            "whatthehell",
            "shutthefuckup"
        ]
        
        print("\n�� Testing Basic Word Segmentation:")
        print("=" * 50)
        
        for text in test_cases:
            segmented = segment(text)
            print(f"'{text}' -> {' '.join(segmented)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in basic segmentation: {e}")
        return False

def test_profanity_detection():
    """ทดสอบการตรวจจับคำหยาบหลังจากแยกคำ"""
    try:
        from wordsegment import load, segment
        
        load()
        
        # คลังคำหยาบตัวอย่าง
        bad_words = {
            'fuck', 'ass', 'shit', 'bitch', 'damn', 'hell',
            'dumb', 'stupid', 'idiot', 'moron'
        }
        
        test_messages = [
            "hellofuck you",
            "youarebitch",
            "thisshit is bad",
            "goddamn it",
            "holyshit wow",
            "whatthehell happened",
            "shutthefuckup",
            "classroom",  # ควรแยกเป็น class room
            "password",   # ควรแยกเป็น pass word
            "grassland"   # ควรแยกเป็น grass land
        ]
        
        print("\n🔍 Testing Profanity Detection After Segmentation:")
        print("=" * 60)
        
        for message in test_messages:
            # แยกคำด้วย wordsegment
            words = message.lower().split()
            segmented_words = []
            
            for word in words:
                if len(word) > 8:  # คำยาว
                    segmented = segment(word)
                    segmented_words.extend(segmented)
                else:
                    segmented_words.append(word)
            
            # ตรวจสอบคำหยาบ
            found_bad_words = [word for word in segmented_words if word in bad_words]
            
            if found_bad_words:
                print(f"'{message}' -> Found: {found_bad_words}")
                print(f"  Segmented: {segmented_words}")
            else:
                print(f"'{message}' -> Clean")
                print(f"  Segmented: {segmented_words}")
            print()
            
        return True
        
    except Exception as e:
        print(f"❌ Error in profanity detection: {e}")
        return False

def test_edge_cases():
    """ทดสอบกรณีขอบ (edge cases)"""
    try:
        from wordsegment import load, segment
        
        load()
        
        edge_cases = [
            "a",           # คำเดียวตัวเดียว
            "hi",          # คำสั้น
            "hello",       # คำปกติ
            "helloworld",  # คำติดกัน
            "helloworldhowareyou",  # คำยาวมาก
            "123456",      # ตัวเลข
            "hello123",    # ตัวอักษร+ตัวเลข
            "hello-world", # มีเครื่องหมาย
            "hello_world", # มี underscore
            "HELLO",       # ตัวใหญ่
            "Hello",       # ตัวใหญ่ตัวแรก
            "",            # สตริงว่าง
            "   ",         # ช่องว่าง
            "hello world", # หลายคำ
            "hello  world" # มีช่องว่างหลายตัว
        ]
        
        print("\n�� Testing Edge Cases:")
        print("=" * 50)
        
        for text in edge_cases:
            try:
                if text.strip():  # ไม่ใช่สตริงว่าง
                    segmented = segment(text)
                    print(f"'{text}' -> {segmented}")
                else:
                    print(f"'{text}' -> [empty]")
            except Exception as e:
                print(f"'{text}' -> Error: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error in edge cases: {e}")
        return False

def test_performance():
    """ทดสอบประสิทธิภาพ"""
    try:
        from wordsegment import load, segment
        import time
        
        load()
        
        # สร้างข้อความทดสอบ
        test_texts = [
            "hellofuck" * 10,  # ข้อความยาว
            "youarebitch " * 50,  # หลายคำ
            "thisshit " * 100,  # ข้อความยาวมาก
        ]
        
        print("\n⚡ Testing Performance:")
        print("=" * 50)
        
        for i, text in enumerate(test_texts):
            start_time = time.time()
            
            # แยกคำ
            segmented = segment(text)
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # มิลลิวินาที
            
            print(f"Test {i+1}: {len(text)} characters")
            print(f"  Time: {processing_time:.2f} ms")
            print(f"  Words: {len(segmented)}")
            print(f"  Sample: {segmented[:5]}...")  # แสดง 5 คำแรก
            print()
            
        return True
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        return False

def test_integration_with_main_system():
    """ทดสอบการใช้งานร่วมกับระบบหลัก"""
    try:
        from wordsegment import load, segment
        
        load()
        
        # จำลองข้อความจาก Twitch chat
        chat_messages = [
            "hellofuck you man",
            "youarebitch stop it",
            "thisshit is getting old",
            "goddamn this game",
            "holyshit that was amazing",
            "whatthehell are you doing",
            "shutthefuckup already",
            "classroom is boring",
            "password is too simple",
            "grassland looks beautiful"
        ]
        
        print("\n🔗 Testing Integration with Main System:")
        print("=" * 60)
        
        for message in chat_messages:
            print(f"Original: {message}")
            
            # แยกคำด้วย wordsegment
            words = message.lower().split()
            all_segmented = []
            
            for word in words:
                if len(word) > 8:  # คำยาว
                    segmented = segment(word)
                    all_segmented.extend(segmented)
                else:
                    all_segmented.append(word)
            
            print(f"Segmented: {all_segmented}")
            
            # จำลองการตรวจจับคำหยาบ
            bad_words = {'fuck', 'ass', 'shit', 'bitch', 'damn', 'hell'}
            found = [word for word in all_segmented if word in bad_words]
            
            if found:
                print(f"�� Bad words detected: {found}")
            else:
                print("✅ Clean message")
            print("-" * 40)
            
        return True
        
    except Exception as e:
        print(f"❌ Error in integration test: {e}")
        return False

def test_comparison_with_other_methods():
    """เปรียบเทียบกับวิธีอื่นๆ"""
    try:
        from wordsegment import load, segment
        
        load()
        
        test_cases = [
            "hellofuck",
            "youarebitch",
            "thisshit",
            "classroom",
            "password"
        ]
        
        print("\n🔄 Comparing with Other Methods:")
        print("=" * 50)
        
        for text in test_cases:
            print(f"Text: '{text}'")
            
            # วิธีที่ 1: wordsegment
            wordsegment_result = segment(text)
            print(f"  wordsegment: {wordsegment_result}")
            
            # วิธีที่ 2: regex แบบเดิม
            regex_result = re.findall(r'\b\w+\b', text.lower())
            print(f"  regex: {regex_result}")
            
            # วิธีที่ 3: แยกด้วย space
            space_result = text.lower().split()
            print(f"  space split: {space_result}")
            
            print()
            
        return True
        
    except Exception as e:
        print(f"❌ Error in comparison test: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 WordSegment Library Test")
    print("=" * 60)
    
    # ทดสอบการติดตั้ง
    if not test_wordsegment_installation():
        print("\n❌ Cannot proceed without wordsegment")
        return
    
    # ทดสอบการแยกคำพื้นฐาน
    test_basic_segmentation()
    
    # ทดสอบการตรวจจับคำหยาบ
    test_profanity_detection()
    
    # ทดสอบกรณีขอบ
    test_edge_cases()
    
    # ทดสอบประสิทธิภาพ
    test_performance()
    
    # ทดสอบการใช้งานร่วมกับระบบหลัก
    test_integration_with_main_system()
    
    # เปรียบเทียบกับวิธีอื่นๆ
    test_comparison_with_other_methods()
    
    print("\n✅ All tests completed!")
    print("\n💡 Key Benefits of wordsegment:")
    print("- แยกคำที่ติดกันได้ดี เช่น 'hellofuck' -> 'hello fuck'")
    print("- ใช้งานง่าย แค่ load() และ segment()")
    print("- มี dictionary ที่ครอบคลุม")
    print("- เหมาะสำหรับการตรวจจับคำหยาบที่ซ่อน")

if __name__ == "__main__":
    main()