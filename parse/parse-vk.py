import requests
import json
import time
import pandas as pd

# переменные 
TOKEN_USER = "" #токен пользователя
VERSION = 5.131 # используемая версия апи
DOMAIN = 'snomephi' #'vmephi'  #'reactorclub' #'mephi_official' #'osomephi' #имя сообщества из адресной строки  mephi_official



array = []
date =  time.time()
i = 0

while date > 1693515599: #парсинг с первого сентября 2023 года 1693515599
	# через api vk вызываем статистику постов
	response = requests.get('https://api.vk.com/method/wall.get',
	params={'access_token': TOKEN_USER,
        	'v': VERSION,
        	'domain': DOMAIN,
		'offset': i,
        	'count': 100,
        	'filter': str('owner')})

	data = response.json()['response']['items']
	print("получено 100 записей")
	for j in range(100):
		date = data[j]['date']
		#print(i*100+j, time.ctime(date)) #, data[i*100+j]['text'])
		array.append( [i*100+j,time.ctime(date),data[j]['id'], data[j]['text']]) 
	i+=1
	pd.DataFrame(array,columns= ['i', 'time', 'id', 'text']).to_csv(f"{DOMAIN}.csv", index=False)




