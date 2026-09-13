"""
Генерує всі текстури для гри (фон, м'ячі, платформи, кнопки) та зберігає їх
у assets/images. Скрипт треба запустити один раз (уже виконано, файли
включені у проєкт), але його можна перезапустити, щоб перегенерувати
або додати нові скіни.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 800, 600
OUT = "assets/images"


def save(img, name):
    img.save(f"{OUT}/{name}.png")
    print("saved", name)


# ---------- ФОНИ ----------

def make_game_background():
    img = Image.new("RGB", (W, H))
    px = img.load()
    top = (8, 8, 36)
    bottom = (28, 18, 64)
    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    draw = ImageDraw.Draw(img)
    random.seed(42)
    for _ in range(140):
        x, y = random.randint(0, W - 1), random.randint(0, H - 1)
        s = random.choice([1, 1, 1, 2])
        b = random.randint(120, 255)
        draw.ellipse((x, y, x + s, y + s), fill=(b, b, b))
    # легке віньєтування по краях поля
    draw.rectangle((0, 0, W - 1, H - 1), outline=(90, 90, 140), width=2)
    save(img, "background_game")


def make_menu_background():
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / H
        r = int(20 + 40 * t)
        g = int(10 + 10 * t)
        b = int(60 + 80 * t)
        for x in range(W):
            wobble = 6 * math.sin((x + y) / 60)
            px[x, y] = (
                max(0, min(255, int(r + wobble))),
                max(0, min(255, int(g + wobble * 0.4))),
                max(0, min(255, int(b + wobble))),
            )
    img = img.filter(ImageFilter.GaussianBlur(1))
    draw = ImageDraw.Draw(img)
    random.seed(7)
    for _ in range(90):
        x, y = random.randint(0, W - 1), random.randint(0, H - 1)
        s = random.choice([1, 1, 2])
        b = random.randint(140, 255)
        draw.ellipse((x, y, x + s, y + s), fill=(b, b, b))
    save(img, "background_menu")


# ---------- М'ЯЧІ (скіни) ----------

def radial_ball(size, colors, glow=None):
    """colors: список (позиція 0..1, (r,g,b)) для радіального градієнта"""
    d = size * 4  # супер-семпл для згладжування
    img = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    px = img.load()
    cx = cy = d / 2
    r_max = d / 2
    for y in range(d):
        for x in range(d):
            dist = math.hypot(x - cx, y - cy) / r_max
            if dist > 1:
                continue
            t = dist
            for i in range(len(colors) - 1):
                p0, c0 = colors[i]
                p1, c1 = colors[i + 1]
                if p0 <= t <= p1:
                    local_t = (t - p0) / (p1 - p0 + 1e-6)
                    r = int(c0[0] + (c1[0] - c0[0]) * local_t)
                    g = int(c0[1] + (c1[1] - c0[1]) * local_t)
                    b = int(c0[2] + (c1[2] - c0[2]) * local_t)
                    px[x, y] = (r, g, b, 255)
                    break
    img = img.resize((size, size), Image.LANCZOS)
    return img


def make_balls():
    save(radial_ball(64, [(0, (255, 255, 255)), (0.7, (225, 225, 235)), (1, (140, 140, 160))]), "ball_classic")
    save(radial_ball(64, [(0, (255, 245, 200)), (0.4, (255, 160, 40)), (0.8, (230, 60, 20)), (1, (120, 10, 0))]), "ball_fire")
    save(radial_ball(64, [(0, (220, 255, 255)), (0.4, (60, 220, 255)), (0.8, (30, 120, 255)), (1, (10, 30, 120))]), "ball_neon")
    save(radial_ball(64, [(0, (255, 220, 255)), (0.35, (200, 100, 255)), (0.7, (90, 30, 160)), (1, (15, 5, 40))]), "ball_galaxy")
    save(radial_ball(64, [(0, (255, 250, 210)), (0.5, (255, 215, 60)), (1, (150, 110, 10))]), "ball_gold")


# ---------- ПЛАТФОРМИ (скіни) ----------

def make_paddle(colors_top_bottom, name, border=None):
    pw, ph = 20, 100
    d = 4
    img = Image.new("RGBA", (pw * d, ph * d), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    top, bottom = colors_top_bottom
    for y in range(ph * d):
        t = y / (ph * d)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line((0, y, pw * d, y), fill=(r, g, b, 255))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw * d - 1, ph * d - 1), radius=10 * d, fill=255)
    rounded = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask)
    if border:
        bd = ImageDraw.Draw(rounded)
        bd.rounded_rectangle((0, 0, pw * d - 1, ph * d - 1), radius=10 * d, outline=border, width=3 * d)
    rounded = rounded.resize((pw, ph), Image.LANCZOS)
    save(rounded, name)


def make_paddles():
    make_paddle(((80, 255, 140), (10, 120, 60)), "paddle_green", border=(200, 255, 220, 255))
    make_paddle(((255, 110, 210), (140, 10, 100)), "paddle_pink", border=(255, 210, 240, 255))
    make_paddle(((110, 180, 255), (10, 60, 150)), "paddle_blue", border=(210, 230, 255, 255))
    make_paddle(((255, 215, 90), (140, 100, 10)), "paddle_gold", border=(255, 245, 200, 255))


# ---------- КНОПКИ ----------

def make_button(size, base, hover_border, name):
    w, h = size
    d = 4
    img = Image.new("RGBA", (w * d, h * d), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    top = tuple(min(255, c + 25) for c in base)
    bottom = tuple(max(0, c - 25) for c in base)
    for y in range(h * d):
        t = y / (h * d)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line((0, y, w * d, y), fill=(r, g, b, 255))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * d - 1, h * d - 1), radius=14 * d, fill=255)
    rounded = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask)
    bd = ImageDraw.Draw(rounded)
    bd.rounded_rectangle((0, 0, w * d - 1, h * d - 1), radius=14 * d, outline=hover_border, width=3 * d)
    rounded = rounded.resize((w, h), Image.LANCZOS)
    save(rounded, name)


def make_buttons():
    make_button((260, 60), (70, 70, 100), (140, 140, 190, 255), "button_normal")
    make_button((260, 60), (90, 130, 90), (160, 230, 160, 255), "button_hover")
    make_button((60, 60), (100, 60, 60), (220, 120, 120, 255), "button_close")


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    make_game_background()
    make_menu_background()
    make_balls()
    make_paddles()
    make_buttons()
    print("Готово! Усі текстури згенеровано у", OUT)
