#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
photomontage.py — замена нарисованных заглушек темы GRUB «СССР»
настоящими фотографиями и официальным Государственным гербом СССР.

Входные файлы (assets/sources/):
  stalin.webp   — портрет И. В. Сталина (topwar.ru)
  lenin.jpg     — портрет В. И. Ленина (chaltlib.ru)
  emblem-1280.png — Герб СССР 1956–1991 (Wikimedia Commons, CC BY-SA / public domain)

Выходные файлы (theme/):
  leader-stalin.png leader-lenin.png leader-trotsky.png
  emblem.png  icons/emblem-64.png  banner.png  countdown_frame.png
  background.png (+ все фоновые варианты разрешений)

Обработка в духе плаката 1930–1950-х: высокая контрастная дуотонная
печать (тёмно-красный тени / золото света), виньетка, зерно, золотая рамка.
Троцкий прижизненных цветных агитфото в наборе не имеет — его портрет
обработан из чёрно-белого исторического снимка тем же плакатным способом.
"""

import os
import sys
import math
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "sources")
THEME = os.path.join(ROOT, "theme")

RED = (204, 0, 0)          # #CC0000
GOLD = (255, 215, 0)       # #FFD700
DARKRED = (139, 0, 0)      # #8B0000
BLACK = (0, 0, 0)
CREAM = (255, 246, 205)    # светло-жёлтый / кремовый

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def font(size):
    for p in FONTS:
        if os.path.exists(p):
            return ImageFont_load(p, size)
    return ImageFont_load(None, size)


def ImageFont_load(path, size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# 1. Скачивание исходников (если ещё не скачаны)
# ---------------------------------------------------------------------------

SOURCES = {
    "stalin.webp": "https://topwar.ru/uploads/posts/2024-09/d860758bdf_stalin-2.webp",
    "lenin.jpg": "https://chaltlib.ru/images/ubilei2017/207.jpg",
    # официальный герб СССР (1956–1991), Wikimedia Commons; качаем PNG-рендер,
    # т.к. upload.wikimedia.org отдаёт SVG только с корректным User-Agent
    "emblem-1280.png": ("https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d9/"
                        "Coat_of_arms_of_the_Soviet_Union_%281956%E2%80%931991%29.svg"
                        "/1280px-Coat_of_arms_of_the_Soviet_Union_%281956%E2%80%931991%29.svg.png"),
}


def download_sources(force=False):
    os.makedirs(SRC, exist_ok=True)
    for name, url in SOURCES.items():
        dst = os.path.join(SRC, name)
        if os.path.exists(dst) and not force and os.path.getsize(dst) > 2048:
            print(f"[src] есть локально: {name}")
            continue
        print(f"[src] скачиваю {name} ...")
        req = urllib.request.Request(url, headers={
            "User-Agent": "GRUB-SSSR-theme-setup/1.0 (personal theme build)",
            "Accept": "*/*",
        })
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        with open(dst, "wb") as f:
            f.write(data)
        print(f"[src] сохранён {name} ({len(data)} байт)")


# ---------------------------------------------------------------------------
# 2. Утилиты
# ---------------------------------------------------------------------------

def load_rgb(path):
    im = Image.open(path)
    im.load()
    return im.convert("RGB")


def duotone_poster(im, shadow=DARKRED, light=GOLD, cutoff_lo=0.30, cutoff_hi=0.72,
                   contrast=1.35, brightness=1.05):
    """Дуотонная обработка в стилеOffsetной пропагандистской печати."""
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=(cutoff_lo * 100, (1 - cutoff_hi) * 100))
    g = ImageEnhance.Contrast(g).enhance(contrast)
    g = ImageEnhance.Brightness(g).enhance(brightness)
    luts = []
    for c in range(3):
        table = []
        for v in range(256):
            t = v / 255.0
            # лёгкая S-кривая: больше «плотного» красного в тенях
            tt = t * t * (3 - 2 * t)
            val = shadow[c] + (light[c] - shadow[c]) * tt
            table.append(max(0, min(255, int(val))))
        luts.append(table)
    out = Image.merge("RGB", tuple(g.point(l) for l in luts))
    return out


def grain(im, amount=16, seed=7):
    """Плёночное зерно / «неровность» офсетной печати."""
    from PIL import ImageChops
    import random
    rnd = random.Random(seed)
    w, h = im.size
    nw, nh = max(1, w // 2), max(1, h // 2)
    nz = Image.new("L", (nw, nh))
    px = nz.load()
    for y in range(nh):
        for x in range(nw):
            px[x, y] = 128 + rnd.randint(-amount, amount)
    nz = nz.resize((w, h), Image.BILINEAR)
    # soft_light требует одинакового режима: приводим шум к RGB
    noise_rgb = Image.merge("RGB", (nz, nz, nz))
    base_rgb = im.convert("RGB")
    diff = ImageChops.soft_light(base_rgb, noise_rgb)
    out = Image.blend(base_rgb, diff, 0.10)
    if im.mode == "RGBA":
        out.putalpha(im.split()[3])
    return out


def vignette(im, strength=0.55, color=BLACK):
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    cx, cy = w / 2, h / 2
    steps = 40
    for i in range(steps, 0, -1):
        a = int(255 * (i / steps))
        rx = w * 0.62 * (i / steps)
        ry = h * 0.62 * (i / steps)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=a)
    mask = mask.filter(ImageFilter.GaussianBlur(min(w, h) // 12))
    dark = Image.new("RGB", (w, h), color)
    return Image.composite(dark, im, mask.point(lambda v: int(v * strength)))


def star_points(cx, cy, r_out, r_in=None, n=5, rot=-math.pi / 2):
    if r_in is None:
        r_in = r_out * 0.382
    pts = []
    for k in range(n * 2):
        r = r_out if k % 2 == 0 else r_in
        a = rot + k * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_star(draw, cx, cy, r_out, fill=GOLD, outline=None, width=1, rot=-math.pi / 2):
    pts = star_points(cx, cy, r_out, rot=rot)
    draw.polygon(pts, fill=fill, outline=outline)
    if outline and width > 1:
        draw.line(pts + [pts[0]], fill=outline, width=width)


def gold_frame(im, border=6, inset=0, color=GOLD, inner=DARKRED):
    """Золотая рамка с тонкой тёмно-красной линией — оправа плаката."""
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.rectangle([inset, inset, w - 1 - inset, h - 1 - inset], outline=color, width=border)
    d.rectangle([inset + border + 3, inset + border + 3,
                 w - 4 - inset - border, h - 4 - inset - border], outline=inner, width=2)
    return im


def crop_to_ratio(im, ratio_w=1.0, ratio_h=1.0, focus_y=0.35):
    """Кадрирование к пропорции с акцентом на лицо (focus_y — доля высоты)."""
    w, h = im.size
    target = ratio_w / ratio_h
    cur = w / h
    if cur > target:
        nh = h
        nw = int(h * target)
        x0 = (w - nw) // 2
        box = (x0, 0, x0 + nw, nh)
    else:
        nw = w
        nh = int(w / target)
        y0 = int((h - nh) * focus_y)
        box = (0, y0, nw, y0 + nh)
    return im.crop(box)


def make_medallion(portrait_path, out_path, size=512, label="", sublabel=""):
    """Круглый медальон-«орден»: дуотонное фото в золотом венце со звездой."""
    src = load_rgb(portrait_path)
    src = crop_to_ratio(src, 1.0, 1.0, focus_y=0.30)
    src = src.resize((size, size), Image.LANCZOS)
    poster = duotone_poster(src)
    poster = grain(poster, amount=14)

    disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    dm = ImageDraw.Draw(mask)
    pad = 10
    dm.ellipse([pad, pad, size - pad, size - pad], fill=255)
    disc.paste(poster, (0, 0), mask)

    d = ImageDraw.Draw(disc)
    # двойной золотой ободок
    d.ellipse([pad, pad, size - pad, size - pad], outline=GOLD, width=6)
    d.ellipse([pad + 10, pad + 10, size - 10 - pad, size - 10 - pad], outline=DARKRED, width=3)
    # звезда-штрих наверху (как наOrders/медальонах)
    draw_star(d, size // 2, pad + 4, 16, fill=GOLD, outline=DARKRED, width=2)

    if label:
        lh = 64 if sublabel else 44
        canvas = Image.new("RGBA", (size, size + lh), (0, 0, 0, 0))
        canvas.paste(disc, (0, 0), disc)
        dc = ImageDraw.Draw(canvas)
        f = font(26 if size >= 448 else 20)
        fs = font(18 if size >= 448 else 14)
        bbox = dc.textbbox((0, 0), label, font=f)
        tw = bbox[2] - bbox[0]
        dc.text(((size - tw) // 2, size + 4), label, font=f, fill=GOLD,
                stroke_width=2, stroke_fill=DARKRED)
        if sublabel:
            bbox2 = dc.textbbox((0, 0), sublabel, font=fs)
            tw2 = bbox2[2] - bbox2[0]
            dc.text(((size - tw2) // 2, size + 34), sublabel, font=fs, fill=CREAM)
        canvas.save(out_path)
    else:
        disc.save(out_path)
    print("[out]", out_path)


# ---------------------------------------------------------------------------
# 3. Герб СССР из официального файла
# ---------------------------------------------------------------------------

def trim_alpha(im, pad=8):
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    m = max(1, min(w, h))
    side = int(m + pad * 2)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return out


def build_emblem():
    path = os.path.join(SRC, "emblem-1280.png")
    em = Image.open(path).convert("RGBA")
    em = trim_alpha(em, pad=12)
    # основной герб темы
    main = em.copy()
    main.thumbnail((720, 720), Image.LANCZOS)
    main.save(os.path.join(THEME, "emblem.png"))
    print("[out] theme/emblem.png", main.size)
    # иконка для заголовка/меню
    ic = em.copy()
    ic.thumbnail((64, 64), Image.LANCZOS)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.paste(ic, ((64 - ic.size[0]) // 2, (64 - ic.size[1]) // 2), ic)
    canvas.save(os.path.join(THEME, "icons", "emblem-64.png"))
    print("[out] theme/icons/emblem-64.png")
    return em


# ---------------------------------------------------------------------------
# 4. Портреты вождей
# ---------------------------------------------------------------------------

def build_leaders():
    # v2: Троцкий УДАЛЁН из темы; вместо него — К. Маркс и Ф. Энгельс
    # (реальное фото пользователя assets/sources/marks.jpg).
    mk = os.path.join(SRC, "marks.jpg")
    if os.path.exists(mk):
        full = load_rgb(mk)
        w, h = full.size
        marx = full.crop((int(w * 0.50), 0, w, h))
        eng = full.crop((0, 0, int(w * 0.52), h))
        make_medallion(marx, os.path.join(THEME, "leader-marx.png"),
                       size=512, label="К. МАРКС", sublabel="1818 — 1883")
        make_medallion(eng, os.path.join(THEME, "leader-engels.png"),
                       size=512, label="Ф. ЭНГЕЛЬС", sublabel="1820 — 1895")
    make_medallion(os.path.join(SRC, "lenin.jpg"),
                   os.path.join(THEME, "leader-lenin.png"),
                   size=512, label="В. И. ЛЕНИН", sublabel="1870 — 1924")
    make_medallion(os.path.join(SRC, "stalin.webp"),
                   os.path.join(THEME, "leader-stalin.png"),
                   size=512, label="И. В. СТАЛИН", sublabel="вождь народов")
    tro = os.path.join(THEME, "leader-trotsky.png")
    if os.path.exists(tro):
        os.remove(tro)
        print("[rm ] theme/leader-trotsky.png (Троцкий убран)")


def _trotsky_fallback(out_path):
    size = 512
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # стилизованный конструктивистский знак вместо фото
    d.ellipse([10, 10, size - 10, size - 10], fill=DARKRED, outline=GOLD, width=6)
    d.ellipse([24, 24, size - 24, size - 24], outline=RED, width=3)
    # молот (условно) + звезда
    cx = size // 2
    d.polygon([(cx - 90, size - 170), (cx + 60, size - 250), (cx + 80, size - 210),
               (cx - 70, size - 130)], fill=GOLD)
    draw_star(d, cx + 40, 150, 46, fill=GOLD, outline=DARKRED, width=3)
    f = font(26)
    txt = "Л. Д. ТРОЦКИЙ"
    bbox = d.textbbox((0, 0), txt, font=f)
    d.text(((size - (bbox[2] - bbox[0])) // 2, size - 60), txt, font=f, fill=GOLD,
           stroke_width=2, stroke_fill=BLACK)
    im.save(out_path)
    print("[out]", out_path, "(заглушка: нет фото, см. README)")


# ---------------------------------------------------------------------------
# 5. Баннер и плашка таймера
# ---------------------------------------------------------------------------

def build_banner(emblem):
    w, h = 1200, 130
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # знамённое полотно
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=RED, outline=GOLD, width=5)
    d.line([10, h - 18, w - 10, h - 18], fill=DARKRED, width=3)
    # герб слева
    e = emblem.copy()
    e.thumbnail((h - 26, h - 26), Image.LANCZOS)
    im.paste(e, (18, (h - e.size[1]) // 2), e)
    # текст
    f = font(44)
    fs = font(22)
    title = "АРХ ЛИНУКС · МАНЖАРО"
    sub = "ПРОЛЕТАРИИ ВСЕХ СТРАН, СОЕДИНЯЙТЕСЬ!"
    d.text((18 + e.size[0] + 24, 18), title, font=f, fill=GOLD,
           stroke_width=2, stroke_fill=DARKRED)
    d.text((18 + e.size[0] + 26, 76), sub, font=fs, fill=CREAM)
    draw_star(d, w - 60, h // 2, 26, fill=GOLD, outline=DARKRED, width=2)
    im.save(os.path.join(THEME, "banner.png"))
    print("[out] theme/banner.png")


def build_countdown(emblem):
    w, h = 280, 120
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=12, fill=DARKRED, outline=GOLD, width=4)
    d.rounded_rectangle([10, 10, w - 11, h - 11], radius=8, outline=RED, width=2)
    e = emblem.copy()
    e.thumbnail((h - 34, h - 34), Image.LANCZOS)
    im.paste(e, (18, (h - e.size[1]) // 2), e)
    f = font(20)
    fs = font(15)
    d.text((18 + e.size[0] + 12, 24), "ОСТАЛОСЬ", font=fs, fill=CREAM)
    d.text((18 + e.size[0] + 12, 50), "ВРЕМЕНИ", font=f, fill=GOLD,
           stroke_width=1, stroke_fill=BLACK)
    # лавровая ветвь справа (упрощённо — дуга с листьями)
    for i in range(7):
        ang = math.radians(200 + i * 12)
        cx = w - 26
        cy = h // 2
        x = cx + 18 * math.cos(ang)
        y = cy + 34 * math.sin(ang)
        d.ellipse([x - 5, y - 2, x + 5, y + 2], fill=GOLD, outline=DARKRED)
    im.save(os.path.join(THEME, "countdown_frame.png"))
    print("[out] theme/countdown_frame.png")


# ---------------------------------------------------------------------------
# 6. ФОН: карта СССР + реальный герб + три портрета
# ---------------------------------------------------------------------------

# очень упрощённый контур территории СССР (условные координаты 0..1 по шир./дол.)
USSR_OUTLINE = [
    (0.030, 0.520), (0.055, 0.430), (0.045, 0.330), (0.075, 0.250), (0.110, 0.290),
    (0.130, 0.220), (0.170, 0.250), (0.195, 0.180), (0.235, 0.210), (0.260, 0.150),
    (0.300, 0.185), (0.335, 0.130), (0.380, 0.170), (0.420, 0.120), (0.470, 0.165),
    (0.520, 0.110), (0.575, 0.160), (0.620, 0.115), (0.675, 0.170), (0.720, 0.130),
    (0.775, 0.185), (0.820, 0.145), (0.870, 0.205), (0.915, 0.170), (0.955, 0.240),
    (0.975, 0.320), (0.945, 0.400), (0.905, 0.455), (0.870, 0.520), (0.825, 0.560),
    (0.780, 0.620), (0.735, 0.660), (0.690, 0.700), (0.640, 0.730), (0.590, 0.760),
    (0.545, 0.800), (0.500, 0.830), (0.455, 0.800), (0.415, 0.840), (0.370, 0.810),
    (0.330, 0.850), (0.285, 0.810), (0.245, 0.845), (0.205, 0.800), (0.165, 0.830),
    (0.125, 0.780), (0.090, 0.720), (0.060, 0.660), (0.035, 0.600),
]


def map_polygon(size, margin_x=0.06, margin_y=0.10):
    w, h = size
    pts = []
    for fx, fy in USSR_OUTLINE:
        x = margin_x * w + fx * (w * (1 - 2 * margin_x))
        y = margin_y * h + fy * (h * (1 - 2 * margin_y))
        pts.append((x, y))
    return pts


def build_background(emblem):
    W, H = 1920, 1080
    base = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(base)

    # радиальный красный градиент (тёмно-красный по краям → алый в центре)
    grad = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    cx, cy = W // 2, H // 2
    for r in range(int(math.hypot(W, H) / 2), 0, -6):
        v = int(255 * (1 - r / (math.hypot(W, H) / 2)))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    red_layer = Image.new("RGB", (W, H), DARKRED)
    bright = Image.new("RGB", (W, H), RED)
    base = Image.composite(bright, red_layer, grad)

    d = ImageDraw.Draw(base)
    # диагональные лучи конструктивизма
    rays = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(rays)
    for k in range(-6, 7):
        x0 = cx + k * 260
        rd.polygon([(x0, 0), (x0 + 120, 0), (x0 - 320, H), (x0 - 440, H)], fill=26)
    base = Image.composite(Image.new("RGB", (W, H), GOLD), base, rays)

    # сетка «полиграфическая»
    grid = Image.new("L", (W, H), 0)
    grd = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        grd.line([(x, 0), (x, H)], fill=12, width=1)
    for y in range(0, H, 60):
        grd.line([(0, y), (W, y)], fill=12, width=1)
    base = Image.composite(Image.new("RGB", (W, H), DARKRED), base, grid)

    d = ImageDraw.Draw(base)
    # стилизованная КАРТА СССР
    pts = map_polygon((W, H))
    # «территории» — тёплая охра/золото приглушённые
    land = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(land)
    ld.polygon(pts, fill=(180, 120, 20, 150))
    ld.polygon(pts, outline=(255, 215, 0, 230), width=5)
    base_rgba = base.convert("RGBA")
    base_rgba.alpha_composite(land)

    # внутренние «республики» — условные блоки
    import random
    rnd = random.Random(1917)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for i in range(9):
        px = rnd.uniform(min(xs) + 40, max(xs) - 40)
        py = rnd.uniform(min(ys) + 40, max(ys) - 40)
        rw = rnd.uniform(70, 150)
        rh = rnd.uniform(50, 110)
        col = [(204, 0, 0, 90), (139, 0, 0, 110), (255, 215, 0, 60)][i % 3]
        ld.ellipse([px - rw / 2, py - rh / 2, px + rw / 2, py + rh / 2], fill=col)

    d = ImageDraw.Draw(base_rgba)
    # звёзды на карте (столицы союзных республик — условно)
    cap_pts = [(0.12, 0.35), (0.20, 0.28), (0.30, 0.30), (0.40, 0.25),
               (0.52, 0.30), (0.62, 0.26), (0.72, 0.32), (0.82, 0.30),
               (0.45, 0.55), (0.55, 0.60), (0.66, 0.55)]
    for fx, fy in cap_pts:
        x = 0.06 * W + fx * W * 0.88
        y = 0.10 * H + fy * H * 0.80
        draw_star(d, x, y, 9, fill=GOLD, outline=DARKRED, width=1)

    # МОСКВА — большая звезда
    mx = 0.06 * W + 0.115 * W * 0.88
    my = 0.10 * H + 0.36 * H * 0.80
    draw_star(d, mx, my, 22, fill=GOLD, outline=DARKRED, width=3)

    # ПОРТРЕТЫ: Ленин (слева), Сталин (по центру сверху), Троцкий (справа)
    def paste_medal(name, box):
        p = os.path.join(THEME, name)
        m = Image.open(p).convert("RGBA")
        bw, bh = box[2] - box[0], box[3] - box[1]
        m = m.resize((bw, bh), Image.LANCZOS)
        base_rgba.paste(m, (box[0], box[1]), m)

    paste_medal("leader-stalin.png", (820, 300, 1100, 580))
    paste_medal("leader-lenin.png", (330, 560, 560, 790))
    for nm, box in (("leader-marx.png", (1360, 560, 1590, 790)),):
        pth = os.path.join(THEME, nm)
        if os.path.exists(pth):
            paste_medal(nm, box)

    # ГЕРБ СССР — крупно в правом верхнем углу (полупрозрачно, как водяной знак)
    e = emblem.copy()
    e.thumbnail((430, 430), Image.LANCZOS)
    alpha = e.split()[3].point(lambda v: int(v * 0.92))
    tmp = Image.new("RGBA", e.size, (0, 0, 0, 0))
    tmp.paste(e, (0, 0), alpha)
    base_rgba.paste(tmp, (W - e.size[0] - 70, 60), tmp)

    # маленькая надпись под гербом
    fsmall = font(20)
    d = ImageDraw.Draw(base_rgba)
    txt = "ГЕРОСИ · СОЮЗ · СОВЕТСКИХ"
    d.text((W - 430 - 70 + 20, 60 + e.size[1] + 8), "СОЮЗ СОВЕТСКИХ РЕСПУБЛИК",
           font=fsmall, fill=GOLD, stroke_width=1, stroke_fill=BLACK)

    # баннер снизу
    ban = Image.open(os.path.join(THEME, "banner.png")).convert("RGBA")
    bw = int(W * 0.62)
    bh = int(ban.size[1] * bw / ban.size[0])
    ban = ban.resize((bw, bh), Image.LANCZOS)
    base_rgba.paste(ban, ((W - bw) // 2, H - bh - 40), ban)

    vig = vignette(base_rgba.convert("RGB"))
    final = grain(vig, amount=10).convert("RGBA")

    # золотая рамка по краю экрана
    fd = ImageDraw.Draw(final)
    fd.rectangle([3, 3, W - 4, H - 4], outline=GOLD, width=6)
    fd.rectangle([14, 14, W - 15, H - 15], outline=DARKRED, width=2)

    final.convert("RGB").save(os.path.join(THEME, "background.png"))
    print("[out] theme/background.png 1920x1080")
    for (w, h) in [(1366, 768), (1280, 720), (2560, 1440), (3840, 2160)]:
        r = final.convert("RGB").resize((w, h), Image.LANCZOS)
        r.save(os.path.join(THEME, f"background-{w}x{h}.png"))
        print(f"[out] theme/background-{w}x{h}.png")


# ---------------------------------------------------------------------------

def main():
    download_sources()
    emblem = build_emblem()
    build_leaders()
    build_banner(emblem)
    build_countdown(emblem)
    build_background(emblem)
    print("\nГотово: тема обновлена реальными фото и официальным гербом СССР.")


if __name__ == "__main__":
    main()
