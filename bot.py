# coding: utf-8

import os
import configparser

import telebot
import vk_api

from threading import Thread
from functools import lru_cache
from vk_api.longpoll import VkLongPoll, VkEventType


# Настройки
config = configparser.ConfigParser()
config.read(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'config.ini'
))

try:
    telegram_token = config['secrets']['telegram_token']
    vk_login = config['secrets']['vk_login']
    vk_password = config['secrets']['vk_password']
except KeyError:
    raise RuntimeError('Invalid config. Check config.ini file!')


# Id чатов в телеге и контаче. Заполняются при регистрации через /start.
tg_chat_id = None
vk_chat_id = None


# Тележечный бот
tg_bot = telebot.TeleBot(telegram_token)
# Контачевский бот
vk_bot = vk_api.VkApi(vk_login, vk_password)
vk_bot.auth()
vk_funcs = vk_bot.get_api()


@lru_cache(maxsize=None)
def get_sender_name(vk_funcs, user_id):
    u"""
    Возвращает имя (строку) пользователя контача по его id.
    """
    sender_info = vk_funcs.users.get(user_ids=str(user_id))[0]
    return '{first_name} {last_name}'.format(**sender_info)


def process_attachment_from_vk(tg_bot, vk_bot, attachment):
    u"""
    Обрабатывает прикрепленные к сообщению данные, такие как
    фото, аудио.
    :param tg_bot: бот телеги
    :param vk_bot: api контача
    :param attachment: приложение.
    """

    # TODO: Позже отрефакторить всю эту портянку.

    if attachment['type'] == 'photo':
        size_keys = (
            'photo_2560', 'photo_1280', 'photo_807', 'photo_604', 'photo_130',
            'photo_75')
        link = None
        for size_key in size_keys:
            if attachment['photo'].get(size_key):
                link = attachment['photo'][size_key]
                break
        if link is not None:
            tg_bot.send_message(
                tg_chat_id,
                'Attachment/photo:\n{}\n{}'.format(
                    attachment['photo']['text'],
                    link
                )
            )
    elif attachment['type'] == 'video':
        size_keys = (
            'photo_800', 'photo_640', 'photo_320', 'photo_130')
        preview_link = None
        for size_key in size_keys:
            if attachment['video'].get(size_key):
                preview_link = attachment['video'][size_key]
                break
        if preview_link is not None:
            tg_bot.send_message(
                tg_chat_id,
                'Attachment/video:\n{}\n{}\n{}\n{}\n'.format(
                    attachment['video']['title'],
                    attachment['video']['description'],
                    preview_link,
                    attachment['video'].get('player', '<no link>'),
                )
            )
    elif attachment['type'] == 'audio':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/audio:\n{}\n{}\n{}\n'.format(
                attachment['audio']['artist'],
                attachment['audio']['title'],
                attachment['audio']['url'],
            )
        )
    elif attachment['type'] == 'doc':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/doc:\n{}(ext is {})\n{}\n'.format(
                attachment['doc']['title'],
                attachment['doc']['ext'],
                attachment['doc']['url'],
            )
        )
    elif attachment['type'] == 'link':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/link:\n{}(ext is {})\n{}\n'.format(
                attachment['link']['title'],
                attachment['link']['description'],
                attachment['link']['url'],
            )
        )
    elif attachment['type'] == 'market':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/market: <not implemented>\n{}\n'.format(
                repr(attachment['market'])
            )
        )
    elif attachment['type'] == 'market_album':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/market_album: <not implemented>\n{}\n'.format(
                repr(attachment['market_album'])
            )
        )
    elif attachment['type'] == 'wall':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/wall: <not implemented>\n{}\n'.format(
                repr(attachment['wall'])
            )
        )
    elif attachment['type'] == 'wall_reply':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/wall_reply: <not implemented>\n{}\n'.format(
                repr(attachment['wall_reply'])
            )
        )
    elif attachment['type'] == 'sticker':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/sticker: <not implemented>\n{}\n'.format(
                repr(attachment['sticker'])
            )
        )
    elif attachment['type'] == 'gift':
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/gift: <not implemented>\n{}\n'.format(
                repr(attachment['gift'])
            )
        )
    else:
        tg_bot.send_message(
            tg_chat_id,
            'Attachment/unknown:\n{}\n'.format(repr(attachment))
        )


def process_message_from_vk(tg_bot, vk_funcs, event):
    u"""
    Обрабатывает сообщение из ВК.
    :param tg_bot: бот телеги
    :param vk_funcs: api контача
    :param event: объект Event с данными полученного сообщения
    """
    sender = get_sender_name(vk_funcs, event.user_id)

    if getattr(event, 'text', None):
        tg_bot.send_message(
            tg_chat_id,
            '{}:\n{}'.format(sender, event.text)
        )
    if getattr(event, 'attachments', {}):
        message_obj = vk_funcs.messages.getById(
            message_ids=str(event.message_id))['items'][0]
        for attachment in message_obj['attachments']:
            process_attachment_from_vk(tg_bot, vk_funcs, attachment)

    if (not getattr(event, 'text', None) and
            not getattr(event, 'attachments', {})):
        tg_bot.send_message(
            tg_chat_id,
            '{} что-то написал, но пока это не поддерживается'.format(sender)
        )


def tg_to_vk_dispatcher():
    """
    "Слушает" телегу, отправляет сообщения в контач.
    Также выполняет регу диалогов (см. /start).
    """
    @tg_bot.message_handler(func=lambda m: True)
    def callback(message):
        """
        В телегу пришло сообщение. Добавляем в очередь отправки.
        """
        if message.text.startswith('/start'):
            # Регистрация в телеге происходит следующим способом:
            # Пользователь вводит /start, запоминается id чатика в
            # телеге. Далее сообщения будут отправляться в этот чат.
            global tg_chat_id
            tg_chat_id = message.chat.id
            tg_bot.send_message(tg_chat_id, 'OK')
        else:
            if vk_chat_id:
                vk_funcs.messages.send(
                    peer_id=vk_chat_id, message=message.text
                )

    tg_bot.polling(none_stop=True)


def vk_to_tg_dispatcher():
    """
    "Слушает" контач, отправляет сообщения в телегу.
    Также выполняет регу диалогов (см. /start).
    """
    longpoll = VkLongPoll(vk_bot)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            # Регистрация в контаче аналогично регистрации в телеге:
            # запоминаем id пользователя, который регается.
            if event.text.startswith('/start'):
                global vk_chat_id
                vk_chat_id = event.peer_id
                vk_funcs.messages.send(peer_id=vk_chat_id, message='OK')

            else:
                if tg_chat_id:
                    process_message_from_vk(tg_bot, vk_funcs, event)


threads = (
    Thread(target=tg_to_vk_dispatcher),
    Thread(target=vk_to_tg_dispatcher),
)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
