import json
import datetime
import os
import aiofiles


async def description_operation(user_id, type_operation, category, amount, date_str, time_str, description=None):
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
    print(user_id, date_str, time_str, description)
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
        print('Nice')
        data[date_str][time_str]['description'] = description
        # Записываем обновленные данные обратно в файл асинхронно
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(data, ensure_ascii=False, indent=4))
