import json
import os
import aiofiles


async def description_operation(user_id, type_operation, category, amount, date_str, time_str, description=None):
    """
    Функция для создания json-файла и добавления в него новых данных о транзакциях
    :param user_id: id пользователя используется для названия файла
    :param type_operation: тип операции Доход или Расход
    :param category: Категория дохода или расхода
    :param amount: Сумма для добавления в описание
    :param date_str: Дата, используется как ключ в json-файле
    :param time_str: Время, используется как ключ в json-файле
    :param description: Описание операции

    :type user_id: string
    :type type_operation: string
    :type category: string
    :type amount: string
    :type date_str: string
    :type time_str: string
    :type description: string

    :return: Создается файл если его не было и добавляется информация о транзакциях
    """
    new_entry = {
        "description": description,
        "type": type_operation,
        "category": category,
        "amount": amount
    }

    # Путь к файлу
    file_path = f'user_files/{user_id}/{user_id}.json'

    # Проверяем, существует ли файл data.json
    if os.path.exists(file_path):
        # Читаем существующие данные из файла асинхронно
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
            data = json.loads(content)
    else:
        # Инициализируем пустой словарь, если файл не существует
        data = {}

    # Обновляем данные
    if date_str not in data:
        data[date_str] = {}
    if time_str not in data[date_str]:
        data[date_str][time_str] = new_entry

    # Записываем обновленные данные обратно в файл асинхронно
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(data, ensure_ascii=False, indent=4))


async def get_description_text(user_id, date_str, time_str, description):
    """
    Функция для добавления описания в транзакциях
    :param user_id: id пользователя используется для названия файла
    :param date_str: Дата, используется как ключ в json-файл
    :param time_str: Время, используется как ключ в json-файле
    :param description: Описание операции

    :type user_id: string
    :type date_str: string
    :type time_str: string
    :type description: string

    :return: Добавляет описания для ранее созданных транзакций
    """
    # print(user_id, date_str, time_str, description)
    # Путь к файлу
    file_path = f'user_files/{user_id}/{user_id}.json'
    # Проверяем, существует ли файл data.json
    if os.path.exists(file_path):
        # Читаем существующие данные из файла асинхронно
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
            data = json.loads(content)
    else:
        # Инициализируем пустой словарь, если файл не существует
        data = {}

    if date_str in data and time_str in data[date_str]:
        data[date_str][time_str]['description'] = description
        # Записываем обновленные данные обратно в файл асинхронно
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(data, ensure_ascii=False, indent=4))
