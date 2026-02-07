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
        print("⚠️ Файл procedures.json не найден. Используем базовые данные.")
        return get_default_procedures()
    except json.JSONDecodeError:
        print("❌ Ошибка чтения procedures.json.")
        return get_default_procedures()
    except Exception as e:
        print(f"❌ Ошибка загрузки процедур: {str(e)}")
        return get_default_procedures()

def get_default_procedures():
    """Возвращает базовые данные если файл не найден."""
    return {
        "procedures": [],
        "clinic_info": {
            "address_sochi": "Сочи, ул. Воровского, 22",
            "address_adler": "Адлер, ул. Бестужева 1/1 ТЦ Мандарин, 1 этаж",
            "phone": "8-928-458-32-88",
            "hours": "Ежедневно 10:00–20:00",
            "no_installment": "Рассрочка и кредитование НЕ предоставляются"
        }
    }

def get_procedure_by_name(procedure_name: str):
    """
    Ищет процедуру по названию (частичное совпадение).
    """
    data = load_procedures()
    procedure_name_lower = procedure_name.lower()
    
    for procedure in data.get('procedures', []):
        if procedure_name_lower in procedure.get('name', '').lower():
            return procedure
    
    return None

def get_clinic_info():
    """
    Возвращает информацию о клинике.
    """
    data = load_procedures()
    return data.get('clinic_info', {})

def format_procedure_info(procedure):
    """
    Форматирует информацию о процедуре для вывода.
    """
    if not procedure:
        return "Информация о процедуре не найдена."
    
    result = f"📋 {procedure.get('name', 'Процедура')}\n"
    
    if 'locations' in procedure:
        result += "\n📍 Доступно в:\n"
        for location, lasers in procedure['locations'].items():
            result += f"  - {location.capitalize()}: {', '.join(lasers)}\n"
    
    if 'prices_hybrid' in procedure:
        result += "\n💰 Цены на гибридном лазере:\n"
        for zone, price in procedure['prices_hybrid'].items():
            result += f"  - {zone}: {price} руб.\n"
    
    if 'prices_alexandrite' in procedure:
        result += "\n💰 Цены на александритовом лазере:\n"
        for zone, price in procedure['prices_alexandrite'].items():
            result += f"  - {zone}: {price} руб.\n"
    
    if 'complexes' in procedure:
        result += "\n🎁 Выгодные комплексы:\n"
        for laser_type, complexes in procedure['complexes'].items():
            result += f"  {laser_type.capitalize()}:\n"
            for complex_item in complexes:
                result += f"    • {complex_item}\n"
    
    if 'course' in procedure:
        result += "\n📅 Курс процедур:\n"
        for laser_type, course_info in procedure['course'].items():
            result += f"  - {laser_type}: {course_info}\n"
    
    if 'types' in procedure:
        result += "\n📝 Виды процедур:\n"
        for type_item in procedure['types']:
            result += f"  - {type_item.get('name')}: {type_item.get('price')} руб.\n"
    
    if 'note' in procedure:
        result += f"\n💡 {procedure['note']}\n"
    
    return result

def search_procedures_by_keyword(keyword: str):
    """
    Ищет процедуры по ключевому слову.
    """
    data = load_procedures()
    keyword_lower = keyword.lower()
    results = []
    
    for procedure in data.get('procedures', []):
        procedure_name = procedure.get('name', '').lower()
        procedure_category = procedure.get('category', '').lower()
        
        if (keyword_lower in procedure_name or 
            keyword_lower in procedure_category or
            any(keyword_lower in str(value).lower() for value in procedure.values() if isinstance(value, str))):
            results.append(procedure)
    
    return results

# Тестовый вызов
if __name__ == "__main__":
    print("🧪 Тестируем загрузку процедур")
    
    procedures = load_procedures()
    clinic_info = get_clinic_info()
    
    print(f"\n🏥 Информация о клинике:")
    print(f"  📍 Сочи: {clinic_info.get('address_sochi')}")
    print(f"  📍 Адлер: {clinic_info.get('address_adler')}")
    print(f"  📞 Телефон: {clinic_info.get('phone')}")
    print(f"  ⏰ Часы работы: {clinic_info.get('hours')}")
    print(f"  💳 {clinic_info.get('no_installment')}")
    
    print(f"\n📋 Всего процедур: {len(procedures.get('procedures', []))}")
    
    # Тестируем поиск
    test_searches = ["эпиляция", "чистка", "тату"]
    for search in test_searches:
        found = search_procedures_by_keyword(search)
        print(f"\n🔍 Поиск '{search}': найдено {len(found)}")
        for proc in found[:2]:
            print(f"  - {proc.get('name')}")
