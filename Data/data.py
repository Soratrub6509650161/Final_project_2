def remove_duplicate_words(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as infile:
        words = infile.readlines()

    # แปลงเป็น set เพื่อกำจัดคำซ้ำ + ตัดช่องว่าง/ขึ้นบรรทัดใหม่
    unique_words = sorted(set(word.strip() for word in words if word.strip()))

    with open(output_path, "w", encoding="utf-8") as outfile:
        for word in unique_words:
            outfile.write(word + "\n")

    print(f"✅ ลบคำซ้ำเรียบร้อยแล้ว ({len(unique_words)} คำ) → {output_path}")

# ตัวอย่างการใช้งาน
remove_duplicate_words("badwords.txt", "badwords_deduplicated.txt")
