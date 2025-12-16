import socket
import threading
import pickle
import struct
import random  

# --- CONFIG ---
HOST = '0.0.0.0'
PORT = 9999
NUM_CITIES = 5  # <--- ปรับเป็น 10 หรือ 12 เมือง (อย่าเกิน 13 เดี๋ยวคอมค้าง)
START_CITY = 0

# --- DATA (Auto Generate Random Graph) ---
# สร้างแผนที่แบบสุ่ม ไม่ต้องพิมพ์เอง
graph = []
for i in range(NUM_CITIES):
    row = []
    for j in range(NUM_CITIES):
        if i == j:
            row.append(0) # ระยะทางไปตัวเองเป็น 0
        else:
            row.append(random.randint(10, 100)) # สุ่มระยะทาง 10-100
    graph.append(row)

# เช็คหน่อยว่าหน้าตาแผนที่เป็นไง (ปริ้นทุกแถวจะได้ตรวจสอบได้)
print(f"[INFO] Generated Random Graph for {NUM_CITIES} cities.")
print("      " + ",  ".join([f"{i:>3}" for i in range(NUM_CITIES)])) # Header หัวตาราง
for idx, r in enumerate(graph):
    print(f"Row {idx}: {r}")

# --- GLOBAL STATE ---
# Queue เก็บ path ที่ยังเดินไม่จบ เช่น [[0], [0,1]]
job_queue = [[START_CITY]] 
# เก็บคำตอบที่ดีที่สุด (Cost ต่ำสุด)
best_cost = float('inf')
best_path = []
lock = threading.Lock() # กันข้อมูลตีกัน

# ฟังก์ชันช่วยส่งข้อมูล (Network Protocol)
# เราจะส่ง Header 4 bytes บอกขนาดข้อมูลก่อน เพื่อความชัวร์ (TCP Stream)
def send_data(conn, data):
    serialized = pickle.dumps(data)
    conn.sendall(struct.pack('>I', len(serialized)) + serialized)

def recv_data(conn):
    raw_msglen = conn.recv(4)
    if not raw_msglen: return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    data = b''
    while len(data) < msglen:
        packet = conn.recv(msglen - len(data))
        if not packet: return None
        data += packet
    return pickle.loads(data)

def handle_client(conn, addr):
    global best_cost, best_path
    print(f"[NEW CONNECTION] {addr} connected.")
    
    # 1. ส่งแผนที่ (Graph) ให้ Worker ก่อน
    send_data(conn, {'type': 'INIT', 'graph': graph, 'num_cities': NUM_CITIES})

    try:
        while True:
            # 2. รอ Worker ของาน
            req = recv_data(conn)
            if not req: break

            if req['type'] == 'REQUEST_JOB':
                job = None
                
                with lock:
                    if job_queue:
                        job = job_queue.pop(0) # ดึงงานหัวแถว
                
                if job:
                    # ส่งงานให้ Worker
                    send_data(conn, {'type': 'JOB', 'path': job, 'current_best': best_cost})
                else:
                    # ถ้าคิวหมด เช็คว่างานจบจริงหรือแค่รอเพื่อน
                    # (ใน PoC นี้ถ้า Queue หมดคือสั่งให้รอหรือจบเลยก็ได้)
                    send_data(conn, {'type': 'WAIT'})
            
            elif req['type'] == 'JOB_RESULT':
                # Worker ส่งผลลัพธ์กลับมา (List ของ Path ใหม่)
                new_paths = req['new_paths']
                found_complete = req.get('complete_path')
                cost_found = req.get('cost')

                with lock:
                    # เอา path ใหม่ไปต่อคิว
                    if new_paths:
                        job_queue.extend(new_paths)
                        print(f"[{addr}] Added {len(new_paths)} paths to queue. Queue size: {len(job_queue)}")
                    
                    # ถ้าเจอเส้นทางครบวงรอบ เช็คว่าเป็น Best Solution ไหม
                    if found_complete:
                        if cost_found < best_cost:
                            best_cost = cost_found
                            best_path = found_complete
                            print(f"*** NEW BEST PATH FOUND: {best_path} Cost: {best_cost} ***")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Listening on {HOST}:{PORT}")
    print(f"[SERVER] Task: TSP for {NUM_CITIES} Cities")

    server.settimeout(1.0) # Check for signals every 1s

    try:
        while True:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
                
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True # Allow thread to close when main program exits
            thread.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        server.close()
        print("[SERVER] Stopped.")

if __name__ == "__main__":
    main()