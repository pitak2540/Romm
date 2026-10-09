# ROM Translator — GBA Edition (Android prototype)

รุ่น Android ต้นแบบที่ใช้ Kivy/Python แยกจากแอปเดสก์ท็อป PySide6 เดิม
เป้าหมายคือมือถือ Android และเครื่อง RAM 8 GB โดยเริ่มจาก Font Studio และเครื่องมือ ROM เบื้องต้น

## ความสามารถในต้นแบบ
- หน้าจอสัมผัสวาด Glyph แบบ Pixel
- ชุดอักขระตั้งต้นภาษาไทย อังกฤษ/ตัวเลข และญี่ปุ่นพื้นฐาน
- บันทึกโปรเจกต์ JSON
- ส่งออก PNG Atlas และ Glyph Map JSON
- เลือก ROM ผ่าน Android Storage Access Framework เมื่อ build environment มี androidstorage4kivy
- อ่าน GBA header และค้นหาช่วง ASCII เบื้องต้น
- ค้นหาช่วงไบต์ FF/00 เพื่อวางแผนพื้นที่ โดยไม่เขียน ROM
- โหมด analyzer/planner เป็น heuristic; ยังไม่ถอด custom encoding หรือ pointer อัตโนมัติ

## ข้อจำกัด
- ยังไม่มี AI Offline translation engine ใน APK รุ่นนี้
- ตัวเลือกขนาด 8×16 ฯลฯ ในหน้าจอแก้ไขปัจจุบันจะลดเป็น grid สี่เหลี่ยมเพื่อวาด; atlas ในรุ่นนี้ยังไม่ได้รองรับ glyph แบบไม่เป็นสี่เหลี่ยมอย่างสมบูรณ์
- Android file saving ใช้ androidstorage4kivy; fallback จะบันทึกใน app-private directory
- ไม่ควรนำผล free-space scan ไปเขียน ROM โดยไม่ตรวจ references/pointers ของเกม
- ต้องทดสอบ file picker/export บน Android จริงหลัง build

## สร้าง APK
แนะนำให้ build บน Linux หรือ WSL2 Ubuntu (ไม่ใช่บน Android โดยตรง)
ต้องติดตั้ง Java JDK, Android SDK/NDK และ Buildozer ตามเอกสารทางการก่อน

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install buildozer
buildozer android debug
```

APK โดยทั่วไปจะอยู่ใน `bin/` เมื่อ build สำเร็จ

## ใช้งาน
1. ติดตั้ง APK บนอุปกรณ์ Android
2. เปิด Font Studio เพื่อวาดพิกเซลและส่งออกไฟล์
3. เปิด ROM Analyzer เพื่อเลือกไฟล์ `.gba`
4. ใช้ ROM Space Planner เพื่อดู candidate พื้นที่ FF/00

รุ่นนี้เป็น starter project สำหรับ build ต่อ ไม่ใช่ APK ที่คอมไพล์เสร็จแล้ว


## รุ่น V2: Auto Space Allocator (ทดลอง)
- จัดอันดับ candidate จากช่วง FF/00 ตามขนาดและ alignment
- แสดง offset ที่เลือกอัตโนมัติ และจำนวน pointer ที่ชี้ตรงต้นช่วงเป็นเพียง clue
- หากไม่มีพื้นที่พอ จะคำนวณขนาด ROM สำเนาแบบ power-of-two สูงสุด 64 MiB
- สร้างสำเนา ROM พร้อมจอง region และส่งออก manifest
- ไม่แก้ pointer และไม่ได้เขียนข้อมูลฟอนต์จริง จึงยังไม่ใช่ ROM แปลที่เล่นได้
- ต้องตรวจสอบ compression, references, custom loader และ pointer format ของเกมก่อนใช้กับ ROM จริง
