import unittest
import re

# ฟังก์ชันตรวจจับคำหยาบจากข้อความ (นำ logic จาก main_gui.py)
def detect_badwords_in_text(text, badwords, word_tokenize=None):
    found_words = set()
    badwords_th = []
    badwords_en = []
    for w in badwords:
        if re.search(r'[ก-๙]', w):
            badwords_th.append(w)
        else:
            badwords_en.append(w)
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
        except re.error:
            pass
        if w_lower in text_no_space_lower:
            found_words.add(w)
    if word_tokenize is not None:
        try:
            words_th = word_tokenize(text, engine='newmm')
            found_words.update([w for w in badwords_th if w in words_th])
        except Exception:
            pass
    return sorted(list(found_words))

class TestBadwordDetection(unittest.TestCase):
    def setUp(self):
        self.badwords = ['fuck', 'shit', 'ควย', 'เหี้ย']
        self.word_tokenize = None  # ถ้ามี pythainlp ให้ import แล้วใส่

    def test_detect_exact(self):
        text = "This is a fuck example."
        found = detect_badwords_in_text(text, self.badwords, self.word_tokenize)
        self.assertIn('fuck', found)
        self.assertNotIn('shit', found)

    def test_detect_thai(self):
        text = "วันนี้อากาศดีมาก ควย"
        found = detect_badwords_in_text(text, self.badwords, self.word_tokenize)
        self.assertIn('ควย', found)

    def test_detect_substring(self):
        text = "He said fucklove is not a word."
        found = detect_badwords_in_text(text, self.badwords, self.word_tokenize)
        self.assertIn('fuck', found)

    def test_detect_with_space(self):
        text = "You are a f u c k ing guy."
        found = detect_badwords_in_text(text, self.badwords, self.word_tokenize)
        self.assertIn('fuck', found)

    def test_no_badword(self):
        text = "Hello, how are you?"
        found = detect_badwords_in_text(text, self.badwords, self.word_tokenize)
        self.assertEqual(found, [])

    def test_multiple_badwords(self):
        text = "เหี้ย ควย fuck"
        found = detect_badwords_in_text(text, self.badwords, self.word_tokenize)
        self.assertIn('fuck', found)
        self.assertIn('ควย', found)
        self.assertIn('เหี้ย', found)

if __name__ == '__main__':
    unittest.main() 