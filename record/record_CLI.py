import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import queue
import threading
import os
import keyboard
from datetime import datetime

# 녹음 설정
samplerate = 44100  # 샘플링 속도
channels = 2  # 오디오 채널 수 (스테레오)
duration = 3600  # 녹음 시간 (초)

# C:\Radio 폴더 경로
radio_folder = "C:\\Radio"

# Radio 폴더가 없으면 생성
if not os.path.exists(radio_folder):
    os.makedirs(radio_folder)

# 녹음 데이터 저장을 위한 큐
q = queue.Queue()

# 녹음 중지 플래그
stop_recording = threading.Event()

def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status)
    q.put(indata.copy())

def record():
    while not stop_recording.is_set():
        # 현재 날짜와 시간을 사용하여 파일 이름 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(radio_folder, f'recording_{current_time}.wav')

        print(f"녹음 파일명: {filename}")
        start_time = datetime.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"녹음 시작 시간: {start_time_str}")

        with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
            print(f"{duration / 60}분 동안 녹음합니다... (CTRL+Z로 중지)")
            for _ in range(int(duration * 10)):  # 0.1초마다 체크
                if stop_recording.is_set():
                    break
                sd.sleep(100)

        end_time = datetime.now()
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"녹음 종료 시간: {end_time_str}")
        print("녹음 완료.")

        save_recording(filename)

def save_recording(filename):
    print("녹음 데이터를 파일로 저장합니다...")
    frames = []
    while not q.empty():
        frames.append(q.get())

    audio_data = np.concatenate(frames, axis=0)
    wav.write(filename, samplerate, audio_data)
    print("파일 저장 완료:", filename)

def check_stop_key():
    keyboard.wait('ctrl+z')
    stop_recording.set()

# 키보드 입력 체크 스레드 실행
keyboard_thread = threading.Thread(target=check_stop_key)
keyboard_thread.start()

# 녹음 스레드 실행
record_thread = threading.Thread(target=record)
record_thread.start()

# 녹음 스레드가 종료될 때까지 대기
record_thread.join()

print("프로그램이 종료되었습니다.")
