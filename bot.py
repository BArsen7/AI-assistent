import asyncio
#import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# Функции для работы с базой данных операторов
from authdb import init_auth_db, is_authorized, authorize_user, deauthorize_user, get_all_authorized_users, logpasscheck

# Функции для работы с базой данных лога диалогов
from operchatlogdb import init_chatlog_db, add_message, get_inbox, detach_operator, get_history, SEPARATOR

# Finite State Machine (для работы с состояниями юзера)
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey

# Для опроса
import csv
import os

# Двунаправленный словарь operator_id <-> user_id (чтобы знать куда сообщения пересылать)
active_chats = {}

# Класс состояний любого пользователя
class UserStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()
    active_dialog = State()
    survey = State()

# Класс состояний оператора
class OperatorStates(StatesGroup):
    picking_inbox = State()

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
    if user_state is None:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Написать оператору", callback_data="ask_operator"),
                InlineKeyboardButton(text="Пройти опрос", callback_data="start_survey")
            ]
        ])
        await message.answer("Привет! Я бот с искусственным интеллектом. Меня создали, чтобы помогать студентам НИЯУ МИФИ. Напиши мне свой вопрос — и я постараюсь тебе помочь. Также можешь написать оператору, воспользовавшись кнопкой ниже. Для вывода списка команд введи /help.",
            reply_markup=keyboard)
    elif user_state == UserStates.waiting_for_answer.state:
        await message.answer("Пока ожидаешь ответ оператора, можешь продолжать переписываться со мной! Буду рад попытаться ответить на твои вопросы.")
    elif user_state in [UserStates.active_dialog.state, UserStates.waiting_for_question.state]:
        await message.answer("Вы начали или собираетесь начать диалог с оператором. Если хотите отменить — нажмите кнопку отмены или используйте /end.")
    elif user_state == UserStates.survey.state:
        await message.answer("Для начала пройди опрос!")
    else:
        await message.answer("Заготовка для других состояний.")


# --- ДИАЛОГ С ОПЕРАТОРОМ ---


# Хэндлер кнопки "Написать оператору"
@dp.callback_query(lambda c: c.data == "ask_operator")
async def handle_operator_request(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)

    user_state = await state.get_state()
    
    if user_state in [UserStates.active_dialog.state, UserStates.waiting_for_question.state, UserStates.waiting_for_answer.state]:
        await callback.answer("Вы уже начали диалог. Завершите текущий, прежде чем писать заново.", show_alert=True)
        return

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_before_dialog")]
        ])
    
    await state.set_state(UserStates.waiting_for_question)
    await callback.message.answer("Напишите свой вопрос оператору:", reply_markup=cancel_kb)
    await callback.answer()


# Хэндлер кнопки отмены начала диалога с оператором (или завершения диалога через неё)
@dp.callback_query(lambda c: c.data == "cancel_before_dialog")
async def cancel_before_dialog(callback: types.CallbackQuery, state: FSMContext):
    user_state = await state.get_state()

    if user_state == UserStates.waiting_for_question.state:
        await state.clear()
        await callback.message.edit_text("Диалог отменён. Если передумаете — нажмите «Написать оператору» снова. Для появления кнопки введите команду /start.")
    elif user_state == UserStates.active_dialog.state:
        await end_dialog(callback.from_user.id)  # message не передаём
        await callback.message.answer("Диалог завершён.")
    else:
        await callback.answer("Вам нечего отменять :]", show_alert=True)
    
    await callback.answer()


# Обработка первого сообщения от пользователя оператору (начала диалога с оператором)
@dp.message(UserStates.waiting_for_question)
async def receive_question(message: types.Message, state: FSMContext):
    operators = get_all_authorized_users()
    if not operators:
        await message.answer("Сейчас нет доступных операторов :/")
        await state.clear()
        return
    
    user_id = message.from_user.id
    username = message.from_user.username or "без имени"
    msg_text = message.text

    add_message(user_id, new_message = msg_text + " ——— from id: " + str(user_id))

    for op_id, in operators: # рассылаем всем операторам уведомление
        try:
            await bot.send_message(
                op_id,
                f"Новое сообщение от пользователя @{username} (id: {user_id}):\n\n{msg_text}\n\nДля ответа введите команду /inbox и выберите данного пользователя."
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение оператору {op_id}: {e}")

    await message.answer("Ваше сообщение отправлено операторам. Ожидайте ответа.")
    await state.clear()
    await state.set_state(UserStates.waiting_for_answer)


# Команда /inbox для просмотра операторами входящих сообщений и последующего ответа на них
@dp.message(Command("inbox"))
async def cmd_inbox(message: types.Message, state: FSMContext):
    if not is_authorized(message.from_user.id):
        await message.answer("Вы не авторизованы, команда недоступна.")
        return

    inbox = get_inbox()
    if not inbox:
        await message.answer("Нет новых сообщений от пользователей.")
        return

    await state.set_state(OperatorStates.picking_inbox)
    await state.update_data(inbox=inbox)

    text = "Список входящих сообщений:\n"
    for idx, (user_id, history) in enumerate(inbox, start=1):
        # Пытаемся вытащить имя пользователя, если не выходит, оставляем айдишник
        try:
            user = await bot.get_chat(user_id)
            name = f"@{user.username}" if user.username else f"{user.first_name or 'Пользователь'}"
        except Exception:
            name = f"id:{user_id}"
    
        separator = SEPARATOR
        parts = history.split(separator)
        last_message = parts[-1].strip() if parts else "Нет сообщений"
        preview = last_message.replace('\n', ' ')
        text += f"{idx}) {name}: {preview}\n"

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_dialog_pick")]
        ])

    text += "\nНапиши номер диалога для начала общения:"
    await message.answer(text, reply_markup=cancel_kb)


# Хэндлер кнопки отмены выбора диалога (выхода из inbox) (или завершения диалога через неё)
@dp.callback_query(lambda c: c.data == "cancel_dialog_pick")
async def cancel_dialog_pick(callback: types.CallbackQuery, state: FSMContext):
    user_state = await state.get_state()
    
    if user_state == OperatorStates.picking_inbox.state:
        await callback.message.edit_text("Выбор диалога отменён.")
        await state.clear()
        await callback.answer()
    elif user_state == UserStates.active_dialog.state:
        await end_dialog(callback.from_user.id)  # message не передаём
        await callback.message.answer("Диалог завершён.")
        await callback.answer()
    else:
        await callback.answer("Вам нечего отменять :]", show_alert=True)


# Начало диалога после выбора сообщения для ответа из inbox'а
@dp.message(OperatorStates.picking_inbox)
async def handle_inbox_choice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inbox = data.get("inbox", [])

    try:
        choice = int(message.text.strip())
        if not (1 <= choice <= len(inbox)):
            raise ValueError
    except ValueError:
        await message.answer("Неверный номер. Попробуй ещё раз.")
        return

    user_id, _ = inbox[choice - 1]
    operator_id = message.from_user.id

    # Просто вызываем add_message с пустым сообщением, он сам привяжет оператора
    add_message(user_id, operator_id)

    await state.clear()
    await state.set_state(UserStates.active_dialog)

    partner_context = FSMContext(
        storage=dp.storage,
        key=StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id),
    )
    await partner_context.set_state(UserStates.active_dialog)

    active_chats[operator_id] = user_id
    active_chats[user_id] = operator_id

    await message.answer(f"Вы подключились к диалогу с пользователем {user_id}. Можете начинать переписку. Для завершения диалога введите /end.")
    await bot.send_message(user_id, "Оператор подключился к вашему диалогу. Для завершения диалога введите /end.")


# Пересылка сообщений в активном диалоге
@dp.message(~Command(commands=["end"]), UserStates.active_dialog)
async def route_message(message: types.Message):
    dude_id = message.from_user.id

    if dude_id in active_chats:
        partner_id = active_chats[dude_id]

        if is_authorized(dude_id):
            sender = "Оператор"
            add_message(partner_id, dude_id, message.text + " ——— from id: " + str(dude_id))
        else:
            sender = "Пользователь"
            add_message(dude_id, partner_id, message.text + " ——— from id: " + str(dude_id))


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

    if is_authorized(dude_id):
        detach_operator(partner_id)
    else:
        detach_operator(dude_id)

    dude_context = FSMContext(storage=dp.storage, key=StorageKey(chat_id=dude_id, user_id=dude_id, bot_id=bot.id))
    partner_context = FSMContext(storage=dp.storage, key=StorageKey(chat_id=partner_id, user_id=partner_id, bot_id=bot.id))

    await dude_context.clear()
    await partner_context.clear()

    await bot.send_message(partner_id, "Диалог завершён.")
    if message:
        await message.answer("Диалог завершён.")


# Команда /end завершения активного диалога
@dp.message(Command("end"), UserStates.active_dialog)
async def cmd_end(message: types.Message):
    await end_dialog(message.from_user.id, message)


# Команда /history получения истории диалога с оператором/пользователем
@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    records = get_history(message.from_user.id)

    if not records:
        await message.answer("История пуста.")
        return

    text_chunks = []
    for i, (other_id, history) in enumerate(records, start=1):
        # Показываем только первые 1000 символов истории, если она большая
        history_preview = history[-1000:] if len(history) > 1000 else history

        text_chunks.append(f"Диалог #{i} с ID {other_id}:\n{history_preview}\n")

    # Делим на части, если слишком длинно
    max_len = 4000
    for chunk in text_chunks:
        for i in range(0, len(chunk), max_len):
            await message.answer(chunk[i:i+max_len])


# --- АУТЕНТИФИКАЦИЯ ---


# Хэндлер команды /auth (вход в операторскую панель)
@dp.message(Command("auth"))
async def cmd_auth(message: types.Message):
    # (!) Возможно в будущем следовало бы проверять ещё и вошёл ли кто с текущим аккаунтом, а не только айдишником
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


# --- ОПРОС ---


# Список вопросов
questions = [
    "1️. В каких олимпиадах, конкурсах или проектах ты принимал(а) участие за последние 2-3 года? Какие из них запомнились больше всего и почему?",
    "2️. Какие школьные предметы или направления науки/техники тебе нравились больше всего? Что именно в них было интересным?",
    "3️. Делал(а) ли ты какие-либо личные или учебные проекты (технические, исследовательские, творческие)? Если да, расскажи кратко о самом интересном.",
    "4️. Что повлияло на твой выбор направления обучения в МИФИ?",
    "5️. Участвовал(а) ли ты в школьном самоуправлении, волонтерских проектах или других общественных активностях? Если да, расскажи о своем опыте.",
    "6️. Увлекаешься ли ты каким-либо видом спорта или активного отдыха?",
    "7. Есть ли у тебя творческие увлечения или хобби? Расскажи о них немного.",
    "8. Есть ли какая-то область знаний или сфера деятельности, которая тебя особенно привлекает и в которой ты хотел(а) бы развиваться глубоко?",
    "9. Хочешь ли ты что-то добавить о своих интересах, планах или ожиданиях?"
]

CSV_SURV = "survey_results.csv"

surv_prog = {}

# Создаём CSV файл, если его нет
if not os.path.exists(CSV_SURV):
    with open(CSV_SURV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id"] + [f"Вопрос {i+1}" for i in range(len(questions))])


# Хэндлер кнопки "Пройти опрос"
@dp.callback_query(lambda c: c.data == "start_survey")
async def handle_start_survey(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.set_state(UserStates.survey)
    surv_prog[callback.from_user.id] = {"step": 0, "answers": []}

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_survey")]
        ])
    
    await callback.message.answer(f"Опрос состоит из {len(questions)} вопросов. После ответа на последний вопрос все данные автоматически сохранятся.\n\n{questions[0]}",
                                   reply_markup=cancel_kb)
    await callback.answer()
    # возможна реализация опционально-анонимного опроса


# Хэндлер кнопки отмены прохождения опроса
@dp.callback_query(lambda c: c.data == "cancel_survey")
async def cancel_survey(callback: types.CallbackQuery, state: FSMContext):
    user_state = await state.get_state()

    if user_state != UserStates.survey.state:
        await callback.answer("Вы не проходите опрос", show_alert=True)
    else:
        surv_prog.pop(callback.from_user.id, None)
        await state.clear()
        await callback.message.answer("Опрос отменён.")
    await callback.answer()


# Прохождение опроса и обработка результатов
@dp.message(UserStates.survey)
async def survey(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id not in surv_prog:
        await message.answer("Ошибка: вы не начали опрос. Нажмите кнопку 'Пройти опрос'.")
        await state.clear()
        return
    
    prog = surv_prog[user_id]
    prog["answers"].append(message.text)
    prog["step"] += 1

    if prog["step"] >= len(questions): # заканчиваем опрос
        with open(CSV_SURV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([user_id] + prog["answers"])

        await message.answer("Спасибо! Опрос завершён, ответы сохранены.")
        surv_prog.pop(user_id, None)
        await state.clear()
    else: # следующий вопрос
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_survey")]
        ])
        await message.answer(questions[prog["step"]], reply_markup=cancel_kb)


# --- ДРУГОЕ ---


# Хэндлер команды /help
# (!) Возможно в будущем доделать поведение для разных стейтов пользователей
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    user_id = message.from_user.id

    ans = "/help — список доступных команд\n"
    ans += "/start — начало (вызов кнопок \"Написать оператору\" и \"Пройти опрос\")\n"
    if is_authorized(user_id):
        ans += "/inbox — список входящих сообщений\n"
        ans += "/history — просмотр истории всех диалогов с вашим участием\n"
        ans += "/logout — выход из аккаунта"
    else:
        ans += "/history — просмотр истории диалогов с оператором\n"
        ans += "/auth <login> <password> — вход в аккаунт оператора"
    await message.answer(ans)


# Обработка сообщений
@dp.message(StateFilter(None, UserStates.waiting_for_answer))
async def cmd(message: types.Message):

    url = "http://127.0.0.1:8965/generate_answer?hellow"
    response = requests.post(url, json={"question": message.text})

    await message.answer(response.text[11:-2])


# Запуск процесса поллинга новых апдейтов
async def main():
    init_auth_db()
    init_chatlog_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
