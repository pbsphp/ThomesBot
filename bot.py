# coding: utf-8

import re
import os
import configparser

import telebot
import vk_api

from queue import Queue
from threading import Thread
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
                print('Send to VK: ', message.text)
                vk_funcs.messages.send(
                    user_id=vk_chat_id, message=message.text
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
                vk_chat_id = event.user_id
                vk_funcs.messages.send(user_id=vk_chat_id, message='OK')

            else:
                if tg_chat_id:
                    tg_bot.send_message(tg_chat_id, event.text)


threads = (
    Thread(target=tg_to_vk_dispatcher),
    Thread(target=vk_to_tg_dispatcher),
)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
