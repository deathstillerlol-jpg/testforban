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
        logging.info(f"Загружено {len(users)} пользователей из файла")
    except FileNotFoundError:
        logging.info("Файл users.txt не найден — начинаем с нуля")
    except Exception as e:
        logging.error(f"Ошибка загрузки пользователей: {e}")
    return users


def save_users(users: set):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for uid in sorted(users):
                f.write(f"{uid}\n")
    except Exception as e:
        logging.error(f"Ошибка сохранения пользователей: {e}")


all_users = load_users()


# ===================== ХЕНДЛЕРЫ =====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    all_users.add(message.from_user.id)
    save_users(all_users)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ", url="https://t.me/sasha_teatr")]]
    )
    
    await message.answer(
        "Здравствуйте! Приветствуем вас в сервисе для продажи пушкинских карт! 👋\n"
        "Нажми кнопку ниже, чтобы перейти в диалог к менеджеру:",
        reply_markup=keyboard
    )


@dp.message()
async def save_user(message: Message):
    if message.from_user.id not in all_users:
        all_users.add(message.from_user.id)
        save_users(all_users)


# ===================== АВТОРАССЫЛКА =====================
async def broadcaster():
    await asyncio.sleep(8)

    text = (
        "Напоминание! 🔥\n\n"
        "БЫСТРЕЕ ПИШЕМ!\n"
        "Пиши менеджеру прямо сейчас 👇"
    )
   
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text="НАПИСАТЬ МЕНЕДЖЕРУ ДЛЯ ПРОДАЖИ →", 
            url="https://t.me/sasha_teatr"
        )]]
    )

    while True:
        try:
            logging.info(f"[РАССЫЛКА] Запуск | Пользователей: {len(all_users)}")
            
            if not all_users:
                await asyncio.sleep(30)
                continue

            sent = 0
            for user_id in list(all_users):
                try:
                    await bot.send_message(
                        user_id,
                        text,
                        reply_markup=keyboard,
                        disable_notification=True
                    )
                    sent += 1
                    await asyncio.sleep(0.07)
                except Exception:
                    all_users.discard(user_id)

            save_users(all_users)
            logging.info(f"[РАССЫЛКА] Завершена → Отправлено: {sent}")

        except Exception as e:
            logging.error(f"[РАССЫЛКА] Неожиданная ошибка: {e}")

        await asyncio.sleep(60)   # ← Для теста оставь 60 (каждую минуту)


# ===================== ТЕСТОВАЯ РАССЫЛКА =====================
@dp.message(Command("broadcast"))
async def manual_broadcast(message: Message):
    if not all_users:
        await message.answer("Нет пользователей.")
        return

    text = "Тестовая рассылка! 🔥\nПиши менеджеру прямо сейчас 👇"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ →", url="https://t.me/sasha_teatr")]]
    )

    sent = 0
    for user_id in list(all_users):
        try:
            await bot.send_message(user_id, text, reply_markup=keyboard, disable_notification=True)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            all_users.discard(user_id)

    save_users(all_users)
    await message.answer(f"✅ Тестовая рассылка завершена!\nОтправлено: {sent}")


# ===================== ЗАПУСК =====================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info(f"Бот запущен | Пользователей в базе: {len(all_users)}")

    try:
        async with asyncio.TaskGroup() as tg:   # Python 3.11+
            tg.create_task(broadcaster())
            tg.create_task(dp.start_polling(bot))
    except* Exception as exc:
        logging.error(f"Ошибка в TaskGroup: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
