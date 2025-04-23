from telethon.sync import TelegramClient

# Введи сюда свой номер телефона
phone = input("Введите номер телефона с +7: ")

# Пусто вместо api_id и api_hash — пусть Telethon сам запросит
client = TelegramClient("session_name", api_id=12345, api_hash="abc123")  # временно фиктивные

client.connect()

if not client.is_user_authorized():
    client.send_code_request(phone)
    code = input("Введи код из Telegram: ")
    client.sign_in(phone, code)

print("✅ Успешно авторизован!")