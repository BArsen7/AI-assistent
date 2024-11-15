from fastapi import FastAPI
from .RAG import rag
from pydantic import BaseModel

# Инициализация FastAPI
app = FastAPI()


class Request(BaseModel):
    question: str


class Response(BaseModel):
    answer: str


# Маршрут для генерации ответа
@app.post("/generate_answer")
async def predict_sentiment(request: Request):
    text = request.question

    answer = rag.generate_answer(text)
    response = Response(answer=answer)
    return response
