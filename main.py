import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

TOKEN = "BOT_TOKEN"  # ← ВСТАВЬ СВОЙ ТОКЕН

bot = Bot(token=TOKEN)
dp = Dispatcher()

USERS_FILE = "users.txt"


def load_users() -> set:
    users = set()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().isdigit():
                    users.add(int(line.strip()))
        logging.info(f"Загружено пользователей: {len(users)}")
    except FileNotFoundError:
        logging.info("users.txt не найден")
    return users


def save_users(users: set):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for uid in sorted(users):
                f.write(f"{uid}\n")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}")


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


# ===================== ПРОСТАЯ АВТОРАССЫЛКА =====================
async def broadcaster():
    await asyncio.sleep(10)

    text = "Напоминание! 🔥\n\nБЫСТРЕЕ ПИШЕМ!\nПиши менеджеру прямо сейчас 👇"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ ДЛЯ ПРОДАЖИ →", url="https://t.me/sasha_teatr")
    ]])

    while True:
        logging.info(f"[РАССЫЛКА] Начинаем | Пользователей: {len(all_users)}")
        
        if not all_users:
            logging.info("[РАССЫЛКА] Нет пользователей")
            await asyncio.sleep(60)
            continue

        sent = 0
        for user_id in list(all_users):
            try:
                await bot.send_message(
                    user_id, text, reply_markup=kb, disable_notification=True
                )
                sent += 1
                await asyncio.sleep(0.08)
            except Exception:
                all_users.discard(user_id)

        save_users(all_users)
        logging.info(f"[РАССЫЛКА] Завершена | Отправлено: {sent}")

        await asyncio.sleep(180)   # ← Для теста поставь 60 (каждую минуту)


# ===================== ТЕСТОВАЯ РАССЫЛКА =====================
@dp.message(Command("broadcast"))
async def manual_broadcast(message: Message):
    if not all_users:
        await message.answer("Нет пользователей")
        return

    text = "Тестовая рассылка! 🔥\nПиши менеджеру прямо сейчас 👇"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ →", url="https://t.me/sasha_teatr")
    ]])

    sent = 0
    for user_id in list(all_users):
        try:
            await bot.send_message(user_id, text, reply_markup=kb, disable_notification=True)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            all_users.discard(user_id)

    save_users(all_users)
    await message.answer(f"✅ Отправлено: {sent}")


# ===================== ЗАПУСК =====================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info(f"Бот запущен | Пользователей: {len(all_users)}")

    # Запускаем рассылку в фоне
    task = asyncio.create_task(broadcaster())

    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Ошибка в polling: {e}")
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
