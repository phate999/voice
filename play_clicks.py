import sounddevice as sd
import numpy as np


def generate_clicks(frequency_hz, duration_seconds=1.0, sample_rate=44100):
    """
    Generates a series of click sounds at the specified frequency (in Hz).

    :param frequency_hz: Frequency of clicks in Hertz (clicks per second).
    :param duration_seconds: Duration of the sound in seconds.
    :param sample_rate: Sampling rate of the sound (default: 44100 Hz).
    """
    # Calculate the time between clicks
    click_interval = 1.0 / frequency_hz

    # Create a time array for the entire duration
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)

    # Generate a click sound (a simple pulse)
    click_sound = np.zeros_like(t)
    click_length = int(sample_rate * 0.01)  # Click duration: 0.01 seconds

    # Place clicks at intervals
    for i in range(0, len(t), int(sample_rate * click_interval)):
        click_sound[i:i + click_length] = 1.0  # Generate a click as a short pulse

    return click_sound


def play_clicks(frequency_hz, duration_seconds=1.0, sample_rate=44100):
    """
    Plays click sounds at the specified frequency using sounddevice.

    :param frequency_hz: Frequency of the clicks in Hertz.
    :param duration_seconds: Duration of the sound in seconds.
    :param sample_rate: Sampling rate (default: 44100 Hz).
    """
    # Generate click sound
    click_sound = generate_clicks(frequency_hz, duration_seconds, sample_rate)

    # Play sound using sounddevice
    sd.play(click_sound, samplerate=sample_rate)
    sd.wait()  # Wait until the sound is done playing


if __name__ == "__main__":
    # Example: play clicks at 2 Hz for 5 seconds
    play_clicks(frequency_hz=2, duration_seconds=5)
