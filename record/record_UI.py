import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox
import threading
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import queue
import os
from datetime import datetime, timedelta
import sys

# 녹음 설정
samplerate = 44100  # 샘플링 레이트 설정
channels = 2        # 채널 수 설정 (스테레오)
duration = 3600     # 최대 녹음 시간 설정 (1시간)

# 녹음 파일 저장 폴더 경로 설정
radio_folder = "C:\\Radio"
if not os.path.exists(radio_folder):
    os.makedirs(radio_folder)  # 폴더가 존재하지 않으면 생성

# 락 파일 경로 설정
instance_lock_file = os.path.join(radio_folder, 'instance.lock')
recording_lock_file = os.path.join(radio_folder, 'recording.lock')

# 녹음 데이터를 저장할 큐
q = queue.Queue()
stop_recording = threading.Event()  # 녹음 중지 이벤트
pause_recording = threading.Event()  # 녹음 일시 중지 이벤트
recording_lock_handle = None  # 녹음 락 핸들
instance_lock_handle = None  # 인스턴스 락 핸들
paused_time = None  # 일시 정지 시간 저장 변수

def audio_callback(indata, frames, time, status):
    """ 오디오 콜백 함수: 입력된 오디오 데이터를 큐에 저장 """
    if not pause_recording.is_set():
        q.put(indata.copy())

def record():
    """ 녹음을 처리하는 메인 함수 """
    with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
        while not stop_recording.is_set():
            sd.sleep(10)
    save_recording()  # 녹음 중지 시 데이터 저장

def save_recording():
    """ 녹음된 오디오 데이터를 파일로 저장 """
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(radio_folder, f'recording_{current_time}.wav')
    frames = []
    while not q.empty():
        frames.append(q.get())
    audio_data = np.concatenate(frames, axis=0)
    wav.write(filename, samplerate, audio_data)

def acquire_lock(lock_file):
    """ 락 파일을 생성하여 프로세스 실행 중복을 방지 """
    try:
        return os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
    except FileExistsError:
        return None

def release_lock(lock_file, lock_handle):
    """ 락 파일을 해제하고 삭제 """
    if lock_handle is not None:
        try:
            os.close(lock_handle)
            os.remove(lock_file)
        except Exception as e:
            print(f"Error releasing lock: {e}")

def start_recording():
    """ 녹음 시작 함수 """
    global recording_lock_handle, start_time, update_job, recording_thread
    recording_lock_handle = acquire_lock(recording_lock_file)
    if recording_lock_handle is None:
        messagebox.showerror("Error", "실행 중 입니다.")
        return

    start_time = datetime.now()
    update_clock()

    stop_recording.clear()
    pause_recording.clear()
    recording_thread = threading.Thread(target=record)
    recording_thread.start()
    message_label.config(text="녹음 중...")
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    pause_button.config(state=tk.NORMAL)

def stop_recording_action():
    """ 녹음 중지 함수 """
    stop_recording.set()
    recording_thread.join()  # 녹음 스레드 완전히 종료 대기

    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    pause_button.config(state=tk.DISABLED)
    message_label.config(text="녹음이 종료되었습니다.")
    app.after_cancel(update_job)

    release_lock(recording_lock_file, recording_lock_handle)

def pause_recording_action():
    """ 녹음 일시정지/재개 함수 """
    global update_job, paused_time, start_time
    if not pause_recording.is_set():
        pause_recording.set()
        message_label.config(text="녹음 일시중지")
        paused_time = datetime.now() - start_time
        app.after_cancel(update_job)
    else:
        pause_recording.clear()
        message_label.config(text="녹음 중...")
        start_time = datetime.now() - paused_time
        update_clock()

def update_clock():
    """ 타이머 업데이트 함수 """
    global update_job
    now = datetime.now()
    elapsed = now - (start_time - timedelta(milliseconds=1))
    elapsed_time.set(str(elapsed)[:-7])
    update_job = app.after(1000, update_clock)

# 애플리케이션 인스턴스 락 확인
instance_lock_handle = acquire_lock(instance_lock_file)
if instance_lock_handle is None:
    messagebox.showerror("Error", "실행 중 입니다.")
    sys.exit()

# 메인 애플리케이션 윈도우 설정
app = tk.Tk()
app.title("녹음 프로그램")
app.geometry("600x300")
app.configure(bg='white')

custom_font = tkFont.Font(size=30, family='Helvetica')  # 사용할 폰트 설정

elapsed_time = tk.StringVar()
elapsed_time.set("00:00:00")  # 초기 경과 시간 설정

message_label = tk.Label(app, text="녹음을 시작해주세요.", font=custom_font)
message_label.pack(pady=10)

status_label = tk.Label(app, textvariable=elapsed_time, font=custom_font)
status_label.pack(pady=10)

# 버튼 생성 및 배치
button_frame = tk.Frame(app, bg='white')
button_frame.pack(fill=tk.BOTH, expand=True)

start_button = tk.Button(button_frame, text="▶", command=start_recording, font=custom_font, fg="black", bg="white", borderwidth=0)
start_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

stop_button = tk.Button(button_frame, text="■", command=stop_recording_action, font=custom_font, fg="red", bg="white", borderwidth=0, state=tk.DISABLED)
stop_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

pause_button = tk.Button(button_frame, text="||", command=pause_recording_action, font=custom_font, fg="black", bg="white", borderwidth=0, state=tk.DISABLED)
pause_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

app.mainloop()  # 애플리케이션 메인 루프

release_lock(instance_lock_file, instance_lock_handle)  # 인스턴스 락 해제
