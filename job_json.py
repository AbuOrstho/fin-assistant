import json
import datetime
import os
import aiofiles

async def description_operation(user_id, description='', type='', category='', amount=''):
    current_time = datetime.datetime.now()
    date_str = current_time.strftime("%d.%m.%Y")
    time_str = current_time.strftime("%H:%M:%S")

    new_entry = {
        "description": description,
        "type": type,
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
    else:
        # Если запись с таким временем уже существует, добавляем миллисекунды
        time_str = current_time.strftime("%H:%M:%S.%f")
        data[date_str][time_str] = new_entry

    # Записываем обновленные данные обратно в файл асинхронно
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(data, ensure_ascii=False, indent=4))

# Пример асинхронного вызова функции
# import asyncio
# asyncio.run(description_operation('1893436617', description='Покупка продуктов', type='Расход', category='Еда', amount='1500'))
