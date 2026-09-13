"""
Генерує звукові ефекти (.wav) без зовнішніх бібліотек - чистий синтез тонів
через модуль wave. Результат зберігається у assets/sounds.
"""
import math
import wave
import struct
import random

RATE = 44100
OUT = "assets/sounds"


def tone(freq, duration, volume=0.5, shape="sine", fade=True, freq_end=None):
    n = int(RATE * duration)
    samples = []
    for i in range(n):
        t = i / RATE
        if freq_end is not None:
            f = freq + (freq_end - freq) * (i / n)
        else:
            f = freq
        if shape == "sine":
            v = math.sin(2 * math.pi * f * t)
        elif shape == "square":
            v = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
        elif shape == "noise":
            v = random.uniform(-1, 1)
        else:
            v = math.sin(2 * math.pi * f * t)
        env = 1.0
        if fade:
            attack = 0.05
            release = 0.3
            if i < n * attack:
                env = i / (n * attack)
            elif i > n * (1 - release):
                env = (n - i) / (n * release)
        samples.append(v * volume * env)
    return samples


def mix(*layers):
    n = max(len(l) for l in layers)
    out = [0.0] * n
    for l in layers:
        for i, v in enumerate(l):
            out[i] += v
    peak = max(1.0, max(abs(v) for v in out))
    return [v / peak for v in out]


def save_wav(samples, name):
    path = f"{OUT}/{name}.wav"
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        frames = b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32000)) for v in samples)
        f.writeframes(frames)
    print("saved", name)


def make_wall_hit():
    s = tone(520, 0.08, volume=0.5, shape="square", freq_end=380)
    save_wav(s, "wall_hit")


def make_paddle_hit():
    s = tone(280, 0.1, volume=0.6, shape="square", freq_end=700)
    save_wav(s, "paddle_hit")


def make_score():
    a = tone(392, 0.12, volume=0.5, shape="sine")
    b = tone(523, 0.12, volume=0.5, shape="sine")
    c = tone(659, 0.22, volume=0.5, shape="sine")
    save_wav(a + b + c, "score")


def make_click():
    s = tone(900, 0.05, volume=0.4, shape="square")
    save_wav(s, "click")


def make_win():
    notes = [523, 659, 784, 1046]
    out = []
    for f in notes:
        out += tone(f, 0.18, volume=0.45, shape="sine")
    save_wav(out, "win")


def make_lose():
    notes = [400, 340, 280, 220]
    out = []
    for f in notes:
        out += tone(f, 0.22, volume=0.4, shape="sine")
    save_wav(out, "lose")


def make_countdown():
    s = tone(660, 0.15, volume=0.5, shape="sine")
    save_wav(s, "countdown_tick")


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    make_wall_hit()
    make_paddle_hit()
    make_score()
    make_click()
    make_win()
    make_lose()
    make_countdown()
    print("Готово! Усі звуки згенеровано у", OUT)
