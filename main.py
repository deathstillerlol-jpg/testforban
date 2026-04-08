# main.py
import asyncio
import logging
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "users.db"


# ── Инициализация базы данных ───────────────────────────────────────────
def init_db():
    """Создаёт таблицу с дополнительными полями"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_user(user_id: int, username: str | None, full_name: str):
    """Сохраняет или обновляет информацию о пользователе"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
        """, (user_id, username, full_name))
        conn.commit()
        logging.info(f"Пользователь сохранён/обновлён: {user_id} (@{username})")
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя {user_id}: {e}")
    finally:
        conn.close()


def get_all_users() -> list[int]:
    """Возвращает список всех user_id"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка чтения пользователей: {e}")
        return []
    finally:
        conn.close()


# ── Инициализируем базу при старте ──────────────────────────────────────
init_db()


# ── Хендлеры ─────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    user_id = user.id
    username = user.username          # может быть None
    full_name = user.full_name or "Без имени"

    save_user(user_id, username, full_name)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="НАПИСАТЬ МЕНЕДЖЕРУ",
                    url="https://t.me/sasha_teatr"
                )
            ]
        ]
    )

    await message.answer(
        "Здравствуйте! Приветствуем вас в сервисе для продажи пушкинских карт! 👋\n"
        "Нажми кнопку ниже, чтобы перейти в диалог к менеджеру:",
        reply_markup=keyboard
    )


@dp.message()
async def echo(message: Message):
    await message.answer(f"Ты написал: {message.text}")


# ── Рассылка каждые 3 часа ──────────────────────────────────────────────
async def broadcaster():
    await asyncio.sleep(30)  # даём боту нормально запуститься

    text = (
        "Напоминание! 🔥\n"
        "БЫСТРЕЕ ПИШЕМ!\n"
        "Пиши менеджеру прямо сейчас 👇"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="НАПИСАТЬ МЕНЕДЖЕРУ ДЛЯ ПРОДАЖИ →",
                    url="https://t.me/sasha_teatr"
                )
            ]
        ]
    )

    while True:
        users = get_all_users()
        logging.info(f"Рассылка → найдено {len(users)} пользователей")

        sent_count = 0
        blocked_count = 0

        for user_id in users:
            try:
                await bot.send_message(
                    user_id,
                    text,
                    reply_markup=keyboard,
                    disable_notification=True
                )
                sent_count += 1
                await asyncio.sleep(0.07)  # безопасный лимит
            except Exception as e:
                err_str = str(e).lower()
                if "blocked" in err_str or "forbidden" in err_str or "chat not found" in err_str:
                    blocked_count += 1
                    logging.warning(f"Пользователь {user_id} заблокировал бота или удалил чат")
                    # При желании можно удалять из базы:
                    # delete_user(user_id)
                else:
                    logging.warning(f"Не удалось отправить {user_id}: {e}")

        logging.info(f"Рассылка завершена: отправлено {sent_count}, заблокировали {blocked_count}")
        await asyncio.sleep(3 * 3600)  # 3 часа


# ── Запуск ───────────────────────────────────────────────────────────────
async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем рассылку в фоне
    asyncio.create_task(broadcaster())

    logging.info("Бот запущен • polling + рассылка каждые 3 часа (SQLite)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
