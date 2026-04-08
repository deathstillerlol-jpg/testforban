import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

TOKEN = "BOT_TOKEN"  # ← ВСТАВЬ ТОКЕН

bot = Bot(token=TOKEN)
dp = Dispatcher()

all_users = set()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    all_users.add(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ", url="https://t.me/sasha_teatr")]])
    await message.answer("Здравствуйте! 👋", reply_markup=kb)


@dp.message()
async def any_message(message: Message):
    all_users.add(message.from_user.id)


async def broadcaster():
    await asyncio.sleep(10)

    text = "Напоминание! 🔥\n\nБЫСТРЕЕ ПИШЕМ!\nПиши менеджеру прямо сейчас 👇"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="НАПИСАТЬ МЕНЕДЖЕРУ →", url="https://t.me/sasha_teatr")]])

    while True:
        logging.info(f"[РАССЫЛКА] НАЧИНАЕМ — пользователей: {len(all_users)}")
        
        sent = 0
        for user_id in list(all_users):
            try:
                await bot.send_message(user_id, text, reply_markup=kb, disable_notification=True)
                sent += 1
                await asyncio.sleep(0.1)
            except:
                all_users.discard(user_id)

        logging.info(f"[РАССЫЛКА] ЗАВЕРШЕНО — отправлено: {sent}")
        await asyncio.sleep(60)  # для теста — каждую минуту


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("БОТ ЗАПУЩЕН — ПРОСТАЯ РАССЫЛКА")

    asyncio.create_task(broadcaster())

    await dp.start_polling(bot, handle_signals=False)  # важно: отключаем обработку сигналов aiogram


if __name__ == "__main__":
    asyncio.run(main())
