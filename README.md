# GRUB-тема «СССР» — красно-золотая, Arch Linux / Manjaro

Тема оформления загрузчика GRUB в эстетике СССР 1930–1950-х: конструктивизм и
социалистический реализм. Палитра: **#CC0000** красный · **#FFD700** золотой ·
**#8B0000** тёмно-красный · **#000000** чёрный. Все надписи — на русском языке.

## Что нового (v2)

Вместо нарисованных заглушек тема использует **реальные фотографии и официальный герб**:

| Элемент | Источник | Файл в теме |
|---|---|---|
| Портрет В. И. Ленина | chaltlib.ru (`assets/sources/lenin.jpg`) | `theme/leader-lenin.png` |
| Портрет И. В. Сталина | topwar.ru (`assets/sources/stalin.webp`) | `theme/leader-stalin.png` |
| Герб СССР (1956–1991) | Wikimedia Commons (общественное достояние) | `theme/emblem.png`, `theme/icons/emblem-64.png` |
| Л. Д. Троцкий | фото не предоставлено — стилизованная заглушка | `theme/leader-trotsky.png` |

Фотографии обработаны в духе агитплаката: высокая контрастная дуотонная печать
(тёмно-красные тени → золото), зерно, виньетка, золотые медальоны с звездами.
Герб вставлен настоящий (водяной знак на фоне + иконка заголовка + плашка таймера).

### Как заменить портреты своими фото

```bash
# положите свои файлы в assets/sources/ под теми же именами:
cp moje_lenin.jpg   assets/sources/lenin.jpg
cp moje_stalin.webp assets/sources/stalin.webp
cp moje_trotsky.jpg assets/sources/trotsky.jpg   # трогатель тоже станет фото
python3 scripts/photomontage.py                  # пересобрать все ассеты
python3 scripts/make_mockup.py                   # обновить предпросмотр
```

## Структура

```
theme/
├── theme.txt                 # конфигурация темы (GRUB 2.06+)
├── background.png            # 1920x1080: карта СССР + фото + герб
├── background-{1366x768,1280x720,2560x1440,3840x2160}.png
├── selected_item.png         # рамка выделения (знамя + звезда)
├── slider_thumb.png          # ползунок списка (золотая звезда)
├── slider_bg.png             # фон полосы прокрутки
├── progress_bar.png          # пластина таймера
├── progress_highlight.png    # золотое заполнение курантов
├── countdown_frame.png       # плашка обратного отсчёта (герб + лавр)
├── emblem.png                # ГОСГЕРБ СССР (файл с Wikimedia)
├── banner.png                # знамённый баннер «Пролетарии всех стран…»
├── leader-lenin.png          # фото Ленина (дуотон-медальон)
├── leader-stalin.png         # фото Сталина (дуотон-медальон)
├── leader-trotsky.png        # заглушка (см. выше — как заменить)
├── icons/                    # иконки пунктов меню (arch, manjaro, star…)
│   └── emblem-64.png         # 64px версия реального герба
├── fonts/
│   ├── dejavu-sans-16.pf2    # кириллица, собрано grub-mkfont
│   └── dejavu-sans-18.pf2
└── previews/
    ├── mockup-1920x1080.png      # композитный предпросмотр всей раскладки
    ├── preview-1920x1080.jpg     # то же в JPG
    ├── assets-contact-sheet.png  # коллаж ассетов (фон, герб, портреты…)
    ├── live-grub-01.png          # скриншот реального GRUB в QEMU (текстовый режим)
    └── live-text-mode.png        # консоль GRUB с кириллицей
scripts/
├── photomontage.py           # сборка ассетов из фото + герба (главный скрипт)
├── generate_assets.py        # генерация рамок/иконок/полос программно
├── make_mockup.py            # предпросмотр по координатам theme.txt
└── mk_pf2.py                 # сборка .pf2 без grub-mkfont
assets/sources/               # исходники фото (lenin.jpg, stalin.webp, emblem-1280.png)
```

## Установка

```bash
# 1. Скопировать тему
sudo mkdir -p /boot/grub/themes
sudo cp -r theme /boot/grub/themes/sssr

# 2. Подключить в /etc/default/grub
#    GRUB_THEME=/boot/grub/themes/sssr/theme.txt
sudo sed -i 's|^#\?GRUB_THEME=.*|GRUB_THEME=/boot/grub/themes/sssr/theme.txt|' /etc/default/grub

# 3. Обновить конфиг (выберите свою команду):
sudo grub-mkconfig -o /boot/grub/grub.cfg        # Arch Linux
sudo update-grub                                 # Manjaro / Ubuntu-подобные

# 4. Перезагрузиться
reboot
```

Проверка синтаксиса до установки: `grub-script-check theme/theme.txt`

## Как посмотреть результат БЕЗ перезагрузки

**Способ 1 — готовые превью:** откройте `theme/previews/mockup-1920x1080.png`
(полная имитация раскладки) и `assets-contact-sheet.png` (ассеты).

**Способ 2 — тестовый GRUB в QEMU:**
```bash
grub-mkimage -O x86_64-efi -o /tmp/grub-efi.bin -p /EFI/BOOT \
  normal configfile part_gpt part_msdos fat ext2 all_video efi_gop efi_uga font gfxterm
mkdir -p /tmp/esp/EFI/BOOT && cp /tmp/grub-efi.bin /tmp/esp/EFI/BOOT/BOOTX64.EFI
cp theme/theme.txt /tmp/esp/ ; cp -r theme/fonts /tmp/esp/ ; cp theme/*.png /tmp/esp/ ; cp -r theme/icons /tmp/esp/
cat > /tmp/esp/grub.cfg <<CFG
set timeout=8
set default=0
search --no-floppy --fs-uuid --set=root <UUID раздела ESP>
load_font /fonts/dejavu-sans-16.pf2
terminal_output gfxterm
set theme=/theme.txt
export theme
menuentry 'Арх Линукс (Ядро Linux)' { linux /vmlinuz }
menuentry 'Манжаро Линукс (Ядро 6.6 LTS)' { linux /vmlinuz }
CFG
mkfs.fat -F32 -n ESP /tmp/esp.img && mcopy -s -i /tmp/esp.img /tmp/esp/* ::/
qemu-system-x86_64 -bios /usr/share/OVMF/OVMF_CODE.fd -drive file=/tmp/esp.img,format=raw \
  -display gtk   # или -vga std для графического режима; Ctrl+Alt+T — консоль
```
⚠️ В эмуляции QEMU (-vga std) графический режим часто недоступен — там будет
только текст (см. `live-grub-01.png`). На реальном железе с UEFI тема рисуется полностью.

**Способ 3 — быстрая проверка фона:** просто откройте `theme/background.png`.

## Шрифты (.pf2) с кириллицей

Рекомендуемые инструменты:
- `grub-mkfont` (пакет `grub` / `grub-tools`) — официальный:
  ```bash
  sudo grub-mkfont -o theme/fonts/dejavu-sans-16.pf2 --size=16 \
      /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
  ```
- **GrubCustomizer** / **Grub2 Themes Manager** (AUR) — GUI-редакторы тем;
- `mk_pf2.py` — чистый Python, если нет grub-mkfont.

Оба шрифта в теме уже содержат полный набор кириллицы (проверено).

## Лицензии исходников

- Герб СССР: Wikimedia Commons, public domain (PD-exempt, госсимвол).
- Фото Ленина/Сталина: предоставлены пользователем; при публичном распространении
  проверьте лицензию источника. Тема распространяется под GPL-3.0 (как и GRUB).
