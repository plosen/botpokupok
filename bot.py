import telebot
from telebot import types
import logging
from database import initialize_db, add_item, remove_item, get_items, clear_items, add_reminder, get_due_reminders, remove_reminder, get_items_grouped
import csv
import io
import schedule
import time
import threading
from datetime import datetime

# Вставьте ваш токен, полученный от BotFather
TOKEN = '7677603819:AAFo0a_nbSAIMlAqwb5rhseaPT8GQLErhtA'

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Инициализируем базу данных
initialize_db()

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот для управления списком покупок. Вот, что я умею:\n"
        "/add [товар] [категория] - Добавить товар в список покупок с категорией.\n"
        "/list - Показать текущий список покупок.\n"
        "/remove [товар] - Удалить товар из списка.\n"
        "/clear - Очистить весь список покупок.\n"
        "/export - Экспортировать список покупок в CSV.\n"
        "/remind [товар] [YYYY-MM-DD HH:MM] - Установить напоминание о покупке товара в указанное время.\n"
        "/help - Показать это сообщение.\n\n"
        "Также вы можете использовать кнопки ниже для удобства."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📋 **Команды бота:**\n\n"
        "/add [товар] [категория] - Добавить товар в список покупок с категорией.\n"
        "/list - Показать текущий список покупок.\n"
        "/remove [товар] - Удалить товар из списка.\n"
        "/clear - Очистить весь список покупок.\n"
        "/export - Экспортировать список покупок в CSV.\n"
        "/remind [товар] [YYYY-MM-DD HH:MM] - Установить напоминание о покупке товара в указанное время.\n"
        "/help - Показать это сообщение."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Команда /add
@bot.message_handler(commands=['add'])
def add_command(message):
    user_id = message.from_user.id
    try:
        args = message.text.split(' ', 2)  # /add товар категория
        if len(args) >= 2:
            item = args[1].strip()
            category = args[2].strip() if len(args) == 3 else "Без категории"
            add_item(user_id, item, category)
            bot.reply_to(message, f"✅ Добавлено: {item} (Категория: {category})")
        else:
            bot.reply_to(message, "❌ Пожалуйста, укажите товар и категорию. Пример: /add Молоко Продукты")
    except Exception as e:
        logger.error(f"Error in add_command: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при добавлении товара.")

# Команда /list
@bot.message_handler(commands=['list'])
def list_command(message):
    user_id = message.from_user.id
    try:
        grouped_items = get_items_grouped(user_id)
        if grouped_items:
            response = "🛒 Ваш список покупок:\n"
            for category, items in grouped_items.items():
                response += f"\n📂 *{category}*\n"
                for item in items:
                    response += f" - {item}\n"
            bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, "Ваш список покупок пуст.", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Error in list_command: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при получении списка покупок.")

# Команда /remove
@bot.message_handler(commands=['remove'])
def remove_command(message):
    user_id = message.from_user.id
    try:
        args = message.text.split(' ', 1)  # /remove товар
        if len(args) == 2:
            item = args[1].strip()
            items = get_items(user_id)
            if item in items:
                remove_item(user_id, item)
                bot.reply_to(message, f"✅ Удалено: {item}")
            else:
                bot.reply_to(message, "❌ Такого товара нет в вашем списке.")
        else:
            bot.reply_to(message, "❌ Пожалуйста, укажите товар для удаления. Пример: /remove Молоко")
    except Exception as e:
        logger.error(f"Error in remove_command: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при удалении товара.")

# Команда /clear
@bot.message_handler(commands=['clear'])
def clear_command(message):
    user_id = message.from_user.id
    try:
        markup = types.InlineKeyboardMarkup()
        btn_yes = types.InlineKeyboardButton(text="Да", callback_data="confirm_clear_yes")
        btn_no = types.InlineKeyboardButton(text="Нет", callback_data="confirm_clear_no")
        markup.add(btn_yes, btn_no)
        bot.send_message(message.chat.id, "Вы уверены, что хотите очистить весь список покупок? 🗑", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in clear_command: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при попытке очистить список покупок.")

# Команда /export
@bot.message_handler(commands=['export'])
def export_command(message):
    user_id = message.from_user.id
    try:
        grouped_items = get_items_grouped(user_id)
        if grouped_items:
            # Создаем CSV в памяти
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Товар', 'Категория'])
            for category, items in grouped_items.items():
                for item in items:
                    writer.writerow([item, category])
            output.seek(0)
            # Отправляем файл
            bot.send_document(message.chat.id, ('shopping_list.csv', output))
        else:
            bot.send_message(message.chat.id, "Ваш список покупок пуст.", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Error in export_command: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при экспорте списка покупок.")

# Команда /remind
@bot.message_handler(commands=['remind'])
def remind_command(message):
    user_id = message.from_user.id
    try:
        args = message.text.split(' ', 2)  # /remind товар время
        if len(args) >= 3:
            item = args[1].strip()
            remind_at = args[2].strip()  # Ожидается формат 'YYYY-MM-DD HH:MM'
            # Проверка формата времени
            try:
                remind_time = datetime.strptime(remind_at, '%Y-%m-%d %H:%M')
                add_reminder(user_id, item, remind_at)
                bot.reply_to(message, f"✅ Напоминание установлено: {item} в {remind_at}")
            except ValueError:
                bot.reply_to(message, "❌ Неверный формат времени. Используйте 'YYYY-MM-DD HH:MM'. Пример: /remind Молоко 2025-12-31 10:00")
        else:
            bot.reply_to(message, "❌ Пожалуйста, укажите товар и время. Пример: /remind Молоко 2025-12-31 10:00")
    except Exception as e:
        logger.error(f"Error in remind_command: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при установке напоминания.")

# Обработка текстовых сообщений для добавления товара
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    text = message.text.lower()
    if text.startswith("добавь") or text.startswith("добавить"):
        parts = message.text.split(' ', 2)
        if len(parts) > 1:
            item = parts[1].strip()
            category = parts[2].strip() if len(parts) == 3 else "Без категории"
            add_item(message.from_user.id, item, category)
            bot.reply_to(message, f"✅ Добавлено: {item} (Категория: {category})")
        else:
            bot.reply_to(message, "❌ Пожалуйста, укажите товар и категорию. Пример: Добавь Молоко Продукты")
    else:
        bot.reply_to(message, "Я не понимаю эту команду. Используйте /help для списка доступных команд.")

# Главное меню с кнопками
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_add = types.KeyboardButton("/add")
    btn_list = types.KeyboardButton("/list")
    btn_remove = types.KeyboardButton("/remove")
    btn_clear = types.KeyboardButton("/clear")
    btn_export = types.KeyboardButton("/export")
    btn_remind = types.KeyboardButton("/remind")
    btn_help = types.KeyboardButton("/help")
    markup.add(btn_add, btn_list, btn_remove, btn_clear, btn_export, btn_remind, btn_help)
    return markup

# Обработка inline-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    data = call.data

    if data.startswith("remove_"):
        # Обработка удаления товара
        item = data.split("remove_", 1)[1]
        try:
            remove_item(user_id, item)
            bot.answer_callback_query(call.id, f"✅ Удалено: {item}")
            # Обновляем список после удаления
            grouped_items = get_items_grouped(user_id)
            if grouped_items:
                response = "🛒 Ваш список покупок:\n"
                for category, items in grouped_items.items():
                    response += f"\n📂 *{category}*\n"
                    for itm in items:
                        response += f" - {itm}\n"
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text=response,
                                      parse_mode='Markdown',
                                      reply_markup=main_menu())
            else:
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Ваш список покупок пуст.",
                                      reply_markup=main_menu())
        except Exception as e:
            logger.error(f"Error in callback_query remove: {e}")
            bot.answer_callback_query(call.id, "❌ Произошла ошибка при удалении товара.")

    elif data == "confirm_clear_yes":
        try:
            clear_items(user_id)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="🗑 Ваш список покупок очищен.",
                                  reply_markup=main_menu())
            bot.answer_callback_query(call.id, "✅ Список очищен.")
        except Exception as e:
            logger.error(f"Error in callback_query clear_yes: {e}")
            bot.answer_callback_query(call.id, "❌ Произошла ошибка при очистке списка.")
    elif data == "confirm_clear_no":
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="✅ Операция отменена.",
                              reply_markup=main_menu())
        bot.answer_callback_query(call.id, "Операция отменена.")

# Функция проверки напоминаний
def check_reminders():
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        due_reminders = get_due_reminders(current_time)
        for user_id, item in due_reminders:
            try:
                bot.send_message(user_id, f"⏰ Напоминание: Пора купить {item}!")
                # Удаляем напоминание после отправки
                remove_reminder(user_id, item, current_time)
            except Exception as e:
                logger.error(f"Error sending reminder to {user_id}: {e}")
        time.sleep(60)  # Проверяем каждую минуту

# Запуск потока для проверки напоминаний
def run_scheduler():
    scheduler_thread = threading.Thread(target=check_reminders)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Функция запуска бота
def main():
    run_scheduler()
    print("Бот запущен и работает...")
    bot.infinity_polling()

if __name__ == '__main__':
    main()
