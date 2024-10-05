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
bot_token = (
    '6848140179:AAFj3nACX5QlrPv6gx_0_gqtvSAl_9u5GFw')  # Рекомендуется использовать переменные окружения для хранения токенов
if not bot_token:
    raise ValueError("Необходимо указать BOT_TOKEN в переменных окружения.")

bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class FinanceState(StatesGroup):
    waiting_for_expense_amount = State()
    waiting_for_income_amount = State()
    expense_category = State()
    income_category = State()
    waiting_for_expense_action = State()
    waiting_for_income_action = State()  # Новое состояние
    waiting_for_description = State()
    waiting_for_income_description = State()  # Новое состояние


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


@dp.callback_query_handler(lambda c: c.data == 'get_description', state=FinanceState.waiting_for_expense_action)
async def handle_get_description(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    category = user_data.get('expense_category')
    amount = user_data.get('expense_amount')

    if not category or not amount:
        await callback_query.message.reply("Не удалось получить данные операции. Попробуйте еще раз.")
        await state.finish()
        return

    await FinanceState.waiting_for_description.set()
    await callback_query.message.reply("Пожалуйста, введите описание расхода или введите /stop для отмены.")


@dp.message_handler(state=FinanceState.waiting_for_description)
async def handle_description(message: types.Message, state: FSMContext):
    description = message.text.strip()

    if description.lower() == '/stop':
        await message.reply("Добавление описания отменено.")
        await state.finish()
        return

    user_data = await state.get_data()
    category = user_data.get('expense_category')
    amount = user_data.get('expense_amount')

    try:
        await job_json.description_operation(
            user_id=message.from_user.id,
            description=description,
            type='Расход',
            category=category,
            amount=amount
        )
        await message.reply(f"Описание '{description}' добавлено к расходу в категории '{category}' на сумму {amount}.")
        logging.info(
            f"Пользователь {message.from_user.id} добавил описание к расходу: {category} - {amount} - {description}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении описания для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении описания: {e}")
    finally:
        await state.finish()


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


# Обработчик ввода суммы дохода
@dp.message_handler(state=FinanceState.waiting_for_income_amount)
async def handle_income_amount(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    category = user_data.get('income_category')
    amount = message.text.strip()

    if amount.lower() == '/stop':
        await message.reply("Операция отменена.")
        await state.finish()
        return

    if not amount.isdigit():
        await message.reply("Пожалуйста, введите корректную сумму (только числа) или введите /stop для отмены.")
        return

    try:
        await job_xls.data_validator(message.from_user.id, category, int(amount))
        await state.update_data(income_amount=amount)  # Сохраняем сумму в состоянии
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text='Получить таблицу', callback_data='manage_output'),
            InlineKeyboardButton(text='Добавить описание', callback_data='get_income_description')
        )
        await message.reply(f"Доход в категории '{category}' на сумму {amount} успешно добавлен!",
                            reply_markup=keyboard)
        logging.info(f"Пользователь {message.from_user.id} добавил доход: {category} - {amount}")
        # Устанавливаем состояние ожидания действия по доходу
        await FinanceState.waiting_for_income_action.set()
    except Exception as e:
        logging.error(f"Ошибка при добавлении дохода для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении дохода: {e}")
        await state.finish()


# Обработчик нажатия на кнопку «Добавить описание» для доходов
@dp.callback_query_handler(lambda c: c.data == 'get_income_description', state=FinanceState.waiting_for_income_action)
async def handle_get_income_description(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    category = user_data.get('income_category')
    amount = user_data.get('income_amount')

    if not category or not amount:
        await callback_query.message.reply("Не удалось получить данные операции. Попробуйте еще раз.")
        await state.finish()
        return

    await FinanceState.waiting_for_income_description.set()
    await callback_query.message.reply("Пожалуйста, введите описание дохода или введите /stop для отмены.")
    await callback_query.answer()


# Обработчик ввода описания дохода
@dp.message_handler(state=FinanceState.waiting_for_income_description)
async def handle_income_description(message: types.Message, state: FSMContext):
    description = message.text.strip()

    if description.lower() == '/stop':
        await message.reply("Добавление описания отменено.")
        await state.finish()
        return

    user_data = await state.get_data()
    category = user_data.get('income_category')
    amount = user_data.get('income_amount')

    try:
        # Асинхронно вызываем функцию сохранения описания
        await job_json.description_operation(
            user_id=message.from_user.id,
            description=description,
            type='Доход',
            category=category,
            amount=amount
        )
        await message.reply(f"Описание '{description}' добавлено к доходу в категории '{category}' на сумму {amount}.")
        logging.info(
            f"Пользователь {message.from_user.id} добавил описание к доходу: {category} - {amount} - {description}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении описания для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении описания: {e}")
    finally:
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
        await job_xls.data_validator(message.from_user.id, category, int(amount))
        await state.update_data(expense_amount=amount)  # Сохраняем сумму в состоянии
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text='Получить таблицу', callback_data='manage_output'),
            InlineKeyboardButton(text='Добавить описание', callback_data='get_description')
        )
        await message.reply(f"Расход в категории '{category}' на сумму {amount} успешно добавлен!",
                            reply_markup=keyboard)
        logging.info(f"Пользователь {message.from_user.id} добавил расход: {category} - {amount}")
        # Устанавливаем новое состояние без завершения текущего
        await FinanceState.waiting_for_expense_action.set()
    except Exception as e:
        logging.error(f"Ошибка при добавлении расхода для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении расхода: {e}")
        await state.finish()  # Завершаем состояние только в случае ошибки


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
