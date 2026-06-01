import numpy as np


def square_wavetable(amp, freq, phase, sample_rate, duration, additive_harmonics, start_time=0.0):
    t = np.linspace(start_time, start_time + duration, int(sample_rate * duration), endpoint=False)

    waveform = np.zeros_like(t)

    for k in range(additive_harmonics):
        n = 2 * k + 1  # 1, 3, 5, 7...

        if freq * n >= sample_rate / 2:
            break

        waveform += np.sin(2 * np.pi * freq * n * t + n * phase) / n

    waveform *= 4 / np.pi

    peak = np.max(np.abs(waveform))
    if peak > 0:
        waveform = waveform / peak * amp

    return waveform

def triangle_wavetable(amp, freq, phase, sample_rate, duration, additive_harmonics, start_time=0.0):
    t = np.linspace(start_time, start_time + duration, int(sample_rate * duration), endpoint=False)

    waveform = np.zeros_like(t)

    for k in range(additive_harmonics):
        n = 2 * k + 1  
        if freq * n >= sample_rate / 2:
            break
        sign = (-1) ** k
        waveform += sign * np.sin(
            2 * np.pi * freq * n * t + n * phase
        ) / (n ** 2)

    waveform *= 8 * amp / (np.pi ** 2)

    peak = np.max(np.abs(waveform))
    if peak > 0:
        waveform = waveform / peak * amp

    return waveform

def saw_wavetable(amp, freq, phase, sample_rate, duration, additive_harmonics, start_time=0.0):
    t = np.linspace(start_time, start_time + duration, int(sample_rate * duration), endpoint=False)
    waveform = np.zeros_like(t)
    
    for k in range(additive_harmonics):
        n = k+1
        if freq * (k + 1) >= sample_rate / 2:
            break
        waveform += np.sin(2 * np.pi * freq * n * t + n * phase) / n
    waveform *= (amp/2 - amp / np.pi)
    
    peak = np.max(np.abs(waveform))
    if peak > 0:
        waveform = waveform / peak * amp
    
    return waveform

def sine_wavetable(amp, freq, phase, sample_rate, duration, additive_harmonics, start_time=0.0):
    t = np.linspace(start_time, start_time + duration, int(sample_rate * duration), endpoint=False)
    waveform = np.sin(2 * np.pi * freq * t + phase)
    return waveform * amp

WAVEFORM_GENERATORS = {
    "sine": sine_wavetable,
    "square": square_wavetable,
    "triangle": triangle_wavetable,
    "saw": saw_wavetable
}