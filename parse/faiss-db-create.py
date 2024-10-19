from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import pandas as pd

print('инициализация')
# Инициализация HuggingFaceEmbeddings
model_name = "hkunlp/instructor-large"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': True}
hf_embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# импорт предобработанных данных 
print("начинаю импорт данных")
all_docs = pd.read_csv('clean_data.csv')['c-text'].tolist()
print("завершён импорт данных")


 
""" импорт вбд
db = FAISS.load_local(
    "faiss_db", hf_embedding, allow_dangerous_deserialization=True
)
"""
#db.similarity_search_with_score("текст") # поиск текста в вбд


# Встраивание и индексация всех документов с использованием FAISS
db = FAISS.from_texts(all_docs, hf_embedding)
print('...')
db.as_retriever()
print("Векторная база данных создана")
# Сохранение индексаированных данных локально
db.save_local("faiss_db")
print("Векторная база данных сохранена")


