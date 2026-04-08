import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = "BOT_TOKEN"  # ← ОБЯЗАТЕЛЬНО ВСТАВЬ СВОЙ ТОКЕН

bot = Bot(token=TOKEN)
dp = Dispatcher()

all_users = set()


# ===================== ХЕНДЛЕРЫ =====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    all_users.add(message.from_user.id)
    
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
    all_users.add(message.from_user.id)


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
            logging.info(f"Начинаем рассылку | Пользователей: {len(all_users)}")
            
            if not all_users:
                logging.info("Пользователей нет, ждём...")
                await asyncio.sleep(60)
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
                    await asyncio.sleep(0.08)   # задержка между сообщениями
                except Exception as e:
                    # Тихо удаляем заблокированных пользователей
                    all_users.discard(user_id)
                    logging.debug(f"Пользователь {user_id} удалён из списка (ошибка: {e})")

            logging.info(f"Рассылка завершена. Успешно отправлено: {sent} сообщений")

        except Exception as e:
            logging.error(f"Критическая ошибка в broadcaster: {e}")
            await asyncio.sleep(10)  # если что-то сломалось — не падаем сразу

        # === ВРЕМЯ МЕЖДУ РАССЫЛКАМИ ===
        await asyncio.sleep(60)   # ← для теста оставь 60 (каждую минуту)
        # После теста поменяй на 1800 (30 минут) или 10800 (3 часа)


# ===================== ТЕСТОВАЯ РАССЫЛКА =====================
@dp.message(Command("broadcast"))
async def manual_broadcast(message: Message):
    if not all_users:
        await message.answer("Пока нет пользователей.")
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
   
    await message.answer(f"✅ Тестовая рассылка завершена!\nОтправлено: {sent}")


# ===================== ЗАПУСК =====================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем рассылку как отдельную задачу
    asyncio.create_task(broadcaster())
    
    logging.info("Бот успешно запущен | Авторассылка активна")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
