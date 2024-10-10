import requests

# переменные 
TOKEN_USER =  #токен пользователя
VERSION = 5.131 # используемая версия апи
DOMAIN =  'mephi_official' #имя сообщества из адресной строки

# через api vk вызываем статистику постов
response = requests.get('https://api.vk.com/method/wall.get',
params={'access_token': TOKEN_USER,
        'v': VERSION,
        'domain': DOMAIN,
        'count': 1, # max = 100
        'filter': str('owner')})


data = response.json() 

print (data)
