import os
import sys
from typing import Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from chatbot_logic import generate_bot_reply, extract_name_with_ai
from telegram_utils import send_to_telegram, send_incomplete_to_telegram, send_complete_application_to_telegram
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import requests
import threading
import time

# Загружаем переменные окружения
load_dotenv()

def validate_environment():
    """Проверяем обязательные переменные окружения."""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = ["REPLICATE_API_TOKEN", "TELEGRAM_BOT_TOKEN"]  # Добавили TELEGRAM_BOT_TOKEN
    
    missing = []
    
    for var_name in required_vars:
        value = os.getenv(var_name)
        
        if not value or value.strip() == "":
            missing.append(var_name)
            print(f"   ❌ {var_name}: ОТСУТСТВУЕТ")
        else:
            if len(value) > 8:
                masked_value = value[:4] + "..." + value[-4:]
            else:
                masked_value = "***"
            print(f"   ✅ {var_name}: {masked_value}")
    
    # Проверяем TELEGRAM_CHAT_ID (может быть пустым для тестов)
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    if not TELEGRAM_CHAT_ID:
        print(f"   ⚠️ TELEGRAM_CHAT_ID: не настроен (может быть пустым)")
    else:
        print(f"   ✅ TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
    
    if missing:
        print(f"\n❌ Отсутствуют обязательные переменные: {missing}")
        return False
    
    print("✅ Все обязательные переменные окружения присутствуют")
    return True

# Проверяем переменные окружения
print("\n" + "="*60)
print("🚀 Запуск GLADIS Chatbot API")
print("="*60)

env_valid = validate_environment()
if not env_valid:
    print("\n❌ Приложение остановлено")
    sys.exit(1)

# Создаем приложение FastAPI
app = FastAPI(
    title="GLADIS Chatbot API",
    description="Чат-бот для клиники эстетической медицины GLADIS в Сочи",
    version="2.0.0"
)

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем папку static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Получаем переменные окружения
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")

# Хранилище сессий пользователей
user_sessions = {}

def get_fallback_response(message: str) -> str:
    """Простая логика ответа когда AI недоступен."""
    message_lower = message.lower()
    
    if any(greet in message_lower for greet in ["добрый", "здравствуйте", "привет"]):
        return "Здравствуйте! Клиника GLADIS, меня зовут Александра. Чем могу вам помочь?"
    
    elif "трихолакс" in message_lower:
        if "запис" in message_lower:
            return "Трихолакс — это инъекционная процедура для укрепления и роста волос. Стоимость: 6000 руб.\n\nДля записи мне нужно ваше имя и телефон."
        else:
            return "Трихолакс — это инъекционная процедура для укрепления и роста волос. Стоимость: 6000 руб."
    
    elif "запис" in message_lower:
        return "Для записи мне нужно ваше имя и телефон. Укажите их, пожалуйста."
    
    elif any(word in message_lower for word in ["цена", "стоимость", "сколько стоит"]):
        return "Стоимость зависит от выбранной процедуры. Могу подсказать цены на:\n• Лазерную эпиляцию\n• Чистку лица\n• Биоревитализацию\n• Ботулотоксин\n\nЧто именно вас интересует?"
    
    elif any(word in message_lower for word in ["адрес", "где находитесь", "локация"]):
        return "📍 Наши адреса:\n• Сочи: ул. Воровского, 22\n• Адлер: ул. Кирова, д. 26а\n\n📞 Телефон: 8-928-458-32-88\n⏰ Ежедневно 10:00-20:00"
    
    elif any(word in message_lower for word in ["эпиляция", "лазерная"]):
        return "Лазерная эпиляция удаляет волосы надолго. Цены зависят от зоны:\n• Подмышки: 1100-1400 руб\n• Бикини: 1900-3500 руб\n• Ноги полностью: 4500-5800 руб\n\nХотите записаться на консультацию?"
    
    else:
        return "Здравствуйте! Клиника GLADIS, меня зовут Александра. Чем могу вам помочь? Расскажите, какая процедура вас интересует."

def is_contact_collection_request(bot_reply: str) -> bool:
    """Проверяет, просит ли бот контакты в ответе."""
    reply_lower = bot_reply.lower()
    
    # ТОЛЬКО явные и полные запросы контактов
    contact_phrases = [
        "для записи мне нужно ваше имя и телефон",
        "укажите ваше имя и телефон для записи",
        "назовите ваше имя и телефон",
        "мне нужны ваше имя и телефон",
        "имя и телефон для записи",
        "ваше имя и номер телефона",
        "предоставьте имя и телефон",
        "оставьте имя и телефон",
        "дайте имя и телефон"
    ]
    
    # Ищем ТОЛЬКО полные фразы про имя И телефон
    for phrase in contact_phrases:
        if phrase in reply_lower:
            return True
    
    return False

def ping_endpoint():
    """Простая функция для пинга эндпоинтов."""
    if not RENDER_EXTERNAL_URL or not RENDER_EXTERNAL_URL.startswith("http"):
        return
    
    try:
        # Пингуем разные эндпоинты
        endpoints = ["/health", "/", "/ping"]
        
        for endpoint in endpoints:
            try:
                url = f"{RENDER_EXTERNAL_URL.rstrip('/')}{endpoint}"
                response = requests.get(url, timeout=5)
                print(f"🔔 Keep-alive ping {endpoint}: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Keep-alive ping failed: {e}")
            except Exception as e:
                print(f"⚠️ Keep-alive error: {e}")
    except Exception as e:
        print(f"❌ Keep-alive function error: {e}")

def start_keep_alive_simple():
    """Запускаем keep-alive в фоновом потоке (упрощенная версия)."""
    print("🔔 Starting simplified keep-alive service...")
    
    while True:
        try:
            time.sleep(180)  # Пингуем каждые 3 минуты (180 секунд)
            ping_endpoint()
        except Exception as e:
            print(f"❌ Keep-alive thread error: {e}")
            time.sleep(60)

def cleanup_old_sessions():
    """Очистка старых сессий."""
    now = datetime.now()
    to_delete = []
    
    for session_id, session_data in user_sessions.items():
        session_age = now - session_data['created_at']
        
        # Если сессии больше 10 минут И есть контакт И еще не отправлено
        if (session_age > timedelta(minutes=10) and 
            not session_data.get('telegram_sent', False) and 
            session_data.get('phone') and 
            session_data.get('name')):
            
            print(f"⏰ ТАЙМАУТ 10 минут: отправляем неполную заявку")
            
            full_text = "\n".join(session_data.get('text_parts', []))
            send_incomplete_to_telegram(
                full_text, 
                session_data.get('name'),
                session_data.get('phone'),
                session_data.get('procedure_type')
            )
            session_data['telegram_sent'] = True
            session_data['incomplete_sent'] = True
        
        # Удаляем очень старые сессии (больше 2 часов)
        if session_age > timedelta(hours=2):
            to_delete.append(session_id)
    
    for session_id in to_delete:
        del user_sessions[session_id]

def extract_contacts_from_message(message: str, session: Dict[str, Any]):
    """Извлекает контакты из сообщения и обновляет сессию."""
    message_lower = message.lower()
    
    # ===== ПОИСК ТЕЛЕФОНА =====
    phone_patterns = [
        r'\b8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
    ]
    
    phone_matches = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, message)
        if matches:
            phone_matches.extend(matches)
            break
    
    if phone_matches and not session['phone']:
        raw_phone = phone_matches[0]
        clean_phone = re.sub(r'\D', '', raw_phone)
        
        # Нормализуем номер
        if len(clean_phone) == 10:
            clean_phone = '7' + clean_phone
        elif len(clean_phone) == 11 and clean_phone.startswith('8'):
            clean_phone = '7' + clean_phone[1:]
        
        if 10 <= len(clean_phone) <= 11:
            session['phone'] = clean_phone
            print(f"📞 Найден телефон: {raw_phone} → {session['phone']}")
    
    # ===== УЛУЧШЕННЫЙ ПОИСК ИМЕНИ =====
    # Сначала ищем имя в текущем сообщении (даже если уже есть имя в сессии)
    temp_name = None
    
    # 1. Ищем слова с заглавной буквы (русские имена)
    russian_names = re.findall(r'\b[А-ЯЁ][а-яё]{1,20}\b', message)
    
    # Список распространенных русских имен
    common_russian_names = [
        'анна', 'мария', 'елена', 'ольга', 'наталья', 'ирина', 'светлана',
        'александра', 'татьяна', 'юлия', 'евгения', 'дарья', 'екатерина',
        'виктория', 'иван', 'алексей', 'сергей', 'андрей', 'дмитрий', 'михаил',
        'владимир', 'павел', 'максим', 'николай', 'евгений', 'артем', 'антон',
        'вадим', 'рома', 'кирилл', 'игорь', 'вадим'
    ]
    
    # 2. Проверяем каждое найденное слово
    for name in russian_names:
        name_lower = name.lower()
        
        # Проверяем что это не процедура
        procedure_words = ['ботокс', 'эпиляция', 'лазер', 'коллаген', 
                         'чистка', 'пилинг', 'смас', 'морфиус', 'александрит',
                         'перманент', 'биоревитализация', 'инъекция', 'мезотерапия']
        
        is_procedure = any(proc in name_lower for proc in procedure_words)
        is_common_name = name_lower in common_russian_names
        is_near_phone = phone_matches and (abs(message.find(name) - message.find(phone_matches[0])) < 30)
        
        # Это имя если:
        # 1. Это распространенное имя И НЕ процедура
        # 2. ИЛИ стоит рядом с телефоном И НЕ процедура
        if (is_common_name and not is_procedure) or (is_near_phone and not is_procedure):
            temp_name = name
            print(f"👤 Найдено возможное имя в сообщении: {temp_name}")
            break
    
    # 3. Если нашли новое имя - обновляем сессию
    if temp_name and temp_name.lower() not in ['привет', 'здравствуйте', 'добрый', 'пока', 'спасибо']:
        session['name'] = temp_name
        print(f"✅ Обновлено имя в сессии: {session['name']}")
    
    # 4. AI поиск имени (только если еще нет имени ИЛИ текущее имя не подходит)
    if (not session['name'] or session['name'].lower() in ['привет', 'здравствуйте', 'добрый']) and REPLICATE_API_TOKEN and len(message.strip()) > 3:
        print(f"🔍 Использую AI для поиска имени в: '{message}'")
        found_name = extract_name_with_ai(REPLICATE_API_TOKEN, message)
        
        if found_name and found_name.lower() not in ['привет', 'здравствуйте', 'добрый']:
            session['name'] = found_name
            print(f"✅ AI определил/исправил имя: {session['name']}")
        else:
            print(f"ℹ️ AI не нашел подходящее имя в сообщении")

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Основной endpoint для общения с ботом."""
    print(f"\n{'='*60}")
    print(f"🔍 /chat endpoint вызван")
    print(f"{'='*60}")
    
    data = await request.json()
    user_message = data.get("message", "")
    user_ip = request.client.host
    
    print(f"👤 IP: {user_ip}")
    print(f"💬 Сообщение: '{user_message}'")
    
    # Проверка AI токена
    print(f"🤖 Replicate API Token: {'✅ Присутствует' if REPLICATE_API_TOKEN else '❌ Отсутствует'}")
    if REPLICATE_API_TOKEN:
        token_length = len(REPLICATE_API_TOKEN)
        print(f"   Длина токена: {token_length} символов")
    
    # Очищаем старые сессии
    cleanup_old_sessions()

    # Создаем или получаем сессию
    if user_ip not in user_sessions:
        user_sessions[user_ip] = {
            'created_at': datetime.now(),
            'name': None,
            'phone': None,
            'stage': 'consultation',
            'text_parts': [],
            'telegram_sent': False,
            'incomplete_sent': False,
            'message_count': 0,
            'contacts_provided': False,
            'procedure_mentioned': False
        }
    
    session = user_sessions[user_ip]
    session['text_parts'].append(user_message)
    session['message_count'] += 1
    
    # Проверяем, упоминались ли процедуры в диалоге
    full_conversation = "\n".join(session['text_parts']).lower()
    procedure_keywords = ['эпиляция', 'лазер', 'ботокс', 'чистка', 'пилинг', 'бикини', 
                         'коллаген', 'биоревитализация', 'инъекция', 'укол', 'смас', 'морфиус']
    
    if any(keyword in full_conversation for keyword in procedure_keywords):
        session['procedure_mentioned'] = True
        print(f"🔍 В диалоге упоминались процедуры")
    
    # Извлекаем контакты из сообщения
    extract_contacts_from_message(user_message, session)
    
    # ===== ОТПРАВКА В TELEGRAM =====
    
    telegram_was_sent_now = False
    
    # Если есть имя И телефон И еще не отправляли
    if session['name'] and session['phone'] and not session.get('telegram_sent', False):
        print(f"🚨 ПРОВЕРКА ОТПРАВКИ В TELEGRAM:")
        print(f"   👤 Имя: {session['name']}")
        print(f"   📞 Телефон: {session['phone']}")
        print(f"   💉 Процедуры упоминались: {session['procedure_mentioned']}")
        print(f"   💬 Последнее сообщение: '{user_message[:50]}...'")
        
        # УПРОЩЕННАЯ ЛОГИКА: Всегда отправляем если есть контакты И была процедура
        should_send = False
        
        # 1. Явное намерение записаться (ключевые слова)
        message_lower = user_message.lower()
        explicit_intent = any(word in message_lower for word in [
            'запис', 'хочу', 'нужно', 'можно', 'готов', 'давайте', 
            'интересует', 'завтра', 'сегодня', 'после'
        ])
        
        # 2. В диалоге упоминались процедуры
        procedure_mentioned = session['procedure_mentioned']
        
        print(f"🔍 Проверка:")
        print(f"   Явное намерение: {explicit_intent}")
        print(f"   Процедуры в диалоге: {procedure_mentioned}")
        
        # Отправляем если: явное намерение ИЛИ процедуры в диалоге
        should_send = explicit_intent or procedure_mentioned
        
        if should_send:
            print(f"🚨 ОТПРАВЛЯЕМ ЗАЯВКУ В TELEGRAM!")
            full_conversation = "\n".join(session['text_parts'])
            success = send_complete_application_to_telegram(session, full_conversation)
            
            if success:
                session['telegram_sent'] = True
                session['stage'] = 'completed'
                session['contacts_provided'] = True
                telegram_was_sent_now = True
                print(f"✅ Заявка отправлена в Telegram")
            else:
                print(f"❌ Ошибка отправки в Telegram")
        else:
            print(f"ℹ️  Контакты есть, но нет явного намерения записаться")
            session['contacts_provided'] = True
    
    # ===== ГЕНЕРАЦИЯ ОТВЕТА БОТА =====
    
    bot_reply = ""
    
    # Определяем первое ли это сообщение в сессии
    is_first_in_session = (session['message_count'] == 1)
    
    # Если заявка ТОЛЬКО ЧТО отправлена в Telegram
    if telegram_was_sent_now:
        print(f"🤖 Заявка отправлена, генерирую подтверждающий ответ")
        if session.get('name'):
            bot_reply = f"✅ Спасибо, {session['name']}! Ваша заявка передана менеджеру. С вами свяжутся для подтверждения записи.\n\n📞 Телефон клиники: 8-928-458-32-88"
        else:
            bot_reply = "✅ Спасибо! Ваша заявка передана менеджеру. С вами свяжутся для подтверждения записи.\n\n📞 Телефон клиники: 8-928-458-32-88"
    
    # Если заявка уже была отправлена ранее
    elif session['stage'] == 'completed' or session.get('telegram_sent', False):
        print(f"🤖 Заявка уже отправлена ранее")
        if session.get('name'):
            bot_reply = f"✅ {session['name']}, ваша заявка уже передана менеджеру. С вами свяжутся для подтверждения записи.\n\n📞 Телефон клиники: 8-928-458-32-88"
        else:
            bot_reply = "✅ Ваша заявка уже передана менеджеру. С вами свяжутся для подтверждения записи.\n\n📞 Телефон клиники: 8-928-458-32-88"
    
    # Иначе используем AI
    elif REPLICATE_API_TOKEN and len(REPLICATE_API_TOKEN) > 20:
        print("🤖 Использую AI для генерации ответа...")
        
        try:
            # Передаем информацию о том, отправлена ли уже заявка
            telegram_already_sent = session.get('telegram_sent', False)
            
            # Генерируем ответ через AI с контекстом сессии
            bot_reply = generate_bot_reply(
                REPLICATE_API_TOKEN, 
                user_message, 
                is_first_in_session,
                bool(session['name']),  # has_name
                bool(session['phone']), # has_phone
                telegram_already_sent   # telegram_sent
            )
            print(f"✅ AI ответ сгенерирован")
            
            # Проверяем, не просит ли AI контакты
            if is_contact_collection_request(bot_reply):
                session['stage'] = 'contact_collection'
                print("📝 AI запросил контакты")
                
        except Exception as e:
            print(f"❌ Ошибка при вызове AI: {str(e)}")
            # Fallback на простую логику
            bot_reply = get_fallback_response(user_message)
            
    # Если AI недоступен или ошибка
    else:
        print("⚠️ AI недоступен, использую простую логику")
        bot_reply = get_fallback_response(user_message)
    
    # Логируем состояние сессии
    print(f"📊 СОСТОЯНИЕ СЕССИИ:")
    print(f"   Этап: {session['stage']}")
    print(f"   👤 Имя: {'✅ ' + session['name'] if session['name'] else '❌ Нет'}")
    print(f"   📞 Телефон: {'✅ ' + str(session['phone']) if session['phone'] else '❌ Нет'}")
    print(f"   📨 Отправлено в Telegram: {'✅' if session.get('telegram_sent') else '❌'}")
    print(f"   📝 Сообщений: {session['message_count']}")
    print(f"   🔍 Контакты получены: {'✅' if session.get('contacts_provided') else '❌'}")
    print(f"   💉 Процедуры упоминались: {'✅' if session.get('procedure_mentioned') else '❌'}")
    
    print(f"🤖 Ответ бота: '{bot_reply[:100]}...'" if len(bot_reply) > 100 else f"🤖 Ответ бота: '{bot_reply}'")
    print("="*40)
    
    return {"reply": bot_reply}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    """Проверка здоровья сервиса."""
    if request.method == "HEAD":
        return Response(status_code=200)
    
    services_status = {
        "replicate_api": bool(REPLICATE_API_TOKEN),
        "telegram_bot": bool(TELEGRAM_BOT_TOKEN),
        "telegram_chat": TELEGRAM_CHAT_ID if TELEGRAM_CHAT_ID else "не настроен",
        "sessions_count": len(user_sessions)
    }
    
    return {
        "status": "ok",
        "service": "gladis-chatbot-api",
        "timestamp": datetime.now().isoformat(),
        "sessions_count": len(user_sessions),
        "services": services_status,
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "service": "GLADIS Chatbot API",
        "description": "Чат-бот для клиники эстетической медицины GLADIS в Сочи",
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": {
                "url": "/chat",
                "method": "POST",
                "description": "Общение с ботом"
            },
            "health": {
                "url": "/health",
                "method": "GET, HEAD",
                "description": "Проверка работоспособности"
            },
            "ping": {
                "url": "/ping",
                "method": "GET",
                "description": "Пинг для keep-alive"
            }
        }
    }

@app.get("/ping")
async def ping():
    """Пинг сервера."""
    return {
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "service": "gladis-chatbot"
    }

@app.get("/debug/sessions")
async def debug_sessions():
    """Просмотр активных сессий (только для отладки)."""
    now = datetime.now()
    active_sessions = {}
    
    for session_id, session_data in user_sessions.items():
        session_age = now - session_data['created_at']
        active_sessions[session_id] = {
            "age_minutes": round(session_age.total_seconds() / 60, 1),
            "name": session_data['name'],
            "phone": session_data['phone'],
            "stage": session_data.get('stage'),
            "message_count": session_data.get('message_count', 0),
            "telegram_sent": session_data.get('telegram_sent', False),
            "contacts_provided": session_data.get('contacts_provided', False),
            "procedure_mentioned": session_data.get('procedure_mentioned', False)
        }
    
    return {
        "active_sessions_count": len(user_sessions),
        "current_time": now.isoformat(),
        "sessions": active_sessions
    }

# Обработчики ошибки
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return Response(
        status_code=404,
        content=f"Endpoint {request.url.path} not found."
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Ошибка: {exc}")
    return Response(
        status_code=500,
        content="Internal Server Error"
    )

# Запускаем keep-alive при старте приложения
@app.on_event("startup")
async def startup_event():
    """Запускается при старте приложения."""
    print("\n" + "="*60)
    print("🏥 GLADIS Chatbot API запущен")
    print("="*60)
    
    print(f"🤖 AI сервис: {'✅ Replicate' if REPLICATE_API_TOKEN else '❌ Не настроен'}")
    if REPLICATE_API_TOKEN:
        print(f"   Длина токена: {len(REPLICATE_API_TOKEN)} символов")
    
    print(f"📱 Telegram: {'✅ Настроен' if TELEGRAM_BOT_TOKEN else '⚠️ Только логи'}")
    print(f"💬 Chat ID: {'✅ Настроен' if TELEGRAM_CHAT_ID else '❌ Не настроен'}")
    
    if RENDER_EXTERNAL_URL and RENDER_EXTERNAL_URL.startswith("http"):
        print(f"🔔 Keep-alive URL: {RENDER_EXTERNAL_URL}")
        # Запускаем keep-alive в отдельном потоке
        keep_alive_thread = threading.Thread(target=start_keep_alive_simple, daemon=True)
        keep_alive_thread.start()
        print("🔔 Keep-alive служба запущена")
    
    print("✅ Приложение готово к работе")
    print("="*60 + "\n")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
