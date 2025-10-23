import json
from datetime import datetime

FAQ_FILE = "faq_data.json"

# Загрузка базы FAQ
def load_faq():
    try:
        with open(FAQ_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение базы FAQ
def save_faq(faq):
    with open(FAQ_FILE, "w", encoding="utf-8") as f:
        json.dump(faq, f, ensure_ascii=False, indent=2)

# Обработка сообщения пользователя
def bot_respond(message):
    faq = load_faq()
    for question, answer in faq.items():
        if question.lower() in message.lower():
            return answer
    # Если вопрос неизвестен, отправляем оператору
    return "Ваш вопрос передан оператору."
    
# Добавление нового вопроса в базу (самообучение)
def add_faq(question, answer):
    faq = load_faq()
    faq[question] = answer
    save_faq(faq)
