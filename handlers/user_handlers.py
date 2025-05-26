from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.queries import (
    get_user_by_telegram_id,
    add_chat_message,
    get_last_messages,
    update_user_last_message,
    update_user_moderator_chat_status,
    create_user
)
from services.openai_service import openai_service
from services.vector_search import vector_search
from services.queue_service import process_moderator_notification
from config import config
import logging
import re
from datetime import datetime

# Создание роутера для обработки сообщений от пользователей
router = Router()

class RegistrationStates(StatesGroup):
    """
    Состояния процесса регистрации пользователя
    Определяет этапы регистрации и валидации данных
    """
    waiting_for_phone = State()  # Ожидание ввода номера телефона

def validate_phone_number(phone: str) -> bool:
    """
    Валидация номера телефона
    Проверяет соответствие номера формату +7XXXXXXXXXX или 8XXXXXXXXXX
    Args:
        phone: Номер телефона для проверки
    Returns:
        bool: True если номер валиден, иначе False
    """
    # Удаляем все нецифровые символы
    phone = re.sub(r'\D', '', phone)
    
    # Проверяем длину и формат
    if len(phone) == 11:
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        return phone.startswith('7')
    return False

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start
    Начинает процесс регистрации нового пользователя
    """
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            # Если пользователь не зарегистрирован, запрашиваем номер телефона
            await message.answer(config.MESSAGES["WELCOME"])
            await state.set_state(RegistrationStates.waiting_for_phone)
        else:
            # Если пользователь уже зарегистрирован, сообщаем об этом
            await message.answer("Вы уже зарегистрированы!")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /start: {str(e)}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """
    Обработчик ввода номера телефона
    Создает нового пользователя в базе данных
    """
    try:
        phone = message.text
        
        # Валидация номера телефона
        if not validate_phone_number(phone):
            await message.answer("Пожалуйста, введите корректный номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX")
            return
        
        # Нормализация номера телефона
        phone = re.sub(r'\D', '', phone)
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        
        # Создание пользователя в базе данных
        user = await create_user(message.from_user.id, phone)
        await message.answer(config.MESSAGES["REGISTRATION_SUCCESS"])
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка при регистрации пользователя: {str(e)}")
        await message.answer("Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        await state.clear()

@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help
    Подключает пользователя к модератору
    """
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if user:
            # Активируем режим чата с модератором
            await update_user_moderator_chat_status(user.telegram_id, True)
            await message.answer(config.MESSAGES["HELP_REQUEST"])
            
            # Уведомляем модераторов о новом запросе
            try:
                await process_moderator_notification.delay(
                    user_id=user.telegram_id,
                    message=f"Пользователь {user.telegram_id} запросил помощь"
                )
                logging.info(f"Отправлено уведомление модераторам о запросе пользователя {user.telegram_id}")
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомления модераторам: {str(e)}")
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /help: {str(e)}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.message(Command("end"))
async def cmd_end(message: Message):
    """
    Обработчик команды /end
    Завершает чат с модератором
    """
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if user and user.is_chatting_with_moderator:
            # Деактивируем режим чата с модератором
            await update_user_moderator_chat_status(user.telegram_id, False)
            await message.answer(config.MESSAGES["CHAT_ENDED"])
        elif user:
            await message.answer("Вы не находитесь в активном чате с модератором.")
    except Exception as e:
        logging.error(f"Ошибка при завершении чата с модератором: {str(e)}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.message()
async def handle_message(message: Message):
    """
    Обработчик всех остальных сообщений
    Обрабатывает обычные сообщения пользователя и генерирует ответы
    """
    try:
        # Проверяем регистрацию пользователя
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start")
            return

        if user.is_chatting_with_moderator:
            # Если пользователь в чате с модератором, пересылаем сообщение
            await add_chat_message(user.id, message.text, True, True)
            return

        # Обновляем время последнего сообщения пользователя
        await update_user_last_message(user.telegram_id)

        # Добавляем сообщение в историю чата
        await add_chat_message(user.id, message.text, True)

        # Получаем последние сообщения для контекста
        chat_history = await get_last_messages(user.id)
        formatted_messages = openai_service.format_messages(chat_history)

        try:
            # Получаем ответ от OpenAI
            response = await openai_service.get_chat_completion(formatted_messages)
            
            # Добавляем ответ бота в историю чата
            await add_chat_message(user.id, response, False)
            
            # Отправляем ответ пользователю
            await message.answer(response)
        except Exception as e:
            logging.error(f"Ошибка при получении ответа от OpenAI: {str(e)}")
            await message.answer("Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {str(e)}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.") 