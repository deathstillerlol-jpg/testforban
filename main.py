import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

TOKEN = "BOT_TOKEN"  # ← ВСТАВЬ СВОЙ ТОКЕН

bot = Bot(token=TOKEN)
dp = Dispatcher()

USERS_FILE = "users.txt"


def load_users():
    users = set()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().isdigit():
                    users.add(int(line.strip()))
        logging.info(f"Загружено пользователей: {len(users)}")
    except FileNotFoundError:
        logging.info("users.txt не найден — пустой список")
    return users


def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for uid in sorted(users):
                f.write(f"{uid}\n")
    except Exception as e:
        logging.error(f"Ошибка сохранения файла: {e}")


all_users = load_users()


# ===================== ХЕНДЛЕРЫ =====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    all_users.add(message.from_user.id)
    save_users(all_users)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ", url="https://t.me/sasha_teatr")
    ]])
    
    await message.answer(
        "Здравствуйте! Приветствуем вас в сервисе для продажи пушкинских карт! 👋\n"
        "Нажми кнопку ниже, чтобы перейти в диалог к менеджеру:",
        reply_markup=kb
    )


@dp.message()
async def save_user(message: Message):
    if message.from_user.id not in all_users:
        all_users.add(message.from_user.id)
        save_users(all_users)


# ===================== АВТОРАССЫЛКА =====================
async def broadcaster():
    await asyncio.sleep(10)  # пауза после старта

    text = "Напоминание! 🔥\n\nБЫСТРЕЕ ПИШЕМ!\nПиши менеджеру прямо сейчас 👇"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ ДЛЯ ПРОДАЖИ →", url="https://t.me/sasha_teatr")
    ]])

    while True:
        logging.info(f"[РАССЫЛКА] === НАЧИНАЕМ ЦИКЛ === Пользователей: {len(all_users)}")

        if not all_users:
            logging.info("[РАССЫЛКА] Нет пользователей, ждём...")
            await asyncio.sleep(30)
            continue

        sent = 0
        for user_id in list(all_users):
            try:
                await bot.send_message(
                    user_id, 
                    text, 
                    reply_markup=kb, 
                    disable_notification=True
                )
                sent += 1
                await asyncio.sleep(0.07)
            except Exception as e:
                logging.info(f"[РАССЫЛКА] Пользователь {user_id} удалён (ошибка)")
                all_users.discard(user_id)

        save_users(all_users)
        logging.info(f"[РАССЫЛКА] === ЦИКЛ ЗАВЕРШЁН === Отправлено: {sent}")

        await asyncio.sleep(60)   # ← ДЛЯ ТЕСТА = 60 секунд. Потом поменяй на 1800 или 10800


# ===================== ЗАПУСК =====================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен | Авторассылка активна")

    # Запускаем рассылку в фоне
    broadcaster_task = asyncio.create_task(broadcaster())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка в polling: {e}")
    finally:
        broadcaster_task.cancel()
        try:
            await broadcaster_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
