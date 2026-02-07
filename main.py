import os
import sys
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from chatbot_logic import generate_bot_reply, check_interesting_application
from telegram_utils import send_to_telegram, send_incomplete_to_telegram
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
    version="1.0.0"
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
            not session_data['telegram_sent'] and 
            session_data.get('phone') and 
            session_data.get('name')):
            
            print(f"⏰ ТАЙМАУТ 10 минут: отправляем неполную заявку")
            
            full_text = "\n".join(session_data['text_parts'])
            send_incomplete_to_telegram(
                full_text, 
                session_data.get('name'),
                session_data.get('phone'),
                session_data.get('email')
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

    # Проверяем, является ли это интересной заявкой
    is_interesting = check_interesting_application(user_message)
    print(f"🔍 Интересная заявка: {is_interesting}")

    # Если это интересная заявка (процедура/запись)
    if is_interesting:
        print(f"📋 ЗАЯВКА НА ПРОЦЕДУРУ/КОНСУЛЬТАЦИЮ")
        
        # Создаем или получаем сессию
        if user_ip not in user_sessions:
            user_sessions[user_ip] = {
                'created_at': datetime.now(),
                'name': None,
                'phone': None,
                'email': None,
                'procedure': None,
                'text_parts': [],
                'telegram_sent': False,
                'incomplete_sent': False,
                'reminder_sent': False,
                'message_count': 0
            }
        
        session = user_sessions[user_ip]
        session['text_parts'].append(user_message)
        session['message_count'] += 1
        full_text = "\n".join(session['text_parts'])
        
        # Ищем контакты в сообщении
        phone_pattern = r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        phone_matches = re.findall(phone_pattern, user_message)
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, user_message)
        
        # Ищем имя
        name_patterns = [
            r'меня\s+зовут\s+([А-ЯЁ][а-яё]+)',
            r'имя\s+([А-ЯЁ][а-яё]+)',
            r'([А-ЯЁ][а-яё]+)\s+(?:это|мое имя)'
        ]
        
        found_name = None
        for pattern in name_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                found_name = match.group(1)
                break
        
        # Обновляем найденные данные
        if phone_matches and not session['phone']:
            session['phone'] = phone_matches[0]
            print(f"📞 Найден телефон: {session['phone']}")
        
        if email_matches and not session['email']:
            session['email'] = email_matches[0]
            print(f"📧 Найден email: {session['email']}")
        
        if found_name and not session['name']:
            session['name'] = found_name
            print(f"👤 Найдено имя: {session['name']}")
        
        # Определяем процедуру по ключевым словам
        procedure_keywords = {
            'SMAS лифтинг': ['smas', 'лифтинг'],
            'Morpheus8': ['morpheus', 'микроигольчатый'],
            'Фотодинамическая терапия': ['фотодинамическая', 'терапия'],
            'Увеличение губ': ['губы', 'увеличение'],
            'Ботулотоксин': ['ботулин', 'ботокс'],
            'Чистка лица': ['чистка', 'пилинг'],
            'Биоревитализация': ['биоревитализация'],
            'Лазерная эпиляция': ['эпиляция', 'лазерная'],
            'Фотоомоложение': ['фотоомоложение', 'lumec'],
            'Капельницы': ['капельницы', 'инфузионная'],
            'Консультация врача': ['консультация', 'врач', 'прием']
        }
        
        if not session['procedure']:
            for proc_name, keywords in procedure_keywords.items():
                if any(kw in user_message.lower() for kw in keywords):
                    session['procedure'] = proc_name
                    print(f"💉 Определена процедура: {proc_name}")
                    break
        
        # Логируем состояние сессии
        print(f"📊 СОСТОЯНИЕ СЕССИИ:")
        print(f"   📝 Сообщений: {session['message_count']}")
        print(f"   👤 Имя: {'✅ ' + session['name'] if session['name'] else '❌ Нет'}")
        print(f"   📞 Телефон: {'✅ ' + str(session['phone']) if session['phone'] else '❌ Нет'}")
        print(f"   💉 Процедура: {'✅ ' + session['procedure'] if session['procedure'] else '❌ Не указана'}")
        print(f"   📨 Отправлено в Telegram: {'✅' if session['telegram_sent'] else '❌'}")
        
        # ===== ЛОГИКА ОТВЕТА БОТА =====
        
        # Случай 1: Уже отправлено в Telegram
        if session['telegram_sent']:
            if session.get('incomplete_sent'):
                bot_reply = "Ваша заявка принята! Мы свяжемся с вами для уточнения деталей. Спасибо!"
            else:
                bot_reply = "Спасибо! Ваша заявка передана менеджеру. С вами свяжутся в течение 30 минут."
        
        # Случай 2: Есть имя и телефон - отправляем ПОЛНУЮ заявку
        elif session['name'] and session['phone']:
            print(f"📨 ОТПРАВЛЯЕМ ПОЛНУЮ ЗАЯВКУ")
            success = send_to_telegram(
                full_text, 
                session['name'], 
                session['phone'],
                session.get('email'),
                session.get('procedure')
            )
            if success:
                session['telegram_sent'] = True
                bot_reply = "Спасибо! Ваша заявка передана менеджеру. С вами свяжутся в течение 30 минут."
            else:
                bot_reply = "Произошла ошибка. Пожалуйста, попробуйте еще раз или позвоните нам."
        
        # Случай 3: Есть только имя ИЛИ телефон
        elif session['name'] or session['phone']:
            has_name = bool(session['name'])
            has_phone = bool(session['phone'])
            
            if not session['reminder_sent'] and session['message_count'] >= 2:
                if has_name and not has_phone:
                    bot_reply = f"Спасибо, {session['name']}! Для записи нужен ваш телефон."
                elif has_phone and not has_name:
                    bot_reply = "Спасибо за телефон! Как вас зовут?"
                session['reminder_sent'] = True
            
            else:
                if has_name and not has_phone:
                    bot_reply = f"Спасибо, {session['name']}! Укажите ваш телефон."
                elif has_phone and not has_name:
                    bot_reply = "Спасибо за телефон! Как вас зовут?"
                else:
                    bot_reply = "Для записи нужно ваше имя и телефон."
        
        # Случай 4: Нет контактов
        else:
            bot_reply = "Для записи на процедуру укажите ваше имя и телефон."
    
    # Обычный запрос (не заявка)
    else:
        print(f"💭 Обычный запрос/вопрос")
        if REPLICATE_API_TOKEN:
            bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)
        else:
            bot_reply = "Извините, сервис временно недоступен. Пожалуйста, позвоните нам."
            print("⚠️ REPLICATE_API_TOKEN отсутствует")

    print(f"🤖 Ответ бота: '{bot_reply}'")
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
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "service": "GLADIS Chatbot API",
        "description": "Чат-бот для клиники эстетической медицины GLADIS в Сочи",
        "status": "running",
        "version": "1.0.0",
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
