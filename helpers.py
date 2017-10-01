# coding: utf-8

import os
import io

from functools import lru_cache


@lru_cache(maxsize=None)
def get_sender_name(vk_funcs, user_id):
    """Возвращает имя (строку) пользователя контача по его id.
    """
    sender_info = vk_funcs.users.get(user_ids=str(user_id))[0]
    return '{first_name} {last_name}'.format(**sender_info)


def get_file_buffer_by_file_id(tg_bot, telegram_file_id):
    """Скачивает файл с сервера телеги по идентификатору.

    :param tg_bot: бот телеги
    :param telegram_file_id: id файла telegram api
    :return: BytesIO с содержимым файла.
    """
    file_obj = tg_bot.get_file(telegram_file_id)
    buf = io.BytesIO(
        tg_bot.download_file(file_obj.file_path)
    )
    buf.name = os.path.basename(file_obj.file_path)
    return buf
