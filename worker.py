import socket
import pickle
import struct
import time

SERVER_IP = '127.0.0.1' # แก้เป็น IP เครื่อง Server ถ้าอยู่คนละเครื่อง
PORT = 9999

# ฟังก์ชันช่วยส่งข้อมูล (เหมือน Server)
def send_data(sock, data):
    serialized = pickle.dumps(data)
    sock.sendall(struct.pack('>I', len(serialized)) + serialized)

def recv_data(sock):
    raw_msglen = sock.recv(4)
    if not raw_msglen: return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    data = b''
    while len(data) < msglen:
        packet = sock.recv(msglen - len(data))
        if not packet: return None
        data += packet
    return pickle.loads(data)

def calculate_path_cost(graph, path):
    cost = 0
    for i in range(len(path) - 1):
        cost += graph[path[i]][path[i+1]]
    return cost

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP, PORT))
        print("[CONNECTED] Connected to Server.")

        # 1. รับ Config เริ่มต้น
        init_data = recv_data(client)
        graph = init_data['graph']
        num_cities = init_data['num_cities']
        print(f"[INFO] Graph received. Cities: {num_cities}")

        while True:
            # 2. ของาน
            send_data(client, {'type': 'REQUEST_JOB'})
            response = recv_data(client)

            if response['type'] == 'JOB':
                path = response['path']
                current_server_best = response['current_best']
                
                print(f"[WORKING] Expanding path: {path}")
                
                # --- BFS LOGIC (EXPANSION) ---
                last_city = path[-1]
                current_cost = calculate_path_cost(graph, path)
                
                # Pruning: ถ้า Cost ปัจจุบันเกิน Best Cost ของ Server ก็ทิ้งเลย
                if current_cost >= current_server_best:
                     send_data(client, {'type': 'JOB_RESULT', 'new_paths': []})
                     continue

                new_generated_paths = []
                complete_path = None
                final_cost = 0

                # ถ้า Path ครบทุกเมืองแล้ว -> ต้องกลับจุดเริ่มต้น (City 0)
                if len(path) == num_cities:
                    # กลับไปจุดเริ่ม 0
                    total_cost = current_cost + graph[last_city][0]
                    complete_path = path + [0]
                    final_cost = total_cost
                else:
                    # ลองเดินไปเมืองอื่นที่ยังไม่เคยไป
                    for next_city in range(num_cities):
                        if next_city not in path:
                            new_path = path + [next_city]
                            new_generated_paths.append(new_path)

                # 3. ส่งผลลัพธ์กลับ
                result_payload = {
                    'type': 'JOB_RESULT',
                    'new_paths': new_generated_paths,
                    'complete_path': complete_path,
                    'cost': final_cost
                }
                send_data(client, result_payload)
                
                # หน่วงเวลานิดนึงให้ดูทัน (เอาออกได้ถ้าอยากให้เร็ว)
                time.sleep(0.5) 

            elif response['type'] == 'WAIT':
                print("[WAIT] Queue empty, waiting for more jobs...")
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("Stopping worker...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()