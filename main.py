import os
import shutil
import datetime
import logging
import asyncio

from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import job_xls
import job_json

# Логирование настроено на уровень DEBUG для подробного вывода
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG)

load_dotenv()

# Инициализация бота и диспетчера с хранилищем состояний в памяти
bot_token = os.getenv('MY_VAR')
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
    """
    Функция для обработки команды /start
    :param message: Аргумент в котором хранится вся необходимая информация

    :type message: str

    :return: Создает папку с id пользователя в которой создается Excel-таблица для хранения данных, а также в этой
    же папке будет создан json-файл для более детальной информации про каждую операцию
    """
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
    """
        Функция для обработки команды /help
        :param message: Аргумент в котором хранится вся необходимая информация

        :type message: str

        :return: Выводит все доступные команды и их возможности
        """
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
    """
    Функция для обработки команды /get_tables
    :param message: Аргумент в котором хранится вся необходимая информация

    :type message: str

    :return: Скидывает Excel-таблицу пользователю
    """
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
    """
        Функция для обработки команды /manage_finance
        :param message: Аргумент в котором хранится вся необходимая информация

        :type message: str

        :return: Выводит сообщение с кнопками 'Доходы', 'Расходы', 'Получить таблицу'
        """
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
    """
    Функция для обработки нажатия на кнопки с префиксом reset_
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)

    :type callback_query: types.CallbackQuery

    :return: В зависимости от действия, полученного из callback запроса, функция либо вызывает процесс сброса данных
    пользователя (reset_user_data), либо продолжает работу с существующими данными (continue_with_existing_data).
    Если действие — "yes", данные пользователя сбрасываются, если "no" — работа продолжается без сброса данных.
    """

    action = callback_query.data.split('_')[1]
    if action == "yes":
        await reset_user_data(callback_query)
    elif action == "no":
        await continue_with_existing_data(callback_query)


# Функция для сброса данных пользователя
async def reset_user_data(callback_query: types.CallbackQuery):
    """
    Функция для сброса данных пользователя
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)

    :type callback_query: Types.CallbackQuery

    :return: Удаляет папку с данными пользователя и создает новую Excel-таблицу для хранения данных. Если папка с данными
    пользователя существует, она удаляется, и создается новая таблица. В случае отсутствия папки, выводится предупреждение
    и отправляется сообщение с предложением создать данные с помощью команды /start.

    Логирование:
    - В случае успешного сброса данных пользователя выводится сообщение в лог о том, что данные сброшены.
    - В случае отсутствия данных выводится предупреждение о том, что папка пользователя не существует.

    Задействованные функции:
    - `job_xls.create_xls(user_id)`: Создает новую Excel-таблицу для пользователя.
    - `callback_query.answer()`: Показывает всплывающее уведомление о успешной операции.
    - `callback_query.message.answer()`: Отправляет сообщение пользователю, если папка отсутствует.
    """

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
    """
    Функция для продолжения работы с существующими данными
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)

    :type callback_query: Types.CallbackQuery

    :return: Функция информирует пользователя, что работа с существующими данными продолжается, и выводит соответствующее
    уведомление. В лог записывается информация о том, что пользователь продолжил работу без сброса данных.

    Логирование:
    - Логируется ID пользователя и факт продолжения работы с существующими данными.

    Используемые методы:
    - `callback_query.answer()`: Отправляет пользователю уведомление с сообщением о том, что работа продолжается.
    """

    logging.info(f"Пользователь {callback_query.from_user.id} продолжает работу с существующими данными.")
    await callback_query.answer("Продолжаем заполнять ваш финансовый отчет.", show_alert=True)


# Обработчик вывода таблицы
@dp.callback_query_handler(lambda c: c.data == 'manage_output')
async def handle_output(callback_query: types.CallbackQuery):
    """
    Функция для обработки вывода таблицы пользователю
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)

    :type callback_query: types.CallbackQuery

    :return: Функция проверяет наличие Excel-файла с данными пользователя. Если файл существует, он отправляется пользователю.
    В случае успешной отправки логируется информация о действии. Если файл не найден, пользователю отправляется сообщение об ошибке,
    а в лог записывается предупреждение. Если при отправке файла возникает ошибка, она логируется, и пользователю отправляется сообщение об ошибке.

    Логирование:
    - Логируется факт успешной отправки файла пользователю.
    - В случае ошибки при отправке файла записывается ошибка с подробностями.
    - Логируется предупреждение, если файл не найден.

    Используемые методы:
    - `callback_query.message.answer_document()`: Отправляет файл Excel пользователю.
    - `callback_query.message.reply()`: Отправляет сообщение пользователю в случае ошибки или отсутствия файла.
    - `callback_query.answer()`: Закрывает уведомление о нажатии кнопки для предотвращения блокировки интерфейса.
    """

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
    """
    Функция для обработки выбора категории доходов
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)

    :type callback_query: Types.CallbackQuery

    :return: Функция выводит пользователю кнопки с возможными категориями доходов для выбора. Каждая кнопка содержит текст категории и
    уникальные данные для callback запроса. После этого пользователю отправляется сообщение с предложением выбрать категорию дохода.

    Категории доходов:
    - "Зп на руки"
    - "Зп на карточку"
    - "Шабашки"
    - "Другие"

    Используемые методы:
    - `callback_query.message.reply()`: Отправляет сообщение с кнопками, позволяющими выбрать категорию дохода.
    - `callback_query.answer()`: Закрывает уведомление о нажатии кнопки для предотвращения блокировки интерфейса.

    Примечание:
    Кнопки для выбора категории доходов организованы в два столбца (row_width=2).
    """

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
    """
    Функция для обработки выбора категории доходов
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)
    :param state: Объект состояния FSMContext, используемый для хранения состояния пользователя

    :type callback_query: types.CallbackQuery
    :type state: FSMContext

    :return: Функция извлекает выбранную категорию доходов из callback запроса, обновляет состояние с выбранной категорией
    и переводит пользователя в состояние ожидания ввода суммы дохода. После этого отправляется сообщение с запросом
    ввода суммы дохода.

    Логика работы:
    1. Из callback запроса извлекается категория дохода (например, 'Зп на руки', 'Шабашки').
    2. Обновляется состояние пользователя с новой категорией дохода (`income_category`).
    3. Пользователю отправляется сообщение с запросом на ввод суммы дохода.
    4. Переводится состояние FinaceState в режим ожидания (`waiting_for_income_amount`).

    Используемые методы:
    - `state.update_data()`: Обновляет данные состояния пользователя.
    - `callback_query.message.answer()`: Отправляет сообщение с запросом на ввод суммы.
    - `FinanceState.waiting_for_income_amount.set()`: Переводит состояние пользователя в режим ожидания ввода суммы.
    - `callback_query.answer()`: Закрывает уведомление о нажатии кнопки для предотвращения блокировки интерфейса.

    Примечание:
    Состояние пользователя используется для хранения выбранной категории дохода и последующего запроса суммы.
    """

    category = callback_query.data.split('_')[1]
    await state.update_data(income_category=category)

    await callback_query.message.answer("Пожалуйста, введите сумму дохода:")
    await FinanceState.waiting_for_income_amount.set()
    await callback_query.answer()


# Обработчик ввода суммы доходов
@dp.message_handler(state=FinanceState.waiting_for_income_amount)
async def handle_income_amount(message: types.Message, state: FSMContext):
    """
    Функция для обработки ввода суммы доходов
    :param message: Сообщение, содержащее текст с суммой дохода
    :param state: Объект состояния FSMContext, используемый для хранения состояния пользователя

    :type message: types.Message
    :type state: FSMContext

    :return: Функция обрабатывает введенную сумму дохода, проверяет корректность ввода и добавляет данные в таблицу и JSON-файл.
    В случае успешного добавления дохода пользователю выводится сообщение с подтверждением и кнопками для дальнейших действий.
    Если ввод некорректен (не числовой), пользователю предлагается ввести сумму заново или отменить операцию.

    Логика работы:
    1. Получение данных из состояния FSMContext, таких как категория дохода.
    2. Проверка введенной суммы на корректность:
       - Если сумма не является числом, пользователю предлагается повторить ввод.
       - Если сумма корректна, данные добавляются в таблицу Excel и JSON-файл.
    3. После успешного добавления дохода пользователю отправляется сообщение с предложением получить таблицу или добавить описание операции.
    4. Если ввод "/stop", операция отменяется, и состояние сбрасывается.
    5. В случае ошибки отправляется сообщение об ошибке, и она логируется.

    Используемые методы:
    - `state.get_data()`: Получает данные, сохраненные в состоянии пользователя.
    - `message.reply()`: Отправляет ответное сообщение пользователю.
    - `job_xls.data_validator()`: Проверяет и добавляет данные о доходе в Excel-таблицу.
    - `job_json.description_operation()`: Добавляет информацию об операции в JSON-файл.
    - `logging.info()`: Логирует успешное добавление дохода.
    - `logging.error()`: Логирует ошибку, если она возникает при добавлении данных.
    - `state.finish()`: Завершает текущее состояние FSM.

    Примечание:
    - Если сумма не введена корректно, пользователю отправляется запрос повторить ввод.
    - Если введена команда "/stop", операция отменяется, и состояние сбрасывается.
    """

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
        await message.reply(f"Доход в категории '{category}' на сумму {amount} успешно добавлен!",
                            reply_markup=keyboard)
        logging.info(f"Пользователь {message.from_user.id} добавил доход: {category} - {amount}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении дохода для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении дохода: {e}")
    finally:
        await state.finish()


# Обработчик нажатия на кнопку "Добавить описание"
@dp.callback_query_handler(lambda c: c.data.startswith('get_description_'))
async def handle_get_description(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Функция для обработки нажатия на кнопку "Добавить описание"
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)
    :param state: Объект состояния FSMContext, используемый для хранения состояния пользователя

    :type callback_query: types.CallbackQuery
    :type state: FSMContext

    :return: Функция извлекает дату и время операции из callback данных и сохраняет их в состоянии FSM для дальнейшего использования.
    Пользователю отправляется сообщение с просьбой ввести текст описания, после чего состояние переводится в режим ожидания ввода описания.

    Логика работы:
    1. Из callback данных извлекаются дата и время операции, которые сохраняются в состоянии FSM для последующего использования при добавлении описания.
    2. Пользователю отправляется сообщение с запросом на ввод описания для выбранной операции.
    3. Состояние пользователя переводится в `FinanceState.waiting_for_description`, чтобы обработчик мог ожидать ввод текста.
    4. Callback запрос завершается с помощью метода `callback_query.answer()`, чтобы не блокировать интерфейс.

    Используемые методы:
    - `callback_query.data.split()`: Извлекает дату и время из callback данных.
    - `state.update_data()`: Сохраняет дату и время операции в состоянии пользователя.
    - `callback_query.message.reply()`: Отправляет сообщение с просьбой ввести описание операции.
    - `FinanceState.waiting_for_description.set()`: Переводит состояние пользователя в режим ожидания ввода описания.
    - `callback_query.answer()`: Закрывает уведомление о нажатии кнопки для предотвращения блокировки интерфейса.

    Примечание:
    Пользователь может ввести описание для выбранной операции или отменить ввод, написав "/stop".
    """

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
    """
    Функция для обработки нажатия на кнопку "Добавить описание"
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)
    :param state: Объект состояния FSMContext, используемый для хранения состояния пользователя

    :type callback_query: types.CallbackQuery
    :type state: FSMContext

    :return: Функция извлекает дату и время операции из callback данных и сохраняет их в состоянии для дальнейшего использования.
    Пользователю отправляется сообщение с просьбой ввести текст описания, после чего состояние переводится в режим ожидания ввода описания.

    Логика работы:
    1. Из callback данных извлекаются дата и время операции, которые сохраняются в состояние FSM.
    2. Пользователю отправляется сообщение с запросом на ввод описания операции.
    3. Состояние пользователя переводится в `FinanceState.waiting_for_description` для ожидания ввода описания.
    4. Callback запрос завершается, чтобы избежать блокировки интерфейса.

    Используемые методы:
    - `callback_query.data.split()`: Извлекает дату и время из callback данных.
    - `state.update_data()`: Сохраняет дату и время операции в состоянии пользователя.
    - `callback_query.message.reply()`: Отправляет сообщение с просьбой ввести описание операции.
    - `FinanceState.waiting_for_description.set()`: Переводит состояние пользователя в режим ожидания ввода описания.
    - `callback_query.answer()`: Закрывает уведомление о нажатии кнопки для предотвращения блокировки интерфейса.

    Примечание:
    Пользователь может ввести описание для выбранной операции, либо отменить операцию, написав "/stop".
    """

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
    await message.reply(f"Описание успешно добавлено.")

    # Завершение состояния
    await state.finish()


# Обработчик категории расходов
@dp.callback_query_handler(lambda c: c.data == 'manage_expense')
async def handle_expense_category(callback_query: types.CallbackQuery):
    """
    Функция для обработки выбора категории расходов
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)

    :type callback_query: types.CallbackQuery

    :return: Функция выводит пользователю кнопки с возможными категориями расходов для выбора. Каждая кнопка содержит текст категории и
    уникальные данные для callback запроса. После этого пользователю отправляется сообщение с предложением выбрать категорию расхода.

    Используемые методы:
    - `callback_query.message.reply()`: Отправляет сообщение с кнопками, позволяющими выбрать категорию расхода.
    - `callback_query.answer()`: Закрывает уведомление о нажатии кнопки для предотвращения блокировки интерфейса.

    Примечание:
    Кнопки для выбора категории расходов организованы в три столбца (row_width=3).
    """

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
    """
    Функция для обработки выбора категории расходов
    :param callback_query: Аргумент, содержащий информацию о callback запросе (нажатии кнопки)

    :type callback_query: Types.CallbackQuery

    :return: Функция выводит пользователю кнопки с возможными категориями расходов для выбора. Каждая кнопка содержит текст категории и
    уникальные данные для callback запроса. После этого пользователю отправляется сообщение с предложением выбрать категорию расхода.

    Используемые методы:
    - `callback_query.message.reply()`: Отправляет сообщение с кнопками, позволяющими выбрать категорию расхода.
    - `callback_query.answer()`: Закрывает уведомление о нажатии кнопки для предотвращения блокировки интерфейса.

    Примечание:
    Кнопки для выбора категории расходов организованы в три столбца (row_width=3).
    """

    category = callback_query.data.split('_')[1]
    await state.update_data(expense_category=category)

    await callback_query.message.answer("Пожалуйста, введите сумму расхода:")
    await FinanceState.waiting_for_expense_amount.set()
    await callback_query.answer()


# Обработчик ввода суммы расходов
@dp.message_handler(state=FinanceState.waiting_for_expense_amount)
async def handle_expense_amount(message: types.Message, state: FSMContext):
    """
    Функция для обработки ввода суммы расходов
    :param message: Сообщение, содержащее текст с суммой расхода
    :param state: Объект состояния FSMContext, используемый для хранения состояния пользователя

    :type message: types.Message
    :type state: FSMContext

    :return: Функция обрабатывает введенную сумму расхода, проверяет корректность ввода и добавляет данные в таблицу и JSON-файл.
    В случае успешного добавления расхода пользователю выводится сообщение с подтверждением и кнопками для дальнейших действий.
    Если ввод некорректен (не числовой), пользователю предлагается ввести сумму заново или отменить операцию.

    Логика работы:
    1. Получение данных из состояния FSMContext, таких как категория расхода.
    2. Проверка введенной суммы на корректность:
       - Если сумма не является числом, пользователю предлагается повторить ввод.
       - Если сумма корректна, данные добавляются в таблицу Excel и JSON-файл.
    3. После успешного добавления расхода пользователю отправляется сообщение с предложением получить таблицу или добавить описание операции.
    4. Если ввод "/stop", операция отменяется, и состояние сбрасывается.
    5. В случае ошибки отправляется сообщение об ошибке, и она логируется.

    Используемые методы:
    - `state.get_data()`: Получает данные, сохраненные в состоянии пользователя.
    - `message.reply()`: Отправляет ответное сообщение пользователю.
    - `job_xls.data_validator()`: Проверяет и добавляет данные о расходе в Excel-таблицу.
    - `job_json.description_operation()`: Добавляет информацию об операции в JSON-файл.
    - `logging.info()`: Логирует успешное добавление расхода.
    - `logging.error()`: Логирует ошибку, если она возникает при добавлении данных.
    - `state.finish()`: Завершает текущее состояние FSM.

    Примечание:
    - Если сумма не введена корректно, пользователю отправляется запрос повторить ввод.
    - Если введена команда "/stop", операция отменяется, и состояние сбрасывается.
    """

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

        await message.reply(f"Расход в категории '{category}' на сумму {amount} успешно добавлен!",
                            reply_markup=keyboard)
        logging.info(f"Пользователь {message.from_user.id} добавил расход: {category} - {amount}")

    except Exception as e:
        logging.error(f"Ошибка при добавлении расхода для пользователя {message.from_user.id}: {e}")
        await message.reply(f"Произошла ошибка при добавлении расхода: {e}")

    finally:
        await state.finish()


@dp.message_handler()
async def message_processing(message: types.Message):
    """
    Функция для обработки всех входящих сообщений
    :param message: Сообщение, отправленное пользователем

    :type message: types.Message

    :return: Функция обрабатывает текст сообщения пользователя. Если текст сообщения равен "Расходы за месяц", функция
    извлекает данные о расходах за текущий месяц из Excel-таблицы и отправляет их пользователю. Расходы берутся из определенной
    ячейки, соответствующей текущему месяцу.

    Логика работы:
    1. Определение текущего месяца с помощью функции `datetime.datetime.now().month`.
    2. Если текст сообщения равен "Расходы за месяц", из Excel-таблицы пользователя извлекаются данные о расходах:
       - Значение из строки 30 для соответствующего столбца месяца.
       - Название месяца из строки 12 для того же столбца.
    3. Пользователю отправляется сообщение с информацией о расходах за текущий месяц.

    Используемые методы:
    - `job_xls.get_cell_value()`: Получает значение из указанной ячейки Excel-таблицы пользователя.
    - `message.reply()`: Отправляет ответное сообщение пользователю с информацией о его расходах за текущий месяц.

    Примечание:
    - В `month_id` содержится сопоставление номеров месяцев с буквами столбцов, в которых хранятся данные о месячных расходах.
    - Функция предполагает, что данные о расходах находятся в строке 30, а название месяца — в строке 12 Excel-таблицы.
    """

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


# Функция для отправки сообщения всем пользователям из списка
async def send_daily_message():
    """
    Асинхронная функция для отправки ежедневного сообщения всем пользователям из списка
    :return: Функция проходит по списку папок с ID пользователей, извлекает данные для каждого пользователя, и отправляет
    сообщение с результатами обработки данных. Если возникает ошибка при отправке, она логируется.

    Логика работы:
    1. Определяется список ID пользователей на основе имен папок в директории 'user_files'. Каждая папка в этой директории
    представляет собой ID пользователя.
    2. Для каждого пользователя (папки) вызывается функция `job_json.read_and_process_file()`, которая обрабатывает данные и возвращает текст сообщения.
    3. Сообщение отправляется пользователю с помощью метода `bot.send_message()` с указанием ID чата.
    4. В случае ошибки при обработке или отправке сообщения она логируется с подробной информацией о пользователе.

    Используемые методы:
    - `os.listdir()`: Возвращает список файлов и папок в указанной директории.
    - `os.path.isdir()`: Проверяет, является ли элемент директорией (чтобы убедиться, что это папка пользователя).
    - `job_json.read_and_process_file()`: Извлекает и обрабатывает данные из JSON-файла пользователя.
    - `bot.send_message()`: Отправляет сообщение пользователю по его ID в формате MarkdownV2.
    - `logging.error()`: Логирует ошибку, если сообщение не удалось отправить.

    Примечание:
    - Функция предполагает, что в директории 'user_files' каждая папка названа по ID пользователя, которому необходимо отправить сообщение.
    - Обработка данных для каждого пользователя производится функцией `job_json.read_and_process_file()`.
    """

    folder_path = 'user_files'
    # Список ID пользователей, которым бот будет отправлять сообщение
    chat_ids = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    for chat_id in chat_ids:
        try:
            res = await job_json.read_and_process_file(chat_id)
            await bot.send_message(chat_id=chat_id, text='''
            Бот был обновлён\! 🎉

Теперь бот может добавлять **описания к транзакциям**, а также будет **каждый день в 23:00** отправлять вам отчет за прошедший день\. 📊

Если у вас есть идеи или предложения по улучшению, не стесняйтесь отправлять их сюда — [@vay\_ahi](https://t.me/vay_ahi)\.

Мы всегда рады вашим отзывам\! 🙌''', parse_mode="MarkdownV2")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")


# Планировщик задач для отправки сообщения каждый день в 23:00
async def scheduler_setup():
    """
    Функция для настройки планировщика задач, отправляющего сообщения ежедневно в 23:00
    :return: Функция создает и настраивает планировщик задач `AsyncIOScheduler`, который каждый день в 23:00 по московскому времени
    запускает задачу `send_daily_message()`.

    Логика работы:
    1. Создается экземпляр `AsyncIOScheduler` с указанием часового пояса "Europe/Moscow".
    2. В планировщике регистрируется задача `send_daily_message()` с использованием триггера `cron`, который запускает задачу каждый день в 23:00.
    3. Планировщик запускается с помощью метода `scheduler.start()`.

    Используемые методы:
    - `AsyncIOScheduler()`: Создает асинхронный планировщик задач с возможностью настройки по времени и дате.
    - `scheduler.add_job()`: Добавляет задачу в планировщик с указанием времени выполнения (каждый день в 23:00).
    - `scheduler.start()`: Запускает планировщик, позволяя задачам выполняться в фоновом режиме.

    Примечание:
    - Планировщик использует часовой пояс "Europe/Moscow". Вы можете изменить его в зависимости от вашего региона.
    - Задача `send_daily_message()` будет выполняться каждый день в 23:00 по московскому времени.
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")  # Укажите нужный вам часовой пояс
    scheduler.add_job(send_daily_message, 'cron', hour=00, minute=00)  # Настройка на 23:00
    scheduler.start()


if __name__ == "__main__":
    logging.info("Бот запущен и готов к работе.")
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_setup())  # Запускаем планировщик
    executor.start_polling(dp)
