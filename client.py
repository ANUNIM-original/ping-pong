from pygame import *
import socket
import json
import os
from threading import Thread

# =========================================================
#                     ПУГАМЕ НАЛАШТУВАННЯ
# =========================================================
WIDTH, HEIGHT = 800, 600
init()
mixer.init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
SND_DIR = os.path.join(BASE_DIR, "assets", "sounds")
SAVE_FILE = os.path.join(BASE_DIR, "save_data.json")

WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GRAY = (180, 180, 190)
DARK = (18, 18, 30)

# =========================================================
#                     ЗБЕРЕЖЕННЯ ГРАВЦЯ
# =========================================================
DEFAULT_SAVE = {
    "player_name": "Гравець",
    "coins": 20,
    "unlocked_balls": ["ball_classic"],
    "unlocked_paddles": ["paddle_green"],
    "selected_ball": "ball_classic",
    "selected_paddle": "paddle_green",
    "sound_on": True,
    "music_on": True,
}


def load_save():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULT_SAVE.copy()
            merged.update(data)
            return merged
        except Exception:
            pass
    return DEFAULT_SAVE.copy()


def write_save():
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)


save_data = load_save()

# =========================================================
#                     ЗАВАНТАЖЕННЯ ТЕКСТУР
# =========================================================


def load_img(name, size=None, alpha=True):
    path = os.path.join(IMG_DIR, f"{name}.png")
    try:
        img = image.load(path)
        img = img.convert_alpha() if alpha else img.convert()
    except Exception:
        img = Surface(size or (64, 64), SRCALPHA)
        img.fill((255, 0, 255, 120))
    if size:
        img = transform.smoothscale(img, size)
    return img


BACKGROUND_GAME = load_img("background_game", (WIDTH, HEIGHT), alpha=False)
BACKGROUND_MENU = load_img("background_menu", (WIDTH, HEIGHT), alpha=False)
BTN_NORMAL = load_img("button_normal", (260, 60))
BTN_HOVER = load_img("button_hover", (260, 60))
BTN_CLOSE = load_img("button_close", (60, 60))

BALL_SKINS = ["ball_classic", "ball_fire", "ball_neon", "ball_galaxy", "ball_gold"]
BALL_PRICES = {"ball_classic": 0, "ball_fire": 20, "ball_neon": 30, "ball_galaxy": 45, "ball_gold": 60}
BALL_LABELS = {
    "ball_classic": "Класичний",
    "ball_fire": "Вогняний",
    "ball_neon": "Неон",
    "ball_galaxy": "Галактика",
    "ball_gold": "Золотий",
}

PADDLE_SKINS = ["paddle_green", "paddle_pink", "paddle_blue", "paddle_gold"]
PADDLE_PRICES = {"paddle_green": 0, "paddle_pink": 20, "paddle_blue": 30, "paddle_gold": 50}
PADDLE_LABELS = {
    "paddle_green": "Смарагдова",
    "paddle_pink": "Рожева",
    "paddle_blue": "Синя",
    "paddle_gold": "Золота",
}

BALL_IMAGES = {n: load_img(n, (20, 20)) for n in BALL_SKINS}
PADDLE_IMAGES = {n: load_img(n, (20, 100)) for n in PADDLE_SKINS}

# =========================================================
#                     ЗВУКИ
# =========================================================


def load_snd(name):
    path = os.path.join(SND_DIR, f"{name}.wav")
    try:
        return mixer.Sound(path)
    except Exception:
        return None


SOUNDS = {
    "wall_hit": load_snd("wall_hit"),
    "platform_hit": load_snd("paddle_hit"),
    "score": load_snd("score"),
    "click": load_snd("click"),
    "win": load_snd("win"),
    "lose": load_snd("lose"),
    "countdown_tick": load_snd("countdown_tick"),
}


def play_sound(key):
    if save_data.get("sound_on", True) and SOUNDS.get(key):
        SOUNDS[key].play()


# =========================================================
#                     ШРИФТИ
# =========================================================
font_title = font.Font(None, 84)
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)
font_small = font.Font(None, 26)
font_btn = font.Font(None, 40)

# =========================================================
#                     UI ХЕЛПЕРИ
# =========================================================


class Button:
    def __init__(self, rect, text, size="normal"):
        self.rect = Rect(rect)
        self.text = text
        self.size = size

    def draw(self, surf):
        hovered = self.rect.collidepoint(mouse.get_pos())
        img = BTN_CLOSE if self.size == "close" else (BTN_HOVER if hovered else BTN_NORMAL)
        img = transform.smoothscale(img, (self.rect.width, self.rect.height))
        surf.blit(img, self.rect.topleft)
        color = GOLD if hovered else WHITE
        label = font_btn.render(self.text, True, color)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            event.type == MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class TextInput:
    def __init__(self, rect, initial=""):
        self.rect = Rect(rect)
        self.text = initial
        self.active = True

    def draw(self, surf):
        draw.rect(surf, (40, 40, 60), self.rect, border_radius=8)
        draw.rect(surf, GOLD if self.active else GRAY, self.rect, width=2, border_radius=8)
        label = font_main.render(self.text or "", True, WHITE)
        surf.blit(label, (self.rect.x + 12, self.rect.y + (self.rect.height - label.get_height()) // 2))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == KEYDOWN and self.active:
            if event.key == K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (K_RETURN, K_KP_ENTER):
                pass
            elif len(self.text) < 14 and event.unicode.isprintable():
                self.text += event.unicode


def draw_background(target=None):
    surf = target if target is not None else BACKGROUND_GAME
    screen.blit(surf, (0, 0))


def draw_center_line():
    dash_h, gap = 15, 10
    y = 0
    while y < HEIGHT:
        draw.rect(screen, (255, 255, 255), (WIDTH // 2 - 2, y, 4, dash_h))
        y += dash_h + gap


def draw_coins_badge(pos=(WIDTH - 140, 16)):
    label = font_small.render(f"Монети: {save_data['coins']}", True, GOLD)
    screen.blit(label, pos)


# =========================================================
#                     СТАНИ ГРИ
# =========================================================
STATE_MENU = "menu"
STATE_SETTINGS = "settings"
STATE_SHOP = "shop"
STATE_PLAYING = "playing"
STATE_GAMEOVER = "gameover"

state = STATE_MENU

# --- мережеві змінні (ініціалізуються при вході в гру) ---
client = None
my_id = None
game_state = {}
buffer = ""
game_over_flag = False
you_winner = None
prev_scores = None


def connect_to_server():
    try:
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.settimeout(2)
        c.connect(("localhost", 8080))
        c.settimeout(None)
        pid = int(c.recv(24).decode())
        return pid, c
    except Exception:
        return None, None


def receive():
    global buffer, game_state, game_over_flag
    while not game_over_flag:
        try:
            data = client.recv(1024).decode()
            if not data:
                raise ConnectionError
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except Exception:
            game_state["winner"] = -1
            break


def start_game():
    """Підключення до сервера і запуск потоку прийому даних."""
    global client, my_id, game_state, buffer, game_over_flag, you_winner, prev_scores, state
    my_id, client = connect_to_server()
    if client is None:
        state = STATE_MENU
        return
    game_state = {}
    buffer = ""
    game_over_flag = False
    you_winner = None
    prev_scores = None
    Thread(target=receive, daemon=True).start()
    state = STATE_PLAYING


# =========================================================
#             ЕКРАНИ (МЕНЮ / НАЛАШТУВАННЯ / МАГАЗИН)
# =========================================================

btn_play = Button((WIDTH // 2 - 130, 260, 260, 60), "Грати")
btn_shop = Button((WIDTH // 2 - 130, 335, 260, 60), "Магазин скінів")
btn_settings = Button((WIDTH // 2 - 130, 410, 260, 60), "Налаштування")
btn_exit = Button((WIDTH // 2 - 130, 485, 260, 60), "Вихід")

name_input = TextInput((WIDTH // 2 - 130, 160, 260, 46), save_data["player_name"])
btn_sound_toggle = Button((WIDTH // 2 - 130, 260, 260, 60), "")
btn_music_toggle = Button((WIDTH // 2 - 130, 335, 260, 60), "")
btn_back_settings = Button((WIDTH // 2 - 130, 480, 260, 60), "Назад")

btn_back_shop = Button((20, 20, 140, 50), "Назад")
btn_tab_balls = Button((WIDTH // 2 - 270, 90, 260, 50), "М'ячі")
btn_tab_paddles = Button((WIDTH // 2 + 10, 90, 260, 50), "Платформи")
shop_tab = "balls"


def draw_menu():
    draw_background(BACKGROUND_MENU)
    title = font_title.render("ПІНГ-ПОНГ", True, GOLD)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 110)))
    subtitle = font_small.render(f"Вітаємо, {save_data['player_name']}!", True, WHITE)
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 165)))
    draw_coins_badge()

    for b in (btn_play, btn_shop, btn_settings, btn_exit):
        b.draw(screen)


def handle_menu_event(e):
    global state
    if btn_play.clicked(e):
        play_sound("click")
        start_game()
    elif btn_shop.clicked(e):
        play_sound("click")
        state = STATE_SHOP
    elif btn_settings.clicked(e):
        play_sound("click")
        state = STATE_SETTINGS
    elif btn_exit.clicked(e):
        write_save()
        exit()


def draw_settings():
    draw_background(BACKGROUND_MENU)
    title = font_main.render("Налаштування", True, GOLD)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 80)))

    label = font_small.render("Ім'я гравця:", True, WHITE)
    screen.blit(label, (name_input.rect.x, name_input.rect.y - 30))
    name_input.draw(screen)

    btn_sound_toggle.text = f"Звук: {'Увімк' if save_data['sound_on'] else 'Вимк'}"
    btn_music_toggle.text = f"Музика: {'Увімк' if save_data['music_on'] else 'Вимк'}"
    for b in (btn_sound_toggle, btn_music_toggle, btn_back_settings):
        b.draw(screen)


def handle_settings_event(e):
    global state
    name_input.handle_event(e)
    save_data["player_name"] = name_input.text or "Гравець"
    if btn_sound_toggle.clicked(e):
        save_data["sound_on"] = not save_data["sound_on"]
        play_sound("click")
    elif btn_music_toggle.clicked(e):
        save_data["music_on"] = not save_data["music_on"]
        play_sound("click")
    elif btn_back_settings.clicked(e):
        play_sound("click")
        write_save()
        state = STATE_MENU


def draw_shop_item(rect, key, label, price, unlocked_list, selected_key, preview_img):
    hovered = rect.collidepoint(mouse.get_pos())
    bg = (55, 55, 80) if hovered else (40, 40, 60)
    draw.rect(screen, bg, rect, border_radius=12)
    is_selected = save_data[selected_key] == key
    border_color = GOLD if is_selected else ((150, 150, 170) if key in unlocked_list else (80, 80, 90))
    draw.rect(screen, border_color, rect, width=3, border_radius=12)

    prev = transform.smoothscale(preview_img, (48, 48) if "ball" in key else (28, 70))
    screen.blit(prev, prev.get_rect(center=(rect.centerx, rect.y + 55)))

    name_lbl = font_small.render(label, True, WHITE)
    screen.blit(name_lbl, name_lbl.get_rect(center=(rect.centerx, rect.y + 110)))

    if key in unlocked_list:
        status = "ОБРАНО" if is_selected else "Обрати"
        status_color = GOLD if is_selected else GRAY
    else:
        status = f"Ціна: {price}"
        status_color = WHITE
    status_lbl = font_small.render(status, True, status_color)
    screen.blit(status_lbl, status_lbl.get_rect(center=(rect.centerx, rect.y + 135)))


def draw_shop():
    draw_background(BACKGROUND_MENU)
    title = font_main.render("Магазин скінів", True, GOLD)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 45)))
    draw_coins_badge((20, 20))

    btn_tab_balls.draw(screen)
    btn_tab_paddles.draw(screen)

    grid_rects = []
    if shop_tab == "balls":
        items, prices, labels = BALL_SKINS, BALL_PRICES, BALL_LABELS
        unlocked, selected_key, imgs = save_data["unlocked_balls"], "selected_ball", BALL_IMAGES
    else:
        items, prices, labels = PADDLE_SKINS, PADDLE_PRICES, PADDLE_LABELS
        unlocked, selected_key, imgs = save_data["unlocked_paddles"], "selected_paddle", PADDLE_IMAGES

    cols = 4
    cell_w, cell_h = 160, 160
    start_x = (WIDTH - cols * cell_w) // 2
    start_y = 170
    for i, key in enumerate(items):
        col, row = i % cols, i // cols
        rect = Rect(start_x + col * cell_w + 10, start_y + row * cell_h, cell_w - 20, cell_h - 20)
        draw_shop_item(rect, key, labels[key], prices[key], unlocked, selected_key, imgs[key])
        grid_rects.append((rect, key))

    btn_back_shop.draw(screen)
    return grid_rects


def handle_shop_event(e, grid_rects):
    global shop_tab, state
    if btn_back_shop.clicked(e):
        play_sound("click")
        write_save()
        state = STATE_MENU
        return
    if btn_tab_balls.clicked(e):
        play_sound("click")
        shop_tab = "balls"
        return
    if btn_tab_paddles.clicked(e):
        play_sound("click")
        shop_tab = "paddles"
        return

    if e.type == MOUSEBUTTONDOWN and e.button == 1:
        for rect, key in grid_rects:
            if rect.collidepoint(e.pos):
                if shop_tab == "balls":
                    unlocked, price, sel_key = save_data["unlocked_balls"], BALL_PRICES[key], "selected_ball"
                else:
                    unlocked, price, sel_key = save_data["unlocked_paddles"], PADDLE_PRICES[key], "selected_paddle"

                if key in unlocked:
                    save_data[sel_key] = key
                    play_sound("click")
                elif save_data["coins"] >= price:
                    save_data["coins"] -= price
                    unlocked.append(key)
                    save_data[sel_key] = key
                    play_sound("score")
                else:
                    play_sound("wall_hit")
                write_save()


# =========================================================
#                     ІГРОВИЙ ЕКРАН
# =========================================================


def draw_playing():
    global prev_scores, you_winner, state

    if "countdown" in game_state and game_state["countdown"] > 0:
        draw_background()
        countdown_text = font_win.render(str(game_state["countdown"]), True, WHITE)
        screen.blit(countdown_text, countdown_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        return

    if "winner" in game_state and game_state["winner"] is not None:
        draw_background()

        if you_winner is None:
            you_winner = game_state["winner"] == my_id
            if you_winner:
                save_data["coins"] += 15
                play_sound("win")
            else:
                save_data["coins"] += 5
                play_sound("lose")
            write_save()

        text = "Ти переміг!" if you_winner else "Пощастить наступним разом!"
        win_text = font_win.render(text, True, GOLD)
        screen.blit(win_text, win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

        reward = "+15 монет" if you_winner else "+5 монет"
        reward_lbl = font_main.render(reward, True, GOLD)
        screen.blit(reward_lbl, reward_lbl.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

        text2 = font_main.render("К - рестарт    М - в меню", True, WHITE)
        screen.blit(text2, text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))
        state = STATE_GAMEOVER
        return

    if game_state:
        draw_background()
        draw_center_line()

        my_paddle_img = PADDLE_IMAGES.get(save_data["selected_paddle"], PADDLE_IMAGES["paddle_green"])
        opp_key = "paddle_blue" if save_data["selected_paddle"] != "paddle_blue" else "paddle_pink"
        opp_paddle_img = PADDLE_IMAGES[opp_key]

        p0y = game_state["paddles"]["0"]
        p1y = game_state["paddles"]["1"]
        if my_id == 0:
            screen.blit(my_paddle_img, (20, p0y))
            screen.blit(opp_paddle_img, (WIDTH - 40, p1y))
        else:
            screen.blit(opp_paddle_img, (20, p0y))
            screen.blit(my_paddle_img, (WIDTH - 40, p1y))

        ball_img = BALL_IMAGES.get(save_data["selected_ball"], BALL_IMAGES["ball_classic"])
        bx, by = game_state["ball"]["x"], game_state["ball"]["y"]
        screen.blit(ball_img, (bx - 10, by - 10))

        scores = game_state["scores"]
        if prev_scores is not None and scores != prev_scores:
            play_sound("score")
        prev_scores = list(scores)

        score_text = font_main.render(f"{scores[0]} : {scores[1]}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - 25, 20))

        name_lbl = font_small.render(save_data["player_name"], True, GOLD)
        screen.blit(name_lbl, (20, HEIGHT - 30))

        se = game_state.get("sound_event")
        if se == "wall_hit":
            play_sound("wall_hit")
        elif se == "platform_hit":
            play_sound("platform_hit")
    else:
        draw_background()
        waiting_text = font_main.render("Очікування гравців...", True, WHITE)
        screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, 20))


# =========================================================
#                     ГОЛОВНИЙ ЦИКЛ
# =========================================================
while True:
    grid_rects = []

    if state == STATE_MENU:
        draw_menu()
    elif state == STATE_SETTINGS:
        draw_settings()
    elif state == STATE_SHOP:
        grid_rects = draw_shop()
    elif state in (STATE_PLAYING, STATE_GAMEOVER):
        draw_playing()

    for e in event.get():
        if e.type == QUIT:
            write_save()
            exit()

        if state == STATE_MENU:
            handle_menu_event(e)
        elif state == STATE_SETTINGS:
            handle_settings_event(e)
        elif state == STATE_SHOP:
            handle_shop_event(e, grid_rects)
        elif state == STATE_GAMEOVER and e.type == KEYDOWN:
            if e.key == K_k:
                start_game()
            elif e.key == K_m:
                try:
                    client.close()
                except Exception:
                    pass
                state = STATE_MENU

    display.update()
    clock.tick(60)

    if state == STATE_PLAYING:
        keys = key.get_pressed()
        try:
            if keys[K_w]:
                client.send(b"UP")
            elif keys[K_s]:
                client.send(b"DOWN")
        except Exception:
            pass
