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
