import os
import time
import re
import threading
from datetime import datetime
from collections import defaultdict
from pathlib import Path

import requests

# ==============================================================================
# КОНФИГУРАЦИЯ — замени на свои значения
# ==============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
LOGS_DIR = "/var/log/remote"  # папка где adminhost хранит логи с воркеров
POLL_INTERVAL = 10  # секунд между проверками новых записей в логах
# ==============================================================================

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN и CHAT_ID не заданы — проверь /etc/tgbot.env")

# Хранит позицию чтения для каждого лог-файла чтобы не перечитывать старое
file_positions = {}

# Статистика по всем логам
stats = defaultdict(lambda: {
    "connections": 0,
    "login_attempts": 0,
    "commands": 0,
    "unique_ips": set()
})


def send_message(text: str, parse_mode: str = "HTML"):
    try:
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": parse_mode
        }, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")


def get_updates(offset: int = None):
    try:
        params = {"timeout": 30, "offset": offset}
        response = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
        return response.json().get("result", [])
    except Exception:
        return []


def find_log_files() -> list:
    log_files = []
    logs_path = Path(LOGS_DIR)

    if not logs_path.exists():
        return log_files

    # Структура: /var/log/remote/<hostname>/<logfile>.log
    for host_dir in logs_path.iterdir():
        if host_dir.is_dir():
            for log_file in host_dir.glob("*.log"):
                log_files.append(log_file)

    return log_files


def parse_log_line(line: str, hostname: str) -> dict | None:
    # Формат строки лога: [2024-01-01 12:00:00] {'action': ..., 'client_ip': ...}
    match = re.match(r"\[(.+?)\] (.+)", line.strip())
    if not match:
        return None

    timestamp_str, data_str = match.groups()

    try:
        # Парсим словарь из строки
        data = eval(data_str)  # логи пишутся как dict.__str__()
        data["hostname"] = hostname
        data["timestamp"] = timestamp_str
        return data
    except Exception:
        return None


def format_notification(entry: dict) -> str | None:
    action = entry.get("action")
    host = entry.get("hostname", "unknown")
    ip = entry.get("client_ip", "unknown")
    ts = entry.get("timestamp", "")

    if action == "connection":
        return (
            f"🔌 <b>Новое подключение</b>\n"
            f"🖥 Хост: <code>{host}</code>\n"
            f"📍 IP: <code>{ip}</code>\n"
            f"🕐 Время: {ts}"
        )
    elif action == "login_attempt":
        username = entry.get("username", "?")
        password = entry.get("password", "?")
        return (
            f"🔑 <b>Попытка входа</b>\n"
            f"🖥 Хост: <code>{host}</code>\n"
            f"📍 IP: <code>{ip}</code>\n"
            f"👤 Логин: <code>{username}</code>\n"
            f"🔐 Пароль: <code>{password}</code>\n"
            f"🕐 Время: {ts}"
        )
    elif action == "command":
        command = entry.get("command", "?")
        return (
            f"💻 <b>Введена команда</b>\n"
            f"🖥 Хост: <code>{host}</code>\n"
            f"📍 IP: <code>{ip}</code>\n"
            f"$ <code>{command}</code>\n"
            f"🕐 Время: {ts}"
        )

    return None


def update_stats(entry: dict):
    host = entry.get("hostname", "unknown")
    action = entry.get("action")
    ip = entry.get("client_ip")

    if action == "connection":
        stats[host]["connections"] += 1
        if ip:
            stats[host]["unique_ips"].add(ip)
    elif action == "login_attempt":
        stats[host]["login_attempts"] += 1
    elif action in ("command", "command_exec"):
        stats[host]["commands"] += 1


def handle_stats_command():
    if not stats:
        send_message("📊 Статистика пока пуста — нет данных из логов.")
        return

    text = "📊 <b>Статистика по хостам:</b>\n\n"
    for host, data in stats.items():
        text += (
            f"🖥 <b>{host}</b>\n"
            f"  🔌 Подключений: {data['connections']}\n"
            f"  🔑 Попыток входа: {data['login_attempts']}\n"
            f"  💻 Команд: {data['commands']}\n"
            f"  📍 Уникальных IP: {len(data['unique_ips'])}\n\n"
        )

    send_message(text)


def handle_logs_command():
    log_files = find_log_files()

    if not log_files:
        send_message("📁 Лог-файлы не найдены.")
        return

    text = "📁 <b>Найденные лог-файлы:</b>\n\n"
    for log_file in log_files:
        size = log_file.stat().st_size
        modified = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        text += f"📄 <code>{log_file}</code>\n   Размер: {size} байт | Обновлён: {modified}\n\n"

    send_message(text)


def handle_ips_command():
    if not stats:
        send_message("📍 Нет данных об IP-адресах.")
        return

    text = "📍 <b>Уникальные IP-адреса:</b>\n\n"
    for host, data in stats.items():
        if data["unique_ips"]:
            ips = "\n".join(f"  • <code>{ip}</code>" for ip in sorted(data["unique_ips"]))
            text += f"🖥 <b>{host}</b>:\n{ips}\n\n"

    send_message(text)


def handle_help_command():
    send_message(
        "🤖 <b>Доступные команды:</b>\n\n"
        "/stats — статистика по всем хостам\n"
        "/logs — список лог-файлов\n"
        "/ips — уникальные IP-адреса атакующих\n"
        "/help — это сообщение"
    )


def watch_logs():
    print(f"[*] Слежение за логами в {LOGS_DIR}")

    while True:
        log_files = find_log_files()

        for log_file in log_files:
            hostname = log_file.parent.name  # имя папки = имя хоста
            path_str = str(log_file)

            try:
                with open(log_file, "r", errors="replace") as f:
                    # Если файл новый — читаем с конца чтобы не слать старые записи
                    if path_str not in file_positions:
                        f.seek(0, 2)
                        file_positions[path_str] = f.tell()
                        continue

                    f.seek(file_positions[path_str])
                    new_lines = f.readlines()
                    file_positions[path_str] = f.tell()

                for line in new_lines:
                    if not line.strip():
                        continue

                    entry = parse_log_line(line, hostname)
                    if not entry:
                        continue

                    update_stats(entry)

                    notification = format_notification(entry)
                    if notification:
                        send_message(notification)

            except Exception as e:
                print(f"Ошибка чтения {log_file}: {e}")

        time.sleep(POLL_INTERVAL)


def poll_commands():
    print("[*] Ожидание команд от пользователя...")
    offset = None

    while True:
        updates = get_updates(offset)

        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")

            # Отвечаем только своему chat_id
            if str(chat_id) != str(CHAT_ID):
                continue

            if text == "/stats":
                handle_stats_command()
            elif text == "/logs":
                handle_logs_command()
            elif text == "/ips":
                handle_ips_command()
            elif text in ("/help", "/start"):
                handle_help_command()


def main():
    send_message(
        "🚀 <b>Honeypot Monitor запущен</b>\n"
        f"📁 Слежу за логами в: <code>{LOGS_DIR}</code>\n"
        "Напиши /help для списка команд."
    )

    # Запускаем слежение за логами в отдельном потоке
    log_thread = threading.Thread(target=watch_logs, daemon=True)
    log_thread.start()

    # Основной поток — опрос команд от пользователя
    poll_commands()


if __name__ == "__main__":
    main()