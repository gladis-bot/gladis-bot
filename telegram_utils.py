from typing import Dict, Any
from datetime import datetime
import os
import requests

def send_to_telegram(text: str, name: str = None, phone: str = None):
    """
    Отправляет сообщение в Telegram.
    """
    try:
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@sochigladisbot")
        
        if not TELEGRAM_BOT_TOKEN:
            print("⚠️ TELEGRAM_BOT_TOKEN не настроен, сообщение не отправлено")
            print(f"📝 Текст сообщения: {text[:200]}...")
            return False
        
        # Формируем URL для отправки
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # Добавляем контакты в сообщение если они есть
        full_text = text
        if name or phone:
            full_text += f"\n\n📋 КОНТАКТЫ:\n"
            if name:
                full_text += f"👤 Имя: {name}\n"
            if phone:
                full_text += f"📞 Телефон: {phone}\n"
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": full_text,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Сообщение отправлено в Telegram")
            return True
        else:
            print(f"❌ Ошибка Telegram API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {str(e)}")
        return False

def send_incomplete_to_telegram(full_text: str, name: str = None, phone: str = None, procedure: str = None):
    """
    Отправляет неполную заявку по таймауту.
    """
    try:
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            print("⚠️ Telegram не настроен, неполная заявка не отправлена")
            return False
        
        telegram_text = f"⚠️ НЕПОЛНАЯ ЗАЯВКА (таймаут 10 минут)\n\n"
        
        if name:
            telegram_text += f"👤 Имя: {name}\n"
        else:
            telegram_text += f"👤 Имя: Не указано\n"
            
        if phone:
            telegram_text += f"📞 Телефон: {phone}\n"
        else:
            telegram_text += f"📞 Телефон: Не указан\n"
            
        if procedure:
            telegram_text += f"💉 Интересовалась процедурой: {procedure}\n"
            
        telegram_text += f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        telegram_text += f"💬 Часть диалога:\n{full_text[:1000]}..."
        
        return send_to_telegram(telegram_text, name, phone)
        
    except Exception as e:
        print(f"❌ Ошибка при отправке неполной заявки: {str(e)}")
        return False

def send_complete_application_to_telegram(session: Dict[str, Any], full_conversation: str):
    """
    Отправляет полную фабулу диалога в Telegram.
    Включает все детали, собранные ботом.
    """
    try:
        print(f"\n📨 ОТПРАВКА ПОЛНОЙ ФАБУЛЫ В TELEGRAM")
        print(f"   👤 Имя: {session.get('name')}")
        print(f"   📞 Телефон: {session.get('phone')}")
        
        # Формируем детализированное сообщение
        telegram_text = f"🚨 ПОЛНАЯ ЗАЯВКА С КОНСУЛЬТАЦИЕЙ\n\n"
        
        # Основная информация
        telegram_text += f"👤 КЛИЕНТ: {session.get('name', 'Не указано')}\n"
        telegram_text += f"📞 ТЕЛЕФОН: {session.get('phone', 'Не указан')}\n"
        telegram_text += f"⏰ ВРЕМЯ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Информация о процедуре
        if session.get('procedure_category'):
            telegram_text += f"📋 КАТЕГОРИЯ ПРОЦЕДУРЫ: {session['procedure_category']}\n"
        
        if session.get('procedure_type'):
            telegram_text += f"💉 ВЫБРАННАЯ ПРОЦЕДУРА: {session['procedure_type']}\n"
        
        if session.get('zone'):
            telegram_text += f"📍 ЗОНА: {session['zone']}\n"
        
        if session.get('laser_type'):
            telegram_text += f"🔬 ТИП ЛАЗЕРА: {session['laser_type']}\n"
        
        if session.get('location'):
            telegram_text += f"🏥 КЛИНИКА: {session['location']}\n"
        
        if session.get('skin_type'):
            telegram_text += f"📝 ТИП КОЖИ: {session['skin_type']}\n"
        
        if session.get('skin_problems'):
            telegram_text += f"🔍 ПРОБЛЕМЫ КОЖИ: {', '.join(session['skin_problems'])}\n"
        
        if session.get('zones'):
            telegram_text += f"🎯 ЗОНЫ ДЛЯ ПРОЦЕДУРЫ: {', '.join(session['zones'])}\n"
        
        # Ответы на вопросы
        if session.get('questions_answered'):
            telegram_text += f"\n📝 ОТВЕТЫ КЛИЕНТА НА ВОПРОСЫ:\n"
            for i, answer in enumerate(session['questions_answered'], 1):
                telegram_text += f"{i}. {answer}\n"
        
        telegram_text += f"\n💬 ПОЛНЫЙ ДИАЛОГ:\n{full_conversation}\n\n"
        telegram_text += f"🔗 ИСТОЧНИК: чат-бот сайта gladissochi.ru"
        
        # Отправляем через существующую функцию
        return send_to_telegram(telegram_text, session.get('name'), session.get('phone'))
        
    except Exception as e:
        print(f"❌ Ошибка при отправке полной заявки: {str(e)}")
        return False
