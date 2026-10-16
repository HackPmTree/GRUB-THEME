#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_v2.py — пересборка темы GRUB «СССР» (v2):

НОВое в этой версии:
  * фон — НАСТОЯЩАЯ карта мира (Natural Earth 1:50m, public domain),
    территория СССР (15 республик) выделена алым #CC0000 с золотой #FFD700
    обводкой и подписью «СОЮЗ СОВЕТСКИХ РЕСПУБЛИК»;
  * добавлен К. Маркс (реальное фото из assets/sources/marks.jpg);
  * Троцкий УДАЛЁН из всех ассетов;
  * портреты (Маркс, Энгельс, Ленин, Сталин) — дуотонные агитмедальоны;
  * слоган «I use Arch, btw» — на плашке у Маркса (по-английски, как мем);
  * заголовок в theme.txt — «Arch Linux / Manjaro» (на английском),
    остальной интерфейс — по-русски;
  * кнопки панели управления («Настройки», «Загрузка», «Выключить») —
    рабочие: привязаны к встроенным действиям GRUB @grub_dir/@bootdir/
    @rootdir (в этих пунктах меню Enter выполняет действие).

Исходники: assets/sources/  (marks.jpg, stalin.webp, lenin.jpg,
                             engels.png, emblem-1280.png, world_countries.geojson)
Пересборка:  python3 scripts/rebuild_v2.py
"""

import os
import io
import json
import math
import random
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "sources")
THEME = os.path.join(ROOT, "theme")
PREV = os.path.join(THEME, "previews")

RED = (204, 0, 0)          # #CC0000
GOLD = (255, 215, 0)       # #FFD700
DARKRED = (139, 0, 0)      # #8B0000
BLACK = (0, 0, 0)
CREAM = (255, 246, 205)    # светло-жёлтый
OLIVE = (58, 46, 30)       # нейтральные страны на карте

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]
FONT_REG_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def font(size, bold=True):
    paths = FONT_PATHS if bold else FONT_REG_PATHS
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Скачивание исходников (если не скачаны)
# ---------------------------------------------------------------------------

SOURCES = {
    "marks.jpg": ("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSNDTavb"
                  "4P_6a2VYzXB4515j936J3WSNrEjFDgVQEZ8lFsQRSm42GAOfTKIYJaXbS3qW55"
                  "r-AkTgiUg-qbU2gf2GZrFkkATnjvituWji6PJ&s=10"),
    "stalin.webp": "https://topwar.ru/uploads/posts/2024-09/d860758bdf_stalin-2.webp",
    "lenin.jpg": "https://chaltlib.ru/images/ubilei2017/207.jpg",
    "emblem-1280.png": ("https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d9/"
                        "Coat_of_arms_of_the_Soviet_Union_%281956%E2%80%931991%29.svg"
                        "/1280px-Coat_of_arms_of_the_Soviet_Union_%281956%E2%80%931991%29.svg.png"),
    "world_countries.geojson": ("https://raw.githubusercontent.com/nvkelso/"
                                "natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson"),
}


def download_sources():
    os.makedirs(SRC, exist_ok=True)
    for name, url in SOURCES.items():
        dst = os.path.join(SRC, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 2048:
            print(f"[src] есть локально: {name}")
            continue
        print(f"[src] скачиваю {name} ...")
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            open(dst, "wb").write(data)
            print(f"[src] сохранён {name} ({len(data)} байт)")
        except Exception as e:
            print(f"[src] НЕ удалось скачать {name}: {e}")


# ---------------------------------------------------------------------------
# Утилиты плакатной обработки
# ---------------------------------------------------------------------------

def load_rgb(path):
    im = Image.open(path)
    im.load()
    return im.convert("RGB")


def duotone_poster(im, shadow=DARKRED, light=GOLD, cutoff_lo=0.28, cutoff_hi=0.70,
                   contrast=1.35, brightness=1.06):
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=(cutoff_lo * 100, (1 - cutoff_hi) * 100))
    g = ImageEnhance.Contrast(g).enhance(contrast)
    g = ImageEnhance.Brightness(g).enhance(brightness)
    luts = []
    for c in range(3):
        table = []
        for v in range(256):
            t = v / 255.0
            tt = t * t * (3 - 2 * t)
            val = shadow[c] + (light[c] - shadow[c]) * tt
            table.append(max(0, min(255, int(val))))
        luts.append(table)
    return Image.merge("RGB", tuple(g.point(l) for l in luts))


def grain(im, amount=14, seed=7):
    rnd = random.Random(seed)
    w, h = im.size
    nw, nh = max(1, w // 2), max(1, h // 2)
    nz = Image.new("L", (nw, nh))
    px = nz.load()
    for y in range(nh):
        for x in range(nw):
            px[x, y] = 128 + rnd.randint(-amount, amount)
    nz = nz.resize((w, h), Image.BILINEAR)
    noise_rgb = Image.merge("RGB", (nz, nz, nz))
    base_rgb = im.convert("RGB")
    diff = ImageChops.soft_light(base_rgb, noise_rgb)
    out = Image.blend(base_rgb, diff, 0.10)
    if im.mode == "RGBA":
        out.putalpha(im.split()[3])
    return out


def vignette(im, strength=0.5, color=BLACK):
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    cx, cy = w / 2, h / 2
    steps = 40
    for i in range(steps, 0, -1):
        a = int(255 * (i / steps))
        rx = w * 0.66 * (i / steps)
        ry = h * 0.66 * (i / steps)
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


def crop_to_ratio(im, ratio_w=1.0, ratio_h=1.0, focus_y=0.32, focus_x=0.5):
    w, h = im.size
    target = ratio_w / ratio_h
    cur = w / h
    if cur > target:
        nw = int(h * target)
        x0 = int((w - nw) * focus_x)
        box = (x0, 0, x0 + nw, h)
    else:
        nh = int(w / target)
        y0 = int((h - nh) * focus_y)
        box = (0, y0, w, y0 + nh)
    return im.crop(box)


def make_medallion(src_im, out_path, size=512, label="", sublabel="", tagline=""):
    """Круглый медальон-«орден»: дуотонное фото в золотом венце со звездой."""
    src = crop_to_ratio(src_im, 1.0, 1.0, focus_y=0.28)
    src = src.resize((size, size), Image.LANCZOS)
    poster = duotone_poster(src)
    poster = grain(poster, amount=12)

    disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    dm = ImageDraw.Draw(mask)
    pad = 10
    dm.ellipse([pad, pad, size - pad, size - pad], fill=255)
    disc.paste(poster, (0, 0), mask)

    d = ImageDraw.Draw(disc)
    d.ellipse([pad, pad, size - pad, size - pad], outline=GOLD, width=6)
    d.ellipse([pad + 10, pad + 10, size - 10 - pad, size - 10 - pad], outline=DARKRED, width=3)
    draw_star(d, size // 2, pad + 4, 16, fill=GOLD, outline=DARKRED, width=2)

    bottom_extra = 34 if tagline else 0
    lh = (64 if sublabel else 44) + bottom_extra
    canvas = Image.new("RGBA", (size, size + lh), (0, 0, 0, 0))
    canvas.paste(disc, (0, 0), disc)
    dc = ImageDraw.Draw(canvas)
    f = font(26 if size >= 448 else 20)
    fs = font(18 if size >= 448 else 14)
    if label:
        bbox = dc.textbbox((0, 0), label, font=f)
        tw = bbox[2] - bbox[0]
        dc.text(((size - tw) // 2, size + 4), label, font=f, fill=GOLD,
                stroke_width=2, stroke_fill=DARKRED)
    if sublabel:
        bbox2 = dc.textbbox((0, 0), sublabel, font=fs)
        tw2 = bbox2[2] - bbox2[0]
        dc.text(((size - tw2) // 2, size + 34), sublabel, font=fs, fill=CREAM)
    if tagline:
        ft = font(17)
        tb = dc.textbbox((0, 0), tagline, font=ft)
        twt = tb[2] - tb[0]
        tx = (size - twt) // 2
        ty = size + (64 if sublabel else 44)
        dc.rounded_rectangle([tx - 12, ty - 5, tx + twt + 12, ty + 27], radius=8,
                             fill=BLACK, outline=GOLD, width=2)
        dc.text((tx, ty), tagline, font=ft, fill=GOLD)
    canvas.save(out_path)
    print("[out]", out_path)


# ---------------------------------------------------------------------------
# Герб СССР
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
    em = Image.open(os.path.join(SRC, "emblem-1280.png")).convert("RGBA")
    em = trim_alpha(em, pad=12)
    main = em.copy()
    main.thumbnail((720, 720), Image.LANCZOS)
    main.save(os.path.join(THEME, "emblem.png"))
    ic = em.copy()
    ic.thumbnail((64, 64), Image.LANCZOS)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.paste(ic, ((64 - ic.size[0]) // 2, (64 - ic.size[1]) // 2), ic)
    canvas.save(os.path.join(THEME, "icons", "emblem-64.png"))
    print("[out] theme/emblem.png + icons/emblem-64.png")
    return em


# ---------------------------------------------------------------------------
# Портреты: Маркс (кадр из user-фото), Энгельс, Ленин, Сталин. Троцкий убран.
# ---------------------------------------------------------------------------

def crop_half(im, right=True):
    """Составное фото классиков: Энгельс — левая половина, Маркс — правая."""
    w, h = im.size
    if right:
        return im.crop((int(w * 0.50), 0, w, h))
    return im.crop((0, 0, int(w * 0.52), h))


def build_leaders():
    marks = load_rgb(os.path.join(SRC, "marks.jpg"))
    marx_src = crop_half(marks, right=True).resize((marks.width, marks.height * 2), Image.LANCZOS)
    make_medallion(marx_src, os.path.join(THEME, "leader-marx.png"), size=512,
                   label="К. МАРКС", sublabel="1818 — 1883",
                   tagline="I use Arch, btw")
    eng_src = crop_half(marks, right=False).resize((marks.width, marks.height * 2), Image.LANCZOS)
    make_medallion(eng_src, os.path.join(THEME, "leader-engels.png"), size=512,
                   label="Ф. ЭНГЕЛЬС", sublabel="1820 — 1895")
    make_medallion(load_rgb(os.path.join(SRC, "lenin.jpg")),
                   os.path.join(THEME, "leader-lenin.png"), size=512,
                   label="В. И. ЛЕНИН", sublabel="1870 — 1924")
    make_medallion(load_rgb(os.path.join(SRC, "stalin.webp")),
                   os.path.join(THEME, "leader-stalin.png"), size=512,
                   label="И. В. СТАЛИН", sublabel="вождь народов")
    # Троцкий удалён
    tro = os.path.join(THEME, "leader-trotsky.png")
    if os.path.exists(tro):
        os.remove(tro)
        print("[rm ] theme/leader-trotsky.png (Троцкий убран)")
    for sub in ("icons", "previews"):
        p = os.path.join(THEME, sub, "trotsky.png")
        if os.path.exists(p):
            os.remove(p)


# ---------------------------------------------------------------------------
# Баннер, плашка таймера, кнопки панели управления
# ---------------------------------------------------------------------------

def build_banner(emblem):
    w, h = 1200, 130
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=RED, outline=GOLD, width=5)
    d.line([10, h - 18, w - 10, h - 18], fill=DARKRED, width=3)
    e = emblem.copy()
    e.thumbnail((h - 26, h - 26), Image.LANCZOS)
    im.paste(e, (18, (h - e.size[1]) // 2), e)
    f = font(44)
    fs = font(22)
    title = "ARCH LINUX · MANJARO"
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
    for i in range(7):
        ang = math.radians(200 + i * 12)
        cx, cy = w - 26, h // 2
        x = cx + 18 * math.cos(ang)
        y = cy + 34 * math.sin(ang)
        d.ellipse([x - 5, y - 2, x + 5, y + 2], fill=GOLD, outline=DARKRED)
    im.save(os.path.join(THEME, "countdown_frame.png"))
    print("[out] theme/countdown_frame.png")


def _btn(text, normal_fill, normal_line, sel_fill, sel_line, w=210, h=52):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=10, fill=normal_fill,
                        outline=normal_line, width=3)
    f = font(22)
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    d.text(((w - tw) // 2, (h - (bbox[3] - bbox[1])) // 2 - 2), text, font=f, fill=GOLD)
    return im, w, h


def build_buttons():
    specs = [("settings", "НАСТРОЙКИ"), ("boot", "ЗАГРУЗКА"), ("power", "ВЫКЛЮЧИТЬ")]
    for key, text in specs:
        im, w, h = _btn(text, DARKRED, GOLD, None, None)
        im.save(os.path.join(THEME, f"btn-{key}.png"))
        # selected-вариант: золотая плашка, тёмно-красный текст
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ds = ImageDraw.Draw(s)
        ds.rounded_rectangle([2, 2, w - 3, h - 3], radius=10, fill=GOLD, outline=BLACK, width=3)
        f = font(22)
        bbox = ds.textbbox((0, 0), text, font=f)
        tw = bbox[2] - bbox[0]
        ds.text(((w - tw) // 2, (h - (bbox[3] - bbox[1])) // 2 - 2), text, font=f, fill=DARKRED)
        s.save(os.path.join(THEME, f"btn-{key}-sel.png"))
        print(f"[out] theme/btn-{key}.png + btn-{key}-sel.png")


# ---------------------------------------------------------------------------
# ФОН: настоящая карта мира (Natural Earth) + СССР алым + портреты + герб
# ---------------------------------------------------------------------------

USSR_ISO = {"RUS", "UKR", "BLR", "UZB", "KAZ", "GEO", "AZE", "LTU", "MDA",
            "LVA", "TJK", "ARM", "TKM", "PRK"}


def geo_rings(geom):
    if geom is None:
        return []
    t = geom["type"]
    c = geom["coordinates"]
    if t == "Polygon":
        return [c]
    if t == "MultiPolygon":
        return c
    return []


def render_world_map(W, H, scale=1.0, center_lon=60.0, center_lat=55.0):
    """Эquirectangular-проекция, увеличенная к центру над территорией СССР."""
    gj = json.load(open(os.path.join(SRC, "world_countries.geojson")))
    # базовая проекция: вся планета вписана в BW x BH, затем «окно» W x H
    # над центром (center_lon, center_lat)
    BW, BH = int(W * scale), int(H * scale)

    def proj(lon, lat):
        x = (lon + 180.0) / 360.0 * BW
        y = (90.0 - lat) / 180.0 * BH
        return x, y

    cx = (center_lon + 180.0) / 360.0 * BW
    cy = (90.0 - center_lat) / 180.0 * BH
    ox = cx - W / 2.0
    oy = cy - H / 2.0

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    # сетка меридианов/параллелей (атласный стиль) поверх красного знамени
    for lon in range(-180, 181, 15):
        x, _ = proj(lon, 0)
        gd.line([(x - ox, -oy), (x - ox, BH - oy)], fill=(46, 16, 16, 255), width=1)
    for lat in range(-90, 91, 15):
        _, y = proj(0, lat)
        gd.line([(-ox, y - oy), (BW - ox, y - oy)], fill=(46, 16, 16, 255), width=1)

    land = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(land)
    ussr_polys = []
    for feat in gj["features"]:
        props = feat["properties"]
        iso = props.get("ISO_A3") or props.get("ADM0_A3")
        is_ussr = iso in USSR_ISO
        for poly in geo_rings(feat["geometry"]):
            outer = poly[0]
            pts = []
            for lon, lat in outer:
                x, y = proj(lon, lat)
                pts.append((x - ox, y - oy))
            seqs, cur, prev = [], [], None
            for p in pts:
                if prev is not None and abs(p[0] - prev[0]) > W / 2:
                    seqs.append(cur)
                    cur = []
                cur.append(p)
                prev = p
            seqs.append(cur)
            for s in seqs:
                if len(s) < 3:
                    continue
                if is_ussr:
                    ussr_polys.append(s)
                else:
                    ld.polygon(s, fill=OLIVE, outline=(84, 66, 40))
    # СССР поверх — алый с золотой обводкой (слегка расширенной)
    for s in ussr_polys:
        ld.polygon(s, fill=RED)
    for s in ussr_polys:
        ld.line(s + [s[0]], fill=GOLD, width=4, joint="curve")
    return land, grid, (ox, oy, BW, BH, proj)


def build_background(emblem):
    W, H = 1920, 1080

    # --- красное знамя с лучами (низ слоя) -------------------------------
    base = Image.new("RGB", (W, H), DARKRED)
    grad = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    cx, cy = W // 2, int(H * 0.42)
    maxr = math.hypot(W, H) / 2
    for r in range(int(maxr), 0, -6):
        v = int(255 * (1 - r / maxr))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    base = Image.composite(Image.new("RGB", (W, H), RED), base, grad)

    rays = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(rays)
    for k in range(-7, 8):
        x0 = cx + k * 240
        rd.polygon([(x0, 0), (x0 + 110, 0), (x0 - 340, H), (x0 - 450, H)], fill=22)
    base = Image.composite(Image.new("RGB", (W, H), GOLD), base, rays)

    grid = Image.new("L", (W, H), 0)
    grd = ImageDraw.Draw(grid)
    for x in range(0, W, 60):
        grd.line([(x, 0), (x, H)], fill=10, width=1)
    for y in range(0, H, 60):
        grd.line([(0, y), (W, y)], fill=10, width=1)
    base = Image.composite(Image.new("RGB", (W, H), BLACK), base, grid)

    rgba = base.convert("RGBA")

    # --- карта мира ------------------------------------------------------
    land, graticule, meta = render_world_map(W, H, scale=1.35,
                                             center_lon=62.0, center_lat=56.0)
    rgba.alpha_composite(graticule)   # сетка меридианов поверх знамени
    map_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    map_layer.paste(land, (0, 0), land)
    # лёгкая прозрачность карты, чтобы знамя «просвечивало»
    a = map_layer.split()[3].point(lambda v: int(v * 0.94))
    map_layer.putalpha(a)
    rgba.alpha_composite(map_layer)

    d = ImageDraw.Draw(rgba)
    # подпись «СОЮЗ СОВЕТСКИХ РЕСПУБЛИК» над центром СССР (примерно Екатеринбург)
    ox, oy, BW, BH, proj = meta
    lx, ly = proj(60.0, 56.5)
    lx -= ox
    ly -= oy
    fname = font(34)
    txt = "СОЮЗ СОВЕТСКИХ РЕСПУБЛИК"
    bb = d.textbbox((0, 0), txt, font=fname)
    tw = bb[2] - bb[0]
    d.text((lx - tw / 2 + 2, ly - 20 + 2), txt, font=fname, fill=BLACK)
    d.text((lx - tw / 2, ly - 20), txt, font=fname, fill=GOLD,
           stroke_width=1, stroke_fill=DARKRED)
    # Москва — звезда
    mx, my = proj(37.6, 55.75)
    draw_star(d, mx - ox, my - oy, 16, fill=GOLD, outline=DARKRED, width=2)

    # --- портреты-медальоны (без Троцкого) -------------------------------
    def paste_medal(name, box):
        m = Image.open(os.path.join(THEME, name)).convert("RGBA")
        bw_, bh_ = box[2] - box[0], box[3] - box[1]
        m = m.resize((bw_, bh_), Image.LANCZOS)
        rgba.paste(m, (box[0], box[1]), m)

    paste_medal("leader-marx.png", (150, 470, 470, 890))      # Маркс — слева
    paste_medal("leader-engels.png", (1480, 470, 1770, 840))  # Энгельс — справа
    paste_medal("leader-lenin.png", (560, 600, 800, 950))     # Ленин
    paste_medal("leader-stalin.png", (1150, 600, 1390, 950))  # Сталин

    # --- герб СССР (водяной знак сверху по центру) -----------------------
    e = emblem.copy()
    e.thumbnail((360, 360), Image.LANCZOS)
    alpha = e.split()[3].point(lambda v: int(v * 0.9))
    tmp = Image.new("RGBA", e.size, (0, 0, 0, 0))
    tmp.paste(e, (0, 0), alpha)
    rgba.paste(tmp, ((W - e.size[0]) // 2, 40), tmp)

    # --- финальная обработка ---------------------------------------------
    final = vignette(rgba.convert("RGB"), strength=0.45)
    final = grain(final, amount=9).convert("RGBA")
    fd = ImageDraw.Draw(final)
    fd.rectangle([3, 3, W - 4, H - 4], outline=GOLD, width=6)
    fd.rectangle([14, 14, W - 15, H - 15], outline=DARKRED, width=2)

    final.convert("RGB").save(os.path.join(THEME, "background.png"))
    print("[out] theme/background.png 1920x1080 (карта мира + СССР)")
    for (w, h) in [(1366, 768), (1280, 720), (2560, 1440), (3840, 2160)]:
        r = final.convert("RGB").resize((w, h), Image.LANCZOS)
        r.save(os.path.join(THEME, f"background-{w}x{h}.png"))
        print(f"[out] theme/background-{w}x{h}.png")


# ---------------------------------------------------------------------------
# Иконки пунктов меню (40px) — звезда/шестерня и пр. в палитре темы
# ---------------------------------------------------------------------------

def build_icons():
    icons = os.path.join(THEME, "icons")
    os.makedirs(icons, exist_ok=True)

    def canvas(size=64):
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([2, 2, size - 3, size - 3], fill=DARKRED, outline=GOLD, width=3)
        return im, d

    S = 64
    # arch — буква A
    im, d = canvas()
    d.polygon([(32, 12), (48, 50), (40, 50), (32, 30), (24, 50), (16, 50)], fill=GOLD)
    im.save(os.path.join(icons, "arch.png"))
    # manjaro — три узла
    im, d = canvas()
    for x, y, r in [(24, 22, 7), (40, 22, 7), (32, 42, 7)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD, outline=RED, width=2)
    im.save(os.path.join(icons, "manjaro.png"))
    # star
    im, d = canvas()
    draw_star(d, 32, 32, 22, fill=GOLD, outline=DARKRED, width=2)
    im.save(os.path.join(icons, "star.png"))
    # gear
    im, d = canvas()
    for k in range(8):
        a = math.radians(k * 45)
        x = 32 + 24 * math.cos(a)
        y = 32 + 24 * math.sin(a)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=GOLD)
    d.ellipse([16, 16, 48, 48], fill=GOLD, outline=DARKRED, width=2)
    d.ellipse([26, 26, 38, 38], fill=DARKRED)
    im.save(os.path.join(icons, "gear.png"))
    # terminal
    im, d = canvas()
    d.text((14, 18), ">_", font=font(26), fill=GOLD)
    im.save(os.path.join(icons, "terminal.png"))
    # memtest / ram
    im, d = canvas()
    d.rectangle([14, 24, 50, 40], fill=GOLD, outline=DARKRED, width=2)
    for x in range(18, 48, 8):
        d.rectangle([x, 40, x + 4, 48], fill=GOLD)
    im.save(os.path.join(icons, "memtest.png"))
    im2 = im.copy()
    im2.save(os.path.join(icons, "ram.png"))
    # windows
    im, d = canvas()
    for (x, y) in [(16, 16), (34, 16), (16, 34), (34, 34)]:
        d.rectangle([x, y, x + 13, y + 13], fill=GOLD)
    im.save(os.path.join(icons, "windows.png"))
    # uefi/power
    im, d = canvas()
    d.arc([16, 16, 48, 48], start=-60, end=240, fill=GOLD, width=5)
    d.line([(32, 10), (32, 32)], fill=GOLD, width=5)
    im.save(os.path.join(icons, "uefi.png"))
    # settings — шестерня
    sim, sd = canvas()
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        x = 32 + 24 * math.cos(a)
        y = 32 + 24 * math.sin(a)
        sd.ellipse([x - 6, y - 6, x + 6, y + 6], fill=GOLD)
    sd.ellipse([16, 16, 48, 48], fill=GOLD, outline=DARKRED, width=2)
    sd.ellipse([26, 26, 38, 38], fill=DARKRED)
    sim.save(os.path.join(icons, "settings.png"))
    print("[out] theme/icons/*.png")


# ---------------------------------------------------------------------------

def main():
    download_sources()
    os.makedirs(PREV, exist_ok=True)
    emblem = build_emblem()
    build_leaders()
    build_banner(emblem)
    build_countdown(emblem)
    build_buttons()
    build_icons()
    build_background(emblem)
    print("\n[v2] Готово: карта мира + СССР, Маркс/Энгельс/Ленин/Сталин, Троцкий удалён.")


if __name__ == "__main__":
    main()
