from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

db_name = "faiss_db_base" #faiss_db_large

# Инициализация HuggingFaceEmbeddings
model_name = "intfloat/multilingual-e5-large-instruct" 
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': True}
hf_embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# импорт вбд
db = FAISS.load_local(
    db_name, hf_embedding, allow_dangerous_deserialization=True
)

#db.similarity_search_with_score("текст")
while True:
    text = input("\nВведите текст для поиска: ")
    print(db.similarity_search_with_score(text, k=5))
