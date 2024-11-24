import asyncio
#import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
import requests


with open("telegram_token.txt") as f:
    token = f.readline() 

bot = Bot(token)

dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот с искуственным интелектом. Меня создали чтобы помогать студентам НИЯУ МИФИ. Напиши мне свой вопрос и я постораюсь тебе помочь.")

#Обработка сообщей
@dp.message()
async def cmd(message: types.Message):

    url = "http://127.0.0.1:8965/generate_answer?hellow"
    response = requests.post(url, json={"question": message.text})

    await message.answer(response.text[11:-2])


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
