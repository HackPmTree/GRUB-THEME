#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mk_pf2.py — генератор шрифтов .pf2 для GRUB 2.01+ (формат Grub Dejavu Sans).

Позволяет собрать дежурный шрифт темы (включая кириллицу) БЕЗ наличия
grub-mkfont в системе. Использует:
  * Pillow  (растеризация глифов из TTF)
  * fontTools (чтение метрик шрифта; опционально)

Формат PF2 (см. grub-core/font.c, header "GPFT"):
  magic "GPFT" | version(4B BE)=0x02 | size of struct(4B BE)
  family(string) + style(string)
  ps_name, ttf_path, bitmap_type, ascender, descender, maxwidth,
  points, height, flags, num_chars(uint32 BE), затем записи char:
    code(4B BE) | is_outline(1B)=0 | bitmap_size(2B BE) | W(1B) H(1B) Xoff(1B signed) Yoff(1B signed)
    затем bitmap ((W+7)//8)*H байт, инверсия: 1 = «краска» (в GRUB бит 0 = пиксель? — нет:
    в GRUB 1-битном бэмапе установленный бит = ПРОЗРАЧНОСТЬ отсутствует...
    Фактически grub-mkfont пишет антиалиас через глубину цвета; для 1bpp
    используется mask, где 1 = пиксель текста.)

Запуск:
  python3 mk_pf2.py --source /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
      --size 16 --output theme/fonts/dejavu-sans-16.pf2
Дополнительно: --size 18 ... --size 24 и т.п.
"""

import argparse
import os
import struct
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Нужен Pillow: pip install pillow")

HAVE_FT = True
try:
    from fontTools.ttLib import TTFont
except ImportError:
    HAVE_FT = False


# Набор символов: латиница + кириллица + цифровая/знаковая необходимость
BASE_CHARS = (
    "".join(chr(c) for c in range(0x20, 0x7F))          # ASCII печатный
    + "".join(chr(c) for c in range(0xA0, 0x130))        # латиница-расширение, знак °
    + "".join(chr(c) for c in range(0x400, 0x450))       # кириллица
    + "№–—‘’“”…•·«»€™†‡„"
    + "⌅⏎"  # служебные (если есть в шрифте)
)


def render_glyph(pil_font, ch, ascent_px, descent_px):
    """Возвращает (w, h, xoff, yoff, bitmap_bytes) для одного символа (1bpp)."""
    pad = 4
    probe = Image.new("L", (10, 10), 0)
    d = ImageDraw.Draw(probe)
    bbox = d.textbbox((0, 0), ch, font=pil_font)
    if bbox[2] - bbox[0] <= 0 or bbox[3] - bbox[1] <= 0:
        return None
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    img = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    dd = ImageDraw.Draw(img)
    dd.text((pad - bbox[0], pad - bbox[1]), ch, font=pil_font, fill=255)
    # порог 1bpp: half-tone по яркости
    bw = (img.width + 7) // 8
    bits = bytearray(bw * img.height)
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y] >= 128:
                bits[y * bw + (x >> 3)] |= 0x80 >> (x & 7)
    xoff = bbox[0] - pad
    yoff = bbox[1] - pad
    return img.width, img.height, xoff, yoff, bytes(bits)


def build_pf2(ttf_path, size, out_path, family="DejaVu Sans", style="Regular"):
    pil_font = ImageFont.truetype(ttf_path, size)

    units_per_em = 2048
    ascent_u, descent_u = 1900, -500
    if HAVE_FT:
        try:
            tt = TTFont(ttf_path)
            cmap = tt.getBestCmap()
            upm = tt["head"].unitsPerEm
            hhea = tt["hhea"]
            os2 = tt["OS/2"] if "OS/2" in tt else None
            ascent_u = int(hhea.ascent if os2 is None else max(hhea.ascent, os2.sTypoAscender))
            descent_u = int(hhea.descent if os2 is None else min(hhea.descent, os2.sTypoDescender))
            scale = size / upm
            ascent_px = round(ascent_u * scale)
            descent_px = round(abs(descent_u) * scale)
        except Exception:
            cmap = {}
            ascent_px = round(size * 0.93)
            descent_px = size - ascent_px
    else:
        cmap = {}
        ascent_px = round(size * 0.93)
        descent_px = size - ascent_px

    chars = []
    for ch in BASE_CHARS:
        cp = ord(ch)
        if HAVE_FT and cmap and cp not in cmap:
            continue
        g = render_glyph(pil_font, ch, ascent_px, descent_px)
        if g is None:
            continue
        chars.append((cp,) + g)

    # --- сборка PF2 (хостовый формат GRUB: little-endian, см. grub-core/font.c) ---
    # Хелпер записи ASCIIZ с выравниванием на 4 байта (как ALIGN4 в GRUB)
    def wr_str(buf: bytearray, text: str):
        raw = text.encode("ascii", "replace") + b"\0"
        buf += raw
        while len(buf) % 4:
            buf += b"\0"

    def align4(n):
        return (n + 3) & ~3

    family_b = family.encode("ascii", "replace")
    style_b = style.encode("ascii", "replace")
    ps_name = f"{family} {style} {size}"
    ps_b = ps_name.encode("ascii", "replace")
    ttf_b = os.path.abspath(ttf_path).encode("utf-8", "surrogateescape")

    str_bytes = (len(family_b) + 1 + (-(len(family_b) + 1)) % 4
                 + len(style_b) + 1 + (-(len(style_b) + 1)) % 4
                 + len(ps_b) + 1 + (-(len(ps_b) + 1)) % 4
                 + len(ttf_b) + 1 + (-(len(ttf_b) + 1)) % 4)
    header_size = align4(4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4) + str_bytes
    # magic(4)+version(4)+size(4)+bitmap_type(4)+maxwidth(4)+ascender(4)+descender(4)
    # +height(4)+flags(4)+num_chars(4)+points(4)+family_off? -- нет: layout font.c:
    #   magic, version, size, family[], style[], ps[], path[], bitmap_type,
    #   ascender, descender, maxwidth, points, height, flags, num_chars
    # Вычислим точно по полю file_offset из grub_font_header:
    # struct {magic u32; version u32; size u32;} затем строки, затем:
    # bitmap_type u32, ascender i32, descender i32, maxwidth u32,
    # points u32, height u32, flags u32, num_chars u32
    fixed_after_strings = 4 * 8
    header_size = align4(4 + 4 + 4) + str_bytes + fixed_after_strings

    body = bytearray()
    body += b"GPFT"
    body += struct.pack("<I", 2)              # версия
    body += struct.pack("<I", header_size)    # размер заголовка (включая строки)
    wr_str(body, family)
    wr_str(body, style)
    wr_str(body, ps_name)
    wr_str(body, os.path.abspath(ttf_path))
    body += struct.pack("<I", 1)              # bitmap type: 1 = однобитный
    body += struct.pack("<i", ascent_px)      # ascender
    body += struct.pack("<i", -descent_px)    # descender (отрицательный)
    maxw = max((c[1] for c in chars), default=size)
    body += struct.pack("<I", maxw)           # maxwidth
    body += struct.pack("<I", size)           # points
    body += struct.pack("<I", ascent_px + descent_px)  # height
    body += struct.pack("<I", 0)              # flags
    body += struct.pack("<I", len(chars))     # num chars
    assert len(body) == header_size, (len(body), header_size)
    for cp, w, h, xoff, yoff, bm in chars:
        # code u32 | is_outline u8 | bitmap_size u16 | W u8 H u8 Xoff i8 Yoff i8
        body += struct.pack("<IBHBBbb", cp, 0, len(bm), w, h, xoff, yoff)
        body += bm

    with open(out_path, "wb") as f:
        f.write(body)
    print(f"[OK] {out_path}: {len(chars)} глифов, {size}px, "
          f"asc={ascent_px} desc={descent_px}, файл {os.path.getsize(out_path)} байт")


def main():
    ap = argparse.ArgumentParser(description="Генератор .pf2 шрифтов для GRUB")
    ap.add_argument("--source", required=True, help="TTF-шрифт с кириллицей")
    ap.add_argument("--size", type=int, action="append", default=None,
                    help="Кегль (можно несколько: --size 16 --size 18 …)")
    ap.add_argument("--family", default="DejaVu Sans")
    ap.add_argument("--style", default="Regular")
    ap.add_argument("--outdir", default="theme/fonts")
    args = ap.parse_args()

    sizes = args.size or [16]
    os.makedirs(args.outdir, exist_ok=True)
    fam_slug = args.family.lower().replace(" ", "-")
    for s in sizes:
        out = os.path.join(args.outdir, f"{fam_slug}-{s}.pf2")
        build_pf2(args.source, s, out, args.family, args.style)


if __name__ == "__main__":
    main()
