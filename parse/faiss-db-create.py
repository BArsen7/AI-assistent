from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
import pandas as pd
import time
import re

print('инициализация')
# Инициализация HuggingFaceEmbeddings
model_name = "hkunlp/instructor-large" # "intfloat/multilingual-e5-large-instruct" #"hkunlp/instructor-large"
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': True}
hf_embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)
print("инициализация завершена")

#==============================ВК==============================#
# импорт предобработанных данных 
print("начинаю импорт данных")
all_docs = pd.read_csv('clean_data.csv')['c-text'].tolist()
print("завершён импорт данных")


"""
# импорт вбд
db = FAISS.load_local(
    "faiss_db2", hf_embedding, allow_dangerous_deserialization=True
)
"""
#db.similarity_search_with_score("текст") # поиск текста в вбд


# Встраивание и индексация всех документов с использованием FAISS
print(time.ctime(time.time()))
db = FAISS.from_texts(all_docs, hf_embedding)
print(time.ctime(time.time()))
print('...')
db.as_retriever()
print(time.ctime(time.time()))
print("Векторная база данных faiss_db_vk создана")
# Сохранение индексаированных данных локально
db.save_local("faiss_db_vk")
print("Векторная база данных faiss_db_vk сохранена")


#===========================Методичка===========================#

loader = Docx2txtLoader("MEPHI.docx")  # Открываем файл
# Разбиваем файл на чанки
text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=128)
data = loader.load_and_split(text_splitter)
# Очищаем полученные чанки
for chunk in data:
    chunk.page_content = re.sub("\\n", " ", chunk.page_content)
    chunk.page_content = re.sub(" +", " ", chunk.page_content)
    chunk.page_content = re.sub("\t", " ", chunk.page_content)
    
db = FAISS.from_documents(data, hf_embedding)
print('...')
db.as_retriever()
print("Векторная база данных faiss_db_policy создана")
# Сохранение индексаированных данных локально
db.save_local("faiss_db_policy")
print("Векторная база данных faiss_db_policy сохранена")