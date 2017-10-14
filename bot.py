# coding: utf-8

import os
import configparser

import telebot
import vk_api

from threading import Thread
from vk_api.longpoll import VkLongPoll, VkEventType

import helpers
import handlers


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


# Id чатов в телеге и контаче. Заполняются при регистрации через
# /start. К одному боту может быть привязан один собеседник (чат)
# в контаче, т. к. в противном случае неясно, кому доставлять
# сообщения из телеги.
tg_chat_id = None
vk_chat_id = None


# Тележечный бот
tg_bot = telebot.TeleBot(telegram_token)
# Контачевский бот
vk_bot = vk_api.VkApi(vk_login, vk_password)
vk_bot.auth()
vk_funcs = vk_bot.get_api()
vk_upload = vk_api.VkUpload(vk_bot)


def process_attachments_from_vk(event, message):
    """
    Обрабатывает прикрепленные к сообщению данные, такие как
    фото, аудио.
    :param event: уведомление боту о сообщении.
    :param message: объект с сообщением из ВК.
    """
    vk_attachment_handlers_map = {
        'photo': handlers.vk_photo,
        'video': handlers.vk_video,
        'audio': handlers.vk_audio,
        'doc': handlers.vk_doc,
        'link': handlers.vk_link,
        'sticker': handlers.vk_sticker,
    }

    handlers_found = False
    for attachment in message['attachments']:
        try:
            handler = vk_attachment_handlers_map[attachment['type']]
        except KeyError:
            pass
        else:
            handlers_found = True
            handler(
                tg_bot, vk_bot, vk_funcs, vk_upload,
                tg_chat_id, vk_chat_id,
                event, message, attachment
            )

    if not handlers_found and not getattr(event, 'text', None):
        vk_funcs.messages.send(
            peer_id=vk_chat_id,
            message='**[sys]** Message is empty or attachment type is not supported.',
        )


def process_fwd_from_vk(event, message_obj):
    """
    Обрабатывает форвард сообщений из ВК
    """
    text_parts = []
    for fwd_message in message_obj['fwd_messages']:
        sender_name = helpers.get_sender_name(vk_funcs, fwd_message['user_id'])
        text_parts.append(
            u'--- {} ---\n{}'.format(sender_name, fwd_message['body'])
        )
    text = '\n\n'.join(text_parts)

    sender = helpers.get_sender_name(vk_funcs, event.user_id)
    tg_bot.send_message(tg_chat_id, '{}: FWD:\n{}'.format(sender, text))


def process_message_from_vk(event):
    """
    Обрабатывает сообщение из ВК.
    :param event: объект Event с данными полученного сообщения
    """
    sender = helpers.get_sender_name(vk_funcs, event.user_id)

    if event.text:
        tg_bot.send_message(
            tg_chat_id,
            '{}:\n{}'.format(sender, event.text)
        )

    if getattr(event, 'attachments', {}):
        message_obj = vk_funcs.messages.getById(
            message_ids=str(event.message_id))['items'][0]

        if 'attachments' in message_obj:
            process_attachments_from_vk(event, message_obj)
        elif 'fwd_messages' in message_obj:
            process_fwd_from_vk(event, message_obj)


def process_attachment_from_tg(message):
    """
    Обрабатывает прикрепленные к сообщению данные, такие как
    фото, аудио.
    :param message: объект Message.
    """
    tg_attachment_handlers_map = {
        'photo': handlers.tg_photo,
        'sticker': handlers.tg_sticker,
        'document': handlers.tg_document,
        'voice': handlers.tg_voice,
        'audio': handlers.tg_audio,
    }

    handlers_to_execute = []
    for attr, handler in tg_attachment_handlers_map.items():
        if getattr(message, attr, None):
            handlers_to_execute.append(handler)

    if handlers_to_execute:
        for handler in handlers_to_execute:
            handler(
                tg_bot, vk_bot, vk_funcs, vk_upload,
                tg_chat_id, vk_chat_id,
                message
            )
    elif not message.text:
        tg_bot.send_message(
            tg_chat_id,
            '**[sys]** Message is empty or attachment type is not supported.',
            parse_mode='Markup'
        )


def process_message_from_tg(message):
    """
    Обрабатывает сообщение из телеги.
    :param message: объект Message с данными полученного сообщения
    """
    if message.text:
        vk_funcs.messages.send(
            peer_id=vk_chat_id, message=message.text
        )

    process_attachment_from_tg(message)


def notify_register_complete():
    """Уведомляет обе стороны об успешной регистрации.
    """
    message = 'VK peer id is {}, telegram peer id is {}. Ebites now.'.format(
        vk_chat_id, tg_chat_id
    )
    tg_bot.send_message(tg_chat_id, message)
    vk_funcs.messages.send(peer_id=vk_chat_id, message=message)


def tg_to_vk_dispatcher():
    """
    "Слушает" телегу, отправляет сообщения в контач.
    Также выполняет регу диалогов (см. /start).
    """
    # Подписываемся на все возможные типы данных, чтобы в случае чего дать
    # пользователю понять, что такой тип сообщения не принимается.
    content_types = [
        'audio', 'photo', 'sticker', 'video', 'video_note', 'new_chat_photo',
        'location', 'contact', 'new_chat_members', 'left_chat_member', 'text',
        'new_chat_title', 'new_chat_photo', 'delete_chat_photo', 'text',
        'group_chat_created', 'supergroup_chat_created', 'voice', 'document',
        'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id',
        'pinned_message',
    ]

    @tg_bot.message_handler(func=lambda m: True, content_types=content_types)
    def callback(message):
        """
        В телегу пришло сообщение. Добавляем в очередь отправки.
        """
        global tg_chat_id
        if (tg_chat_id is None and message.text and
                message.text.startswith('/start')):
            # Регистрация в телеге происходит следующим способом:
            # Пользователь вводит /start, запоминается id чатика в
            # телеге. Далее сообщения будут отправляться в этот чат.
            tg_chat_id = message.chat.id
            if vk_chat_id is not None:
                notify_register_complete()
            else:
                tg_bot.send_message(tg_chat_id, 'OK. Waiting for VK...')
        else:
            if vk_chat_id:
                process_message_from_tg(message)

    tg_bot.polling(none_stop=True)


def vk_to_tg_dispatcher():
    """
    "Слушает" контач, отправляет сообщения в телегу.
    Также выполняет регу диалогов (см. /start).
    """
    global vk_chat_id
    longpoll = VkLongPoll(vk_bot)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            # Регистрация в контаче аналогично регистрации в телеге:
            # запоминаем id пользователя, который регается.
            if vk_chat_id is None and event.text.startswith('/start'):
                vk_chat_id = event.peer_id
                if tg_chat_id is not None:
                    notify_register_complete()
                else:
                    vk_funcs.messages.send(
                        peer_id=vk_chat_id,
                        message='OK. Waiting for telegram...'
                    )

            else:
                if tg_chat_id:
                    process_message_from_vk(event)


threads = (
    Thread(target=tg_to_vk_dispatcher),
    Thread(target=vk_to_tg_dispatcher),
)

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
