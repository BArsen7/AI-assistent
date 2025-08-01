import asyncio
#import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import random

# Функции для работы с базой данных операторов
from userdb import init_auth_user_db, is_authorized, authorize_user, deauthorize_user, get_all_authorized_users, logpasscheck

# Finite State Machine (для работы с состояниями юзера)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey


# Двунаправленный словарь operator_id <-> user_id (чтобы знать куда сообщения пересылать)
active_chats = {}

# Класс состояний пользователя
class UserStates(StatesGroup):
    waiting_for_question = State()
    active_dialog = State()

with open("telegram_token.txt") as f:
    token = f.readline() 

bot = Bot(token)

dp = Dispatcher(storage=MemoryStorage()) # FSM состояния пользователей храняться до перезапуска бота

#------------------------------------------------------------------------------

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_state = await state.get_state()

    # Кнопку показываем только если пользователь вне диалога
    if user_state not in [UserStates.waiting_for_question.state, UserStates.active_dialog.state]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Написать оператору", callback_data="ask_operator")]
            ])
        await message.answer("Привет! Я бот с искусственным интеллектом. Меня создали, чтобы помогать студентам НИЯУ МИФИ. Напиши мне свой вопрос — и я постараюсь тебе помочь. Также можешь написать оператору, воспользовавшись кнопкой ниже.",
            reply_markup=keyboard)
    else:
        await message.answer("Вы начали или собираетесь начать диалог с оператором. Если хотите отменить — нажмите кнопку отмены или используйте /end.")


# Обработка нажатия на кнопку "Написать оператору"
@dp.callback_query(lambda c: c.data == "ask_operator")
async def handle_operator_request(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)

    user_state = await state.get_state()
    
    if user_state == UserStates.active_dialog.state:
        await callback.answer("Вы уже начали диалог. Завершите текущий, прежде чем писать заново.", show_alert=True)
        return

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_before_dialog")]
        ])
    
    await state.set_state(UserStates.waiting_for_question)
    await callback.message.answer("Напишите свой вопрос оператору:", reply_markup=cancel_kb)
    await callback.answer()


# Обработка нажатия на кнопку отмены начала диалога с оператором
@dp.callback_query(lambda c: c.data == "cancel_before_dialog")
async def cancel_before_dialog(callback: types.CallbackQuery, state: FSMContext):
    user_state = await state.get_state()

    if user_state == UserStates.waiting_for_question.state:
        await state.clear()
        await callback.message.edit_text("Диалог отменён. Если передумаете — нажмите «Написать оператору» снова. Для появления кнопки введите команду /start.")
        await callback.answer()
    elif user_state == UserStates.active_dialog.state:
        await end_dialog(callback.from_user.id)  # message не передаём
        await callback.message.answer("Диалог завершён.")
        await callback.answer()
    else:
        await callback.answer("Вам нечего отменять :]", show_alert=True)


# Обработка первого сообщения от пользователя оператору (начала диалога с оператором)
@dp.message(UserStates.waiting_for_question)
async def receive_question(message: types.Message, state: FSMContext):
    operators = get_all_authorized_users()
    if not operators:
        await message.answer("Сейчас нет доступных операторов :/")
        await state.clear()
        return

    chosen_operator = random.choice(operators)
    operator_id = chosen_operator[0]
    user_id = message.from_user.id

    active_chats[operator_id] = user_id
    active_chats[user_id] = operator_id

    await state.set_state(UserStates.active_dialog)

    operator_context = FSMContext(storage=dp.storage, key=StorageKey(chat_id=operator_id, user_id=operator_id, bot_id=bot.id))
    await operator_context.set_state(UserStates.active_dialog)

    await bot.send_message(operator_id, f"Новый диалог с пользователем @{message.from_user.username or 'без имени'} (для завершения диалога введите /end):\n\n{message.text}")
    await message.answer("Вы соединены с оператором. Пишите сообщения, чтобы продолжить. Введите /end для завершения.")


# Пересылка сообщений в активном диалоге
@dp.message(~Command(commands=["end"]), UserStates.active_dialog)
async def route_message(message: types.Message):
    dude_id = message.from_user.id

    if dude_id in active_chats:
        partner_id = active_chats[dude_id]
        sender = "Оператор" if is_authorized(dude_id) else "Пользователь"
        await bot.send_message(partner_id, f"{sender}:\n{message.text}")
    else:
        await message.answer("Ошибка: вы по какой-то причине не находитесь в активном диалоге, но находитесь в состоянии active_dialog :/")


# Общая функция завершения диалога для /end и кнопки отмены
async def end_dialog(dude_id: int, message: types.Message = None):
    if dude_id not in active_chats:
        if message:
            await message.answer("У вас нет активного диалога :/")
        return

    partner_id = active_chats[dude_id]

    del active_chats[dude_id]
    if partner_id in active_chats:
        del active_chats[partner_id]

    dude_context = FSMContext(storage=dp.storage, key=StorageKey(chat_id=dude_id, user_id=dude_id, bot_id=bot.id))
    partner_context = FSMContext(storage=dp.storage, key=StorageKey(chat_id=partner_id, user_id=partner_id, bot_id=bot.id))

    await dude_context.clear()
    await partner_context.clear()

    await bot.send_message(partner_id, "Диалог завершён.")
    if message:
        await message.answer("Диалог завершён.")


# Команда завершения активного диалога
@dp.message(Command("end"), UserStates.active_dialog)
async def handle_end(message: types.Message):
    await end_dialog(message.from_user.id, message)


# Хэндлер команды /auth (вход в операторскую панель)
@dp.message(Command("auth"))
async def cmd_auth(message: types.Message):
    if is_authorized(message.from_user.id):
        await message.answer("Вы уже авторизованы. Для входа в другой аккаунт введите команду /logout и попробуйте снова.")
        return

    temp = message.text.strip().split()

    if len(temp) != 3:
        await message.answer("Введите: /auth <login> <password>")
        return
    
    curr_login, curr_password = temp[1], temp[2]
    
    if logpasscheck(curr_login, curr_password) is True:
        authorize_user(message.from_user.id)
        await message.answer(f"Вы авторизировались как {curr_login}")
    else:
        await message.answer("Неверный логин или пароль :/")


# Хэндлер команды /logout
@dp.message(Command("logout"))
async def cmd_logout(message: types.Message):
    user_id = message.from_user.id

    if is_authorized(user_id):
        deauthorize_user(user_id)
        await message.answer("Вы вышли из аккаунта.")
    else:
        await message.answer("Вы не авторизованы :/")


#Обработка сообщений
@dp.message()
async def cmd(message: types.Message):

    url = "http://127.0.0.1:8965/generate_answer?hellow"
    response = requests.post(url, json={"question": message.text})

    await message.answer(response.text[11:-2])


# Запуск процесса поллинга новых апдейтов
async def main():
    init_auth_user_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
