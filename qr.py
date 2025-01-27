import qrcode

# Замените 'your_bot_token' на токен вашего Telegram-бота
bot_token = "7077073303:AAEq2WnUl6Eb-T7DtM9qDexf-9sx6EZQDqs"

# Создаем ссылку для Telegram-бота
bot_link = f'https://t.me/{bot_token}'

# Создаем объект QRCode
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

# Добавляем данные в QR-код
qr.add_data(bot_link)
qr.make(fit=True)

# Создаем изображение QR-кода
img = qr.make_image(fill_color="black", back_color="white")

# Сохраняем изображение в файл
img.save("telegram_bot_qr.png")
