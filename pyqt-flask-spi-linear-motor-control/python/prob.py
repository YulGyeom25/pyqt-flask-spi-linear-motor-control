# flask import
from flask import Flask, request, jsonify

# spidev import
import spidev
import struct
import subprocess
import threading
import time
import os

# Flask 기능 정의
app = Flask(__name__)

# SPI 설정
spi = spidev.SpiDev()
spi.open(0, 0)  # bus: 0, device: 0 (CS0 사용)
spi.max_speed_hz = 50000  # 속도 설정 (Hz 단위)
spi.mode = 0b00  # SPI 모드 설정

# initiate variables
Velocity = 0.0
Pulse = 0
direction = "stop"
stepAngle = 1.8
microsteping = 200
lead = 1  # linearVelocity = lead*rev
last_update_time = time.time()  # 마지막 거리 업데이트 시간 <gochim!!!>

MIN_DISTANCE = 1.0
MAX_DISTANCE = 49.0

DISTANCE_FILE = "distance.txt"

def load_distance():
    global distance
    if os.path.exists(DISTANCE_FILE):  # 파일이 존재하는 경우
        with open(DISTANCE_FILE, "r") as f:
            try:
                distance = float(f.read().strip())
                if distance < MIN_DISTANCE:  # 최소 거리 제한
                    distance = MIN_DISTANCE
                print(f"Loaded distance: {distance} mm")
            except ValueError:
                distance = MIN_DISTANCE  # 파일이 손상된 경우 초기화
    else:
        distance = MIN_DISTANCE  # 파일이 없으면 최소 거리로 초기화

def save_distance():
    with open(DISTANCE_FILE, "w") as f:
        f.write(str(distance))

# distance 불러오기 (Flask 시작 시 실행)
load_distance()

# 현재 위치 초기화 및 전송 (Start 버튼)
@app.route('/start', methods=['GET'])
def start():
    global distance
    try:
        distance = 0  # 현재 위치 초기화
        save_distance()

        # SPI를 통해 'Start' 신호 전송
        start_signal = [0xFF]  
        spi.xfer2(start_signal)

        print("Start signal sent to Arduino, Position Reset to 0mm")

        # 🔹 속도를 0 → 1mm/s로 서서히 증가
        for speed in range(0, 11, 2):  # 0, 2, 4, ..., 10 (10mm/min)
            send_data(speed, "right")
            time.sleep(0.5)  # 천천히 증가

        return jsonify({"message": "Start complete, moved smoothly", "current_position": distance})

    except Exception as e:
        return jsonify({"error": f"Failed to start: {e}"}), 500

# 모터 정지
def stop_motor():
    global Velocity, last_update_time
    Velocity = 0
    last_update_time = time.time()

    pulse_bytes = struct.pack('<f', 0)
    direction_code = 0  # Stop 명령
    spi.xfer2(list(pulse_bytes) + [direction_code])
    print("Motor stopped")

def update_distance():
    """ 거리 자동 업데이트 스레드 """
    global distance, Velocity, direction, last_update_time

    while True:
# <gochim>
        current_time = time.time()
        elapsed_time = current_time - last_update_time  
        #elapsed_time  = 0.3
        if Velocity > 0 and direction in ["right", "left"]:
            if elapsed_time > 0.3:  # 0.3초마다 거리 업데이트 <gochim>
                if direction == "right":
                    distance += (Velocity * elapsed_time / 60.0)
                    if distance >= MAX_DISTANCE:
                        distance = MAX_DISTANCE
                        stop_motor()
                elif direction == "left":
                    distance -= (Velocity * elapsed_time / 60.0)
                    if distance <= MIN_DISTANCE:
                        distance = MIN_DISTANCE
# <gochim>
                last_update_time = current_time
                save_distance()  # distance.txt에 저장

                print(f"🔄 Updated Distance: {distance:.2f} mm | Direction: {direction}")

        else :
            last_update_time = time.time()
# <gochim>
        time.sleep(0.1)  

# 거리 자동 전송 함수 (1초마다 Flask에 거리 정보 전송)
def send_distance_periodically():
    global last_sent_distance
    while True:
        time.sleep(3)
        if distance != last_sent_distance:
            last_sent_distance = distance
            print(f"[Auto Update] Current Distance: {distance:.2f} mm")

# 거리 업데이트 스레드 실행
threading.Thread(target=update_distance, daemon=True).start()
threading.Thread(target=send_distance_periodically, daemon=True).start()

# 속도 및 방향 명령 처리
@app.route('/submit', methods=['POST'])
def submit_form():
    global Velocity, Pulse, direction

    try:
        data = request.get_json()
        Velocity = float(data['velocity'])
        direction = data['direction']

        # 속도 → 펄스 변환
        Pulse = abs(((Velocity / (lead * 60)) * 360 * microsteping) / (stepAngle))

        if direction not in ['left', 'right', 'stop']:
            return jsonify({"error": "Invalid direction selected"}), 400

        print(f"Velocity: {Velocity}, Pulse: {Pulse}, Direction: {direction}")
        send_data(Pulse, direction)
        return jsonify({"message": "Command received", "velocity": Velocity, "direction": direction})

    except ValueError:
        return jsonify({"error": "Invalid input for Velocity"}), 400

# 현재 위치 데이터 반환
last_sent_distance = None  

@app.route('/current_position', methods=['GET'])
def get_current_position():
    global last_sent_distance  # 전역 변수 선언

    if distance != last_sent_distance:  # 중복 값 전송 방지
        last_sent_distance = distance
        print(f"[Position Update] Current Position: {distance:.2f} mm")  # 터미널에 거리 출력

    return jsonify({"current_position": distance})  # 소수점 2자리로 반환


# SPI 데이터 전송 함수
def send_data(pulse, direction_code):
    try:
        pulse_bytes = struct.pack('<f', pulse)
        direction_code = {'left': 1, 'right': 2, 'stop': 0}.get(direction_code, 0)

        spi.xfer2(list(pulse_bytes) + [direction_code])
        print(f"Data sent - Pulse: {pulse}, Direction: {direction_code}")

    except Exception as e:
        print(f"Failed to send data via SPI: {e}")

def run_ui():
    subprocess.Popen(["python3", "subwindow.py"])  # PySide6 UI 파일 실행

# Flask 앱 실행
if __name__ == '__main__':
    run_ui()  # Flask 실행 전 UI 한 번만 실행
    threading.Thread(target=update_distance, daemon=True).start()
    threading.Thread(target=send_distance_periodically, daemon=True).start()

    try:
        app.run(host='127.0.0.1', port=5000, debug=True)
    finally:
        print("Flask server shutting down")
