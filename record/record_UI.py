import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk
import threading
import sounddevice as sd
import numpy as np
import os
from datetime import datetime, timedelta
import sys
import wave  # 파일 쓰기를 위해 필요

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

stop_recording = threading.Event()  # 녹음 중지 이벤트
pause_recording = threading.Event()  # 녹음 일시 중지 이벤트
recording_lock_handle = None  # 녹음 락 핸들
instance_lock_handle = None  # 인스턴스 락 핸들
paused_time = None  # 일시 정지 시간 저장 변수
wf = None  # 녹음 파일 핸들

def resource_path(relative_path):
    """ 리소스 파일의 절대 경로를 반환합니다. """
    try:
        # PyInstaller가 생성한 임시 폴더에서 실행 중인지 확인합니다.
        base_path = sys._MEIPASS
    except Exception:
        # 그렇지 않다면 일반적인 Python 환경에서 실행 중입니다.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def resize_image(image_path, new_width, new_height):
    # 수정된 경로로 이미지 파일 열기
    adjusted_path = resource_path(image_path)
    original_image = Image.open(adjusted_path)
    resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(resized_image)

def reset_recording_state():
    """ 스레드 조인 로직 조정 """
    global recording_thread
    stop_recording.clear()
    pause_recording.clear()

    # 스레드가 자신을 조인하지 않도록 확인
    if threading.current_thread() != recording_thread and recording_thread.is_alive():
        recording_thread.join()
    release_lock(recording_lock_file, recording_lock_handle)
    # UI 업데이트
    app.after_cancel(update_job)
    elapsed_time.set("녹음 진행 시간 00:00:00")
    limit_time.set("녹음 남은 시간 01:00:00")
    start_button.config(state=tk.NORMAL, image=record_on_button_image)
    stop_button.config(state=tk.DISABLED, image=stop_off_button_image)
    pause_button.config(state=tk.DISABLED, image=pause_button_image)
    message_label.config(text="녹음을 시작해주세요.")


def record():
    """ 녹음을 처리하는 메인 함수 """
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(radio_folder, f'recording_{current_time}.wav')
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(np.dtype(np.int16).itemsize)  # Numpy dtype을 사용
    wf.setframerate(samplerate)

    try:
        with sd.InputStream(samplerate=samplerate, channels=channels, dtype='int16', callback=lambda indata, frames, time, status: wf.writeframes(indata.tobytes())):
            while not stop_recording.is_set():
                sd.sleep(100)
    except Exception as e:
        messagebox.showerror("녹음 오류", f"녹음 중 오류가 발생했습니다: {str(e)}")
        wf.close()
        reset_recording_state()
    finally:
        wf.close()

def acquire_lock(lock_file):
    """ 락 파일을 생성하여 프로세스 실행 중복을 방지 """
    try:
        return os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
    except FileExistsError:
        return None

def release_lock(lock_file, lock_handle):
    """ 락 파일을 해제하고 삭제하며, 실패 시 에러를 출력합니다. """
    error = False  # 에러 상태를 추적합니다.
    if lock_handle is not None:
        try:
            os.close(lock_handle)  # 파일 핸들 닫기
            os.remove(lock_file)  # 파일 삭제
        except Exception as e:
            print(f"Error releasing lock for {lock_file}: {e}")
            error = True
    return error

def start_recording():
    global recording_lock_handle, start_time, update_job, recording_thread
    if pause_recording.is_set():
        # 일시 정지된 상태에서 다시 시작
        pause_recording.clear()
        message_label.config(text="녹음 중...")
        start_time = datetime.now() - paused_time  # 저장된 경과 시간을 기준으로 시작 시간을 재설정
        update_clock()  # 타이머 업데이트를 재개합니다.
        start_button.config(state=tk.DISABLED, image=record_off_button_image)
        stop_button.config(state=tk.NORMAL, image=stop_on_button_image)
        pause_button.config(state=tk.NORMAL, image=pause_button_image)
    else:
        # 새로운 녹음 시작
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
        start_button.config(state=tk.DISABLED,fg="black", image=record_off_button_image)
        stop_button.config(state=tk.NORMAL, image=stop_on_button_image)
        pause_button.config(state=tk.NORMAL, image=pause_button_image)


def stop_recording_action():
    """ 녹음 중지 함수 """
    stop_recording.set()
    recording_thread.join()  # 녹음 스레드 완전히 종료 대기

    start_button.config(state=tk.NORMAL,fg="black", image=record_on_button_image)
    stop_button.config(state=tk.DISABLED, image=stop_off_button_image)
    pause_button.config(state=tk.DISABLED, image=pause_button_image)
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
        pause_button.config(state="disabled", image= pause_button_image)  # 일시정지 버튼 비활성화
        start_button.config(state="normal", image= record_on_button_image)  # 녹음 시작 버튼 활성화
    else:
        pause_recording.clear()
        message_label.config(text="녹음 중...")
        start_time = datetime.now() - paused_time
        update_clock()
        pause_button.config(state="normal", image=pause_button_image)  # 일시정지 버튼 활성화
        start_button.config(state="disabled", image=record_off_button_image)  # 녹음 시작 버튼 비활성화

def update_clock():
    """ 타이머 업데이트 함수 """
    global update_job
    now = datetime.now()
    elapsed = now - (start_time - timedelta(milliseconds=1))

    limit = timedelta(seconds=duration + 1) - elapsed

    if limit.total_seconds() < 0:
        limit = timedelta(seconds=0)

    elapsed_time.set("녹음 진행 시간 " + str(elapsed)[:-7])
    limit_time.set("녹음 남은 시간 " + str(limit)[:-7])

    update_job = app.after(1000, update_clock)
    if elapsed.total_seconds() >= duration:
        stop_recording_action()

# 애플리케이션 인스턴스 락 확인
instance_lock_handle = acquire_lock(instance_lock_file)
if instance_lock_handle is None:
    messagebox.showerror("Error", "실행 중 입니다.")
    sys.exit()


def exit_program():
    """ 프로그램을 종료하기 전에 모든 리소스가 제대로 해제되도록 깔끔하게 종료합니다. """
    global wf
    error_messages = []

    # UI 업데이트 부분을 제외하고 녹음을 중지
    if not stop_recording.is_set():
        stop_recording.set()
        if recording_thread.is_alive():
            recording_thread.join()

        # wave 파일 핸들을 닫습니다
        if wf is not None:
            wf.close()

        release_lock(recording_lock_file, recording_lock_handle)

    # 인스턴스 락 해제 시도
    if os.path.exists(instance_lock_file):
        if release_lock(instance_lock_file, instance_lock_handle):
            error_messages.append(f"인스턴스 락 해제 실패: {instance_lock_file}")

    if error_messages:
        error_msg = "\n".join(error_messages)
        messagebox.showerror("Lock Release Error", error_msg)

    sys.exit()  # 애플리케이션을 종료합니다

# 프로그램이 정상적으로 종료될 때 exit_program을 호출



def resize_image(image_path, new_width, new_height):
    # 이미지 파일을 열고 크기를 조정합니다.
    original_image = Image.open(image_path)
    resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(resized_image)

# 메인 애플리케이션 윈도우 설정
app = tk.Tk()
app.title("녹음 프로그램")
app.geometry("650x350")
app.configure(bg='white')

# 기존의 코드에서 이미지 로드 부분을 수정
record_on_button_image = resize_image(resource_path("record_on.png"), 100, 100)
record_off_button_image = resize_image(resource_path("record_off.png"), 100, 100)
stop_on_button_image = resize_image(resource_path("stop_on.png"), 100, 100)
stop_off_button_image = resize_image(resource_path("stop_off.png"), 100, 100)
pause_button_image = resize_image(resource_path("pause.png"), 100, 100)



custom_font = tkFont.Font(size=30, family='Helvetica')  # 사용할 폰트 설정
custom_font_time = tkFont.Font(size=20, family='Helvetica')

elapsed_time = tk.StringVar()
elapsed_time.set("녹음 진행 시간 00:00:00")  # 초기 경과 시간 설정

limit_time  = tk.StringVar()
limit_time .set("녹음 남은 시간 01:00:00") # 초기 제한 시간 설정

message_label = tk.Label(app, text="녹음을 시작해주세요.", font=custom_font)
message_label.pack(pady=10)

status_label = tk.Label(app, textvariable=limit_time, font=custom_font_time)
status_label.pack(pady=10)

status_label = tk.Label(app, textvariable=elapsed_time, font=custom_font_time)
status_label.pack(pady=10)

# 버튼 생성 및 배치
button_frame = tk.Frame(app, bg='white')
button_frame.pack(fill=tk.BOTH, expand=True)

start_button = tk.Button(button_frame, image=record_on_button_image, command=start_recording, font=custom_font, bg="white", borderwidth=0, state=tk.NORMAL)
start_button.pack(side=tk.LEFT,expand=True, fill=tk.BOTH)

stop_button = tk.Button(button_frame, image= stop_off_button_image, command=stop_recording_action, font=custom_font, fg="red", bg="white", borderwidth=0, state=tk.DISABLED)
stop_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

pause_button = tk.Button(button_frame, image=pause_button_image, command=pause_recording_action, font=custom_font, fg="black", bg="white", borderwidth=0, state=tk.DISABLED)
pause_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

app.protocol("WM_DELETE_WINDOW", exit_program)

app.mainloop()  # 애플리케이션 메인 루프

# 메인 루프가 끝나면 exit_program 호출
exit_program()
