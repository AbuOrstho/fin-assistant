import os
import shutil
import datetime
import logging

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import job_xls
import job_json

# Логирование настроено на уровень DEBUG для подробного вывода
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG)

# Инициализация бота и диспетчера с хранилищем состояний в памяти
bot_token = ('5184064788:AAHpyj6L6z7A2oSWT0JRvXNZe-6r9varvgU')  # Рекомендуется использовать переменные окружения для хранения токенов
if not bot_token:
    raise ValueError("Необходимо указать BOT_TOKEN в переменных окружения.")

bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Состояния бота для управления финансовыми данными
class FinanceState(StatesGroup):
    waiting_for_expense_amount = State()
    waiting_for_income_amount = State()
    expense_category = State()
    income_category = State()
    waiting_for_description = State()



# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    folder_path = f'user_files/{user_id}'

    logging.info(f"Пользователь {message.from_user.full_name} ({message.from_user.username}), ID: {user_id} "
                 f"вызвал команду /start в {datetime.datetime.now()}. Сообщение: {message.text}")

    if os.path.exists(folder_path):
        logging.debug(f"Папка {folder_path} существует.")
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text="Да", callback_data='reset_yes'),
            InlineKeyboardButton(text="Нет", callback_data='reset_no')
        )
        await message.reply(
            'У вас уже есть созданные таблицы! '
            'Чтобы получить информацию, напишите команду /help. '
            'Если вы хотите очистить свою таблицу и начать заново, нажмите на кнопку "Да".',
            reply_markup=keyboard
        )
    else:
        os.makedirs(folder_path, exist_ok=True)
        job_xls.create_xls(user_id)
        await message.reply(
            f'Привет, {message.from_user.first_name}! Я бот, который поможет вам вести финансовую отчетность. '
            f'Для вас создана отдельная папка, в которой будут храниться Excel-таблицы с вашими расходами и доходами. '
            f'Чтобы получить информацию, напишите команду /help.'
        )


# Обработчик команды /help
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = (
        "*Добро пожаловать в финансового помощника!*\n\n"
        "Этот бот поможет вам вести учет ваших доходов и расходов, сохраняя всю информацию в Excel-таблицах. "
        "Вот список команд, которые вы можете использовать:\n\n"
        "*/start* - *Инициализация бота.*\n"
        "При первом запуске бот создаст папку и Excel-таблицу, где будут храниться ваши данные. "
        "Если вы уже использовали бота ранее, бот предложит вам очистить текущую таблицу и начать заново.\n\n"
        "*/help* - *Помощь по использованию бота.*\n"
        "Выводит это сообщение с описанием всех доступных команд и функционала.\n\n"
        "*/get_tables* - *Получение вашей таблицы.*\n"
        "Бот отправит вам текущую Excel-таблицу, в которой хранятся все ваши записи о доходах и расходах. "
        "Вы можете открыть этот файл, чтобы просмотреть или отредактировать данные.\n\n"
        "*/manage_finance* - *Управление финансами.*\n"
        "Эта команда позволяет вам добавить новые записи о доходах или расходах. "
        "После выбора типа операции (Доходы или Расходы) вам будет предложено выбрать категорию и ввести сумму.\n\n"
        "*Для расходов доступны следующие категории:*  "
        "`Жилье`, `Коммуналка`, `Еда`, `Проезд`, `Интернет`, `Сотовая связь`, `Одежда`, `Медикаменты`, `Процент кредита`, "
        "`Хоз расходы`, `Техника`, `Парикмахерская`, `Развлечения`, `Обучение`, `Подарки`, `Прочие`.\n\n"
        "Если у вас возникли вопросы или нужна помощь, не стесняйтесь обращаться к @vay\_ahi за поддержкой!"
    )
    await message.reply(help_text, parse_mode="Markdown")


# Обработчик команды /get_tables
@dp.message_handler(commands=['get_tables'])
async def get_tables_command(message: types.Message):
    file_path = f'user_files/{message.from_user.id}/{message.from_user.id}.xlsx'

    if os.path.exists(file_path):
        try:
            await message.answer_document(InputFile(file_path))
            logging.info(f"Пользователю {message.from_user.id} отправлена таблица {file_path}.")
        except Exception as e:
            logging.error(f"Ошибка при отправке файла {file_path} пользователю {message.from_user.id}: {e}")
            await message.reply(f"Произошла ошибка при отправке файла: {e}")
    else:
        logging.warning(f"Файл {file_path} не найден для пользователя {message.from_user.id}.")
        await message.reply("Файл не найден.")


# Обработчик команды /manage_finance
@dp.message_handler(commands=['manage_finance'])
async def manage_finance_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text='Доходы', callback_data='manage_income'),
        InlineKeyboardButton(text='Расходы', callback_data='manage_expense'),
        InlineKeyboardButton(text='Получить таблицу', callback_data='manage_output')
    )
    await message.reply("Выберите тип операции:", reply_markup=keyboard)


# Обработчик нажатия на кнопки
@dp.callback_query_handler(lambda c: c.data.startswith('reset_'))
async def process_reset_callback(callback_query: types.CallbackQuery):
    action = callback_query.data.split('_')[1]
    if action == "yes":
        await reset_user_data(callback_query)
    elif action == "no":
        await continue_with_existing_data(callback_query)


# Функция для сброса данных пользователя
async def reset_user_data(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    folder_path = f'user_files/{user_id}'

    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        job_xls.create_xls(user_id)
        logging.info(f"Данные пользователя {user_id} успешно сброшены.")
        await callback_query.answer("Вы успешно обновили свою таблицу!", show_alert=True)
    else:
        logging.warning(f"Попытка сброса данных для несуществующего пользователя {user_id}.")
        await callback_query.message.answer('Сначала создайте папку с помощью команды /start.')


# Функция для продолжения работы с существующими данными
async def continue_with_existing_data(callback_query: types.CallbackQuery):
    logging.info(f"Пользователь {callback_query.from_user.id} продолжает работу с существующими данными.")
    await callback_query.answer("Продолжаем заполнять ваш финансовый отчет.", show_alert=True)


# Обработчик вывода таблицы
@dp.callback_query_handler(lambda c: c.data == 'manage_output')
async def handle_output(callback_query: types.CallbackQuery):
    file_path = f'user_files/{callback_query.from_user.id}/{callback_query.from_user.id}.xlsx'

    if os.path.exists(file_path):
        try:
            await callback_query.message.answer_document(InputFile(file_path))
            logging.info(f"Пользователю {callback_query.from_user.id} отправлена таблица {file_path}.")
        except Exception as e:
            logging.error(f"Ошибка при отправке файла {file_path} пользователю {callback_query.from_user.id}: {e}")
            await callback_query.message.reply(f"Произошла ошибка при отправке файла: {e}")
    else:
        logging.warning(f"Файл {file_path} не найден для пользователя {callback_query.from_user.id}.")
        await callback_query.message.reply("Файл не найден.")
    await callback_query.answer()


# Обработчик категории доходов
@dp.callback_query_handler(lambda c: c.data == 'manage_income')
async def handle_income_category(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    categories = [
        "Зп на руки", "Зп на карточку", "Шабашки", "Другие"
    ]
    keyboard.add(*[InlineKeyboardButton(text=cat, callback_data=f'income_{cat}') for cat in categories])

    await callback_query.message.reply("Выберите категорию расхода:", reply_markup=keyboard)
    await callback_query.answer()


# Обработчик выбора категории доходов
@dp.callback_query_handler(lambda c: c.data.startswith('income_'))
async def process_income_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.split('_')[1]
    await state.update_data(income_category=category)

    await callback_query.message.answer("Пожалуйста, введите сумму дохода:")
    await FinanceState.waiting_for_income_amount.set()
    await callback_query.answer()


# Обработчик ввода суммы доходов
@dp.message_handler(state=FinanceState.waiting_for_income_amount)
async def handle_income_amount(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    category = user_data.get('income_category')
    datetime_str = user_data.get('income_category')
    amount = message.text.strip()
    print(message.from_user.id, category, int(amount))
    if amount.lower() == '/stop':
        await message.reply("Операция отменена.")
        await state.finish()
        return

    if not amount.isdigit():
        await message.reply("Пожалуйста, введите корректную сумму (только числа) или введите /stop для отмены.")
        return

    try:
        current_time = datetime.datetime.now()
        date_str = current_time.strftime("%d.%m.%Y")
        time_str = current_time.strftime("%H:%M:%S")
        await job_xls.data_validator(message.from_user.id, category, int(amount))
        await job_json.description_operation(user_id=message.from_user.id, type_operation='Доход',
                                             category=category, amount=int(amount),
                                             date_str=date_str, time_str=time_str)
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text='Получить таблицу', callback_data='manage_output'),
            InlineKeyboardButton(text='Добавить описание', callback_data=f'get_description_{date_str}_{time_str}')
        )
        await message.reply(f"Доход в категории '{category}' на сумму {amount} успешно добавлен!", reply_markup=keyboard)
        logging.info(f"Пользователь {message.from_user.id} добавил доход: {category} - {amount}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении дохода для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении дохода: {e}")
    finally:
        await state.finish()


# Обработчик нажатия на кнопку "Добавить описание"
@dp.callback_query_handler(lambda c: c.data.startswith('get_description_'))
async def handle_get_description(callback_query: types.CallbackQuery, state: FSMContext):
    # Извлечение даты и времени из callback_data
    callback_data_parts = callback_query.data.split('_')
    date_str = callback_data_parts[2]
    time_str = callback_data_parts[3]

    # Сохранение даты и времени в state (чтобы использовать при вводе текста)
    await state.update_data(date_str=date_str, time_str=time_str)

    # Сообщение пользователю с просьбой ввести текст описания
    await callback_query.message.reply("Пожалуйста, введите описание или напишите /stop для отмены.")
    await FinanceState.waiting_for_description.set()  # Перевод в состояние ожидания описания
    await callback_query.answer()


# Обработчик ввода описания
@dp.message_handler(state=FinanceState.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    # Если пользователь вводит команду /stop, отменяем ввод
    if message.text.lower() == '/stop':
        await message.reply("Операция добавления описания отменена.")
        await state.finish()
        return

    # Получаем дату и время из state
    user_data = await state.get_data()
    date_str = user_data.get('date_str')
    time_str = user_data.get('time_str')

    # Сообщение пользователю с введенным текстом и временем создания кнопки
    await job_json.get_description_text(user_id=message.from_user.id, date_str=date_str,
                                        time_str=time_str, description=message.text)
    await message.reply(f"Описание: '{message.text}' было добавлено."
                        f"\nКнопка была создана {date_str} в {time_str}.")

    # Завершение состояния
    await state.finish()



# Обработчик категории расходов
@dp.callback_query_handler(lambda c: c.data == 'manage_expense')
async def handle_expense_category(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=3)
    categories = [
        "Жилье", "Коммуналка", "Еда", "Проезд", "Интернет", "Сотовая связь",
        "Одежда", "Медикаменты", "Процент кредита", "Хоз расходы", "Техника",
        "Парикмахерская", "Развлечения", "Обучение", "Подарки", "Прочие"
    ]
    print([f"{text} expense_{text}" for text in categories])
    keyboard.add(*[InlineKeyboardButton(text=cat, callback_data=f'expense_{cat}') for cat in categories])

    await callback_query.message.reply("Выберите категорию расхода:", reply_markup=keyboard)
    await callback_query.answer()


# Обработчик выбора категории расходов
@dp.callback_query_handler(lambda c: c.data.startswith('expense_'))
async def process_expense_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.split('_')[1]
    await state.update_data(expense_category=category)

    await callback_query.message.answer("Пожалуйста, введите сумму расхода:")
    await FinanceState.waiting_for_expense_amount.set()
    await callback_query.answer()


# Обработчик ввода суммы расходов
@dp.message_handler(state=FinanceState.waiting_for_expense_amount)
async def handle_expense_amount(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    category = user_data.get('expense_category')
    amount = message.text.strip()

    if amount.lower() == '/stop':
        await message.reply("Операция отменена.")
        await state.finish()
        return

    if not amount.isdigit():
        await message.reply("Пожалуйста, введите корректную сумму (только числа) или введите /stop для отмены.")
        return

    try:
        current_time = datetime.datetime.now()
        date_str = current_time.strftime("%d.%m.%Y")
        time_str = current_time.strftime("%H:%M:%S")

        # Добавляем запись о расходах в JSON файл
        await job_json.description_operation(user_id=message.from_user.id, type_operation='Расход',
                                             category=category, amount=int(amount),
                                             date_str=date_str, time_str=time_str)

        # Валидируем и добавляем данные в Excel таблицу
        await job_xls.data_validator(message.from_user.id, category, int(amount))

        # Создаем клавиатуру с кнопками
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text='Получить таблицу', callback_data='manage_output'),
            InlineKeyboardButton(text='Добавить описание', callback_data=f'get_description_{date_str}_{time_str}')
        )

        await message.reply(f"Расход в категории '{category}' на сумму {amount} успешно добавлен!", reply_markup=keyboard)
        logging.info(f"Пользователь {message.from_user.id} добавил расход: {category} - {amount}")

    except Exception as e:
        logging.error(f"Ошибка при добавлении расхода для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении расхода: {e}")

    finally:
        await state.finish()

@dp.message_handler()
async def message_processing(message: types.Message):
    month_id = {
        1: 'H', 2: 'I', 3: 'J', 4: 'K',
        5: 'L', 6: 'M', 7: 'N', 8: 'C',
        9: 'D', 10: 'E', 11: 'F', 12: 'G'
    }
    month = datetime.datetime.now().month
    if message.text == 'Расходы за месяц':
        amount = await job_xls.get_cell_value(cell_address=f'{month_id[month]}30', user_id=message.from_user.id)
        m = await job_xls.get_cell_value(cell_address=f'{month_id[month]}12', user_id=message.from_user.id)
        await message.reply(text=f"Расходы за {m[0]} составляют {amount[0]}")


if __name__ == "__main__":
    logging.info("Бот запущен и готов к работе.")
    executor.start_polling(dp)