from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.queries import (
    get_user_by_telegram_id,
    get_all_users,
    add_chat_message,
    update_user_moderator_chat_status
)
from config import config
import logging

# Создание роутера для обработки сообщений от модераторов
router = Router()

def is_moderator(user):
    """
    Проверяет, является ли пользователь модератором
    Args:
        user: Объект пользователя из базы данных
    Returns:
        bool: True если пользователь модератор, иначе False
    """
    return user and user.role == "MODERATOR"

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """
    Обработчик команды /broadcast
    Отправляет сообщение всем пользователям бота
    """
    # Проверяем права модератора
    user = await get_user_by_telegram_id(message.from_user.id)
    if not is_moderator(user):
        await message.answer("Недостаточно прав для выполнения операции")
        return

    # Получаем текст для рассылки (всё после команды /broadcast)
    broadcast_text = message.text.replace("/broadcast", "").strip()
    if not broadcast_text:
        await message.answer("Пожалуйста, укажите текст для рассылки")
        return

    # Получаем список всех пользователей
    users = await get_all_users()
    success_count = 0
    
    # Отправляем сообщение каждому пользователю
    for user in users:
        try:
            await message.bot.send_message(user.telegram_id, broadcast_text)
            success_count += 1
        except Exception as e:
            logging.error(f"Ошибка при отправке рассылки пользователю {user.telegram_id}: {str(e)}")

    await message.answer(f"Рассылка отправлена {success_count} пользователям")

@router.message(Command("end"))
async def cmd_end(message: Message):
    """
    Обработчик команды /end
    Завершает чат с конкретным пользователем
    """
    # Проверяем права модератора
    user = await get_user_by_telegram_id(message.from_user.id)
    if not is_moderator(user):
        await message.answer("Недостаточно прав для выполнения операции")
        return

    # Получаем ID пользователя из сообщения
    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("Пожалуйста, укажите ID пользователя: /end <user_id>")
        return

    # Получаем пользователя
    target_user = await get_user_by_telegram_id(user_id)
    if not target_user:
        await message.answer("Пользователь не найден")
        return

    # Проверяем, находится ли пользователь в чате с модератором
    if not target_user.is_chatting_with_moderator:
        await message.answer("Пользователь не находится в чате с модератором")
        return

    # Завершаем чат
    await update_user_moderator_chat_status(target_user.telegram_id, False)
    
    # Отправляем уведомления
    await message.answer(f"Чат с пользователем {user_id} завершен")
    try:
        await message.bot.send_message(
            target_user.telegram_id,
            config.MESSAGES["CHAT_ENDED"]
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления пользователю {user_id}: {str(e)}")
        await message.answer(f"Ошибка при отправке уведомления пользователю: {str(e)}")

@router.message(lambda message: message.text and message.text.startswith('/reply'))
async def handle_reply(message: Message):
    """
    Обработчик команды /reply
    Отправляет сообщение конкретному пользователю
    """
    # Проверяем права модератора
    user = await get_user_by_telegram_id(message.from_user.id)
    if not is_moderator(user):
        return

    # Проверяем формат сообщения: /reply <user_id> <message>
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("Используйте формат: /reply <user_id> <message>")
            return
        
        user_id = int(parts[1])
        reply_text = parts[2]
    except (IndexError, ValueError):
        await message.answer("Используйте формат: /reply <user_id> <message>")
        return

    # Получаем пользователя
    target_user = await get_user_by_telegram_id(user_id)
    if not target_user:
        await message.answer("Пользователь не найден")
        return

    # Проверяем, находится ли пользователь в чате с модератором
    if not target_user.is_chatting_with_moderator:
        await message.answer("Пользователь не находится в чате с модератором")
        return

    try:
        # Отправляем сообщение пользователю
        await message.bot.send_message(target_user.telegram_id, reply_text)
        
        # Сохраняем сообщение в истории
        await add_chat_message(target_user.id, reply_text, False, True)
        
        # Подтверждаем отправку модератору
        await message.answer(f"Сообщение отправлено пользователю {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {str(e)}")
        await message.answer(f"Ошибка при отправке сообщения: {str(e)}") 