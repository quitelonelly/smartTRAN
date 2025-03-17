from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Основная клавиатура
reg_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Поделиться контактом', request_contact=True)]
    ],
    resize_keyboard=True
)
    
inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Зарегистрироваться", callback_data="register"),
        ]
    ]
)