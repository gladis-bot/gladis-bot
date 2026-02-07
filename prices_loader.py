import json
import os

def load_procedures():
    """
    Загружает список процедур из data/procedures.json
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'data', 'procedures.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Загружено {len(data.get('procedures', []))} процедур")
        return data
        
    except FileNotFoundError:
        print("⚠️ Файл procedures.json не найден. Создайте его.")
        return {"procedures": []}
    except json.JSONDecodeError:
        print("❌ Ошибка чтения procedures.json. Проверьте формат файла.")
        return {"procedures": []}
    except Exception as e:
        print(f"❌ Ошибка загрузки процедур: {str(e)}")
        return {"procedures": []}

def get_procedure_info(procedure_name: str):
    """
    Возвращает информацию о конкретной процедуре.
    """
    data = load_procedures()
    
    for procedure in data.get('procedures', []):
        if procedure_name.lower() in procedure.get('name', '').lower():
            return procedure
    
    return None

def get_all_procedures():
    """
    Возвращает список всех процедур.
    """
    data = load_procedures()
    return data.get('procedures', [])

def get_procedures_by_category(category: str):
    """
    Возвращает процедуры по категории.
    """
    data = load_procedures()
    
    filtered = []
    for procedure in data.get('procedures', []):
        if procedure.get('category', '').lower() == category.lower():
            filtered.append(procedure)
    
    return filtered

def format_price(price: int) -> str:
    """
    Форматирует цену для вывода.
    """
    return f"{price:,} руб.".replace(',', ' ')

# Тестовый вызов
if __name__ == "__main__":
    print("🧪 Тестируем загрузку процедур")
    procedures = load_procedures()
    
    print(f"\n📋 Всего процедур: {len(procedures.get('procedures', []))}")
    
    for i, proc in enumerate(procedures.get('procedures', [])[:5], 1):
        print(f"{i}. {proc.get('name')} - {proc.get('price')} руб.")
