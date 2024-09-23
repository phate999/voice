# the following program is provided by DevMiser - https://github.com/DevMiser

import datetime
import io
import openai
import os
import pvcobra
import pvleopard
import pvporcupine
import pyaudio
import random
import struct
import sys
import textwrap
import threading
import time
import json

from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

from openai import OpenAI
from pvleopard import *
from pvrecorder import PvRecorder
from threading import Thread, Event
from time import sleep
from csclient import EventingCSClient
import logging

logging.basicConfig(filename='/usr/src/app/audio_recording.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

audio_stream = None
cobra = None
pa = None
porcupine = None
recorder = None
wav_file = None

defaults = {
    "GPT_model": "gpt-4",
    "openai.api_key": "Your OpenAI API Key",
    "pv_access_key": "Your Picovoice Access Key"
}

prompt = ["Cradlepoint here!",
          "How may I assist you?",
          "How may I help?",
          "What can I do for you?",
          "Ask me anything.",
          "Yes?",
          "I'm listening.",
          "What would you like me to do?"]


chat_log = [
    {"role": "system",
     "content": "Your name is Cradlepoint. You do not have a namesake. You are a helpful AI-based assistant."},
]

solid_bar = {"LED_BAR_0": 1, "LED_BAR_1": 1, "LED_BAR_2": 1, "LED_BAR_3": 1, "LED_BAR_4": 1, "LED_BAR_5": 1,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 1, "LED_BAR_10": 1, "LED_BAR_11": 1,
         "LED_BAR_12": 1, "LED_BAR_13": 1, "LED_BAR_14": 1}

# Cradlepoint will 'remember' earlier queries so that it has greater continuity in its response
# the following will delete that 'memory' three minutes after the start of the conversation
def append_clear_countdown():
    sleep(180)
    global chat_log
    chat_log.clear()
    chat_log = [
        {"role": "system", "content": "Your name is Cradlepoint. You do not have a namesake. You are a helpful assistant."},
    ]
    global count
    count = 0
    t_count.join


def ChatGPT(query):
    user_query = [
        {"role": "user", "content": query},
    ]
    send_query = (chat_log + user_query)
    response = client.chat.completions.create(
        model=GPT_model,
        messages=send_query
    )
    answer = response.choices[0].message.content
    chat_log.append({"role": "assistant", "content": answer})
    return answer


def current_time():
    time_now = datetime.datetime.now()
    formatted_time = time_now.strftime("%m-%d-%Y %I:%M %p\n")
    print("The current date and time is:", formatted_time)


def detect_silence():
    cobra = pvcobra.create(access_key=pv_access_key)

    silence_pa = pyaudio.PyAudio()

    cobra_audio_stream = silence_pa.open(
        rate=cobra.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=cobra.frame_length)

    last_voice_time = time.time()

    while True:
        cobra_pcm = cobra_audio_stream.read(cobra.frame_length)
        cobra_pcm = struct.unpack_from("h" * cobra.frame_length, cobra_pcm)

        if cobra.process(cobra_pcm) > 0.2:
            last_voice_time = time.time()
        else:
            silence_duration = time.time() - last_voice_time
            if silence_duration > 1.3:
                print("End of query detected\n")
                cobra_audio_stream.stop_stream
                cobra_audio_stream.close()
                cobra.delete()
                last_voice_time = None
                break

def listen():
    cobra = pvcobra.create(access_key=pv_access_key)

    listen_pa = pyaudio.PyAudio()

    listen_audio_stream = listen_pa.open(
        rate=cobra.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=cobra.frame_length)

    print("Listening...")

    while True:
        listen_pcm = listen_audio_stream.read(cobra.frame_length)
        listen_pcm = struct.unpack_from("h" * cobra.frame_length, listen_pcm)

        if cobra.process(listen_pcm) > 0.3:
            print("Voice detected")
            listen_audio_stream.stop_stream
            listen_audio_stream.close()
            cobra.delete()
            break

def responseprinter(chat):
    wrapper = textwrap.TextWrapper(width=70)  # Adjust the width to your preference
    paragraphs = res.split('\n')
    wrapped_chat = "\n".join([wrapper.fill(p) for p in paragraphs])
    for word in wrapped_chat:
        time.sleep(0.055)
        print(word, end="", flush=True)
    print()


def voice(chat):
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=chat
    )

    response.stream_to_file("speech.mp3")

    pygame.mixer.init()
    pygame.mixer.music.load("speech.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pass
    sleep(0.2)


def wake_word():
    porcupine = pvporcupine.create(keyword_paths=['cradle-point_en_raspberry-pi_v3_0_0.ppn'], access_key=pv_access_key)
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)

    wake_pa = pyaudio.PyAudio()

    porcupine_audio_stream = wake_pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length)

    print('Listening for "Cradlepoint"...')

    Detect = True

    while Detect:
        porcupine_pcm = porcupine_audio_stream.read(porcupine.frame_length)
        porcupine_pcm = struct.unpack_from("h" * porcupine.frame_length, porcupine_pcm)

        porcupine_keyword_index = porcupine.process(porcupine_pcm)

        if porcupine_keyword_index >= 0:

            print("\nWake word detected\n")
            current_time()
            porcupine_audio_stream.stop_stream
            porcupine_audio_stream.close()
            porcupine.delete()
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            Detect = False


class Recorder(Thread):
    def __init__(self):
        super().__init__()
        self._pcm = list()
        self._is_recording = False
        self._stop = False

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True

        recorder = PvRecorder(device_index=-1, frame_length=512)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())
        recorder.stop()

        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass

        return self._pcm

def wake_LEDs():
    time.sleep(1)
    leds = [
        {"LED_BAR_0": 0, "LED_BAR_1": 0, "LED_BAR_2": 0, "LED_BAR_3": 0, "LED_BAR_4": 0, "LED_BAR_5": 0,
         "LED_BAR_6": 0, "LED_BAR_7": 0, "LED_BAR_8": 0, "LED_BAR_9": 0, "LED_BAR_10": 0, "LED_BAR_11": 0,
         "LED_BAR_12": 0, "LED_BAR_13": 0, "LED_BAR_14": 0},
        {"LED_BAR_0": 0, "LED_BAR_1": 0, "LED_BAR_2": 0, "LED_BAR_3": 0, "LED_BAR_4": 0, "LED_BAR_5": 0,
         "LED_BAR_6": 0, "LED_BAR_7": 1, "LED_BAR_8": 0, "LED_BAR_9": 0, "LED_BAR_10": 0, "LED_BAR_11": 0,
         "LED_BAR_12": 0, "LED_BAR_13": 0, "LED_BAR_14": 0},
        {"LED_BAR_0": 0, "LED_BAR_1": 0, "LED_BAR_2": 0, "LED_BAR_3": 0, "LED_BAR_4": 0, "LED_BAR_5": 0,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 0, "LED_BAR_10": 0, "LED_BAR_11": 0,
         "LED_BAR_12": 0, "LED_BAR_13": 0, "LED_BAR_14": 0},
        {"LED_BAR_0": 0, "LED_BAR_1": 0, "LED_BAR_2": 0, "LED_BAR_3": 0, "LED_BAR_4": 0, "LED_BAR_5": 1,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 1, "LED_BAR_10": 0, "LED_BAR_11": 0,
         "LED_BAR_12": 0, "LED_BAR_13": 0, "LED_BAR_14": 0},
        {"LED_BAR_0": 0, "LED_BAR_1": 0, "LED_BAR_2": 0, "LED_BAR_3": 0, "LED_BAR_4": 1, "LED_BAR_5": 1,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 1, "LED_BAR_10": 1, "LED_BAR_11": 0,
         "LED_BAR_12": 0, "LED_BAR_13": 0, "LED_BAR_14": 0},
        {"LED_BAR_0": 0, "LED_BAR_1": 0, "LED_BAR_2": 0, "LED_BAR_3": 1, "LED_BAR_4": 1, "LED_BAR_5": 1,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 1, "LED_BAR_10": 1, "LED_BAR_11": 1,
         "LED_BAR_12": 0, "LED_BAR_13": 0, "LED_BAR_14": 0},
        {"LED_BAR_0": 0, "LED_BAR_1": 0, "LED_BAR_2": 1, "LED_BAR_3": 1, "LED_BAR_4": 1, "LED_BAR_5": 1,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 1, "LED_BAR_10": 1, "LED_BAR_11": 1,
         "LED_BAR_12": 1, "LED_BAR_13": 0, "LED_BAR_14": 0},
        {"LED_BAR_0": 0, "LED_BAR_1": 1, "LED_BAR_2": 1, "LED_BAR_3": 1, "LED_BAR_4": 1, "LED_BAR_5": 1,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 1, "LED_BAR_10": 1, "LED_BAR_11": 1,
         "LED_BAR_12": 1, "LED_BAR_13": 1, "LED_BAR_14": 0},
        {"LED_BAR_0": 1, "LED_BAR_1": 1, "LED_BAR_2": 1, "LED_BAR_3": 1, "LED_BAR_4": 1, "LED_BAR_5": 1,
         "LED_BAR_6": 1, "LED_BAR_7": 1, "LED_BAR_8": 1, "LED_BAR_9": 1, "LED_BAR_10": 1, "LED_BAR_11": 1,
         "LED_BAR_12": 1, "LED_BAR_13": 1, "LED_BAR_14": 1}
    ]
    for i in range(8, -1, -1):
        cp.put('control/gpio', leds[i])
        time.sleep(.02)
    for i in range(0, 9, 1):
        cp.put('control/gpio', leds[i])
        time.sleep(.02)
    for i in range(0, 3):
        cp.put('control/gpio', leds[7])
        time.sleep(.3)
        cp.put('control/gpio', leds[6])
        time.sleep(.3)
        cp.put('control/gpio', leds[7])
        time.sleep(.3)
        cp.put('control/gpio', leds[8])
        time.sleep(.3)

class Thinker:
    def __init__(self):
        self.thinking = True
    def start(self):
        leds = {}
        for i in range(14, -1, -1):
            leds[f"LED_BAR_{i}"] = 0
            cp.put('control/gpio', leds)
            time.sleep(.05)
        while self.thinking:
            for i in range(0, 15, 1):
                leds[f"LED_BAR_{i}"] = 1
                if i > 0:
                    leds[f"LED_BAR_{i-1}"] = 0
                cp.put('control/gpio', leds)
                time.sleep(0.05)
            for i in range(14, -1, -1):
                leds[f"LED_BAR_{i}"] = 1
                if i < 14:
                    leds[f"LED_BAR_{i + 1}"] = 0
                cp.put('control/gpio', leds)
                time.sleep(.05)
        for i in range(0, 15, 1):
            leds[f"LED_BAR_{i}"] = 1
            cp.put('control/gpio', leds)
            time.sleep(.01)

def network_status():
    connection_state = cp.get('status/wan/connection_state')
    primary_device = cp.get('status/wan/primary_device')
    carrier = cp.get(f'status/wan/devices/{primary_device}/diagnostics/CARRID')
    nc_state = cp.get('status/ecm/state')
    if carrier:
        RSRP = cp.get(f'status/wan/devices/{primary_device}/diagnostics/RSRP')
        res = f"The router is currently {connection_state} to {carrier} with {RSRP} R S R P. Net cloud is {nc_state}."
    else:
        primary_device = primary_device.replace('-', ' ')
        res = f"The router is currently {connection_state} on {primary_device}. Net cloud is {nc_state}."
    return res

def load_settings(name):
    """Load settings from SDK Appdata"""
    try:
        appdata = cp.get('config/system/sdk/appdata')
        data = json.loads([x["value"] for x in appdata if x["name"] == name][0])
    except:
        cp.log('No config found - saving defaults.')
        cp.post('config/system/sdk/appdata', {"name": name, "value": json.dumps(defaults)})
        data = defaults
    return data

try:
    cp = EventingCSClient('Voice')
    cp.log('Starting...')
    print('Starting...')

    data = load_settings('voice')
    GPT_model = data["GPT_model"]
    openai.api_key = data["openai.api_key"]
    pv_access_key = data["pv_access_key"]

    client = OpenAI(api_key=openai.api_key)

    o = create(access_key=pv_access_key)

    event = threading.Event()
    count = 0

    while True:

        try:

            Chat = 1
            if count == 0:
                t_count = threading.Thread(target=append_clear_countdown)
                t_count.start()
            else:
                pass
            count += 1
            voice("Say Cradlepoint to ask a question.")
            wake_word()
            Thread(target=wake_LEDs).start()
            # comment out the next line if you do not want Cradlepoint to verbally respond to his name
            voice(random.choice(prompt))
            recorder = Recorder()
            recorder.start()
            listen()
            detect_silence()
            thinking = True
            think = Thinker()
            t3 = threading.Thread(target=think.start)
            t3.start()
            transcript, words = o.process(recorder.stop())
            recorder.stop()
            print("You said: " + transcript)
            if transcript.lower() == 'network status':
                (res) = network_status()
            else:
                (res) = ChatGPT(transcript)
            print(f"\nCradlepoint's response is:\n{res}")
            t1 = threading.Thread(target=voice, args=(res,))
            t2 = threading.Thread(target=responseprinter, args=(res,))
            t1.start()
            t2.start()
            think.thinking = False
            t1.join()
            t2.join()
            t3.join()
            event.set()
            o.delete
            recorder = None

        except openai.APIError as e:
            print("\nThere was an API error.  Please try again in a few minutes.")
            voice("\nThere was an A P I error.  Please try again in a few minutes.")
            event.set()
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)

        except openai.RateLimitError as e:
            print("\nYou have hit your assigned rate limit.")
            voice("\nYou have hit your assigned rate limit.")
            event.set()
            recorder.stop()
            o.delete
            recorder = None
            break

        except openai.APIConnectionError as e:
            print(
                "\nI am having trouble connecting to the API.  Please check your network connection and then try again.")
            voice("\nI am having trouble connecting to the A P I.  Please check your network connection and try again.")
            event.set()
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)

        except openai.AuthenticationError as e:
            print(
                "\nYour OpenAI API key or token is invalid, expired, or revoked.  Please fix this issue and then restart my program.")
            voice(
                "\nYour OpenAI API key or token is invalid, expired, or revoked.  Please fix this issue and then restart my program.")
            event.set()
            recorder.stop()
            o.delete
            recorder = None
            break

except KeyboardInterrupt:
    print("\nExiting ChatGPT Virtual Assistant")
    o.delete
