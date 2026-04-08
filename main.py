import asyncio
import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ===================== НАСТРОЙКИ =====================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# Важно! Bothost.ru сам даёт публичный URL. Обычно он выглядит так:
# https://твой-логин-бота.bothost.ru
# Замени ниже на свой реальный домен от bothost
BASE_WEBHOOK_URL = "http://nsk7.bothost.ru/api/webhooks/github"   # ← ИЗМЕНИ НА СВОЙ

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "users.db"


# ===================== БАЗА ДАННЫХ =====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()


def save_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_all_users() -> list[int]:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    conn.close()
    return users


init_db()


# ===================== ХЕНДЛЕРЫ =====================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    save_user(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ", url="https://t.me/sasha_teatr")
    ]])
    await message.answer(
        "Здравствуйте! Приветствуем вас! 👋\n"
        "Нажми кнопку ниже, чтобы перейти в диалог к менеджеру:",
        reply_markup=kb
    )


@dp.message()
async def any_message(message: Message):
    save_user(message.from_user.id)
    # await message.answer("Сообщение получено")  # можно раскомментировать


# ===================== АВТОРАССЫЛКА =====================
async def broadcaster():
    await asyncio.sleep(30)  # пауза после старта

    text = "Напоминание! 🔥\n\nБЫСТРЕЕ ПИШЕМ!\nПиши менеджеру прямо сейчас 👇"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ →", url="https://t.me/sasha_teatr")
    ]])

    while True:
        users = get_all_users()
        logging.info(f"Рассылка → найдено {len(users)} пользователей")

        sent = 0
        for user_id in users:
            try:
                await bot.send_message(
                    user_id, text, reply_markup=kb, disable_notification=True
                )
                sent += 1
                await asyncio.sleep(0.08)
            except Exception:
                pass  # игнорируем ошибки (заблокировал и т.д.)

        logging.info(f"Рассылка завершена: отправлено {sent}")

        await asyncio.sleep(20)   # ← Для теста 20 секунд. Потом поставь 1800 (30 мин) или 10800 (3 часа)


# ===================== ЗАПУСК WEBHOOK =====================
async def on_startup(bot: Bot):
    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True   # очищаем старые обновления
    )
    logging.info(f"Webhook успешно установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("Webhook удалён")


def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запускаем рассылку в фоне
    asyncio.create_task(broadcaster())

    # Настраиваем aiohttp приложение
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    logging.info("Бот запущен на Webhook (bothost.ru)")
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
