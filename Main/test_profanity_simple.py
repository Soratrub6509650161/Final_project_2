#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test file สำหรับตรวจสอบ profanity_check library
ทดสอบการ import และการใช้งานฟังก์ชันต่างๆ
"""

import sys
import traceback

def test_import():
    """ทดสอบการ import profanity_check"""
    print("🔍 Testing profanity_check import...")
    
    try:
        from profanity_check import predict, predict_prob  # type: ignore
        print("✅ Import successful!")
        print(f"   predict function: {predict}")
        print(f"   predict_prob function: {predict_prob}")
        return True, predict, predict_prob
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False, None, None
        
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        print(f"   Error type: {type(e).__name__}")
        traceback.print_exc()
        return False, None, None

def test_basic_usage(predict_func, predict_prob_func):
    """ทดสอบการใช้งานพื้นฐาน"""
    print("\n🧪 Testing basic usage...")
    
    if not predict_func or not predict_prob_func:
        print("❌ Functions not available")
        return False
    
    try:
        # ทดสอบ predict function
        print("📝 Testing predict function:")
        
        test_texts = [
            "hello world",
            "fuck you", 
            "this is a test",
            "go to hell"
        ]
        
        for text in test_texts:
            result = predict_func([text])
            print(f"   '{text}' -> {result}")
        
        # ทดสอบ predict_prob function
        print("\n📊 Testing predict_prob function:")
        
        for text in test_texts:
            prob = predict_prob_func([text])
            print(f"   '{text}' -> {prob}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during basic usage: {e}")
        traceback.print_exc()
        return False

def test_word_segmentation():
    """ทดสอบ word segmentation"""
    print("\n✂️ Testing word segmentation...")
    
    try:
        from wordsegment import load, segment  # type: ignore
        print("✅ wordsegment import successful!")
        
        # โหลด dictionary
        load()
        print("✅ Dictionary loaded!")
        
        # ทดสอบการแยกคำ
        test_words = ["helloass", "hellofuck", "class", "glass"]
        
        for word in test_words:
            segmented = segment(word)
            print(f"   '{word}' -> {segmented}")
        
        return True
        
    except ImportError as e:
        print(f"❌ wordsegment import failed: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error during word segmentation: {e}")
        traceback.print_exc()
        return False

def test_combined_detection():
    """ทดสอบการตรวจจับแบบรวม"""
    print("\n🎯 Testing combined detection...")
    
    try:
        from profanity_check import predict, predict_prob  # type: ignore
        from wordsegment import load, segment  # type: ignore
        
        # โหลด dictionary
        load()
        
        # ทดสอบข้อความที่ซับซ้อน
        test_messages = [
            "helloass",
            "hellofuck", 
            "this is a class",
            "fuck you asshole"
        ]
        
        for message in test_messages:
            print(f"\n📝 Message: '{message}'")
            
            # แยกคำด้วย wordsegment
            words = message.split()
            segmented_words = []
            
            for word in words:
                if len(word) > 6:  # ลดความยาวขั้นต่ำ
                    try:
                        segmented = segment(word)
                        segmented_words.extend(segmented)
                        print(f"   Segmented '{word}' -> {segmented}")
                    except:
                        segmented_words.append(word)
                else:
                    segmented_words.append(word)
            
            print(f"   Final words: {segmented_words}")
            
            # ตรวจสอบแต่ละคำ
            found_profanity = []
            for word in segmented_words:
                if len(word) >= 3:
                    result = predict([word])
                    if result[0] == 1:
                        found_profanity.append(word)
                        print(f"   🚨 Found profanity: '{word}'")
            
            # ตรวจสอบข้อความโดยรวม
            message_prob = predict_prob([message])[0]
            print(f"   📊 Message probability: {message_prob:.3f}")
            
            if found_profanity:
                print(f"   ✅ Found profanity: {found_profanity}")
            else:
                print(f"   ✅ No profanity detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during combined detection: {e}")
        traceback.print_exc()
        return False

def check_python_version():
    """ตรวจสอบเวอร์ชัน Python และ packages"""
    print("🐍 Python Environment Check:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    
    try:
        import pkg_resources
        print(f"   Setuptools version: {pkg_resources.get_distribution('setuptools').version}")
    except:
        print("   Setuptools version: Unknown")
    
    try:
        import sklearn  # type: ignore
        print(f"   Scikit-learn version: {sklearn.__version__}")
    except:
        print("   Scikit-learn: Not installed")

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 Profanity Check Library Test")
    print("=" * 50)
    
    # ตรวจสอบ environment
    check_python_version()
    
    # ทดสอบการ import
    import_success, predict_func, predict_prob_func = test_import()
    
    if import_success:
        # ทดสอบการใช้งานพื้นฐาน
        basic_success = test_basic_usage(predict_func, predict_prob_func)
        
        # ทดสอบ word segmentation
        seg_success = test_word_segmentation()
        
        # ทดสอบการตรวจจับแบบรวม
        if basic_success and seg_success:
            combined_success = test_combined_detection()
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"   Import: {'✅' if import_success else '❌'}")
        print(f"   Basic Usage: {'✅' if import_success and 'basic_success' in locals() else '❌'}")
        print(f"   Word Segmentation: {'✅' if 'seg_success' in locals() and seg_success else '❌'}")
        print(f"   Combined Detection: {'✅' if 'combined_success' in locals() and combined_success else '❌'}")
        
    else:
        print("\n❌ Cannot proceed without successful import")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if profanity-check is installed: pip install profanity-check")
        print("   2. Check scikit-learn version: pip install scikit-learn>=1.0.0")
        print("   3. Try upgrading: pip install --upgrade profanity-check")
        print("   4. Check Python version compatibility")

if __name__ == "__main__":
    main()
