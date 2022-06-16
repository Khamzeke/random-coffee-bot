import asyncio
import random
from datetime import datetime, date, timedelta

import aioschedule as aioschedule
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext

import database
from cfg import BOT_TOKEN
from states import FSMData, UserState
from pprint import pprint
import sheet_base

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

after7days = InlineKeyboardButton(text='Пропущу неделю', callback_data='choice:week')
after30days = InlineKeyboardButton(text='Пропущу месяц..', callback_data='choice:month')
ready = InlineKeyboardButton(text='Да, конечно!', callback_data='choice:ready')

choice = InlineKeyboardMarkup().add(*[ready, after7days, after30days])


@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        'Привет! Каждую неделю я тебе буду отправлять человека, случайно выбранного из списка людей '
        'нашего сообщества!\n'
        'Для этого тебе придётся ответить на несколько вопросов, погнали!')
    await message.answer('Напиши имя и фамилию')
    await FSMData.name.set()
    await message.answer_chat_action('typing')


@dp.message_handler(state=FSMData.name)
async def getName(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('Где ты живешь?')
    await FSMData.next()


@dp.message_handler(state=FSMData.city)
async def getCity(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city'] = message.text
    await message.answer(
        'Пришли ссылку на свой профиль в любой соц. сети, где есть наиболее подробная информация о тебе.')
    await FSMData.next()


@dp.message_handler(state=FSMData.profile)
async def getProfile(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['profile'] = message.text
    await message.answer('В какой компании ты работаешь?')
    await FSMData.next()


@dp.message_handler(state=FSMData.company)
async def getCompany(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['company'] = message.text
    await message.answer('Какова твоя роль в компании?(Должность, позиция)')
    await FSMData.next()


@dp.message_handler(state=FSMData.role)
async def getRole(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['role'] = message.text
    await message.answer('Чем ты можешь быть полезен своему собеседнику?')
    await FSMData.next()


@dp.message_handler(state=FSMData.usefulness)
async def getUsefulness(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['usefulness'] = message.text
    async with state.proxy() as data:
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add('Хочу общаться')
        await message.answer(f"Отлично! Теперь ты зарегистрирован в нашей системе и твой профиль выглядит так:\n"
                             f"<b>Имя:</b> {data['name']}\n"
                             f"<b>Город:</b> {data['city']}\n"
                             f"<b>Компания:</b> {data['company']}\n"
                             f"<b>Занятие:</b> {data['role']}\n"
                             f"<b>О себе:</b> {data['usefulness']}\n\n"
                             f"Нажми <b>Хочу общаться</b> и я начну искать тебе собеседника для встречи!",
                             parse_mode='HTML'
                             , reply_markup=kb)
        database.addUser(message.from_user.id, data)
    await state.finish()


@dp.message_handler(state='*', text=['Хочу общаться'])
async def search(message: types.Message):
    await message.reply("Отлично, в скором времени я найду тебе собеседника, ожидай!")
    database.updateUserStatus(message.from_user.id, True)


async def findCompanion():
    users = database.getUsersByReadyStatus(True)
    users = random.sample(users, len(users))
    while len(users) > 1:
        try:
            await bot.send_chat_action(users[0][0],"typing")
        except:
            database.deleteUser(users[0][0])
            continue
        try:
            await bot.send_chat_action(users[1][0], "typing")
        except:
            database.deleteUser(users[1][0])
            continue

        database.createAppointment(users[0][0], users[1][0])
        database.makeReadyStatus(users[0][0], False)
        database.makeReadyStatus(users[1][0], False)
        try:
            button = InlineKeyboardButton('Написать собеседнику!', url=f"tg://user?id={users[0][0]}")
            await bot.send_message(users[1][0], f"Привет!👋​\n"
                                                f"Твоя пара в Random Coffee на эту неделю:\n"
                                                f"{users[0][1]}({users[0][2]})\n"
                                                f"Профиль - {users[0][3]}\n"
                                                f"Компания: {users[0][4]}\n"
                                                f"Должность: {users[0][5]}\n"
                                                f"Чем может быть полезен партнер: {users[0][6]}\n"
                                                f"\nНе откладывай, договорись о встрече сразу 🙂 ", parse_mode='HTML', reply_markup=InlineKeyboardMarkup().add(button))
        except:
            print(f'[ERROR] The user {users[1][0]} blocked the bot')
        try:
            button = InlineKeyboardButton('Написать собеседнику!', url=f"tg://user?id={users[1][0]}")
            await bot.send_message(users[0][0], f"Привет!👋​\n"
                                                f"Твоя пара в Random Coffee на эту неделю:\n"
                                                f"{users[1][1]}({users[1][2]})\n"
                                                f"Профиль - {users[1][3]}\n"
                                                f"Компания: {users[1][4]}\n"
                                                f"Должность: {users[1][5]}\n"
                                                f"Чем может быть полезен партнер: {users[1][6]}\n"
                                                f"\nНе откладывай, договорись о встрече сразу 🙂 ", parse_mode='HTML', reply_markup=InlineKeyboardMarkup().add(button))
        except:
            print(f'[ERROR] The user {users[0][0]} blocked the bot')
        users.remove(users[0])
        users.remove(users[0])


async def searching():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
        await asyncio.sleep(300)
        if datetime.now().weekday() == 3:  # monday and after 17:00
            database.clearAppointments()
            sheet_base.inputUsers(database.getUsers(), len(database.getUsers()))
            await findCompanion()
            sheet_base.inputAppointments(database.getAppointments(), len(database.getAppointments()))
        await asyncio.sleep(600)
        if datetime.now().weekday() == 3:  # wednesday and after 14:00
            users = database.getUsersByReadyStatus(False)
            for user in users:
                if database.getUserLastAppointment(user[0]) is not None:
                    #appointment = database.getUserLastAppointment(user[0])
                    findNewBtn = InlineKeyboardButton(text='Партнер не отвечает', callback_data='newcomp')
                    try:
                        await bot.send_message(user[0],
                                               "👋 Привет! Не забудь написать рэндом-собеседнику — это правда важно.\n"
                                               "Если же человек не отвечает на сообщения, нажми кнопку ниже, "
                                               "и я постараюсь подобрать новую пару 🎲",
                                               reply_markup=InlineKeyboardMarkup().add(findNewBtn))
                    except:
                        print(f'[ERROR] The user {user[0]} blocked the bot')
        await asyncio.sleep(600)
        if datetime.now().weekday() == 3:  # datetime.now().weekday() == 5 and datetime.now().hour == 14 and
            # datetime.now().minute = 3
            users = database.getUsersByReadyStatus(False)
            for user in users:
                if user[8] <= date.today():
                    try:
                        database.setAnswerDate(user[0],'week')
                        await bot.send_message(user[0],
                                               f"ВНИМАНИЕ, ЭТО ТЕСТИРОВАНИЕ! Если Вы хотите отказаться от тестирования, "
                                               f"напишите @yeapit\n\n"
                                               f"Привет!👋\n"
                                               f"Встречи Random Coffee продолжаются :)\n"
                                               f"Участвуешь на следующей неделе?", reply_markup=choice)
                    except:
                        print(f'[ERROR] The user {user[0]} blocked the bot')
            #database.execute(f"update users set ready=true where answer_date<= '{date.today()}'")
        await asyncio.sleep(20)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('choice:'))
async def getChoice(callback_query: types.CallbackQuery):
    text = callback_query.message.text
    if callback_query.data == 'choice:ready':
        database.makeReadyStatus(callback_query.from_user.id, True)
        database.setAnswerDate(callback_query.from_user.id, date.today())
        await callback_query.message.edit_text(text+"\n\n👉 Да, конечно!")
        await callback_query.message.answer('Отлично!👍\nНапишу тебе в понедельник.')
    elif callback_query.data == 'choice:week':
        database.makeReadyStatus(callback_query.from_user.id, False)
        database.setAnswerDate(callback_query.from_user.id, 'week')
        await callback_query.message.edit_text(text+"\n\n👉 Пропущу неделю")
        await callback_query.message.answer('Ок, записал! 👌\nНапишу тебе через неделю!')
    elif callback_query.data == 'choice:month':
        database.makeReadyStatus(callback_query.from_user.id, False)
        database.setAnswerDate(callback_query.from_user.id, 'month')
        await callback_query.message.edit_text(text+"\n\n👉 Пропущу месяц..")
        await callback_query.message.answer('Ок, записал! 👌\nНапишу тебе через месяц!')
    yes_btn = InlineKeyboardButton('Да, состоялась!', callback_data='event:yes')
    no_btn = InlineKeyboardButton('Нет, не состоялось...', callback_data='event:no')
    kb = InlineKeyboardMarkup().add(*[yes_btn, no_btn])
    await callback_query.message.answer(f'Небольшой опрос.\n'
                                        f'Состоялась ли встреча с {database.getUserCompanion(callback_query.from_user.id)[1]}?', reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('event:'))
async def eventListen(callback_query: types.CallbackQuery):
    text = callback_query.message.text
    if callback_query.data == 'event:yes':
        await callback_query.message.edit_text(text+'\n\n👉 Да, состоялась!')
        online_btn = InlineKeyboardButton('Онлайн', callback_data='event:online')
        offline_btn = InlineKeyboardButton('Вживую', callback_data='event:offline')
        await callback_query.message.answer('Вы встретились вживую или онлайн?', reply_markup=InlineKeyboardMarkup().add(*[offline_btn,online_btn]))
    elif callback_query.data == 'event:no':
        await callback_query.message.edit_text(text+'\n\n👉 Нет, не состоялось...')
        ignored_btn = InlineKeyboardButton('Не отвечал на сообщения', callback_data='event:online')
        _btn = InlineKeyboardButton('Вживую', callback_data='event:offline')
        await callback_query.message.answer('Чтобы лучше понимать, какую пару для тебя подбирать, расскажи, почему не подошел этот собеседник?',
                                            reply_markup=InlineKeyboardMarkup().add(*[]))

@dp.callback_query_handler(lambda c: c.data and c.data=='newcomp')
async def newCompanion(callback_query: types.CallbackQuery):
    text = callback_query.message.text
    await callback_query.message.edit_text(text+'\n\n👉 Партнер не отвечает')
    await callback_query.message.answer('Принято! Ищу новую пару. Это может занять некоторое время.')
    database.makeReadyStatus(callback_query.from_user.id, True)
    await findCompanion()


async def on_startup(_):
    sheet_base.inputUsers(database.getUsers(), len(database.getUsers()))
    asyncio.create_task(searching())
    sheet_base.inputAppointments(database.getAppointments(), len(database.getAppointments()))
    print('Бот успешно запущен!')


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
