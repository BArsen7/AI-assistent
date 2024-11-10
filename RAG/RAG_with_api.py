import requests
from langchain_community.llms import YandexGPT
from langchain_core.prompts import PromptTemplate
from create_iam_token import get_iam_token


class RAG:
    def __init__(self):
        super().__init__()
        # Настройка LLM
        llm_name = "yandexgpt-lite"
        # Получаем iam_token
        iam_token = get_iam_token()

        self.yandex_gpt = YandexGPT(
            iam_token=iam_token,
            folder_id="b1ge2ut**********",
            model_name=llm_name,
            temperature=0.2
        )

        self.template = """Ты умный чат-бот. Ты любишь отвечать на вопросы пользователей, касающиеся студенческих активностей в НИЯУ МИФИ.\n
                Ниже представлена основная информация про студенческие активности в НИЯУ МИФИ:\n
                {context_str}\n
                На основе вышеуказанной информации, ответь на вопрос пользователя. В ответе укажи только содержательную часть без повторения вопроса.\n
                Вопрос: {query}\n
            """

        # URL для обращения к API векторной базы данных
        self.api_url = "http://127.0.0.1:8000"

    def search_db(self, query, k):
        # Выполнение POST-запроса к API для поиска
        search_url = f"{self.api_url}/search/"
        response = requests.post(search_url, json={"text": query, "number_doc_to_return": k})
        # Проверка ответа от API
        if response.status_code == 200:
            search_results = response.json()
            return [res["content"] for res in search_results]
        else:
            print("Ошибка при выполнении поиска:", response.status_code, response.text)
            return []

    def add_document(self, file_path):
        # Отправка документа на сервер для добавления в FAISS
        add_url = f"{self.api_url}/add_document/"

        # Открываем файл и отправляем запрос с файлом
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}
            response = requests.post(add_url, files=files)

        # Проверка ответа от API
        if response.status_code == 200:
            print("Документ успешно добавлен в базу данных")
            return response.json()
        else:
            print("Ошибка при добавлении документа:", response.status_code, response.text)
            return None

    def generate_answer(self, query):
        # Поиск в базе данных через API
        context_data = self.search_db(query, 6)
        context_str = "\n\n".join(context_data)

        # Создание промпта с контекстом
        prompt = PromptTemplate.from_template(self.template)
        inputs = {
            "context_str": context_str,
            "query": query
        }
        

        # Встраивание вопроса и контекста в промпт для LLM
        llm_sequence = prompt | self.yandex_gpt
        return llm_sequence.invoke(inputs)


rag = RAG()