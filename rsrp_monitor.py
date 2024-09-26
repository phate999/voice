import pyaudio
import numpy as np
import threading
from csclient import EventingCSClient

# Global variable to hold the frequency
frequency = 440.0
duration = 1.0  # Duration of each buffer chunk in seconds
sample_rate = 44100  # Sample rate (samples per second)


# Function to generate audio data for the current frequency
def generate_sine_wave(freq, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = 0.5 * np.sin(2 * np.pi * freq * t)
    audio_data = (audio_data * 32767).astype(np.int16)  # Convert to 16-bit audio
    return audio_data.tobytes()


# Function to continuously play audio
def play_tone():
    global frequency
    p = pyaudio.PyAudio()

    # Open an audio stream
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True)

    try:
        while True:
            # Generate the sine wave for the current frequency
            audio_bytes = generate_sine_wave(frequency, duration, sample_rate)
            stream.write(audio_bytes)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        # Stop and close the stream, terminate PyAudio
        stream.stop_stream()
        stream.close()
        p.terminate()


# Function to accept user input for frequency change
def change_frequency():
    global frequency
    try:
        while True:
            wan = cp.get('status/wan/primary_device')
            rsrp = cp.get(f'status/wan/devices/{wan}/diagnostics/RSRP')
            if rsrp:
                frequency = map_range(int(rsrp))
    except KeyboardInterrupt:
        print("\nStopping frequency change...")


def map_range(x, in_min=-50, in_max=-125, out_min=300, out_max=3000):
    """
    Maps a value x from one range to another.

    Parameters:
    x (float): The input value to map.
    in_min (float): The minimum value of the input range (default -50).
    in_max (float): The maximum value of the input range (default -125).
    out_min (float): The minimum value of the output range (default 300).
    out_max (float): The maximum value of the output range (default 3000).

    Returns:
    float: The value mapped to the output range.
    """
    # Apply the linear mapping formula
    return out_min + ((x - in_min) * (out_max - out_min) / (in_max - in_min))


# Setup CP
cp = EventingCSClient('monitor')

# Create and start the audio playing thread
audio_thread = threading.Thread(target=play_tone)
audio_thread.daemon = True  # Daemonize thread to allow program to exit
audio_thread.start()

# Start frequency change in the main thread
change_frequency()

# Wait for the audio thread to finish (which will never happen unless interrupted)
audio_thread.join()
