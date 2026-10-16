#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор графики для GRUB-темы «СССР» (Arch Linux / Manjaro).
Стиль: конструктивизм и социалистический реализм 1930–1950-х.

Палитра:
  красный      #CC0000
  золотой      #FFD700
  тёмно-красный #8B0000
  чёрный       #000000

Запуск:  python3 scripts/generate_assets.py [outdir]
По умолчанию outdir = ./theme
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ----------------------------------------------------------------------------
# Палитра
# ----------------------------------------------------------------------------
RED        = (204, 0, 0)        # #CC0000
GOLD       = (255, 215, 0)      # #FFD700
DARK_RED   = (139, 0, 0)        # #8B0000
BLACK      = (0, 0, 0)          # #000000
WHITE      = (255, 255, 255)
CREAM      = (255, 246, 205)    # светло-жёлтый/кремовый (для текста)
DEEP_BLACK = (8, 4, 4)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
LIB_DIR  = "/usr/share/fonts/truetype/liberation"


def font(path, size):
    return ImageFont.truetype(path, size)


DEJAVU_SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
DEJAVU_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
DEJAVU_SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
LIB_SANS_B  = os.path.join(LIB_DIR, "LiberationSans-Bold.ttf")


# ----------------------------------------------------------------------------
# Базовые геометрические примитивы (конструктивизм)
# ----------------------------------------------------------------------------
def polygon_pts(cx, cy, r, n, rot=-math.pi / 2):
    """Вершины правильного многоугольника."""
    return [(cx + r * math.cos(rot + 2 * math.pi * i / n),
             cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]


def star5(draw, cx, cy, r, fill, rot=-math.pi / 2):
    """Пятиконечная звезда."""
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.382
        a = rot + math.pi * i / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(pts, fill=fill)


def ray_circle(draw, cx, cy, r_in, r_out, n, fill, width_frac=0.45):
    """Лучи/звезда восходящего солнца вокруг точки."""
    for i in range(n):
        a = 2 * math.pi * i / n
        w = width_frac * math.pi / n
        pts = [
            (cx + r_in * math.cos(a - w), cy + r_in * math.sin(a - w)),
            (cx + r_out * math.cos(a - w * 0.35), cy + r_out * math.sin(a - w * 0.35)),
            (cx + r_out * math.cos(a + w * 0.35), cy + r_out * math.sin(a + w * 0.35)),
            (cx + r_in * math.cos(a + w), cy + r_in * math.sin(a + w)),
        ]
        draw.polygon(pts, fill=fill)


def hammer_sickle(draw, cx, cy, s, fill):
    """
    Серп и молот (стилизованные, векторные примитивы).
    s — масштаб (примерно высота эмблемы в пикселях).
    """
    sick_r_out = int(s * 0.46)
    sick_r_in = int(s * 0.30)
    tmp = Image.new("RGBA", (int(s * 1.6), int(s * 1.6)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    c2 = tmp.width // 2
    # серп: дуга-полукольцо
    td.arc([c2 - sick_r_out, c2 - sick_r_out, c2 + sick_r_out, c2 + sick_r_out],
           start=200, end=70, fill=fill + (255,), width=max(3, sick_r_out - sick_r_in))
    # остриё серпа (сужающийся клин)
    tip_ang = math.radians(70)
    tx, ty = c2 + (sick_r_out + s * 0.02) * math.cos(tip_ang), c2 + (sick_r_out + s * 0.02) * math.sin(tip_ang)
    base_a = math.radians(55)
    p1 = (c2 + sick_r_in * math.cos(base_a), c2 + sick_r_in * math.sin(base_a))
    p2 = (c2 + sick_r_out * math.cos(math.radians(80)), c2 + sick_r_out * math.sin(math.radians(80)))
    td.polygon([p1, p2, tx, ty], fill=fill + (255,))
    # рукоять серпа
    hnd_a = math.radians(200)
    hx, hy = c2 + sick_r_out * 0.92 * math.cos(hnd_a), c2 + sick_r_out * 0.92 * math.sin(hnd_a)
    td.line([(hx, hy), (hx - s * 0.14, hy + s * 0.20)], fill=fill + (255,), width=max(3, int(s * 0.07)))
    tmp = tmp.rotate(-18, resample=Image.BICUBIC, center=(c2, c2))
    draw._image.alpha_composite(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)))

    # --- молот: перекрещенная рукоять + боек
    ang = math.radians(45)
    L = s * 0.95
    x1, y1 = cx - L / 2 * math.cos(ang), cy + L / 2 * math.sin(ang)
    x2, y2 = cx + L / 2 * math.cos(ang), cy - L / 2 * math.sin(ang)
    draw.line([(x1, y1), (x2, y2)], fill=fill, width=max(3, int(s * 0.085)))
    # боек молота (прямоугольник на конце)
    hw, hh = int(s * 0.30), int(s * 0.16)
    head = Image.new("RGBA", (hw * 2, hh * 2), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head)
    hd.rectangle([0, 0, hw * 2, hh * 2], fill=fill + (255,))
    head = head.rotate(-45, resample=Image.BICUBIC, expand=True)
    px = int(x2 - head.width / 2 + s * 0.10 * math.cos(ang))
    py = int(y2 - head.height / 2 - s * 0.10 * math.sin(ang))
    draw._image.alpha_composite(head, (px, py))


def mkdraw(img):
    """ImageDraw с привязкой к исходному RGBA-полотну (для alpha_composite)."""
    d = ImageDraw.Draw(img)
    d._image = img
    return d


# ----------------------------------------------------------------------------
# Карта СССР (стилизованный блок «евразия»)
# ----------------------------------------------------------------------------
def make_ussr_map(size, land=DARK_RED, ocean=None):
    """
    Возвращает RGBA-карту размером size=(w,h).
    Стилизованный силуэт: Запад (Брест) — Восток (Камчатка),
    собран из эллиптических регионов реальной географии (широта/долгота).
    """
    W, H = size
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = mkdraw(img)

    lon_min, lon_max = 10.0, 180.0     # долгота: Прибалтика -> Чукотка
    lat_min, lat_max = 38.0, 82.0      # широта: Кавказ -> Таймыр/Земля Франца-Иосифа

    def proj(lon, lat):
        x = (lon - lon_min) / (lon_max - lon_min) * W
        # сжатие по меридианам (проекция ~ Альберса, упрощённо cos(35°))
        y = (lat_max - lat) / (lat_max - lat_min) * H
        return x, y

    # регионы: (центр_долгота, центр_широта, радиус_долгота, радиус_широта)
    blobs = [
        # Европейская часть
        (37.5, 55.5, 14.0, 8.5),   # Москва/центр РСФСР + Белоруссия/Украина обобщённо
        (24.0, 53.0, 6.5, 5.0),    # Прибалтийско-Белорусский выступ
        (31.0, 47.5, 8.0, 4.5),    # Украина/Крым
        (44.0, 44.5, 6.5, 4.0),    # Кавказ (Сталинград/Грузия)
        (52.0, 46.5, 7.0, 4.5),    # Казахстан западный
        # Урал и Сибирь
        (60.0, 57.0, 5.0, 8.0),    # Урал
        (70.0, 54.0, 8.0, 5.5),    # Казахстан вост./Новосибирск
        (83.0, 61.0, 9.0, 7.0),    # Западная Сибирь
        (98.0, 62.0, 9.0, 7.5),    # Среднесибирское плоскогорье
        (113.0, 60.0, 9.0, 7.0),   # Восточная Сибирь (Красноярск/Якутск)
        (128.0, 61.0, 9.0, 8.0),   # Якутия
        (142.0, 62.0, 8.0, 8.5),   # Дальний Восток: Охотск/Магадан
        (156.0, 60.0, 7.5, 8.0),   # Камчатка/Корякия
        (161.0, 66.0, 6.0, 5.0),   # Чукотка
        # Северные архипелаги (упрощённо)
        (95.0, 76.5, 10.0, 3.5),   # Таймыр/Северная Земля
        (68.0, 73.0, 6.0, 3.0),    # Новая Земля
        (105.0, 71.5, 5.0, 2.5),
        # Южные республики
        (63.0, 41.0, 6.0, 3.5),    # Узбекистан
        (75.0, 40.0, 6.0, 3.0),    # Таджикистан/Киргизия
        (58.0, 40.0, 4.5, 3.0),    # Туркменистан
        # Сахалин/Курилы
        (143.0, 49.0, 1.8, 4.0),
        (152.0, 45.5, 1.5, 2.2),
    ]

    for lon, lat, dlon, dlat in blobs:
        cx, cy = proj(lon, lat)
        rx = abs(proj(lon + dlon, lat)[0] - cx)
        ry = abs(proj(lon, lat + dlat)[1] - cy)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=land + (255,))

    if ocean is not None:
        pass  # фон остаётся прозрачным; океан рисуется снаружи
    return img


# ----------------------------------------------------------------------------
# Фоновое изображение background.png (1920x1080)
# ----------------------------------------------------------------------------
def build_background(W=1920, H=1080):
    img = Image.new("RGB", (W, H), DEEP_BLACK)
    d = mkdraw(img)

    # 1. Градиент: чёрный -> тёмно-красный (ленивый линейный градиент по горизонтали)
    grad = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        t = x / W
        c1 = (10, 2, 2)
        c2 = DARK_RED
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * (t ** 1.6)) for i in range(3))
        gd.line([(x, 0), (x, H)], fill=col)
    img = grad
    d = mkdraw(img)

    # 2. Диагональные красные лучи (конструктивизм) из левого нижнего угла
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    ox, oy = int(W * 0.14), int(H * 0.96)
    for i, (a_deg, w_deg, col) in enumerate([
        (-8, 5, RED + (70,)), (14, 4, GOLD + (38,)), (30, 6, RED + (60,)),
        (46, 3, GOLD + (30,)), (62, 5, RED + (55,)), (78, 4, GOLD + (26,)),
    ]):
        for sign in (1,):
            a1 = math.radians(a_deg - w_deg / 2)
            a2 = math.radians(a_deg + w_deg / 2)
            R = 2600
            rd.polygon([(ox, oy),
                        (ox + R * math.cos(a1), oy + R * math.sin(a1)),
                        (ox + R * math.cos(a2), oy + R * math.sin(a2))], fill=col)
    base = img.convert("RGBA")
    base.alpha_composite(rays)
    img = base

    # 3. Стилизованная карта СССР — полупрозрачный «водяной знак» справа/по центру
    m = make_ussr_map((int(W * 0.78), int(H * 0.52)), land=(120, 8, 8))
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    mscale = Image.new("RGBA", m.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(mscale)
    md.rectangle([0, 0, m.width, m.height], outline=GOLD + (60,), width=2)
    mx = int(W * 0.19)
    my = int(H * 0.20)
    map_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mm = m.copy()
    mm.putalpha(mm.split()[3].point(lambda a: int(a * 0.55)))
    map_layer.paste(mm, (mx, my), mm)
    base = img
    base.alpha_composite(map_layer)
    # тонкая золотая рамка карты
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fr)
    fd.rectangle([mx - 14, my - 14, mx + m.width + 14, my + m.height + 14],
                 outline=GOLD + (90,), width=3)
    # угловые засечки рамки
    for (cx, cy) in [(mx - 14, my - 14), (mx + m.width + 14, my - 14),
                     (mx - 14, my + m.height + 14), (mx + m.width + 14, my + m.height + 14)]:
        fd.line([cx - 18, cy, cx + 18, cy], fill=GOLD + (140,), width=4)
        fd.line([cx, cy - 18, cx, cy + 18], fill=GOLD + (140,), width=4)
    base.alpha_composite(fr)
    img = base

    # 4. Восходящее солнце слева внизу + лучистая звезда
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    sx, sy = ox, oy
    ray_circle(sd, sx, sy, 150, 900, 24, GOLD + (26,), width_frac=0.30)
    sd.ellipse([sx - 120, sy - 120, sx + 120, sy + 120], fill=RED + (120,))
    sd.ellipse([sx - 90, sy - 90, sx + 90, sy + 90], fill=GOLD + (110,))
    star5(sd, sx, sy, 70, GOLD + (200,))
    base.alpha_composite(sun)
    img = base

    # 5. Конструктивистская геометрия: клинья и полосы в правом верхнем углу
    geo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gwd = ImageDraw.Draw(geo)
    gwd.polygon([(W, 0), (W - 520, 0), (W, 300)], fill=RED + (110,))
    gwd.polygon([(W, 0), (W - 300, 0), (W, 170)], fill=GOLD + (90,))
    for i in range(6):
        y0 = 0 + i * 26
        gwd.line([W - 620 + i * 40, y0, W, y0 + 320], fill=BLACK + (70,), width=8)
    # индустриальные силуэты: заводские трубы внизу справа
    bx = int(W * 0.62)
    by = H
    smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    smd = ImageDraw.Draw(smoke)
    silh = BLACK + (150,)
    # корпуса
    smd.rectangle([bx, by - 170, bx + 260, by], fill=silh)
    smd.polygon([(bx + 260, by - 170), (bx + 330, by - 110), (bx + 330, by), (bx + 260, by)], fill=silh)
    # зубчатый верх (социалистическая индустрия)
    for k in range(7):
        x0 = bx + k * 38
        smd.polygon([(x0, by - 170), (x0 + 19, by - 200), (x0 + 38, by - 170)], fill=silh)
    # трубы
    for j, (dx, hh, ww) in enumerate([(30, 330, 26), (95, 380, 30), (160, 300, 22)]):
        smd.rectangle([bx + dx, by - hh, bx + dx + ww, by], fill=silh)
        smd.rectangle([bx + dx - 4, by - hh, bx + dx + ww + 4, by - hh + 14], fill=silh)
    base.alpha_composite(smoke)
    img = base

    # 6. Виньетка
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    mask = vig.point(lambda a: 255 - int(a * 0.9))
    black.putalpha(mask)
    base.alpha_composite(black)
    img = base

    # 7. Зернистость (эффект печатного плаката)
    import random
    rnd = random.Random(1917)
    noise = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise)
    for _ in range(26000):
        x, y = rnd.randrange(W), rnd.randrange(H)
        v = rnd.randint(0, 40)
        nd.point((x, y), fill=(v, v, v, rnd.randint(8, 30)))
    base.alpha_composite(noise)

    # 8. Декоративные надписи на русском
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    f_big = font(DEJAVU_SERIF_B, 64)
    f_small = font(DEJAVU_SANS, 26)
    td.text((W // 2, 46), "ПРОЛЕТАРИИ ВСЕХ СТРАН, СОЕДИНЯЙТЕСЬ!",
            font=f_small, fill=GOLD + (120,), anchor="ma")
    td.text((W - 40, H - 40), "ВЛАСТЬ — СОВЕТАМ! МИР — НАРОДАМ! 1917—1991",
            font=f_small, fill=GOLD + (110,), anchor="ra")
    td.text((40, H - 40), "СЛАВА ТРУДУ · СОЮЗ РЕСПУБЛИК · 1/6 ЧАСТИ СВЕТА",
            font=f_small, fill=CREAM + (90,), anchor="la")
    base.alpha_composite(txt)

    return base.convert("RGB")


# ----------------------------------------------------------------------------
# Гербы / эмблемы для иконок
# ----------------------------------------------------------------------------
def emblem_star_hammer(size=256, bg=RED, fg=GOLD, ring=True):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = mkdraw(img)
    m = size // 2
    pad = int(size * 0.06)
    d.ellipse([pad, pad, size - pad, size - pad], fill=bg + (255,))
    if ring:
        d.ellipse([pad, pad, size - pad, size - pad], outline=fg + (255,), width=max(2, size // 32))
    # колосья (стилизация — дуги по бокам)
    for side in (-1, 1):
        for k in range(5):
            r0 = size * (0.40 + 0.012 * k)
            a1 = math.radians(side * (78 - k * 9) - 90)
            a2 = math.radians(side * (66 - k * 9) - 90)
            cx = m + r0 * math.cos(a1)
            cy = m + r0 * math.sin(a1)
            d.ellipse([cx - size * 0.028, cy - size * 0.05, cx + size * 0.028, cy + size * 0.05],
                      fill=fg + (255,))
    star5(d, m, int(size * 0.30), size * 0.13, fg)
    hammer_sickle(d, m, int(size * 0.58), size * 0.42, fg)
    return img


def icon_base(name, glyph_fn, outdir, size=64):
    """Иконка пункта меню: красная пластина + золотая эмблема."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = mkdraw(img)
    # щит-пластина
    d.rounded_rectangle([2, 2, size - 3, size - 3], radius=size // 8, fill=RED + (255,),
                        outline=GOLD + (255,), width=3)
    glyph_fn(d, size)
    path = os.path.join(outdir, "icons", name)
    img.save(path)
    return img


# Глифы для иконок -----------------------------------------------------------
def g_arch(d, s):
    """Архи-«зуб» — стилизованная буква А (Arch Linux)."""
    c = s // 2
    d.polygon([(c, int(s*0.22)), (int(s*0.78), int(s*0.80)), (int(s*0.64), int(s*0.80)),
               (c, int(s*0.44)), (int(s*0.36), int(s*0.80)), (int(s*0.22), int(s*0.80))], fill=GOLD)
    d.line([int(s*0.34), int(s*0.62), int(s*0.66), int(s*0.62)], fill=GOLD, width=max(2, s//22))


def g_manjaro(d, s):
    """Manjaro — три холма (логотип-подобные волны) в золоте."""
    for i, dy in enumerate((0.30, 0.50, 0.70)):
        d.arc([int(s*0.18), int(s*(dy-0.16)), int(s*0.82), int(s*(dy+0.16))],
              start=200, end=340, fill=GOLD, width=max(3, s // 12))


def g_gear(d, s):
    """Шестерня (дополнительные параметры ядра) — символ индустриализации."""
    c = s // 2
    r1, r2 = int(s * 0.30), int(s * 0.16)
    pts = []
    n = 8
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.pi * i / n
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=GOLD)
    d.ellipse([c - s*0.07, c - s*0.07, c + s*0.07, c + s*0.07], fill=RED)


def g_ram(d, s):
    """Память (загрузка в RAM): красное знамя на древке."""
    d.line([int(s*0.28), int(s*0.18), int(s*0.28), int(s*0.84)], fill=GOLD, width=max(2, s//20))
    d.polygon([(int(s*0.28), int(s*0.20)), (int(s*0.78), int(s*0.28)),
               (int(s*0.62), int(s*0.40)), (int(s*0.78), int(s*0.52)),
               (int(s*0.28), int(s*0.44))], fill=GOLD)


def g_star(d, s):
    star5(d, s // 2, s // 2, int(s * 0.32), GOLD)


def g_terminal(d, s):
    """Терминал: прямоугольник-экран + greater-than."""
    d.rectangle([int(s*0.16), int(s*0.20), int(s*0.84), int(s*0.72)], outline=GOLD, width=max(2, s//18))
    d.line([int(s*0.28), int(s*0.36), int(s*0.40), int(s*0.46)], fill=GOLD, width=max(2, s//16))
    d.line([int(s*0.40), int(s*0.46), int(s*0.28), int(s*0.56)], fill=GOLD, width=max(2, s//16))
    d.line([int(s*0.48), int(s*0.56), int(s*0.66), int(s*0.56)], fill=GOLD, width=max(2, s//16))


def g_uefi(d, s):
    """UEFI/BIOS: шестерня + стрелка загрузки."""
    g_gear(d, s)
    d.polygon([(int(s*0.72), int(s*0.16)), (int(s*0.86), int(s*0.30)), (int(s*0.72), int(s*0.30))], fill=GOLD)


def g_windows(d, s):
    """Windows: четыре окна-квадрата."""
    q = s * 0.26
    c = s // 2
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        d.rectangle([c + (dx * 2 - 1) * q / 2 - 2, c + (dy * 2 - 1) * q / 2 - 2,
                     c + (dx * 2 + 1) * q / 2 - 2, c + (dy * 2 + 1) * q / 2 - 2], fill=GOLD)


def g_memtest(d, s):
    """Memtest: чип памяти с ножками."""
    d.rectangle([int(s*0.24), int(s*0.30), int(s*0.76), int(s*0.70)], outline=GOLD, width=max(2, s//20))
    for i in range(4):
        x = int(s * (0.30 + 0.14 * i))
        d.line([x, int(s*0.18), x, int(s*0.30)], fill=GOLD, width=max(2, s//22))
        d.line([x, int(s*0.70), x, int(s*0.82)], fill=GOLD, width=max(2, s//22))
    d.line([int(s*0.32), int(s*0.50), int(s*0.68), int(s*0.50)], fill=GOLD, width=max(2, s//18))


# ----------------------------------------------------------------------------
# selected_item.png — рамка выделенного пункта
# ----------------------------------------------------------------------------
def build_selected(w=640, h=64, scale=3):
    W, H = w * scale, h * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = mkdraw(img)
    bw = max(6, H // 10)
    # золотая двойная рамка
    d.rectangle([bw, bw, W - bw - 1, H - bw - 1], outline=GOLD + (255,), width=bw)
    d.rectangle([bw * 3, bw * 3, W - bw * 3 - 1, H - bw * 3 - 1], outline=GOLD + (160,), width=max(2, bw // 3))
    # угловые звёзды
    for (cx, cy) in [(bw * 2, bw * 2), (W - bw * 2, bw * 2), (bw * 2, H - bw * 2), (W - bw * 2, H - bw * 2)]:
        star5(d, cx, cy, bw * 1.6, GOLD + (255,))
    return img.resize((w, h), Image.LANCZOS)


# ----------------------------------------------------------------------------
# slider_thumb.png — «медаль» прокрутки
# ----------------------------------------------------------------------------
def build_slider_thumb(size=32):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = mkdraw(img)
    d.ellipse([1, 1, size - 2, size - 2], fill=RED + (255,), outline=GOLD + (255,), width=2)
    star5(d, size // 2, size // 2, size * 0.30, GOLD + (255,))
    return img


def build_slider_bg(w=24, h=64):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = mkdraw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=DARK_RED + (200,), outline=GOLD + (140,), width=2)
    return img


def build_progress_bar(w=300, h=24):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = mkdraw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=BLACK + (200,), outline=GOLD + (255,), width=2)
    return img


def build_progress_highlight(w=300, h=24):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = mkdraw(img)
    d.rectangle([1, 1, w - 2, h - 2], fill=GOLD + (230,))
    return img


# ----------------------------------------------------------------------------
# Советский таймер обратного отсчёта (plakat-style countdown)
# ----------------------------------------------------------------------------
def build_countdown_frame(w=280, h=120):
    """
    Рамка-«окончины» для таймера: красное знамя, звезда, лавровые ветви.
    GRUB не поддерживает анимацию, поэтому это статичная плашка под time_left;
    живую «стрелку курантов» добавляет скрипт gen_countdown_frames.py.
    """
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = mkdraw(img)
    # корпус
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=10, fill=DARK_RED + (235,), outline=GOLD + (255,), width=3)
    # верхняя полоса-знамя
    d.polygon([(6, 6), (w - 6, 6), (w - 6, h * 0.30), (6, h * 0.22)], fill=RED + (255,))
    # звезда
    star5(d, w // 2, int(h * 0.17), int(h * 0.12), GOLD + (255,))
    # лавровые ветви (дуги из «листьев»)
    for side in (-1, 1):
        cx = w // 2 + side * int(w * 0.34)
        for k in range(6):
            yy = int(h * (0.42 + k * 0.09))
            xx = cx + side * int(w * 0.06 * math.sin(k * 0.5))
            d.ellipse([xx - 7, yy - 4, xx + 7, yy + 4], fill=GOLD + (210,))
    return img


# ----------------------------------------------------------------------------
# Портреты вождей (силуэты в духе агитплаката)
# ----------------------------------------------------------------------------
def leader_silhouette(kind, size=256):
    """
    Стилизованная silhouette-карточка вождя (не фоторобот —
    обобщённые черты: кепка/усы/фуражка), как на плакате РОСТА.
    kind: lenin | stalin | trotsky
    """
    S = size
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = mkdraw(img)
    # карточка
    d.rounded_rectangle([2, 2, S - 3, S - 3], radius=S // 12, fill=BLACK + (255,), outline=GOLD + (255,), width=3)
    # красный круг-знамя сзади головы
    d.ellipse([S * 0.18, S * 0.10, S * 0.82, S * 0.74], fill=RED + (255,))
    ink = CREAM + (255,)
    cx = S // 2
    # голова (овал) + шея + плечи
    d.ellipse([cx - S*0.16, S*0.24, cx + S*0.16, S*0.52], fill=ink)
    d.polygon([(cx - S*0.07, S*0.48), (cx + S*0.07, S*0.48), (cx + S*0.09, S*0.60), (cx - S*0.09, S*0.60)], fill=ink)
    d.polygon([(cx - S*0.30, S*0.86), (cx - S*0.12, S*0.58), (cx + S*0.12, S*0.58), (cx + S*0.30, S*0.86)], fill=ink)
    # воротник-китель
    d.polygon([(cx - S*0.10, S*0.60), (cx, S*0.70), (cx + S*0.10, S*0.60), (cx + S*0.06, S*0.60), (cx, S*0.66), (cx - S*0.06, S*0.60)], fill=RED + (255,))

    if kind == "lenin":
        # лысина + шапка-французик? нет: характерная «шапка» волос по бокам
        d.ellipse([cx - S*0.15, S*0.22, cx + S*0.15, S*0.40], fill=BLACK + (255,))  # тень верхней части
        d.pieslice([cx - S*0.17, S*0.20, cx + S*0.17, S*0.50], 180, 360, fill=ink)   # купол черепа
        d.polygon([(cx - S*0.17, S*0.34), (cx - S*0.10, S*0.30), (cx - S*0.12, S*0.44), (cx - S*0.18, S*0.42)], fill=ink)  # волосы сбоку
        d.polygon([(cx + S*0.17, S*0.34), (cx + S*0.10, S*0.30), (cx + S*0.12, S*0.44), (cx + S*0.18, S*0.42)], fill=ink)
        # борода
        d.polygon([(cx - S*0.10, S*0.44), (cx + S*0.10, S*0.44), (cx + S*0.06, S*0.58), (cx, S*0.62), (cx - S*0.06, S*0.58)], fill=ink)
        d.ellipse([cx - S*0.05, S*0.50, cx + S*0.05, S*0.60], fill=ink)
    elif kind == "stalin":
        # фуражка с околышем и кокардой
        d.pieslice([cx - S*0.20, S*0.10, cx + S*0.20, S*0.36], 180, 360, fill=ink)
        d.rectangle([cx - S*0.20, S*0.24, cx + S*0.20, S*0.30], fill=ink)
        d.rectangle([cx - S*0.22, S*0.28, cx + S*0.22, S*0.34], fill=BLACK + (255,))  # тулья тёмная
        d.rectangle([cx - S*0.20, S*0.24, cx + S*0.20, S*0.30], fill=RED + (255,))    # красный околыш
        star5(d, cx, S * 0.27, S * 0.035, GOLD + (255,))                              # кокарда-звезда
        # бакенбарды + усы
        d.polygon([(cx - S*0.16, S*0.36), (cx - S*0.10, S*0.40), (cx - S*0.12, S*0.52), (cx - S*0.17, S*0.46)], fill=ink)
        d.polygon([(cx + S*0.16, S*0.36), (cx + S*0.10, S*0.40), (cx + S*0.12, S*0.52), (cx + S*0.17, S*0.46)], fill=ink)
        d.polygon([(cx - S*0.09, S*0.44), (cx + S*0.09, S*0.44), (cx + S*0.06, S*0.48), (cx, S*0.47), (cx - S*0.06, S*0.48)], fill=ink)
        # причёска назад
        d.pieslice([cx - S*0.17, S*0.26, cx + S*0.17, S*0.42], 0, 180, fill=ink)
    elif kind == "trotsky":
        # очки + бородка-клинышек + мягкая шапка
        d.pieslice([cx - S*0.18, S*0.14, cx + S*0.18, S*0.38], 180, 360, fill=ink)
        d.rectangle([cx - S*0.19, S*0.30, cx + S*0.19, S*0.36], fill=ink)
        # пенсне
        r = S * 0.045
        for ex in (cx - S*0.07, cx + S*0.07):
            d.ellipse([ex - r, S*0.36 - r, ex + r, S*0.36 + r], outline=BLACK + (255,), width=max(2, int(S*0.012)))
        d.line([cx - S*0.025, S*0.36, cx + S*0.025, S*0.36], fill=BLACK + (255,), width=max(2, int(S*0.01)))
        # острая борода
        d.polygon([(cx - S*0.09, S*0.46), (cx + S*0.09, S*0.46), (cx, S*0.66)], fill=ink)
    # табличка снизу
    f = font(DEJAVU_BOLD, max(10, int(S * 0.085)))
    names = {"lenin": "ИЛЬИЧ", "stalin": "СТАЛИН", "trotsky": "ТРОЦКИЙ"}
    d.text((cx, S * 0.93), names[kind], font=f, fill=GOLD + (255,), anchor="mm")
    return img


# ----------------------------------------------------------------------------
# Основной заголовок title panel (не обязателен для theme.txt, но красиво)
# ----------------------------------------------------------------------------
def build_banner(w=1200, h=110):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = mkdraw(img)
    d.polygon([(0, 0), (w, 0), (w - 30, h), (30, h)], fill=RED + (235,))
    d.line([0, 0, w, 0], fill=GOLD + (255,), width=6)
    d.line([30, h - 4, w - 30, h - 4], fill=GOLD + (255,), width=6)
    f1 = font(DEJAVU_SERIF_B, 58)
    f2 = font(DEJAVU_BOLD, 22)
    star5(d, 90, h // 2, 34, GOLD + (255,))
    star5(d, w - 90, h // 2, 34, GOLD + (255,))
    d.text((w // 2, h // 2 - 18), "ARCH LINUX · MANJARO", font=f1, fill=GOLD + (255,), anchor="mm")
    d.text((w // 2, h // 2 + 30), "ЗАГРУЗОЧНАЯ СИСТЕМА НАРОДНОГО КОМПЬЮТЕРА · ГОСТ Р 1917-2026", font=f2, fill=CREAM + (230,), anchor="mm")
    return img


# ----------------------------------------------------------------------------
# Сборка всего
# ----------------------------------------------------------------------------
def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "theme")
    os.makedirs(os.path.join(outdir, "fonts"), exist_ok=True)
    os.makedirs(os.path.join(outdir, "icons"), exist_ok=True)
    os.makedirs(os.path.join(outdir, "previews"), exist_ok=True)

    print("[*] background.png (1920x1080)…")
    build_background(1920, 1080).save(os.path.join(outdir, "background.png"))

    print("[*] варианты разрешений…")
    for (w, h, fname) in [(1366, 768, "background-1366x768.png"),
                          (1280, 720, "background-1280x720.png"),
                          (2560, 1440, "background-2560x1440.png"),
                          (3840, 2160, "background-3840x2160.png")]:
        build_background(w, h).save(os.path.join(outdir, fname))

    print("[*] selected_item.png / slider / progress…")
    build_selected().save(os.path.join(outdir, "selected_item.png"))
    build_slider_thumb().save(os.path.join(outdir, "slider_thumb.png"))
    build_slider_bg().save(os.path.join(outdir, "slider_bg.png"))
    build_progress_bar().save(os.path.join(outdir, "progress_bar.png"))
    build_progress_highlight().save(os.path.join(outdir, "progress_highlight.png"))
    build_countdown_frame().save(os.path.join(outdir, "countdown_frame.png"))

    print("[*] иконки пунктов меню…")
    icons = {
        "arch.png": g_arch, "manjaro.png": g_manjaro, "gear.png": g_gear,
        "ram.png": g_ram, "star.png": g_star, "terminal.png": g_terminal,
        "uefi.png": g_uefi, "windows.png": g_windows, "memtest.png": g_memtest,
    }
    for name, fn in icons.items():
        icon_base(name, fn, outdir, size=64)

    print("[*] герб СССР (emblem.png)…")
    emblem_star_hammer(512).save(os.path.join(outdir, "emblem.png"))
    emblem_star_hammer(64, ring=False).save(os.path.join(outdir, "icons", "emblem-64.png"))

    print("[*] портреты вождей…")
    for k in ("lenin", "stalin", "trotsky"):
        leader_silhouette(k, 256).save(os.path.join(outdir, f"leader-{k}.png"))

    print("[*] баннер…")
    build_banner().save(os.path.join(outdir, "banner.png"))

    print("[*] превью-композиция…")
    prev = Image.open(os.path.join(outdir, "background.png")).convert("RGBA")
    ov = Image.new("RGBA", prev.size, (0, 0, 0, 0))
    emb = emblem_star_hammer(200)
    ov.paste(emb, (60, 60), emb)
    x = 300
    for k in ("lenin", "stalin", "trotsky"):
        p = Image.open(os.path.join(outdir, f"leader-{k}.png")).resize((150, 150))
        ov.paste(p, (x, 70), p)
        x += 170
    ban = build_banner()
    ov.paste(ban, ((prev.width - ban.width) // 2, 260), ban)
    menu = Image.new("RGBA", (640, 380), (0, 0, 0, 150))
    md = ImageDraw.Draw(menu)
    items = ["Arch Linux (ядro linux)", "Arch Linux (fallback)", "Manjaro Linux",
             "Дополнительные параметры ядра", "Загрузка в текстовом режиме",
             "Проверка памяти (memtest)", "Система Windows"]
    fy = font(DEJAVU_SANS, 24)
    for i, it in enumerate(items):
        y = 10 + i * 52
        if i == 0:
            sel = build_selected(620, 48)
            menu.paste(sel, (10, y - 4), sel)
            md.text((30, y + 8), it, font=fy, fill=GOLD + (255,))
        else:
            md.text((30, y + 8), it, font=fy, fill=CREAM + (255,))
    ov.paste(menu, (120, 470), menu)
    cf = build_countdown_frame(280, 120)
    cd = ImageDraw.Draw(cf)
    ft = font(DEJAVU_SERIF_B, 46)
    cd.text((140, 78), "0:07", font=ft, fill=GOLD + (255,), anchor="mm")
    ov.paste(cf, (prev.width - 330, prev.height - 160), cf)
    prev.alpha_composite(ov)
    prev.convert("RGB").save(os.path.join(outdir, "previews", "preview-1920x1080.jpg"), quality=92)

    print("[OK] Все ассеты созданы в:", outdir)


if __name__ == "__main__":
    main()
