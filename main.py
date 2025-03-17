import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers import reg_handlers

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = "7796843686:AAEXkFreLUqDNzUHIvPp1LmoeIu31kbXWf4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

reg_handlers(dp)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())