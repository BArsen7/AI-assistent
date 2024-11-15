import time
import jwt
import json
import requests


def get_iam_token() -> str:
    # Чтение закрытого ключа из JSON-файла
    # JSON-файл с ключами создается в сервисном аккаунте (вкладка 'создать авторизованный ключ')
    with open('RAG/kyes.json', 'r') as f:
        obj = f.read()
        obj = json.loads(obj)
        private_key = obj['private_key']
        key_id = obj['id']
        service_account_id = obj['service_account_id']

    now = int(time.time())
    payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': service_account_id,
            'iat': now,
            'exp': now + 3600
        }

    # Формирование JWT
    encoded_token = jwt.encode(
        payload,
        private_key,
        algorithm='PS256',
        headers={'kid': key_id}
    )

    # URL для запроса
    url = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'

    # Тело запроса
    data = {
        "jwt": encoded_token
    }

    # Заголовки
    headers = {
        "Content-Type": "application/json"
    }

    # Выполнение POST-запроса на обмен jwt на iam_token
    response = requests.post(url, json=data, headers=headers)

    # Проверка и вывод ответа
    if response.status_code == 200:
        print('iamToken create successful')
        return response.json()['iamToken']
