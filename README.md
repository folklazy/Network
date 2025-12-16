# Distributed Parallel TSP Solver via Socket

โปรเจคนี้เป็นการจำลองระบบ **Distributed Computing** เพื่อแก้ปัญหา **Traveling Salesman Problem (TSP)** หรือการหาเส้นทางท่องเที่ยวให้ครบทุกเมืองด้วยระยะทางที่สั้นที่สุด โดยใช้ Python Socket

ระบบทำงานโดยแบ่งเป็น **Server** (ผู้แจกงาน) และ **Worker** (ผู้ช่วยคำนวณ) ซึ่งสามารถเปิด Worker ได้หลายตัวพร้อมกันเพื่อช่วยกันหาคำตอบให้เร็วขึ้น (Parallel Processing)

## ไฟล์ในโปรเจค
- **`server.py`**: ทำหน้าที่สร้างโจทย์ (สุ่มกราฟเมือง), แจกจ่ายงาน (Path) ให้ Worker, และเก็บสถิติเส้นทางที่ดีที่สุด (Best Solution)
- **`worker.py`**: เชื่อมต่อกับ Server เพื่อดึงงานมาคำนวณแบบ BFS (Breadth-First Search) และส่งผลลัพธ์กลับไปยัง Server

## วิธีใช้งาน (How to Run)

### 1. เปิด Server (ผู้สั่งการ)
รันไฟล์ `server.py` ก่อนเพื่อรอการเชื่อมต่อ
```bash
python server.py
```
Server จะแสดงข้อมูลกราฟ (Distance Matrix) และรอ Worker เข้ามาเชื่อมต่อ

### 2. เปิด Worker (ลูกน้อง)
เปิด Terminal ใหม่ (หรือหลายๆ หน้าต่าง) แล้วรันไฟล์ `worker.py`
```bash
python worker.py
```
*Tip: คุณสามารถรัน `worker.py` ได้หลายๆ terminal พร้อมกันเพื่อช่วยกันคำนวณ*

## การตั้งค่า (Configuration)
สามารถแก้ไขค่า Config ได้ในไฟล์ `server.py`:
- `NUM_CITIES`: จำนวนเมืองที่ต้องการทดสอบ (แนะนำ 5-10 เมือง ถ้าเยอะกว่านี้จะใช้เวลานานมาก)
- `HOST` / `PORT`: ตั้งค่า IP และ Port สำหรับเชื่อมต่อ

## หลักการทำงาน
1. **Server** สุ่มสร้างตารางระยะทาง (Adjacency Matrix)
2. **Worker** ขอเส้นทางเดิน (Path) จาก Server ไปขยายต่อ
3. ใช้การค้นหาแบบ **BFS** เพื่อหาเส้นทางที่เป็นไปได้
4. มีการใช้ **Pruning** (ตัดกิ่ง) โดยถ้าระยะทางปัจจุบันเกิน Best Cost ของ Server แล้ว จะหยุดคำนวณในเส้นทางนั้นทันทีเพื่อให้ทำงานเร็วขึ้น
