import asyncio
import logging
import json
import aiofiles
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Настройки
TELEGRAM_TOKEN = "7077073303:AAEq2WnUl6Eb-T7DtM9qDexf-9sx6EZQDqs"
EMAIL_ADDRESS = 'dbguin@gmail.com'
EMAIL_PASSWORD = 'your_email_password'
RECIPIENT_EMAIL = 'dbguin@gmail.com'
USERS_FILE = 'users.json'

import logging
import json
import aiofiles
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для отправки электронной почты
async def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, text)
    server.quit()

# Функция для загрузки пользователей из JSON-файла
async def load_users():
    try:
        async with aiofiles.open(USERS_FILE, 'r') as file:
            content = await file.read()
            return json.loads(content)
    except FileNotFoundError:
        return {}

# Функция для сохранения пользователей в JSON-файл
async def save_users(users):
    async with aiofiles.open(USERS_FILE, 'w') as file:
        await file.write(json.dumps(users, indent=4))

# Функция для регистрации нового пользователя
async def register_user(user_id, apartment):
    users = await load_users()
    users[user_id] = {'apartment': apartment}
    await save_users(users)

# Функция для проверки существующего пользователя
async def is_user_registered(user_id):
    users = await load_users()
    return user_id in users

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if await is_user_registered(user_id):
        apartment = (await load_users())[user_id]['apartment']
        await update.message.reply_text(f'Привет! Вы зарегистрированы в квартире {apartment}. Отправьте мне показания счетчиков горячей и холодной воды в формате: "Горячая: 123, Холодная: 456".')
    else:
        await update.message.reply_text('Привет! Пожалуйста, зарегистрируйтесь, отправив номер вашей квартиры в формате: "Квартира: 123".')

# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.message.from_user.id

    if not await is_user_registered(user_id):
        if 'Квартира:' in text:
            apartment = text.split('Квартира:')[1].strip()
            await register_user(user_id, apartment)
            await update.message.reply_text('Вы успешно зарегистрированы. Теперь вы можете отправлять показания счетчиков.')
        else:
            await update.message.reply_text('Пожалуйста, зарегистрируйтесь, отправив номер вашей квартиры в формате: "Квартира: 123".')
        return

    if 'Горячая:' in text and 'Холодная:' in text:
        hot_water = text.split('Горячая:')[1].split(',')[0].strip()
        cold_water = text.split('Холодная:')[1].strip()
        apartment = (await load_users())[user_id]['apartment']
        await send_email(f'Показания счетчиков воды для квартиры {apartment}', f'ID отправителя: {user_id}\nКвартира: {apartment}\nГорячая вода: {hot_water}\nХолодная вода: {cold_water}')
        await update.message.reply_text('Показания успешно отправлены на электронную почту.')
    else:
        await update.message.reply_text('Пожалуйста, используйте правильный формат: "Горячая: 123, Холодная: 456".')

# Функция для обработки ошибок
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error)

    await application.initialize()
    await application.start_polling()
    await application.idle()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


