#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_mockup.py — композитный предпросмотр темы GRUB «СССР» (1920x1080).

Эмулирует отрисовку theme.txt поверх background.png (заголовок, меню с
рамкой выделения и иконками, плашка таймера, полоса @timeout, подсказки)
и сохраняет PNG/JPG в theme/previews/. Это НЕ скриншот реального GRUB,
а точная имитация раскладки по координатам из theme.txt.

Запуск:  python3 scripts/make_mockup.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TH = os.path.join(ROOT, "theme")
PV = os.path.join(TH, "previews")
W, H = 1920, 1080


def F(sz, bold=True):
    p = f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf"
    return ImageFont.truetype(p, sz)


def main():
    bg = Image.open(os.path.join(TH, "background.png")).convert("RGBA")

    # +title: align=center top=2% height=48, icons_on=emblem-64, color #FFD700
    title = "Arch Linux / Манжаро · Власть Советам!"
    em = Image.open(os.path.join(TH, "icons", "emblem-64.png")).convert("RGBA")
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    tb = d.textbbox((0, 0), title, font=F(30)); tw = tb[2] - tb[0]
    x0 = (W - (tw + em.size[0] + 18)) // 2; y0 = int(H * 0.02) + 6
    d.text((x0 + em.size[0] + 18, y0 - 6), title, font=F(30), fill=(255, 215, 0),
           stroke_width=2, stroke_fill=(139, 0, 0))
    tmp.alpha_composite(em, (x0, y0 - 8)); bg.alpha_composite(tmp)

    # +menu_panel: left 5% top 34% width 46% height 46%, bg #000000AA border #8B0000
    ml = int(W * 0.05); mt = int(H * 0.34); mw = int(W * 0.46); mh = int(H * 0.46)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(panel)
    pd.rectangle([ml, mt, ml + mw, mt + mh], fill=(0, 0, 0, 170), outline=(139, 0, 0), width=3)
    items = [("icons/arch.png", "Arch Linux (Ядро Linux)"),
             ("icons/manjaro.png", "Манжаро Линукс (Ядро 6.6 LTS)"),
             ("icons/gear.png", "Дополнительные параметры ядра"),
             ("icons/terminal.png", "Загрузка в текстовом режиме (console)"),
             ("icons/memtest.png", "Проверка оперативной памяти (Memtest86+)")]
    ih, sp, pad, iconw, ispace = 42, 6, 18, 40, 14
    mf = F(20)
    selimg = Image.open(os.path.join(TH, "selected_item.png")).convert("RGBA")
    y = mt + sp
    for i, (ic, txt) in enumerate(items):
        col = (255, 215, 0) if i == 0 else (255, 246, 205)   # selected_color / color
        if i == 0:
            fr = selimg.resize((mw - 2 * pad, ih), Image.LANCZOS)
            panel.paste(fr, (ml + pad, y), fr.split()[3])
        icon = Image.open(os.path.join(TH, ic)).convert("RGBA").resize((iconw, iconw), Image.LANCZOS)
        panel.paste(icon, (ml + pad + 2, y + (ih - iconw) // 2), icon)
        pd.text((ml + pad + iconw + ispace, y + 8), txt, font=mf, fill=col)
        y += ih + sp
    em2 = Image.open(os.path.join(TH, "icons", "emblem-64.png")).convert("RGBA").resize((48, 48), Image.LANCZOS)
    panel.paste(em2, (ml + pad, y + 10), em2)
    pd.text((ml + pad + 60, y + 18), "Государственный герб СССР · 1922–1991",
            font=F(18, False), fill=(255, 215, 0))
    bg.alpha_composite(panel)

    # +message / +timeout_style: bottom_right top=84% right=3% 280x120
    cf = Image.open(os.path.join(TH, "countdown_frame.png")).convert("RGBA")
    cx = W - int(W * 0.03) - cf.size[0]; cy = int(H * 0.84)
    bg.paste(cf, (cx, cy), cf)
    dd = ImageDraw.Draw(bg)
    dd.text((cx + 150, cy + 52), "5 сек.", font=F(28), fill=(255, 215, 0),
            stroke_width=2, stroke_fill=(0, 0, 0))

    # +progress_bar id=@timeout: left 20% top 94% width 60% height 24
    px, py, pw, ph = int(W * 0.20), int(H * 0.94), int(W * 0.60), 24
    bar = Image.open(os.path.join(TH, "progress_bar.png")).convert("RGBA").resize((pw, ph), Image.LANCZOS)
    hl = Image.open(os.path.join(TH, "progress_highlight.png")).convert("RGBA").resize((pw, ph), Image.LANCZOS)
    frac = 0.62
    bg.paste(bar, (px, py), bar)
    crop = hl.crop((0, 0, int(pw * frac), ph))
    bg.paste(crop, (px + pw - crop.size[0], py), crop)   # заполнение справа налево

    # +label (подсказки): bottom_center top=96%
    hint = "↑↓ — выбор · Enter — запуск · e — правка · c — консоль · Esc — сброс"
    t2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(t2)
    hb = td.textbbox((0, 0), hint, font=F(18, False))
    td.text(((W - (hb[2] - hb[0])) // 2, int(H * 0.96)), hint, font=F(18, False), fill=(255, 246, 205))
    bg.alpha_composite(t2)

    out = bg.convert("RGB")
    os.makedirs(PV, exist_ok=True)
    out.save(os.path.join(PV, "mockup-1920x1080.png"))
    out.save(os.path.join(PV, "preview-1920x1080.jpg"), quality=90)
    print("mockup saved:", os.path.join(PV, "mockup-1920x1080.png"))


if __name__ == "__main__":
    main()
