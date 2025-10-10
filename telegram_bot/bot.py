import json
from logger import logger
import asyncio
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.enums import ParseMode, ChatAction
from aiogram.types import Message, CallbackQuery, ChatJoinRequest, FSInputFile, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from spam_protection import AntiSpamMiddleware
from datetime import datetime
from aiogram.utils.markdown import hcode
from scheduler import start_scheduler 


# === Загрузка переменных из .env ===
load_dotenv('.env')
TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
ADMINS = os.getenv("ADMINS")

# === Проверка обязательных переменных окружения ===
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в .env файле")
if not PRIVATE_CHANNEL_ID:
    raise ValueError("❌ PRIVATE_CHANNEL_ID не установлен в .env файле")
if not ADMINS:
    raise ValueError("❌ ADMINS не установлен в .env файле")

# === Инициализация бота ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())


with open("files/random_messages.json", encoding="utf-8") as f:
    fallback_replies = json.load(f)


async def send_service_message(bot: Bot, text: str):
    if PRIVATE_CHANNEL_ID:
        await bot.send_message(PRIVATE_CHANNEL_ID, text)


async def welcome_user(user_id: int):
    # 1. Приветствие с картинкой
    photo_path = FSInputFile("files/welcome.png")
    welcome_message = """
        <b>Добро пожаловать в D-space.</b>

Бесплатная обучающая платформа от экосистемы dept. Здесь представлены курсы для заработка вместе с нами. 

<b>Доступно всем по кнопке ниже:</b>
        """
    # Инлайн-кнопка для открытия веб‑приложения, прикрепленного к боту
    kb = InlineKeyboardBuilder()
    kb.button(text="Открыть приложение", url="https://t.me/dept_mainbot/dspace")
    kb.adjust(1)

    await bot.send_photo(user_id, photo_path, caption=welcome_message, reply_markup=kb.as_markup())


# === Старт ===
@dp.message(F.chat.type == "private", CommandStart())
async def start_handler(message: Message, state: FSMContext, command: CommandObject):
    if not message.from_user:
        logger.warning("⚠️ Получено сообщение без информации о пользователе")
        return
   
    user = message.from_user
    logger.info(f"{user.full_name} нажал start")
    
    # Обработка диплинков (/start <payload>)
    if command and command.args:
        logger.info(f"Получен диплинк payload: {command.args}")
    await welcome_user(user.id)
     # Формирование информации о пользователе для логирования
    username = f"@{user.username}" if user.username else "без username"
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    await send_service_message(bot, f"👤 Пользователь @{user.username} {user.first_name} {user.last_name} нажал /start в боте")


@dp.message(F.chat.type == "private")
async def fallback_handler(message: Message):
    if not message.from_user:
        return
    
    reply = random.choice(fallback_replies)
    logger.info(f"Заглушка: {message.from_user.full_name} написал: {message.text}")
    await message.answer(reply)


# === Запуск ===
async def main():
    logger.info("Бот запущен")
    if ADMINS:
        try:
            admin_id = int(ADMINS)
            await bot.send_message(admin_id, text="🤖 Бот запущен")
        except ValueError:
            logger.error(f"❌ Неверный формат ADMINS: {ADMINS}")


    # Регистрируем антиспам
    dp.message.middleware(AntiSpamMiddleware(bot))
    dp.callback_query.middleware(AntiSpamMiddleware(bot))


    scheduler_task = asyncio.create_task(start_scheduler(bot))
    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        scheduler_task.cancel()
        if ADMINS:
            try:
                admin_id = int(ADMINS)
                await bot.send_message(admin_id, text="🤖 Бот остановлен")
            except ValueError:
                logger.error(f"❌ Неверный формат ADMINS: {ADMINS}")


if __name__ == "__main__":
    asyncio.run(main())