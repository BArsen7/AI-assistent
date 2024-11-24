import asyncio

bot = True

async def start_faiss_db():
    # Запуск ВБД на порту 8975
    process_db = await asyncio.create_subprocess_exec(
        "uvicorn", "parse.faiss_db_api:app", "--host", "localhost", "--port", "8975"
    )
    await process_db.wait()


async def start_RAG():
    #  Запуск RAG на порту 8965
    process_rag = await asyncio.create_subprocess_exec(
        "uvicorn", "RAG.RAG_api:app", "--host", "localhost", "--port", "8965"
    )
    await process_rag.wait()

async def start_bot():
    # Запуск телеграм бота
    if bot:
        process_db = await asyncio.create_subprocess_exec("python", "bot.py")
    


async def main():
    # Параллельный запуск обоих процессов
    await asyncio.gather(start_faiss_db(), start_RAG(), start_bot())

asyncio.run(main())
