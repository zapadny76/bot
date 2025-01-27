import os
import json
from dotenv import load_dotenv
import logging
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from datetime import datetime

load_dotenv()  # Загрузите переменные среды из файла .env

TOKEN = os.getenv("TOKEN")  # Используйте переменную среды TELEGRAM_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Путь к JSON-файлам
USERS_FILE = 'users.json'
METER_DATA_FILE = 'meter_data.json'

# Состояния разговора
REGISTER, RECORD_METER_DATA = range(2)

# Функция для загрузки данных из JSON-файла
def load_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Функция для сохранения данных в JSON-файл
def save_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    users = load_data(USERS_FILE)

    await update.message.reply_text(
        'Здравствуйте! Вас приветствует телеграмм бот ЖСК Западный для передачи показаний счетчиков воды.'
    )

    if str(user_id) in users:
        meter_data = load_data(METER_DATA_FILE)
        if str(user_id) in meter_data and meter_data[str(user_id)]:
            last_entry = meter_data[str(user_id)][-1]
            await update.message.reply_text(
                f'Предыдущие показания счетчиков:\n'
                f'Холодная вода: {last_entry["cold_water"]}\n'
                f'Горячая вода: {last_entry["hot_water"]}\n'
                f'Дата: {last_entry["date"]}'
            )

        await update.message.reply_text(
            f'Вы уже зарегистрированы с номером квартиры {users[str(user_id)]}. '
            'Теперь вы можете ввести данные по показаниям счетчиков воды. '
            'Отправьте данные в формате: "холодная_вода горячая_вода".'
        )
        return RECORD_METER_DATA
    else:
        await update.message.reply_html(
            rf"Hi {user.mention_html()}! Отправьте ваш номер квартиры для регистрации.",
            reply_markup=ForceReply(selective=True),
        )
        return REGISTER

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Register the user with their apartment number."""
    user_id = update.message.from_user.id
    apartment_number = update.message.text

    users = load_data(USERS_FILE)
    if str(user_id) in users:
        meter_data = load_data(METER_DATA_FILE)
        if str(user_id) in meter_data and meter_data[str(user_id)]:
            last_entry = meter_data[str(user_id)][-1]
            await update.message.reply_text(
                f'Предыдущие показания счетчиков:\n'
                f'Холодная вода: {last_entry["cold_water"]}\n'
                f'Горячая вода: {last_entry["hot_water"]}\n'
                f'Дата: {last_entry["date"]}'
            )

        await update.message.reply_text(
            f'Вы уже зарегистрированы с номером квартиры {users[str(user_id)]}. '
            'Теперь вы можете ввести данные по показаниям счетчиков воды. '
            'Отправьте данные в формате: "холодная_вода горячая_вода".'
        )
        return RECORD_METER_DATA
    else:
        users[str(user_id)] = apartment_number
        save_data(USERS_FILE, users)
        await update.message.reply_text(f'Вы успешно зарегистрированы с номером квартиры {apartment_number}.')
        await update.message.reply_text('Теперь вы можете ввести данные по показаниям счетчиков воды. Отправьте данные в формате: "холодная_вода горячая_вода".')
        return RECORD_METER_DATA

async def record_meter_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Record the meter data for the user."""
    user_id = update.message.from_user.id
    message_text = update.message.text

    users = load_data(USERS_FILE)
    if str(user_id) not in users:
        await update.message.reply_text('Вы не зарегистрированы. Пожалуйста, отправьте ваш номер квартиры для регистрации.')
        return REGISTER

    try:
        cold_water, hot_water = map(int, message_text.split())
    except ValueError:
        await update.message.reply_text('Пожалуйста, отправьте данные в формате: "холодная_вода горячая_вода". Показания должны быть только цифрами.')
        return RECORD_METER_DATA

    meter_data = load_data(METER_DATA_FILE)
    if str(user_id) in meter_data:
        last_entry = meter_data[str(user_id)][-1]
        if cold_water < last_entry["cold_water"] or hot_water < last_entry["hot_water"]:
            await update.message.reply_text('Введенные показания счетчиков должны быть больше или равны предыдущим показаниям. Пожалуйста, проверьте данные и попробуйте снова.')
            return RECORD_METER_DATA

    apartment_number = users[str(user_id)]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if str(user_id) not in meter_data:
        meter_data[str(user_id)] = []

    meter_data[str(user_id)].append({
        "apartment_number": apartment_number,
        "date": date,
        "cold_water": cold_water,
        "hot_water": hot_water
    })

    save_data(METER_DATA_FILE, meter_data)
    await update.message.reply_text(f'Данные по счетчикам воды успешно сохранены для квартиры {apartment_number} на {date}.')

    # Завершение сеанса работы с пользователем
    await update.message.reply_text('Спасибо за использование нашего бота!')
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register)],
            RECORD_METER_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, record_meter_data)],
        },
        fallbacks=[CommandHandler("help", help_command)],
        per_user=True,  # Устанавливаем per_user=True для отслеживания состояния для каждого пользователя
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
