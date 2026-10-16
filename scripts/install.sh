#!/usr/bin/env bash
# ============================================================================
# install.sh — установка темы GRUB «СССР» v2 (Arch Linux / Manjaro)
#   1. копирует тему в /boot/grub/themes/sssr
#   2. включает её в /etc/default/grub (GRUB_THEME=...)
#   3. добавляет РАБОЧИЕ кнопки-пункты (Настройки/Загрузка/Выключить/Перезагрузить)
#      через /etc/grub.d/40_custom
#   4. перегенерирует grub.cfg (grub-mkconfig или update-grub на Manjaro)
# Использование:  sudo ./install.sh
# ============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
THEME_SRC="$HERE/theme"
THEME_DIR="/boot/grub/themes/sssr"
DEFAULT_GRUB="/etc/default/grub"
CUSTOM="/etc/grub.d/40_custom"

if [[ $EUID -ne 0 ]]; then
    echo "Запустите с правами root: sudo $0" >&2
    exit 1
fi

echo "==> 1/4 Копирование темы в $THEME_DIR"
mkdir -p "$THEME_DIR"
cp -a "$THEME_SRC"/. "$THEME_DIR"/
chmod -R a+rX "$THEME_DIR"

echo "==> 2/4 Включение темы в $DEFAULT_GRUB"
cp -n "$DEFAULT_GRUB" "$DEFAULT_GRUB.bak.$(date +%s)" || true
# закомментировать старые GRUB_THEME и дописать наш
sed -i 's/^GRUB_THEME=/#GRUB_THEME=/' "$DEFAULT_GRUB"
grep -q '^GRUB_THEME=' "$DEFAULT_GRUB" || echo 'GRUB_THEME=/boot/grub/themes/sssr/theme.txt' >> "$DEFAULT_GRUB"
# графический режим + кириллица в терминале GRUB
grep -q '^GRUB_GFXMODE=' "$DEFAULT_GRUB" || echo 'GRUB_GFXMODE=1920x1080,1366x768,auto' >> "$DEFAULT_GRUB"
grep -q '^GRUB_TIMEOUT_STYLE=' "$DEFAULT_GRUB" || echo 'GRUB_TIMEOUT_STYLE=countdown' >> "$DEFAULT_GRUB"

echo "==> 3/4 Рабочие кнопки-пункты в $CUSTOM"
if ! grep -q 'sssr-settings' "$CUSTOM"; then
    cp -n "$CUSTOM" "$CUSTOM.bak.$(date +%s)" || true
    cat >> "$CUSTOM" <<'CFG'

# --- ТЕМА «СССР»: панель управления (рабочие пункты меню) ---------------
menuentry 'НАСТРОЙКИ — консоль GRUB (правка)' --id=sssr-settings --class settings {
    echo 'Открыта консоль GRUB. Команда configfile перезагрузит конфиг.'
    terminal_input console
    terminal_output console
}
submenu 'ЗАГРУЗКА — дополнительные варианты' --id=sssr-bootcfg --class gear {
    menuentry 'Арх Линукс (загрузка по умолчанию)' --id=sssr-arch-default {
        configfile "${prefix}/grub.cfg"
    }
    menuentry 'Проверка оперативной памяти (Memtest86+)' --class memtest {
        if [ "${grub_platform}" = pc ]; then chainloader +1; fi
    }
}
menuentry 'ВЫКЛЮЧИТЬ компьютер' --id=sssr-poweroff --class power {
        halt
}
menuentry 'ПЕРЕЗАГРУЗИТЬ компьютер' --id=sssr-reboot --class reboot {
        reboot
}
CFG
    chmod +x "$CUSTOM"
    echo "    добавлены пункты: НАСТРОЙКИ / ЗАГРУЗКА / ВЫКЛЮЧИТЬ / ПЕРЕЗАГРУЗИТЬ"
else
    echo "    уже установлены, пропускаю"
fi

echo "==> 4/4 Обновление конфигурации GRUB"
if command -v update-grub >/dev/null 2>&1; then
    update-grub                       # Manjaro / Ubuntu-подобные
elif command -v grub-mkconfig >/dev/null 2>&1; then
    grub-mkconfig -o /boot/grub/grub.cfg   # Arch (BIOS и UEFI с grub-install)
else
    echo "Не найден ни update-grub, ни grub-mkconfig — установите пакет grub." >&2
    exit 1
fi

echo
echo "Готово. Перезагрузитесь: systemctl reboot"
echo "Если тема не появилась: проверьте GRUB_ENABLE_CRYPTODISK, gfxterm и"
echo "вывод 'Searched for themes... / Found theme' в логе выше."
