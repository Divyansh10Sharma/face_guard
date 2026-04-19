import pygame
import numpy as np


def generate_tone(frequency, duration_ms, volume=0.6, wave="sine", fade_ms=30):
    """
    Generates a pygame Sound object for a single tone.

    frequency   : pitch in Hz (440=A4, 880=A5)
    duration_ms : length in milliseconds
    volume      : loudness 0.0–1.0
    wave        : "sine" (smooth), "square" (buzzy), "triangle" (in-between)
    fade_ms     : fade in/out duration to prevent audio clicks
    """
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)

    if wave == "sine":
        samples = np.sin(2 * np.pi * frequency * t)
    elif wave == "square":
        samples = np.sign(np.sin(2 * np.pi * frequency * t))
    elif wave == "triangle":
        samples = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
    else:
        samples = np.sin(2 * np.pi * frequency * t)

    fade_n = int(sample_rate * fade_ms / 1000)
    if len(samples) > 2 * fade_n:
        samples[:fade_n]  *= np.linspace(0, 1, fade_n)
        samples[-fade_n:] *= np.linspace(1, 0, fade_n)

    samples = (samples * volume * 32767).astype(np.int16)
    stereo = np.column_stack([samples, samples])
    return pygame.sndarray.make_sound(stereo.copy())
