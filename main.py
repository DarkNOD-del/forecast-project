import os
import asyncio
from aiogram import Bot, Dispatcher

from app.config import TELEGRAM_TOKEN
from app.handlers import commands, states


async def main():
    os.system("cls || clear")

    bot = Bot(token = TELEGRAM_TOKEN)
    dp = Dispatcher()
    
    print("[BOT] Бот успешно запущен!")

    dp.include_router(commands.router)
    dp.include_router(states.router)

    await bot.delete_webhook(drop_pending_updates = True)
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())