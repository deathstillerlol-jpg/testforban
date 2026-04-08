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
# ===================== РАССЫЛКА (замени свою функцию broadcaster) =====================
async def broadcaster():
    await asyncio.sleep(20)  # пауза после старта

    text = (
        "Напоминание! 🔥\n"
        "БЫСТРЕЕ ПИШЕМ!\n"
        "Пиши менеджеру прямо сейчас 👇"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ →", url="https://t.me/sasha_teatr")
        ]]
    )

    while True:
        try:
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
                    await asyncio.sleep(0.08)
                except Exception as e:
                    err = str(e).lower()
                    if any(x in err for x in ["blocked", "forbidden", "chat not found"]):
                        blocked += 1
                    logging.warning(f"Ошибка отправки {user_id}: {e}")

            logging.info(f"Рассылка завершена: отправлено {sent}, заблокировали {blocked}")

        except Exception as e:
            logging.error(f"Ошибка в broadcaster: {e}")

        # Для теста — 20 секунд. Когда заработает, поставь 1800 (30 мин) или 10800 (3 часа)
        await asyncio.sleep(20)


# ===================== ЗАПУСК (замени свою функцию main) =====================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем рассылку
    asyncio.create_task(broadcaster())

    logging.info("Бот запущен • polling + рассылка (bothost.ru)")

    # Критично для bothost.ru
    await dp.start_polling(bot, handle_signals=False)


if __name__ == "__main__":
    asyncio.run(main())
