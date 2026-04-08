import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = "ТОКЕН_БОТА_СЮДА"   # ← ВСТАВЬ СВОЙ ТОКЕН

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
    """Сохраняем всех, кто пишет боту"""
    all_users.add(message.from_user.id)


# ===================== КОМАНДА ДЛЯ ТЕСТА =====================

@dp.message(Command("broadcast"))
async def manual_broadcast(message: Message):
    """Принудительная рассылка по команде /broadcast (для теста)"""
    if not all_users:
        await message.answer("Пока нет пользователей для рассылки.")
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
        except Exception:
            all_users.discard(user_id)
    
    await message.answer(f"✅ Тестовая рассылка завершена!\nОтправлено: {sent} сообщений")


# ===================== АВТОРАССЫЛКА =====================

async def broadcaster():
    await asyncio.sleep(10)  # небольшая пауза после запуска
    
    text = (
        "Напоминание! 🔥\n\n"
        "БЫСТРЕЕ ПИШЕМ!\n"
        "Пиши менеджеру прямо сейчас 👇"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ ДЛЯ ПРОДАЖИ →", url="https://t.me/sasha_teatr")]]
    )
    
    while True:
        logging.info(f"Авторассылка запущена | Пользователей: {len(all_users)}")
        
        if not all_users:
            logging.info("Нет пользователей для рассылки")
            await asyncio.sleep(60)
            continue
        
        sent = 0
        blocked = 0
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
            except Exception as e:
                blocked += 1
                all_users.discard(user_id)
        
        logging.info(f"Рассылка завершена → Отправлено: {sent} | Заблокировано/ошибок: {blocked}")
        
        await asyncio.sleep(1800)   # ← Каждые 30 минут (для теста). Потом поставишь 10800 (3 часа)


# ===================== ЗАПУСК =====================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    
    asyncio.create_task(broadcaster())   # Запускаем рассылку
    
    logging.info("Бот запущен | Авторассылка активна")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
