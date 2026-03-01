"""
Модуль для обработки входящих сообщений в Telegram боте
Поддерживает:
- Личные сообщения боту (@sochigladisbot)
- Бизнес-сообщения (личка @gladisSochi через Business Mode)
"""

import os
import asyncio
import requests
from typing import Dict, Any
from datetime import datetime

# Хранилище сессий для Telegram пользователей
telegram_sessions = {}

def get_bot_token():
    """Возвращает токен бота"""
    return os.getenv("TELEGRAM_BOT_TOKEN", "")

async def handle_telegram_update(update: Dict[str, Any]):
    """
    Обрабатывает входящее обновление от Telegram
    """
    try:
        # Определяем тип сообщения
        message = None
        chat_id = None
        user_id = None
        text = None
        username = None
        chat_type = None
        is_business = False
        
        # Обычное сообщение (личка боту)
        if 'message' in update:
            message = update['message']
            chat_type = message['chat']['type']
            
            # Игнорируем групповые чаты и каналы
            if chat_type in ['group', 'supergroup', 'channel']:
                print(f"⏭️ Игнорируем сообщение из группы/канала")
                return
            
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message.get('text', '')
            username = message['from'].get('first_name', 'Пользователь')
            is_business = False
        
        # Бизнес-сообщение (личка @gladisSochi)
        elif 'business_message' in update:
            message = update['business_message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message.get('text', '')
            username = message['from'].get('first_name', 'Пользователь')
            is_business = True
        
        else:
            return  # Игнорируем другие типы
        
        # Игнорируем команды
        if text.startswith('/'):
            return
        
        print(f"\n📱 ВХОДЯЩЕЕ СООБЩЕНИЕ В TELEGRAM")
        print(f"   Тип: {'Бизнес (личка @gladisSochi)' if is_business else 'Личка боту'}")
        print(f"   От: {username} (ID: {user_id})")
        print(f"   Текст: {text[:50]}..." if len(text) > 50 else f"   Текст: {text}")
        
        # Получаем или создаем сессию
        session_key = f"tg_{user_id}"
        if session_key not in telegram_sessions:
            telegram_sessions[session_key] = {
                'created_at': datetime.now(),
                'name': None,
                'phone': None,
                'text_parts': [],
                'message_count': 0,
                'last_procedure': None,
                'telegram_chat_id': chat_id,
                'telegram_user_id': user_id,
                'is_business': is_business
            }
        
        session = telegram_sessions[session_key]
        session['text_parts'].append(text)
        session['message_count'] += 1
        
        # Пытаемся извлечь имя и телефон (упрощенная версия)
        await extract_contacts_from_message(text, session)
        
        # Генерируем ответ через AI
        from chatbot_logic import generate_bot_reply
        
        api_key = os.getenv("REPLICATE_API_TOKEN")
        if not api_key:
            reply = "Здравствуйте! Клиника GLADIS. Чем могу помочь?"
        else:
            is_first = session['message_count'] == 1
            has_name = bool(session['name'])
            has_phone = bool(session['phone'])
            telegram_sent = False  # В Telegram не отправляем повторно
            last_procedure = session.get('last_procedure')
            
            # Генерируем ответ (в отдельном потоке, чтобы не блокировать)
            reply = await asyncio.to_thread(
                generate_bot_reply,
                api_key,
                text,
                is_first,
                has_name,
                has_phone,
                telegram_sent,
                last_procedure
            )
        
        # Отправляем ответ
        await send_telegram_reply(chat_id, reply)
        
        # Если есть имя и телефон, отправляем заявку в группу
        if session['name'] and session['phone'] and not session.get('telegram_sent'):
            from telegram_utils import send_complete_application_to_telegram
            
            full_conversation = "\n".join(session['text_parts'])
            source = "Telegram (личка @gladisSochi)" if is_business else "Telegram (личка боту)"
            
            # Добавляем источник в заявку
            session_with_source = session.copy()
            session_with_source['source'] = source
            
            await asyncio.to_thread(
                send_complete_application_to_telegram,
                session_with_source,
                f"📱 ИСТОЧНИК: {source}\n\n{full_conversation}"
            )
            session['telegram_sent'] = True
            print(f"✅ Заявка из Telegram отправлена в группу")
        
        print(f"✅ Ответ отправлен")
        
    except Exception as e:
        print(f"❌ Ошибка обработки Telegram сообщения: {e}")
        import traceback
        traceback.print_exc()

async def extract_contacts_from_message(message: str, session: Dict[str, Any]):
    """Упрощенное извлечение контактов (можно скопировать из main.py)"""
    import re
    
    message_lower = message.lower()
    
    # Поиск телефона
    phone_patterns = [
        r'\b8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, message)
        if matches and not session['phone']:
            clean_phone = re.sub(r'\D', '', matches[0])
            if len(clean_phone) == 10:
                clean_phone = '7' + clean_phone
            elif len(clean_phone) == 11 and clean_phone.startswith('8'):
                clean_phone = '7' + clean_phone[1:]
            session['phone'] = clean_phone
            print(f"📞 Найден телефон: {session['phone']}")
            break
    
    # Поиск имени (упрощенно)
    name_match = re.search(r'\b[А-ЯЁ][а-яё]{2,}\b', message)
    if name_match and not session['name']:
        name = name_match.group(0)
        # Проверяем, что это не процедура
        procedure_words = ['ботокс', 'эпиляция', 'лазер', 'чистка', 'пилинг']
        if name.lower() not in procedure_words:
            session['name'] = name
            print(f"👤 Найдено имя: {session['name']}")

async def send_telegram_reply(chat_id: int, text: str):
    """
    Отправляет ответ пользователю в Telegram
    """
    try:
        token = get_bot_token()
        if not token:
            print("❌ Нет токена бота")
            return False
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        response = await asyncio.to_thread(
            requests.post, url, json=payload, timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Ошибка Telegram API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

async def telegram_polling():
    """
    Постоянный опрос Telegram API (long polling)
    """
    token = get_bot_token()
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не настроен, polling отключен")
        return
    
    print("🔄 Запуск Telegram polling...")
    print("   Будет обрабатывать:")
    print("   - личные сообщения @" + os.getenv("TELEGRAM_BOT_TOKEN", "").split(':')[0])
    print("   - бизнес-сообщения @gladisSochi (если бот подключен)")
    
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": ["message", "business_message"]
            }
            
            response = await asyncio.to_thread(
                requests.get, url, params=params, timeout=35
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        await handle_telegram_update(update)
                        offset = update["update_id"] + 1
            
            await asyncio.sleep(0.5)
            
        except asyncio.CancelledError:
            print("🛑 Telegram polling остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")
            await asyncio.sleep(5)
