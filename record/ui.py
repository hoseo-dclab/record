# import tkinter as tk
# import tkinter.font as tkFont
# from tkinter import messagebox
# import threading
# import sounddevice as sd
# import numpy as np
# import scipy.io.wavfile as wav
# import queue
# import os
# from datetime import datetime, timedelta
# import sys
#
# # 녹음 설정
# samplerate = 44100
# channels = 2
# duration = 3600
#
# # C:\Radio 폴더 경로
# radio_folder = "C:\\Radio"
# if not os.path.exists(radio_folder):
#     os.makedirs(radio_folder)
#
# # 락 파일 경로 설정
# instance_lock_file = os.path.join(radio_folder, 'instance.lock')
# recording_lock_file = os.path.join(radio_folder, 'recording.lock')
#
# q = queue.Queue()
# stop_recording = threading.Event()
# pause_recording = threading.Event()
# recording_lock_handle = None
# instance_lock_handle = None
# paused_time = None  # 일시 정지 시간을 저장할 변수
#
# def audio_callback(indata, frames, time, status):
#     if not pause_recording.is_set():
#         q.put(indata.copy())
#
# def record():
#     with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
#         while not stop_recording.is_set():
#             sd.sleep(100)
#     save_recording()
#
# def save_recording():
#     current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = os.path.join(radio_folder, f'recording_{current_time}.wav')
#     frames = []
#     while not q.empty():
#         frames.append(q.get())
#     audio_data = np.concatenate(frames, axis=0)
#     wav.write(filename, samplerate, audio_data)
#     release_lock(recording_lock_file, recording_lock_handle)
#
# def acquire_lock(lock_file):
#     try:
#         return os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
#     except FileExistsError:
#         return None
#
# def release_lock(lock_file, lock_handle):
#     if lock_handle is not None:
#         os.close(lock_handle)
#         os.remove(lock_file)
#     except Exception as e:
#         print(f"Error releasing lock: {e}")
# def start_recording():
#     global recording_lock_handle, start_time, update_job, recording_thread
#     recording_lock_handle = acquire_lock(recording_lock_file)
#     if recording_lock_handle is None:
#         messagebox.showerror("Error", "Another recording process is already running.")
#         return
#
#     start_time = datetime.now()
#     update_clock()
#
#     stop_recording.clear()
#     pause_recording.clear()
#     recording_thread = threading.Thread(target=record)
#     recording_thread.start()
#     message_label.config(text="녹음 중...")
#     start_button.config(state=tk.DISABLED)
#     stop_button.config(state=tk.NORMAL)
#     pause_button.config(state=tk.NORMAL)
#
# def stop_recording_action():
#     stop_recording.set()
#     start_button.config(state=tk.NORMAL)
#     stop_button.config(state=tk.DISABLED)
#     pause_button.config(state=tk.DISABLED)
#     message_label.config(text="녹음이 종료되었습니다.")
#     app.after_cancel(update_job)
#
# def pause_recording_action():
#     global update_job, paused_time, start_time
#     if not pause_recording.is_set():
#         pause_recording.set()
#         message_label.config(text="녹음 일시중지")
#         paused_time = datetime.now() - start_time  # 일시 정지 시간을 저장
#         app.after_cancel(update_job)  # 타이머 업데이트를 중지합니다.
#     else:
#         pause_recording.clear()
#         message_label.config(text="녹음 중...")
#         start_time = datetime.now() - paused_time  # 저장된 경과 시간을 기준으로 시작 시간을 재설정
#         update_clock()  # 타이머 업데이트를 재개합니다.
#
# def update_clock():
#     global update_job
#     now = datetime.now()
#     elapsed = now - (start_time - timedelta(milliseconds = 1))  # 시작 시간부터 현재 시간까지의 경과 시간
#     elapsed_time.set(str(elapsed)[:-7])  # 밀리초를 제외하고 시간을 표시
#     update_job = app.after(1000, update_clock)  # 1초마다 시간 업데이트
#
# app = tk.Tk()
# app.title("녹음 프로그램")
# app.geometry("600x200")
# app.configure(bg='white')
#
# custom_font = tkFont.Font(size=25, family='Helvetica')
#
# elapsed_time = tk.StringVar()
# elapsed_time.set("00:00:00")
#
# message_label = tk.Label(app, text="녹음을 시작해주세요.", font=custom_font)
# message_label.pack(pady=10)
#
# status_label = tk.Label(app, textvariable=elapsed_time, font=custom_font)
# status_label.pack(pady=10)
#
# # 버튼
# button_frame = tk.Frame(app, bg='white')
# button_frame.pack(fill=tk.BOTH, expand=True)
#
# start_button = tk.Button(button_frame, text="▶", command=start_recording, font=custom_font, fg="black", bg="white", borderwidth=0)
# start_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
#
# stop_button = tk.Button(button_frame, text="■", command=stop_recording_action, font=custom_font, fg="red", bg="white", borderwidth=0)
# stop_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
#
# pause_button = tk.Button(button_frame, text="||", command=pause_recording_action, font=custom_font, fg="black", bg="white", borderwidth=0)
# pause_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
#
# app.mainloop()


import tkinter as tk
from tkinter import messagebox
import threading
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import queue
import os
from datetime import datetime
import sys

# 녹음 설정
samplerate = 44100
channels = 2
duration = 3600

# C:\Radio 폴더 경로
radio_folder = "C:\\Radio"
if not os.path.exists(radio_folder):
    os.makedirs(radio_folder)

# 락 파일 경로 설정
instance_lock_file = os.path.join(radio_folder, 'instance.lock')
recording_lock_file = os.path.join(radio_folder, 'recording.lock')

q = queue.Queue()
stop_recording = threading.Event()
pause_recording = threading.Event()
recording_lock_handle = None
instance_lock_handle = None

def audio_callback(indata, frames, time, status):
    if not pause_recording.is_set():
        q.put(indata.copy())

def record():
    with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
        while not stop_recording.is_set():
            sd.sleep(100)
    save_recording()

def save_recording():
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(radio_folder, f'recording_{current_time}.wav')
    frames = []
    while not q.empty():
        frames.append(q.get())
    audio_data = np.concatenate(frames, axis=0)
    wav.write(filename, samplerate, audio_data)
    release_lock(recording_lock_file, recording_lock_handle)

def acquire_lock(lock_file):
    try:
        return os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
    except FileExistsError:
        return None

def release_lock(lock_file, lock_handle):
    if lock_handle is not None:
        try:
            os.close(lock_handle)
            os.remove(lock_file)
        except Exception as e:
            print(f"Error releasing lock: {e}")

def start_recording():
    global recording_lock_handle
    recording_lock_handle = acquire_lock(recording_lock_file)
    if recording_lock_handle is None:
        messagebox.showerror("Error", "Another recording process is already running.")
        return

    global recording_thread
    stop_recording.clear()
    pause_recording.clear()
    recording_thread = threading.Thread(target=record)
    recording_thread.start()
    status_label.config(text="녹음 중...")
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    pause_button.config(state=tk.NORMAL)
    app.after(100, check_thread)

def stop_recording_action():
    stop_recording.set()
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    pause_button.config(state=tk.DISABLED)

def pause_recording_action():
    if not pause_recording.is_set():
        pause_recording.set()
        status_label.config(text="녹음 일시중지")
    else:
        pause_recording.clear()
        status_label.config(text="녹음 재개")

def check_thread():
    if recording_thread.is_alive():
        app.after(100, check_thread)
    else:
        status_label.config(text="녹음이 종료되었습니다.")
        start_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)
        pause_button.config(state=tk.DISABLED)
        release_lock(recording_lock_file, recording_lock_handle)

# 인스턴스 락을 확인
instance_lock_handle = acquire_lock(instance_lock_file)
if instance_lock_handle is None:
    messagebox.showerror("Error", "Another instance of the program is already running.")
    sys.exit()  # 종료

app = tk.Tk()
app.title("녹음 프로그램")
app.geometry("300x150")

status_label = tk.Label(app, text="녹음을 시작해주세요.")
status_label.pack(pady=10)

start_button = tk.Button(app, text="녹음 시작", command=start_recording)
start_button.pack(fill=tk.X, padx=50, pady=5)

stop_button = tk.Button(app, text="녹음 중지", command=stop_recording_action, state=tk.DISABLED)
stop_button.pack(fill=tk.X, padx=50, pady=5)

pause_button = tk.Button(app, text="일시 중지/재개", command=pause_recording_action, state=tk.DISABLED)
pause_button.pack(fill=tk.X, padx=50, pady=5)

app.mainloop()

# Release the instance lock when the main application loop is exited
release_lock(instance_lock_file, instance_lock_handle)




