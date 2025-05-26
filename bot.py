import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from automation import run_once

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = "bot_state.json"

declare_manual_run = False

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump({"declare_manual_run": declare_manual_run}, f)

def load_state():
    global declare_manual_run
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            declare_manual_run = data.get("declare_manual_run", False)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Бот готов. Используйте /make чтобы запустить процесс вручную.")


@dp.message(Command("make"))
async def make_cmd(message: Message):
    global declare_manual_run
    declare_manual_run = True
    save_state()
    await message.answer("Цикл будет запущен в ближайшее время.")


@dp.message(Command("status"))
async def status_cmd(message: Message):
    await message.answer("Бот работает. Ожидаем следующий запуск.")


async def main_loop():
    load_state()
    while True:
        global declare_manual_run
        if declare_manual_run:
            await bot.send_message(CHAT_ID, "Запущен ручной цикл по команде /make")
            try:
                run_once()
                await bot.send_message(CHAT_ID, "Видео успешно загружено")
            except Exception as e:
                await bot.send_message(CHAT_ID, f"Ошибка в ручном цикле: {e}")
            declare_manual_run = False
            save_state()
        await asyncio.sleep(60)


async def run():
    loop_task = asyncio.create_task(main_loop())
    await dp.start_polling(bot)
    await loop_task


if __name__ == "__main__":
    asyncio.run(run())