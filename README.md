ThomesBot - бот для коммуникации между ВК и телегой
===================================================

Перенаправляет переписку из в ВК в Телеграм и наоборот. Позволяет переписываться из Телеграма с пользователем (или чатом) в ВК. Может быть полезен если нужно вести коммуникацию с определенными пользователями в ВК не сидя при этом в ВК.

Установка
---------
1. Установить requirements.txt.
2. Скопировать config_example.ini в config.ini, заполнить там тележечный токен и логпасс из ВК.

Использование
-------------
1. python bot.py.
2. Написать /start боту в телеграме. После этого бот будет отсылать вам принятые сообщения.
3. Написать /start аккаунту в ВК, который указан в config.ini. Можно добавить в чат и написать там. После этого аккаунт будет отвечать вам сообщениями из Телеграма.

Что не так?
-----------
1. Могут не работать некоторые типы сообщений.
2. Нельзя использовать несколько аккаунтов для одного бота, т.к. в этом случае при отправке всех сообщений приходилось бы указывать адресатов.