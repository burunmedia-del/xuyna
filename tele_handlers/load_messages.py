from telethon import events
from xtelethon import CustomParseMode
from data.config import BOT_ID
from data.database import Database
from data.config import *
from datetime import datetime
import asyncio
import re
from telethon.tl.functions.channels import JoinChannelRequest


db = Database(MYSQL_host, MYSQL_user, MYSQL_password, MYSQL_database)


def fix_markdown_styles_in_links(text: str) -> str:
    """
    Исправляет markdown-стили внутри квадратных скобок ссылок,
    вынося их наружу, чтобы Telegram корректно отображал форматирование.
    Например:
    [**текст**](url) -> **[текст](url)**
    [_текст_](url) -> _[текст](url)_
    [~~текст~~](url) -> ~~[текст](url)~~
    """
    # Паттерн для поиска markdown стилей внутри квадратных скобок
    pattern = re.compile(r'\[((?:\*\*|__|\*|_|~~)+)?(.+?)(\1)?\]\((.+?)\)')

    def replacer(match):
        style_start = match.group(1) or ''
        inner_text = match.group(2)
        style_end = match.group(3) or ''
        url = match.group(4)
        # Выносим стили наружу
        return f'{style_start}[{inner_text}]({url}){style_end}'

    return pattern.sub(replacer, text)


def register_handlers(client):
    @client.on(events.NewMessage(incoming=True, from_users=BOT_ID))
    async def handle_new_message(event: events.NewMessage.Event):
        if event.message.message.strip().upper() == "ZAMENA":
            channel_id = replace_links_chat

            # Получаем все сообщения из канала
            all_messages = []
            async for msg in client.iter_messages(channel_id):
                all_messages.append(msg)
            all_messages.reverse()  # чтобы идти от первого к последнему

            # Последнее сообщение с айди и ссылками
            last_message = all_messages[-1]
            if not last_message.message:
                await event.reply("Последнее сообщение пустое, нет ссылок.")
                return

            # Получаем айди из первой строки
            user_id_line = last_message.message.split('\n')[0].strip()
            last_message_id = last_message.id
            first_message_id = all_messages[1].id
            try:
                user_id = int(user_id_line)
            except ValueError:
                await event.reply("Не удалось получить числовой ID из первой строки последнего сообщения.")
                return

            # Парсим ссылки из остальных строк
            lines = last_message.message.split('\n')[1:]
            LINKS = []
            for line in lines:
                parts = line.split('—')
                if len(parts) == 2:
                    first_part = parts[0].strip()  # например, "@usertag 27.05 700"
                    second_part = parts[1].strip() # ссылка
                    LINKS.append((first_part, second_part))

            # Сообщения для обработки — все кроме последнего
            messages_to_process = all_messages[:-1]

            url_pattern = r'https?://[^\s)]+|www\.[^\s)]+'

            parser = CustomParseMode('markdown')

            # Отправляем сообщение с айди
            await client.send_message(
                entity=await event.get_input_chat(),
                message=f'Отправка постов\nid={user_id}'
            )

            for link in LINKS:
                for event_msg in messages_to_process:
                    if not event_msg.message:
                        continue

                    text = event_msg.message or ""
                    entities = event_msg.entities
                    markdown_text = parser.unparse(text, entities) if entities else text

                    # Исправляем markdown-стили внутри ссылок
                    markdown_text = fix_markdown_styles_in_links(markdown_text)

                    replaced_text = re.sub(url_pattern, link[1], markdown_text)

                    if event_msg.media:
                        await client.send_file(
                            entity=await event.get_input_chat(),
                            file=event_msg.media,
                            caption=replaced_text,
                            caption_parse_mode=parser,
                        )
                    else:
                        await client.send_message(
                            entity=await event.get_input_chat(),
                            message=replaced_text,
                            parse_mode=parser,
                            link_preview=False
                        )

                await asyncio.sleep(0.1)
                await client.send_message(
                    entity=await event.get_input_chat(),
                    message=link[0],
                    parse_mode=parser
                )
                await asyncio.sleep(0.1)
                await client.send_message(
                    entity=await event.get_input_chat(),
                    message='______________________________'
                )
                await asyncio.sleep(0.5)

            await client.send_message(
                entity=await event.get_input_chat(),
                message=f'стоп {first_message_id}-{last_message_id}',
            )

