import os
import requests
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@sochigladisbot")

def send_to_telegram(message: str, name: str, phone: str, procedure: str = None):
    """
    Отправляет полную заявку в Telegram.
    """
    try:
        print(f"\n📨 ОТПРАВКА ЗАЯВКИ В TELEGRAM")
        print(f"   👤 Имя: {name}")
        print(f"   📞 Телефон: {phone}")
        if procedure:
            print(f"   💉 Процедура: {procedure}")
        
        if not TELEGRAM_CHAT_ID:
            print("❌ TELEGRAM_CHAT_ID не настроен.")
            return False
        
        # Формируем текст сообщения
        telegram_text = f"🚨 НОВАЯ ЗАЯВКА С САЙТА GLADIS\n\n"
        telegram_text += f"👤 Имя: {name}\n"
        telegram_text += f"📞 Телефон: {phone}\n"
        
        if procedure:
            telegram_text += f"💉 Процедура: {procedure}\n"
        
        telegram_text += f"📝 Сообщение клиента:\n{message}\n"
        telegram_text += f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        telegram_text += f"🔗 Источник: чат-бот сайта"
        
        # Если есть токен бота, отправляем через Bot API
        if TELEGRAM_BOT_TOKEN:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": telegram_text,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data, timeout=10)
            print(f"   Статус Telegram API: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Сообщение отправлено в Telegram")
                return True
            else:
                print(f"❌ Ошибка Telegram API: {response.text}")
                return False
        else:
            # Если нет токена, просто логируем
            print(f"📋 Текст для Telegram:\n{telegram_text}")
            print("⚠️ TELEGRAM_BOT_TOKEN не настроен, сообщение не отправлено")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {str(e)}")
        return False


def send_incomplete_to_telegram(message: str, name: str = None, phone: str = None, procedure: str = None):
    """
    Отправляет неполную заявку в Telegram.
    """
    try:
        print(f"\n📨 ОТПРАВКА НЕПОЛНОЙ ЗАЯВКИ В TELEGRAM")
        
        telegram_text = f"⚠️ НЕПОЛНАЯ ЗАЯВКА (таймаут 10 минут)\n\n"
        
        if name:
            telegram_text += f"👤 Имя: {name}\n"
        else:
            telegram_text += f"👤 Имя: НЕ УКАЗАНО\n"
            
        if phone:
            telegram_text += f"📞 Телефон: {phone}\n"
        else:
            telegram_text += f"📞 Телефон: НЕ УКАЗАНО\n"
        
        if procedure:
            telegram_text += f"💉 Процедура: {procedure}\n"
        
        telegram_text += f"📝 Сообщение клиента:\n{message}\n"
        telegram_text += f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        telegram_text += f"💡 Причина: клиент не оставил все данные"
        
        return send_to_telegram(telegram_text, name or "Неизвестно", phone or "Не указан", procedure)
        
    except Exception as e:
        print(f"❌ Ошибка при отправке неполной заявки: {str(e)}")
        return False


def test_telegram_connection():
    """
    Тестируем подключение к Telegram.
    """
    print("\n🔍 ТЕСТИРУЕМ ПОДКЛЮЧЕНИЕ К TELEGRAM...")
    
    if not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID не настроен")
        return False
    
    try:
        if TELEGRAM_BOT_TOKEN:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                print(f"✅ Бот подключен: @{bot_info['result']['username']}")
                print(f"   Имя бота: {bot_info['result']['first_name']}")
                return True
            else:
                print(f"❌ Ошибка подключения: {response.status_code}")
                return False
        else:
            print("⚠️ TELEGRAM_BOT_TOKEN не настроен, отправка не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


# Тестовый вызов
if __name__ == "__main__":
    print("🧪 Тестируем модуль telegram_utils.py")
    test_result = test_telegram_connection()
    print(f"Результат теста: {'✅ УСПЕХ' if test_result else '❌ ПРОВАЛ'}")
