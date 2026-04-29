import requests
import re
import time
from datetime import datetime

def get_reviews_count(url: str):# -> Optional[int]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return None

    # Ищем паттерн: "Отзывы" и рядом число
    patterns = [
        # Вариант 1: Отзывы\n\n91
        r'Отзывы[^>]*>\s*(\d+)',

        # Вариант 2: "91 отзыв" в тексте
        r'(\d+)\s+отзыв',

        # Вариант 3: После слова Отзывы идёт число в отдельном блоке
        r'Отзывы.*?(\d+)\s*(?:отзыв|отзыва|отзывов)',

        # Вариант 4: Конкретно из вашего скриншота (после "### 91 отзыв")
        r'###\s*(\d+)\s+отзыв',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        if matches:
            # Берем первое число, которое НЕ 4 (если это новости)
            for match in matches:
                num = int(match)
                if num != 4:  # Исключаем кол-во новостей
                    return num

    return None


# ========== НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ) ==========
TELEGRAM_BOT_TOKEN = "8662736063:AAG2w8pwfc-BjQdVqgOUsAnSSTURQYZKFGY"  # Токен от @BotFather
TELEGRAM_CHAT_ID = "5186084249"  # ID от @userinfobot
YANDEX_MAPS_URL = "https://yandex.ru/maps/?ll=43.617771%2C56.304468&mode=poi&poi%5Bpoint%5D=43.617708%2C56.304723&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D238425370862&tab=reviews&z=18"
CHECK_INTERVAL_MINUTES = 30  # Проверка каждые 30 минут


# =================================================

def get_reviews_count_v2(url):
    """Получает количество отзывов"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text

        # Паттерны поиска числа отзывов
        patterns = [
            r'Отзывы[^>]*>\s*(\d+)',
            r'(\d+)\s+отзыв',
            r'Отзывы.*?(\d+)\s*(?:отзыв|отзыва|отзывов)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if matches:
                for match in matches:
                    num = int(match)
                    if num != 4:  # исключаем новости
                        return num
        return None
    except Exception as e:
        print(f"[{datetime.now()}] Ошибка: {e}")
        return None


def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        return response.ok
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False


# Отправляем приветствие при запуске
send_telegram_message("✅ Бот запущен на Render.com! Начинаю отслеживание отзывов.")

last_count = None
print("Бот запущен, отслеживаю отзывы...")

while True:
    current_count = get_reviews_count(YANDEX_MAPS_URL)

    if current_count is not None:
        print(f"[{datetime.now()}] Текущее количество: {current_count}")

        if last_count is None:
            last_count = current_count
            send_telegram_message(f"📋 Начальное количество: <b>{current_count}</b> отзывов\n\nОтслеживание запущено! ✅")

        elif current_count > last_count:
            diff = current_count - last_count
            message = f"🆕 <b>НОВЫЙ ОТЗЫВ!</b>\n\n"
            message += f"📊 Было: {last_count}\n"
            message += f"📈 Стало: <b>{current_count}</b>\n"
            message += f"➕ Прибавилось: +{diff}\n\n"
            message += f"🔗 <a href='{YANDEX_MAPS_URL}'>Посмотреть отзывы</a>"
            send_telegram_message(message)
            last_count = current_count

        elif current_count < last_count:
            diff = last_count - current_count
            message = f"⚠️ <b>Количество отзывов уменьшилось</b>\n\n"
            message += f"📊 Было: {last_count}\n"
            message += f"📉 Стало: {current_count}\n"
            message += f"➖ Убавилось: -{diff}"
            send_telegram_message(message)
            last_count = current_count

    time.sleep(CHECK_INTERVAL_MINUTES * 60)
