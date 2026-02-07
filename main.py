import os
import sys
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from chatbot_logic import generate_bot_reply, extract_name_with_ai
from telegram_utils import send_to_telegram, send_incomplete_to_telegram, send_complete_application_to_telegram
from dialog_logic import analyze_client_needs_simple, handle_contact_collection
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

def is_simple_greeting(message: str) -> bool:
    """Проверяет, является ли сообщение простым приветствием."""
    message_lower = message.lower()
    
    greetings = [
        "добрый день", "добрый вечер", "доброе утро",
        "здравствуйте", "привет", "здрасьте", "приветствую",
        "доброго времени суток", "доброй ночи"
    ]
    
    # Проверяем точные совпадения
    for greeting in greetings:
        if greeting in message_lower:
            # Дополнительно проверяем, что это действительно только приветствие
            words = message_lower.split()
            if len(words) <= 3:  # "добрый день" - 2 слова
                return True
            elif all(word in greetings + ["", " "] for word in words[:3]):
                return True
    
    return False

def should_move_to_contacts(message: str, session: Dict[str, Any]) -> bool:
    """
    Определяет, пора ли переходить к сбору контактов.
    """
    message_lower = message.lower()
    
    # Ключевые слова, указывающие на готовность записаться
    ready_keywords = [
        "хочу записаться", "запишите", "можно записаться", 
        "готов записаться", "давайте запишем", "хочу на процедуру",
        "интересует запись", "хочу сделать", "запишите меня",
        "давайте", "согласен", "ок", "хорошо", "идемте", "хотел записаться"
    ]
    
    # Если клиент явно говорит о записи
    if any(keyword in message_lower for keyword in ready_keywords):
        return True
    
    # Если клиент дает контакты
    contact_patterns = [
        r'\d{10,11}',
        r'[\+7]?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2,3}',
        r'меня\s+зовут',
        r'имя\s+',
        r'телефон'
    ]
    
    for pattern in contact_patterns:
        if re.search(pattern, message_lower):
            return True
    
    # Если клиент спрашивает о конкретной процедуре и хочет записаться
    procedure_keywords = [
        "трихолакс", "эпиляция", "ботокс", "чистка", "пилинг",
        "лифтинг", "мезотерапия", "биоревитализация"
    ]
    
    has_procedure = any(keyword in message_lower for keyword in procedure_keywords)
    wants_to_register = "запис" in message_lower
    
    if has_procedure and wants_to_register:
        return True
    
    # Если уже было много сообщений в диалоге
    if session.get('message_count', 0) >= 5:
        return True
    
    return False

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
            'procedure_category': None,
            'procedure_type': None,
            'zone': None,
            'laser_type': None,
            'location': None,
            'skin_type': None,
            'skin_problems': [],
            'zones': [],
            'preferences': [],
            'questions_answered': [],
            'stage': 'needs_analysis',
            'text_parts': [],
            'telegram_sent': False,
            'incomplete_sent': False,
            'message_count': 0,
            'consultation_complete': False
        }
    
    session = user_sessions[user_ip]
    session['text_parts'].append(user_message)
    session['message_count'] += 1
    
    # ===== УЛУЧШЕННОЕ РАСПОЗНАВАНИЕ ТЕЛЕФОНА =====
    phone_patterns = [
        r'\b8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
        r'\b\d{4}[\s\-]?\d{3}[\s\-]?\d{4}\b',
        r'\b\d{11}\b',
        r'\b\d{10}\b',
    ]
    
    phone_matches = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, user_message)
        if matches:
            phone_matches.extend(matches)
            break
    
    # Обработка телефона
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
    
    # ===== РАСПОЗНАВАНИЕ ИМЕНИ С ИСПОЛЬЗОВАНИЕМ AI =====
    found_name = None
    
    # 1. Сначала пробуем стандартные паттерны
    name_patterns = [
        r'(?:меня\s+зовут|имя|зовут|мое\s+имя)[\s:]+([а-яё\-]+\s*[а-яё\-]*)',
        r'([а-яё\-]+)[\s,]*\+?\d',
        r'([а-яё\-]+)[\s,]*(?:телефон|тел\.?|мобильный|номер)',
        r'^([а-яё\-]+)[,\s]',
        r'([а-яё\-]+)\s+(?:это|мое имя|меня|здесь|я)',
        r'я\s+([а-яё\-]+)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, user_message.lower())
        if match:
            found_name = match.group(1).strip()
            found_name = re.sub(r'[\d\+]', '', found_name).strip()
            if found_name and len(found_name) >= 2:
                if '-' in found_name:
                    parts = found_name.split('-')
                    found_name = '-'.join([part.capitalize() for part in parts])
                else:
                    found_name = found_name.capitalize()
                break
    
    # 2. Если не нашли по паттернам, используем AI (если есть токен)
    if not found_name and REPLICATE_API_TOKEN:
        print(f"🔍 Использую AI для поиска имени в: '{user_message}'")
        found_name = extract_name_with_ai(REPLICATE_API_TOKEN, user_message)
        if found_name:
            print(f"✅ AI нашел имя: {found_name}")
    
    # 3. Если AI не нашел или нет токена, пробуем простую логику
    if not found_name:
        words = re.findall(r'[а-яё\-]+', user_message.lower())
        if words and len(words[0]) >= 2:
            candidate = words[0]
            stop_words = {'добрый', 'день', 'вечер', 'утро', 'здравствуйте', 
                         'привет', 'хочу', 'записаться', 'на', 'процедуру', 'по'}
            if candidate not in stop_words:
                found_name = candidate.capitalize()
    
    # Сохраняем найденное имя
    if found_name and not session['name']:
        session['name'] = found_name
        print(f"👤 Найдено имя: {session['name']}")
    
    # ===== ОСНОВНАЯ AI-ЛОГИКА =====
    
    bot_reply = ""
    
    # Если доступен AI - используем его как основной движок
    if REPLICATE_API_TOKEN:
        print("🤖 Генерация ответа через AI...")
        
        # Проверяем, не нужно ли сразу перейти к сбору контактов
        if should_move_to_contacts(user_message, session):
            session['stage'] = 'contact_collection'
            print("📝 Прямой переход к сбору контактов")
            
            # Формируем ответ для сбора контактов
            if session['name'] and session['phone']:
                bot_reply = "Спасибо! Сейчас передам всю информацию администратору."
            elif session['name']:
                bot_reply = f"Спасибо, {session['name']}! Теперь укажите ваш телефон для связи."
            elif session['phone']:
                bot_reply = f"Спасибо! Вижу ваш телефон {session['phone']}. Как вас зовут?"
            else:
                bot_reply = "Для записи мне нужно ваше имя и телефон для связи. Укажите их, пожалуйста."
        else:
            # Используем AI для генерации ответа
            bot_reply = generate_bot_reply(REPLICATE_API_TOKEN, user_message)
            
            # Определяем этап на основе ответа AI
            reply_lower = bot_reply.lower()
            
            # Если AI запросил контакты - переходим к сбору
            contact_phrases = [
                "ваше имя", "ваш телефон", "для записи мне нужно",
                "назовите ваше имя", "укажите телефон", "как вас зовут",
                "мне нужно ваше имя", "ваше имя и телефон"
            ]
            
            if any(phrase in reply_lower for phrase in contact_phrases):
                if session['stage'] != 'contact_collection':
                    session['stage'] = 'contact_collection'
                    print("📝 Переход к сбору контактов (по запросу AI)")
            
            # Если это первое сообщение - переходим в консультацию
            elif session['stage'] == 'needs_analysis':
                session['stage'] = 'consultation'
                print("💬 Переход к консультации")
                
            # Сохраняем ответы на вопросы если это не приветствие
            is_greeting_reply = "чем могу вам помочь" in reply_lower and "8-928" not in bot_reply
            if not is_greeting_reply and "questions_answered" in session:
                session['questions_answered'].append(user_message)
    
    # Если AI недоступен - используем упрощенную логику
    else:
        print("⚠️ AI недоступен, использую упрощенную логику")
        
        if session['stage'] == 'needs_analysis':
            # Используем простую логику для первого сообщения
            bot_reply = analyze_client_needs_simple(user_message, session)
            session['stage'] = 'consultation'
            
        elif session['stage'] == 'consultation':
            # Для сложных вопросов без AI
            bot_reply = "Извините, сервис временно недоступен. Пожалуйста, позвоните по телефону 8-928-458-32-88"
            
        elif session['stage'] == 'contact_collection':
            # Сбор контактов без AI
            bot_reply = handle_contact_collection(user_message, session)
            
        else:
            bot_reply = "Извините, возникла ошибка. Пожалуйста, позвоните нам."
    
    # ===== ОБРАБОТКА СОБРАННЫХ КОНТАКТОВ =====
    
    # Если собрали все контакты - отправляем в Telegram
    if session['stage'] == 'contact_collection' and session['name'] and session['phone']:
        print(f"📨 ОТПРАВЛЯЕМ ПОЛНУЮ ФАБУЛУ В TELEGRAM")
        full_text = "\n".join(session['text_parts'])
        success = send_complete_application_to_telegram(session, full_text)
        if success:
            session['telegram_sent'] = True
            session['stage'] = 'completed'
            bot_reply += "\n\n✅ Спасибо! Вся информация передана администратору. С вами свяжутся для подтверждения записи."
    
    # Этап 5: Завершено
    elif session['stage'] == 'completed':
        bot_reply = "Ваша заявка уже передана администратору. С вами свяжутся для подтверждения записи.\n\n📞 Телефон: 8-928-458-32-88\n📍 Адреса:\n   📍 Сочи: ул. Воровского, 22\n   📍 Адлер: ул. Кирова, д. 26а\n⏰ Ежедневно 10:00-20:00"
    
    # Логируем состояние сессии
    print(f"📊 СОСТОЯНИЕ СЕССИИ:")
    print(f"   Этап: {session['stage']}")
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
