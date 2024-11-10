from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import pandas as pd
import time


print('инициализация')
# Инициализация HuggingFaceEmbeddings
model_name = "intfloat/multilingual-e5-large-instruct" #"hkunlp/instructor-large"
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': True}
hf_embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)
print("инициализация завершена")

# импорт предобработанных данных 
print("начинаю импорт данных")
all_docs = pd.read_csv('clean_data.csv')['c-text'].tolist()
print("завершён импорт данных")


"""
# импорт вбд
db = FAISS.load_local(
    "faiss_db2", hf_embedding, allow_dangerous_deserialization=True
)

#db.similarity_search_with_score("текст")
while True:
    text = input("\nвведите текст для поиска: ")
    print(db.similarity_search_with_score(text, k=10))
"""
#db.similarity_search_with_score("текст") # поиск текста в вбд


# Встраивание и индексация всех документов с использованием FAISS
print(time.ctime(time.time()))
db = FAISS.from_texts(all_docs, hf_embedding)
print(time.ctime(time.time()))
print('...')
db.as_retriever()
print(time.ctime(time.time()))
print("Векторная база данных создана")
# Сохранение индексаированных данных локально
db.save_local("faiss_db")
print("Векторная база данных сохранена")



