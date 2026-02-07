import os
import sys
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from chatbot_logic import generate_bot_reply, check_interesting_application
from telegram_utils import send_to_telegram, send_incomplete_to_telegram, send_complete_application_to_telegram
from dialog_logic import analyze_client_needs, clarify_procedure_details, handle_contact_collection, should_move_to_contacts
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import requests
import threading
import asyncio

# Загружаем переменные окружения
load_dotenv()

def validate_environment():
    """Проверяем обязательные переменные окружения."""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = ["REPLICATE_API_TOKEN"]
    
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
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@sochigladisbot")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")

# Хранилище сессий пользователей
user_sessions = {}

# ====== ФУНКЦИИ ДЛЯ ПОДДЕРЖАНИЯ АКТИВНОСТИ ======

async def keep_alive_ping():
    """Периодически пингуем сервер, чтобы не засыпал на Render."""
    if not RENDER_EXTERNAL_URL:
        return
        
    while True:
        try:
            await asyncio.sleep(300)
            
            base_url = RENDER_EXTERNAL_URL
            endpoints_to_ping = ["/health", "/", "/ping"]
            
            for endpoint in endpoints_to_ping:
                try:
                    url = f"{base_url}{endpoint}"
                    response = requests.get(url, timeout=10)
                    print(f"🔔 Keep-alive ping: {response.status_code}")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Keep-alive error: {e}")
            await asyncio.sleep(60)

def start_keep_alive():
    """Запускаем keep-alive в фоновом потоке."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(keep_alive_ping())
    except:
        pass

# Запускаем keep-alive при старте приложения
@app.on_event("startup")
async def startup_event():
    """Запускается при старте приложения."""
    print("\n" + "="*60)
    print("🏥 GLADIS Chatbot API запущен")
    print("="*60)
    
    print(f"🤖 AI сервис: {'✅ Replicate' if REPLICATE_API_TOKEN else '❌ Не настроен'}")
    print(f"📱 Telegram: {'✅ Настроен' if TELEGRAM_BOT_TOKEN else '⚠️ Только логи'}")
    print(f"💬 Канал: {TELEGRAM_CHAT_ID}")
    
    if RENDER_EXTERNAL_URL and RENDER_EXTERNAL_URL.startswith("http"):
        print("🔔 Starting keep-alive service...")
        threading.Thread(target=start_keep_alive, daemon=True).start()
    
    print("✅ Приложение готово к работе")
    print("="*60 + "\n")

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

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Основной endpoint для общения с ботом."""
    data = await request.json()
    user_message = data.get("message", "")
    user_ip = request.client.host
    
    print(f"\n=== /chat endpoint вызван ===")
    print(f"👤 IP: {user_ip}")
    print(f"💬 Сообщение: '{user_message}'")

    # Очищаем старые сессии
    cleanup_old_sessions()

    # Создаем или получаем сессию
    if user_ip not in user_sessions:
        user_sessions[user_ip] = {
            'created_at': datetime.now(),
            'name': None,
            'phone': None,
            'procedure_category': None,      # Категория (эпиляция, чистка и т.д.)
            'procedure_type': None,          # Конкретный тип (карбоновый пилинг и т.д.)
            'zone': None,                    # Зона (лицо, ноги и т.д.)
            'laser_type': None,              # Тип лазера (гибридный/александритовый)
            'location': None,                # Сочи или Адлер
            'skin_type': None,               # Тип кожи
            'skin_problems': [],             # Проблемы кожи
            'zones': [],                     # Зоны для процедуры
            'preferences': [],               # Предпочтения клиента
            'questions_answered': [],        # Ответы на вопросы
            'stage': 'needs_analysis',       # Текущий этап диалога
            'text_parts': [],
            'telegram_sent': False,
            'incomplete_sent': False,
            'message_count': 0,
            'consultation_complete': False   # Консультация завершена
        }
    
    session = user_sessions[user_ip]
    session['text_parts'].append(user_message)
    session['message_count'] += 1
    
    # Ищем контакты в сообщении (улучшенные паттерны)
    phone_pattern = r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2,3}'
    phone_matches = re.findall(phone_pattern, user_message)
    
    # Также ищем просто 11 цифр подряд
    if not phone_matches:
        phone_pattern2 = r'\b\d{10,11}\b'
        phone_matches = re.findall(phone_pattern2, user_message)
    
    # Улучшенные паттерны для имени
    name_patterns = [
        r'меня\s+зовут\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
        r'имя\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
        r'зовут\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
        r'^([А-ЯЁ][а-яё]+)[,\s]',  # Имя в начале сообщения с запятой или пробелом
        r'([А-ЯЁ][а-яё]+)\s+(?:это|мое имя|меня)',  # "Вадим это", "Вадим мое имя"
    ]
    
    found_name = None
    for pattern in name_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            found_name = match.group(1)
            # Удаляем возможные цифры после имени
            found_name = re.sub(r'\d+$', '', found_name).strip()
            break
    
    # Если не нашли по паттернам, ищем русские слова с заглавной буквы
    if not found_name:
        words = re.findall(r'[А-ЯЁа-яё]+', user_message)
        russian_words = [word for word in words if re.match(r'^[А-ЯЁ][а-яё]*$', word)]
        if russian_words:
            found_name = russian_words[0]
    
    # Обновляем контакты если найдены
    if phone_matches and not session['phone']:
        clean_phone = re.sub(r'\D', '', phone_matches[0])
        if 10 <= len(clean_phone) <= 11:
            session['phone'] = clean_phone
            print(f"📞 Найден телефон: {session['phone']}")
    
    if found_name and not session['name']:
        session['name'] = found_name
        print(f"👤 Найдено имя: {session['name']}")
    
    # ===== ИСПРАВЛЕННАЯ ЛОГИКА ЭТАПОВ =====
    
    # Этап 1: Анализ потребностей
    if session['stage'] == 'needs_analysis':
        bot_reply = analyze_client_needs(user_message, session)
        
        # Проверяем, переходим ли к следующему этапу
        if session.get('procedure_category'):
            # Если нашли процедуру - переходим к уточнению
            session['stage'] = 'details_clarification'
        elif should_move_to_contacts(user_message, session):
            # Если клиент сразу хочет записаться или дает контакты
            session['stage'] = 'contact_collection'
            # НЕ добавляем повторно запрос контактов, если уже в ответе есть
            if "ваше имя и телефон" not in bot_reply:
                bot_reply += "\n\nДля записи мне нужно ваше имя и телефон. Укажите их, пожалуйста."
    
    # Этап 2: Консультация через AI (ТОЛЬКО для сложных вопросов)
    elif session['stage'] == 'consultation' and REPLICATE_API_TOKEN:
        bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)
        
        # Сохраняем ответы на вопросы
        if 'questions_answered' not in session:
            session['questions_answered'] = []
        session['questions_answered'].append(user_message)
        
        # Проверяем, не пора ли переходить к контактам
        if should_move_to_contacts(user_message, session):
            session['stage'] = 'contact_collection'
            if "ваше имя и телефон" not in bot_reply:
                bot_reply += "\n\nДля записи мне нужно ваше имя и телефон. Укажите их, пожалуйста."
    
    # Этап 3: Уточнение деталей процедуры
    elif session['stage'] == 'details_clarification':
        bot_reply = clarify_procedure_details(user_message, session)
        
        # Если функция вернула, что нужно перейти к контактам
        if "Для записи мне нужно" in bot_reply or "ваше имя и телефон" in bot_reply:
            session['stage'] = 'contact_collection'
    
    # Этап 4: Сбор контактов
    elif session['stage'] == 'contact_collection':
        bot_reply = handle_contact_collection(user_message, session)
        
        # Если собрали все контакты - отправляем в Telegram
        if session['name'] and session['phone']:
            print(f"📨 ОТПРАВЛЯЕМ ПОЛНУЮ ФАБУЛУ В TELEGRAM")
            full_text = "\n".join(session['text_parts'])
            success = send_complete_application_to_telegram(session, full_text)
            if success:
                session['telegram_sent'] = True
                session['stage'] = 'completed'
                bot_reply += "\n\n✅ Спасибо! Вся информация передана администратору. С вами свяжутся для подтверждения записи."
    
    # Этап 5: Завершено
    elif session['stage'] == 'completed':
        bot_reply = "Ваша заявка уже передана администратору. С вами свяжутся для подтверждения записи. 📞 Телефон: 8-928-458-32-88"
    
    # Резервный вариант: AI для нераспознанных сообщений
    else:
        if REPLICATE_API_TOKEN:
            bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)
        else:
            bot_reply = "Извините, сервис временно недоступен. Пожалуйста, позвоните по телефону 8-928-458-32-88"
    
    # Логируем состояние сессии
    print(f"📊 СОСТОЯНИЕ СЕССИИ:")
    print(f"   Этап: {session['stage']}")
    print(f"   Процедура: {session.get('procedure_category', 'Не выбрана')}")
    print(f"   👤 Имя: {'✅ ' + session['name'] if session['name'] else '❌ Нет'}")
    print(f"   📞 Телефон: {'✅ ' + str(session['phone']) if session['phone'] else '❌ Нет'}")
    print(f"   📨 Отправлено: {'✅' if session.get('telegram_sent') else '❌'}")
    
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
        "telegram_chat": TELEGRAM_CHAT_ID
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
            "procedure": session_data.get('procedure_category'),
            "stage": session_data.get('stage'),
            "message_count": session_data.get('message_count', 0),
            "telegram_sent": session_data.get('telegram_sent', False)
        }
    
    return {
        "active_sessions_count": len(user_sessions),
        "current_time": now.isoformat(),
        "sessions": active_sessions
    }

# Обработчики ошибок
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
