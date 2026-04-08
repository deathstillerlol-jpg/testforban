import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = "BOT_TOKEN"  # ← ВСТАВЬ СВОЙ ТОКЕН

bot = Bot(token=TOKEN)
dp = Dispatcher()

USERS_FILE = "users.txt"

# ===================== ЗАГРУЗКА / СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ =====================
def load_users() -> set:
    users = set()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    users.add(int(line))
        logging.info(f"Загружено пользователей из файла: {len(users)}")
    except FileNotFoundError:
        logging.info("Файл users.txt не найден, начинаем с пустого списка")
    except Exception as e:
        logging.error(f"Ошибка при загрузке пользователей: {e}")
    return users


def save_users(users: set):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for user_id in users:
                f.write(f"{user_id}\n")
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователей: {e}")


all_users = load_users()


# ===================== ХЕНДЛЕРЫ =====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    all_users.add(message.from_user.id)
    save_users(all_users)  # сохраняем сразу
    
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


# ===================== НАДЁЖНАЯ АВТОРАССЫЛКА =====================
async def broadcaster():
    await asyncio.sleep(10)  # пауза после запуска

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
            logging.info(f"[РАССЫЛКА] Начинаем... Пользователей: {len(all_users)}")
            
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
                        reply_markup=keyboard,
                        disable_notification=True
                    )
                    sent += 1
                    await asyncio.sleep(0.08)   # задержка
                except Exception:
                    all_users.discard(user_id)   # удаляем заблокированных

            save_users(all_users)  # сохраняем после каждой рассылки (на случай удалений)
            logging.info(f"[РАССЫЛКА] Завершена. Успешно отправлено: {sent} сообщений")

        except Exception as e:
            logging.error(f"[РАССЫЛКА] Критическая ошибка: {e}")

        await asyncio.sleep(60)   # ← Для теста = 60 секунд (каждую минуту)


# ===================== ТЕСТОВАЯ РАССЫЛКА =====================
@dp.message(Command("broadcast"))
async def manual_broadcast(message: Message):
    if not all_users:
        await message.answer("Нет пользователей для рассылки.")
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
    
    logging.info(f"Бот запущен | Пользователей в базе: {len(all_users)} | Авторассылка активна")

    # Запускаем рассылку
    broadcaster_task = asyncio.create_task(broadcaster())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка polling: {e}")
    finally:
        broadcaster_task.cancel()
        try:
            await broadcaster_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
