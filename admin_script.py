import json
import os

def load_admin_script():
    """
    Загружает скрипт администратора из data/admin_script.json
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'data', 'admin_script.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Загружен скрипт администратора")
        return data
        
    except FileNotFoundError:
        print("⚠️ Файл admin_script.json не найден.")
        return {}
    except json.JSONDecodeError:
        print("❌ Ошибка чтения admin_script.json.")
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки скрипта: {str(e)}")
        return {}

def get_greeting():
    """
    Возвращает случайное приветствие.
    """
    script = load_admin_script()
    greetings = script.get('greetings', [])
    
    if greetings:
        import random
        return random.choice(greetings)
    else:
        return "Здравствуйте! Я менеджер клиники GLADIS. Чем могу помочь?"

def get_answer_for_question(question: str):
    """
    Ищет ответ на частый вопрос.
    """
    script = load_admin_script()
    faq = script.get('frequent_questions', [])
    
    question_lower = question.lower()
    
    for item in faq:
        if item.get('question', '').lower() in question_lower:
            return item.get('answer')
    
    return None

def get_closing_phrase():
    """
    Возвращает случайную завершающую фразу.
    """
    script = load_admin_script()
    closings = script.get('closing_phrases', [])
    
    if closings:
        import random
        return random.choice(closings)
    else:
        return "Буду рада видеть вас в нашей клинике!"

def get_all_questions():
    """
    Возвращает список всех частых вопросов.
    """
    script = load_admin_script()
    return [item.get('question') for item in script.get('frequent_questions', [])]

# Тестовый вызов
if __name__ == "__main__":
    print("🧪 Тестируем скрипт администратора")
    
    print(f"\n📝 Приветствие: {get_greeting()}")
    
    questions = get_all_questions()
    print(f"\n❓ Частые вопросы ({len(questions)}):")
    for q in questions[:5]:
        print(f"  - {q}")
    
    print(f"\n👋 Завершающая фраза: {get_closing_phrase()}")
