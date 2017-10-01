# coding: utf-8

import helpers


def vk_photo(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        event, message, attachment):
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
        sender_name = helpers.get_sender_name(vk_funcs, event.user_id)
        tg_bot.send_message(
            tg_chat_id,
            '{}:\n{}\n{}'.format(
                sender_name,
                attachment['photo']['text'],
                link
            )
        )


def vk_video(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        event, message, attachment):
    """Видео из ВК"""
    preview_link = None
    for size_key in 'photo_800', 'photo_640', 'photo_320', 'photo_130':
        if attachment['video'].get(size_key):
            preview_link = attachment['video'][size_key]
            break
    if preview_link is not None:
        sender_name = helpers.get_sender_name(vk_funcs, event.user_id)
        tg_bot.send_message(
            tg_chat_id,
            '{}:\n{}\n{}\n{}\n{}\n'.format(
                sender_name,
                attachment['video']['title'],
                attachment['video']['description'],
                preview_link,
                attachment['video'].get('player', '<no link>'),
            )
        )


def vk_audio(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        event, message, attachment):
    """Аудио из ВК"""
    sender_name = helpers.get_sender_name(vk_funcs, event.user_id)
    tg_bot.send_message(
        tg_chat_id,
        '{}:\n{}\n{}\n{}\n'.format(
            sender_name,
            attachment['audio']['artist'],
            attachment['audio']['title'],
            attachment['audio']['url'],
        )
    )


def vk_doc(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        event, message, attachment):
    """Документ из ВК"""
    sender_name = helpers.get_sender_name(vk_funcs, event.user_id)
    tg_bot.send_message(
        tg_chat_id,
        '{}:\n{} (ext={})\n{}\n'.format(
            sender_name,
            attachment['doc']['title'],
            attachment['doc']['ext'],
            attachment['doc']['url'],
        )
    )


def vk_link(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        event, message, attachment):
    """Ссылка в ВК (пока неизвестно, что это)"""
    sender_name = helpers.get_sender_name(vk_funcs, event.user_id)
    tg_bot.send_message(
        tg_chat_id,
        '{}:\n{}\n{}\n{}\n'.format(
            sender_name,
            attachment['link']['title'],
            attachment['link']['description'],
            attachment['link']['url'],
        )
    )


def vk_sticker(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id,
        event, message, attachment):
    """Стикер в ВК"""
    size_keys = (
        'photo_512', 'photo_352', 'photo_256', 'photo_128', 'photo_64')
    sticker = attachment['sticker']
    url = None
    for size_key in size_keys:
        if size_key in sticker:
            url = sticker[size_key]
            break
    if url is not None:
        sender_name = helpers.get_sender_name(vk_funcs, event.user_id)
        tg_bot.send_message(
            tg_chat_id,
            '{}:\n{}\n'.format(sender_name, url)
        )


def tg_photo(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id, message):
    """Фото из телеги"""
    file_size_obj = message.photo[-1]
    vk_uploaded_msg = vk_upload.photo_messages(
        helpers.get_file_buffer_by_file_id(tg_bot, file_size_obj.file_id)
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
        helpers.get_file_buffer_by_file_id(tg_bot, message.sticker.file_id)
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
        helpers.get_file_buffer_by_file_id(tg_bot, message.document.file_id)
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
        helpers.get_file_buffer_by_file_id(tg_bot, message.voice.file_id)
    )[0]
    vk_funcs.messages.send(
        peer_id=vk_chat_id,
        attachment='doc{}_{}'.format(
            vk_uploaded_msg['owner_id'], vk_uploaded_msg['id']),
        message='<document/audio>'
    )


def tg_audio(
        tg_bot, vk_bot, vk_funcs, vk_upload, tg_chat_id, vk_chat_id, message):
    """Аудио из телеги"""
    vk_uploaded_msg = vk_upload.audio(
        helpers.get_file_buffer_by_file_id(tg_bot, message.audio.file_id),
        message.audio.performer or 'Unknown',
        message.audio.title or 'Unknown',
    )
    vk_funcs.messages.send(
        peer_id=vk_chat_id,
        attachment='audio{}_{}'.format(
            vk_uploaded_msg['owner_id'], vk_uploaded_msg['id']),
        message=message.audio.title
    )
