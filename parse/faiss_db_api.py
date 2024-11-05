from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from pydantic import BaseModel
import re
import tempfile
import shutil

# Инициализация приложения FastAPI
app = FastAPI()


class Query(BaseModel):
    text: str
    number_doc_to_return: int


# Инициализация HuggingFaceEmbeddings
model_name = "hkunlp/instructor-large"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': True}
hf_embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)


# Загрузка базы данных FAISS
db_path = "faiss_db"
try:
    db = FAISS.load_local(db_path, hf_embedding, allow_dangerous_deserialization=True)
except Exception:
    empty_document = Document(page_content=" ")
    db = FAISS.from_documents([empty_document], hf_embedding)
    db.save_local(db_path) # Сохранение пустой вбд, если ее еще нет

# Конфигурация для разбиения текста на части
text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=128)


# Маршрут для поиска по запросу
@app.post("/search/")
async def search(query: Query):
    results = db.similarity_search(query.text, query.number_doc_to_return)
    context_str = "\n\n".join([n.page_content for n in results])
    return [{"content": context_str}]


# Маршрут для добавления нового документа
@app.post("/add_document/")
async def add_document(file: UploadFile = File(...)):
    if file.filename.endswith(".docx"):
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Записываем контент во временный файл
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name  # Сохраняем путь к временному файлу

        loader = Docx2txtLoader(tmp_path)  # Открываем файл
    elif file.filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        loader = PyMuPDFLoader(tmp_path)
    elif file.filename.endswith(".txt"):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        loader = TextLoader(tmp_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Разбиваем файл на чанки
    data = loader.load_and_split(text_splitter)
    # Очищаем полученные чанки
    for chunk in data:
        chunk.page_content = re.sub("\\n", " ", chunk.page_content)
        chunk.page_content = re.sub(" +", " ", chunk.page_content)
        chunk.page_content = re.sub("\t", " ", chunk.page_content)

    # Проверка на то, есть ли такая информация в вбд
    similarity_threshold = 0.2
    doc_add_to_db_flag = False
    for chunk in data:
        search_results = db.similarity_search_with_score(chunk.page_content, 1)
        if search_results[0][1] > similarity_threshold:
            # Если такой информации в вбд нет, добавляем в нее чанк
            db.add_documents(data)
            doc_add_to_db_flag = True

    if not doc_add_to_db_flag:
        return HTTPException(status_code=409, detail="Document already exists in the database")
    else:
        db.save_local(db_path)  # Сохраняем изменения в вбд
        return HTTPException(status_code=200, detail="Document added successfully") 
