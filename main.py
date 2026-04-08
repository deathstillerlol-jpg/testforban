import asyncio
import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "users.db"


# ===================== БАЗА ДАННЫХ =====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_users() -> list[int]:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


init_db()


# ===================== ХЕНДЛЕРЫ =====================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    save_user(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ", url="https://t.me/sasha_teatr")
    ]])
    await message.answer(
        "Здравствуйте! Приветствуем вас! 👋\n"
        "Нажми кнопку ниже, чтобы перейти в диалог к менеджеру:",
        reply_markup=keyboard
    )


@dp.message()
async def echo(message: Message):
    save_user(message.from_user.id)   # сохраняем даже если не /start
    await message.answer(f"Ты написал: {message.text}")


# ===================== РАССЫЛКА =====================
async def broadcaster():
    await asyncio.sleep(30)  # пауза после запуска

    text = "Напоминание! 🔥\nБЫСТРЕЕ ПИШЕМ!\nПиши менеджеру прямо сейчас 👇"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ →", url="https://t.me/sasha_teatr")
    ]])

    while True:
        users = get_all_users()
        logging.info(f"Рассылка → найдено {len(users)} пользователей")

        sent = 0
        blocked = 0

        for user_id in users:
            try:
                await bot.send_message(
                    user_id, text, reply_markup=keyboard, disable_notification=True
                )
                sent += 1
                await asyncio.sleep(0.07)
            except Exception as e:
                err = str(e).lower()
                if "blocked" in err or "forbidden" in err or "chat not found" in err:
                    blocked += 1
                else:
                    logging.warning(f"Ошибка у {user_id}: {e}")

        logging.info(f"Рассылка завершена: отправлено {sent}, заблокировали {blocked}")

        await asyncio.sleep(20)  # 3 часа


# ===================== ЗАПУСК =====================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    asyncio.create_task(broadcaster())

    logging.info("Бот запущен • polling + рассылка каждые 3 часа (bothost.ru)")

    # Важно для bothost.ru и хостингов с SIGTERM
    await dp.start_polling(bot, handle_signals=False)


if __name__ == "__main__":
    asyncio.run(main())
