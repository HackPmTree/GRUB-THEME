#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_mockup.py v2 — композитный предпросмотр темы GRUB «СССР» (1920x1080).

Точно эмулирует отрисовку theme.txt поверх background.png:
  * заголовок «Arch Linux / Manjaro» (англ.) с гербом;
  * меню ОСей с рамкой выделения и иконками;
  * РАБОЧАЯ панель кнопок НАСТРОЙКИ / ЗАГРУЗКА / ВЫКЛЮЧИТЬ (btn-*.png);
  * плашка таймера + полоса курантов @timeout;
  * подсказки по-русски.

Запуск:  python3 scripts/make_mockup.py
Выход:   theme/previews/mockup-1920x1080.png (+ .jpg), assets-contact-sheet.png
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

    # ---- +title -----------------------------------------------------------
    title = "Arch Linux / Manjaro"
    em = Image.open(os.path.join(TH, "icons", "emblem-64.png")).convert("RGBA")
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    tb = d.textbbox((0, 0), title, font=F(30))
    tw = tb[2] - tb[0]
    x0 = (W - (tw + em.size[0] + 18)) // 2
    y0 = int(H * 0.02) + 6
    d.text((x0 + em.size[0] + 18, y0 - 6), title, font=F(30), fill=(255, 215, 0),
           stroke_width=2, stroke_fill=(139, 0, 0))
    tmp.alpha_composite(em, (x0, y0 - 8))
    bg.alpha_composite(tmp)

    # ---- +menu_panel (left 5% top 30% w 46% h 44%) -----------------------
    ml = int(W * 0.05)
    mt = int(H * 0.30)
    mw = int(W * 0.46)
    mh = int(H * 0.44)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rectangle([ml, mt, ml + mw, mt + mh], fill=(0, 0, 0, 170),
                 outline=(139, 0, 0), width=3)
    items = [
        ("icons/arch.png",     "Arch Linux (Ядро Linux)"),
        ("icons/manjaro.png",  "Manjaro Linux (Ядро 6.6 LTS)"),
        ("icons/gear.png",     "Дополнительные параметры ядра"),
        ("icons/terminal.png", "Загрузка в текстовом режиме (console)"),
        ("icons/memtest.png",  "Проверка оперативной памяти (Memtest86+)"),
        ("icons/windows.png",  "Windows Boot Manager"),
    ]
    ih, sp, pad, iconw, ispace = 42, 6, 18, 40, 14
    mf = F(20)
    selimg = Image.open(os.path.join(TH, "selected_item.png")).convert("RGBA")
    y = mt + sp
    for i, (ic, txt) in enumerate(items):
        col = (255, 215, 0) if i == 0 else (255, 246, 205)
        if i == 0:
            fr = selimg.resize((mw - 2 * pad, ih), Image.LANCZOS)
            panel.paste(fr, (ml + pad, y), fr.split()[3])
        icon = Image.open(os.path.join(TH, ic)).convert("RGBA").resize((iconw, iconw), Image.LANCZOS)
        panel.paste(icon, (ml + pad + 2, y + (ih - iconw) // 2), icon)
        pd.text((ml + pad + iconw + ispace, y + 8), txt, font=mf, fill=col)
        y += ih + sp
    bg.alpha_composite(panel)

    # ---- панель РАБОЧИХ кнопок (справа) ----------------------------------
    btns = [("btn-settings", "пункт id=settings → терминал/правка grub.cfg"),
            ("btn-boot",     "submenu id=bootcfg → варианты загрузки"),
            ("btn-power",    "пункт id=poweroff → halt/reboot")]
    bx = W - int(W * 0.05) - 210
    by = mt + 10
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((bx, by - 34), "ПАНЕЛЬ УПРАВЛЕНИЯ", font=F(20), fill=(255, 215, 0),
            stroke_width=1, stroke_fill=(0, 0, 0))
    for name, note in btns:
        img = Image.open(os.path.join(TH, name + ".png")).convert("RGBA")
        layer.paste(img, (bx, by), img)
        ld.text((bx, by + 56), note, font=F(15, False), fill=(255, 246, 205))
        by += 52 + 26 + 10
    bg.alpha_composite(layer)

    # ---- +message / +timeout_style ---------------------------------------
    cf = Image.open(os.path.join(TH, "countdown_frame.png")).convert("RGBA")
    cx = W - int(W * 0.03) - cf.size[0]
    cy = int(H * 0.84)
    bg.paste(cf, (cx, cy), cf)
    dd = ImageDraw.Draw(bg)
    dd.text((cx + 150, cy + 52), "5 сек.", font=F(28), fill=(255, 215, 0),
            stroke_width=2, stroke_fill=(0, 0, 0))

    # ---- +progress_bar @timeout -------------------------------------------
    px, py, pw, ph = int(W * 0.20), int(H * 0.93), int(W * 0.60), 24
    bar = Image.open(os.path.join(TH, "progress_bar.png")).convert("RGBA").resize((pw, ph), Image.LANCZOS)
    hl = Image.open(os.path.join(TH, "progress_highlight.png")).convert("RGBA").resize((pw, ph), Image.LANCZOS)
    frac = 0.62
    bg.paste(bar, (px, py), bar)
    crop = hl.crop((0, 0, int(pw * frac), ph))
    bg.paste(crop, (px + pw - crop.size[0], py), crop)

    # ---- +label -----------------------------------------------------------
    hint = "↑↓ — выбор · Enter — запуск · e — правка · c — консоль · Esc — сброс"
    t2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(t2)
    hb = td.textbbox((0, 0), hint, font=F(18, False))
    td.text(((W - (hb[2] - hb[0])) // 2, int(H * 0.96)), hint, font=F(18, False),
            fill=(255, 246, 205))
    bg.alpha_composite(t2)

    out = bg.convert("RGB")
    os.makedirs(PV, exist_ok=True)
    out.save(os.path.join(PV, "mockup-1920x1080.png"))
    out.save(os.path.join(PV, "preview-1920x1080.jpg"), quality=90)
    print("mockup saved:", os.path.join(PV, "mockup-1920x1080.png"))

    # ---- контактный лист ассетов ------------------------------------------
    names = ["leader-marx.png", "leader-engels.png", "leader-lenin.png",
             "leader-stalin.png", "emblem.png", "banner.png",
             "countdown_frame.png", "selected_item.png", "slider_thumb.png",
             "btn-settings-sel.png"]
    cols = 5
    cell = 240
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 28)), (12, 4, 4))
    sd = ImageDraw.Draw(sheet)
    for idx, n in enumerate(names):
        p = os.path.join(TH, n)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        im.thumbnail((cell - 16, cell - 16), Image.LANCZOS)
        x = (idx % cols) * cell
        yy = (idx // cols) * (cell + 28)
        sheet.paste(im, (x + (cell - im.size[0]) // 2, yy + (cell - im.size[1]) // 2), im)
        sd.text((x + 8, yy + cell + 4), n, font=F(14, False), fill=(255, 215, 0))
    sheet.save(os.path.join(PV, "assets-contact-sheet.png"))
    print("contact sheet saved")


if __name__ == "__main__":
    main()
