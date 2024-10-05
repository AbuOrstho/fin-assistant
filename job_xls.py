import os
import shutil
import openpyxl
import datetime
import asyncio


def create_xls(user_id):
    source = 'Простой бюджет на месяц1.xlsx'
    destination_folder = f"user_files/{user_id}/"
    destination = f"{destination_folder}/{user_id}.xlsx"

    # Создание папки, если она не существует
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    shutil.copy2(source, destination)
    print('Папка создана и файл скопирован')


async def get_cell_value(cell_address, user_id, sheet_name='2024'):
    file_path = f'user_files/{user_id}/{user_id}.xlsx'
    """
    Функция для получения значения из конкретной ячейки в Excel.

    :param user_id: Имя файла которое схоже с id пользователя
    :param sheet_name: Название листа
    :param cell_address: Адрес ячейки в формате A1, B2 и т.д.
    :return: Значение ячейки
    """
    # Открываем файл Excel асинхронно
    workbook = await asyncio.to_thread(openpyxl.load_workbook, file_path)

    # Выбираем лист по имени
    sheet = workbook[sheet_name]

    # Получаем значение ячейки
    cell_value = sheet[cell_address].value

    return cell_value, workbook


async def add_value_to_cell(cell_address, value_to_add, user_id, sheet_name='2024'):
    file_path = f'user_files/{user_id}/{user_id}.xlsx'
    """
    Функция для добавления значения к ячейке и сохранения изменений в файл.

    :param user_id: Имя файла которое схоже с id пользователя
    :param sheet_name: Название листа
    :param cell_address: Адрес ячейки в формате A1, B2 и т.д.
    :param value_to_add: Значение, которое нужно прибавить к существующему значению ячейки
    """
    # Получаем текущее значение ячейки и объект workbook
    cell_value, workbook = await get_cell_value(cell_address, user_id, sheet_name)

    # Если значение в ячейке пустое, считать его за 0
    if cell_value is None:
        cell_value = 0

    # Добавляем значение
    new_value = cell_value + value_to_add

    # Обновляем значение в ячейке
    sheet = workbook[sheet_name]
    sheet[cell_address].value = new_value

    # Сохраняем изменения в файл асинхронно
    await asyncio.to_thread(workbook.save, file_path)


async def data_validator(user_id, button_type, amount):
    month = datetime.datetime.now().month
    buttons = {
        "Зп на руки": '3', "Зп на карточку": '4', "Шабашки": '5', "Другие": '6',
        "Жилье": '13', "Коммуналка": '14',
        "Еда": '15', "Проезд": '16',
        "Интернет": '17', "Сотовая связь": '18',
        "Одежда": '19', "Медикаменты": '20',
        "Процент кредита": '21', "Хоз расходы": '22',
        "Техника": '23', "Парикмахерская": '24',
        "Развлечения": '25', "Обучение": '26',
        "Подарки": '27', "Прочие": '28'
    }
    month_id = {
        1: 'H', 2: 'I', 3: 'J', 4: 'K',
        5: 'L', 6: 'M', 7: 'N', 8: 'C',
        9: 'D', 10: 'E', 11: 'F', 12: 'G'
    }
    await add_value_to_cell(cell_address=f'{month_id[month]}{buttons[button_type]}', value_to_add=amount,
                            user_id=user_id)
