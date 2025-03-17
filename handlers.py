import os
from dotenv import load_dotenv
import gspread
from pathlib import Path
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import reg_kb, inline_kb

# ID админа
ADMIN_ID = 894963514

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = "7796843686:AAEXkFreLUqDNzUHIvPp1LmoeIu31kbXWf4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_telegram_id_by_company_id(sheet, company_id):
    """
    Ищет Telegram ID по ID компании в Google Sheets.
    """
    try:
        # Получаем все данные из таблицы
        all_values = sheet.get_all_values()
        
        # Ищем строку с нужным ID компании
        for row in all_values:
            if row[0] == str(company_id):  # ID компании в первом столбце
                return row[1]  # Telegram ID во втором столбце
        
        # Если ID компании не найден
        return None
    except Exception as e:
        print(f"Ошибка при поиске Telegram ID: {e}")
        return None

# Настройка Google Sheets API
def setup_google_sheets(sheet_index=0):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "/home/klim-petrov/projects/tgbot/credentials.json", scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1CoDQJn0T_scUV7ZsbYU8x2nZTzu_F9CBrculeQIG2KA").get_worksheet(sheet_index)
    return sheet

# Функция для получения следующего ID
def get_next_id(sheet):
    try:
        ids = sheet.col_values(1)
        if len(ids) > 1:
            last_id = int(ids[-1])
            return last_id + 1
        else:
            return 1
    except Exception as e:
        print(f"Ошибка при получении ID: {e}")
        return 1

# Функция для обновления листа конверсии
def update_conversion_sheet(sheet, argument, column_name):
    try:
        all_values = sheet.get_all_values()
        
        # Ищем строку с нужным аргументом
        for i, row in enumerate(all_values):
            if row[0] == argument:
                # Находим индекс столбца по его названию
                column_index = all_values[0].index(column_name)
                current_value = int(row[column_index]) if row[column_index] else 0
                sheet.update_cell(i + 1, column_index + 1, current_value + 1)
                return
        
        # Если строка с таким аргументом не найдена, создаем новую
        new_row = [argument] + [0] * (len(all_values[0]) - 1)
        column_index = all_values[0].index(column_name)
        new_row[column_index] = 1
        sheet.append_row(new_row)
    except Exception as e:
        print(f"Ошибка при обновлении листа конверсии: {e}")

# Состояния для FSM
class Form(StatesGroup):
    waiting_for_contact = State()
    waiting_for_business_info = State()

# Обработка команды /start с аргументом
async def cmd_start(message: types.Message, command: Command, state: FSMContext):
    args = command.args
    
    if args:
        try:
            await message.answer(
                "https://rutube.ru/video/3a0ee47db8e2e0f8a75001fbe618fdd3/", 
                parse_mode="HTML", 
                reply_markup=inline_kb
            )

            sheet = setup_google_sheets()
            next_id = get_next_id(sheet)
            sheet.append_row([next_id, message.from_user.id, args])

            conversion_sheet = setup_google_sheets(1)
            update_conversion_sheet(conversion_sheet, args, "start_clicked")

            # Сохраняем аргумент в состоянии
            await state.update_data(argument=args)
            await state.set_state(Form.waiting_for_contact)
        except Exception as e:
            print(f"Ошибка в cmd_start: {e}")  # Вывод ошибки в консоль
            await message.answer(f"Ошибка при записи в таблицу", parse_mode="HTML")
    else:
        await message.answer("Ты не передал аргумент.", parse_mode="HTML")

# Обработка кнопки "Зарегистрироваться"
async def process_registration_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Чтобы получить тестовый доступ, поделитесь контактом.", 
        reply_markup=reg_kb
    )
    await callback_query.answer()

# Обработка отправленного контакта
async def process_contact(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    argument = user_data.get("argument")

    await message.answer(
        "Спасибо за ваш контакт! 🤩\n\nТеперь расскажите поподробнее о вашем бизнесе. 🗒", 
        reply_markup=ReplyKeyboardRemove()
    )
    
    try:
        conversion_sheet = setup_google_sheets(1)
        update_conversion_sheet(conversion_sheet, argument, "contact_clicked")
        await state.set_state(Form.waiting_for_business_info)
    except Exception as e:
        print(f"Ошибка в process_contact: {e}")  # Вывод ошибки в консоль

# Функция для обработки завершения заполнения
async def process_business_info(message: types.Message, state: FSMContext):
    business_info = message.text
    user_data = await state.get_data()
    argument = user_data.get("argument")

    try:
        sheet = setup_google_sheets()
        all_values = sheet.get_all_values()
        last_row = len(all_values)
        sheet.update_cell(last_row, 4, business_info)
        
        await message.answer("Спасибо большое! 🎉")

        pdf_path = Path(__file__).parent / "guide.pdf"
        if pdf_path.exists():
            pdf_file = FSInputFile(pdf_path)
            await message.answer_document(pdf_file)
        else:
            await message.answer("Файл guide.pdf не найден. 😢")
        
        conversion_sheet = setup_google_sheets(1)
        update_conversion_sheet(conversion_sheet, argument, "info_sent")
        
        await send_new_application_to_admin(sheet)

    except Exception as e:
        print(f"Ошибка в process_business_info: {e}")  # Вывод ошибки в консоль
        await message.answer(f"Ошибка при записи в таблицу: {str(e)}", parse_mode="HTML")

# Функция для отправки последней заявки администратору
async def send_new_application_to_admin(sheet):
    try:
        all_values = sheet.get_all_values()
        if len(all_values) > 1:
            last_row = all_values[-1]
            application_id = last_row[0]
            argument = last_row[2]
            description = last_row[3] if len(last_row) > 2 else "Нет описания"
            message = f"НОВАЯ ЗАЯВКА\nID: {application_id}\nARG: {argument}\nDESCRIPTION: {description}"
            await bot.send_message(ADMIN_ID, message, parse_mode="HTML")
        else:
            print("Нет данных для отправки администратору.")
    except Exception as e:
        print(f"Ошибка в send_new_application_to_admin: {e}")  # Вывод ошибки в консоль

# Регистрация всех обработчиков
def reg_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command(commands=['start']))
    dp.callback_query.register(process_registration_callback, F.data == "register")
    dp.message.register(process_contact, F.contact, Form.waiting_for_contact)
    dp.message.register(process_business_info, Form.waiting_for_business_info)