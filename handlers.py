# coding: utf-8

import os
import io


def vk_photo(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        message, attachment):
    """Фото из ВК"""
    available_photo_sizes = (
        'photo_2560', 'photo_1280', 'photo_807', 'photo_604', 'photo_130',
        'photo_75')
    link = None
    for size_key in available_photo_sizes:
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


def vk_video(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        message, attachment):
    """Видео из ВК"""
    preview_link = None
    for size_key in 'photo_800', 'photo_640', 'photo_320', 'photo_130':
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


def vk_audio(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        message, attachment):
    """Аудио из ВК"""
    tg_bot.send_message(
        tg_chat_id,
        'Attachment/audio:\n{}\n{}\n{}\n'.format(
            attachment['audio']['artist'],
            attachment['audio']['title'],
            attachment['audio']['url'],
        )
    )


def vk_doc(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        message, attachment):
    """Документ из ВК"""
    tg_bot.send_message(
        tg_chat_id,
        'Attachment/doc:\n{}(ext is {})\n{}\n'.format(
            attachment['doc']['title'],
            attachment['doc']['ext'],
            attachment['doc']['url'],
        )
    )


def vk_link(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        message, attachment):
    """Ссылка в ВК (пока неизвестно, что это)"""
    tg_bot.send_message(
        tg_chat_id,
        'Attachment/link:\n{}(ext is {})\n{}\n'.format(
            attachment['link']['title'],
            attachment['link']['description'],
            attachment['link']['url'],
        )
    )



def vk_sticker(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        message, attachment):
    """Стикер в ВК"""
    tg_bot.send_message(
        tg_chat_id,
        'Attachment/sticker: <not implemented>\n{}\n'.format(
            repr(attachment['sticker'])
        )
    )


def _get_file_buffer_by_file_id(tg_bot, telegram_file_id):
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


def tg_photo(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id, message):
    """Фото из телеги"""
    file_size_obj = message.photo[-1]
    vk_uploaded_msg = vk_upload.photo_messages(
        _get_file_buffer_by_file_id(tg_bot, file_size_obj.file_id)
    )[0]
    vk_funcs.messages.send(
        peer_id=vk_chat_id,
        attachment='photo{}_{}'.format(
            vk_uploaded_msg['owner_id'], vk_uploaded_msg['id']),
        message=message.caption
    )


def tg_sticker(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id, message):
    """Стикер из телеги"""
    vk_uploaded_msg = vk_upload.document_wall(
        _get_file_buffer_by_file_id(tg_bot, message.sticker.file_id)
    )[0]
    vk_funcs.messages.send(
        peer_id=vk_chat_id,
        attachment='doc{}_{}'.format(
            vk_uploaded_msg['owner_id'], vk_uploaded_msg['id']),
        message='<document/sticker>'
    )


def tg_document(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id, message):
    """Документ из телеги"""
    vk_uploaded_msg = vk_upload.document(
        _get_file_buffer_by_file_id(tg_bot, message.document.file_id)
    )[0]
    vk_funcs.messages.send(
        peer_id=vk_chat_id,
        attachment='doc{}_{}'.format(
            vk_uploaded_msg['owner_id'], vk_uploaded_msg['id']),
        message='<document/file>'
    )


def tg_voice(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id, message):
    """Войсач из телеги"""
    vk_uploaded_msg = vk_upload.audio_message(
        _get_file_buffer_by_file_id(tg_bot, message.voice.file_id)
    )[0]
    vk_funcs.messages.send(
        peer_id=vk_chat_id,
        attachment='doc{}_{}'.format(
            vk_uploaded_msg['owner_id'], vk_uploaded_msg['id']),
        message='<document/audio>'
    )
