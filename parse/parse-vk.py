import requests
import json
import time
import pandas as pd

# переменные 
TOKEN_USER = "vk1.a.cNDFQMsmnlQ5Q_knYUvc1iXCMKHrNZrYBd_Tk3WGTNGiJJh6h3On7o3bwJqn39BHjz-9DmfVE-XUHoHyxm7rGXyFhn8MogvWTjxvsFKxFeSpWerc6nSP8R658q6OSYY5jAE-2uLzBJU86LIq9xCsxrptrD42wJ6aBIXmEFONn6c8zmPVsRHq8xDv1gzZXsIrjcPwUNSY2bkLv9HIQzA2CA" #токен пользователя
VERSION = 5.131 # используемая версия апи
DOMAIN = 'snomephi' #'vmephi'  #'reactorclub' #'mephi_official' #'osomephi'  #snomephi #имя сообщества из адресной строки  mephi_official
only = False

domains = ['vmephi', 'reactorclub', 'mephi_official', 'osomephi',  'snomephi']


array = []



if only:
	date =  time.time()
	i = 0
	while date > 1693515599: #парсинг с первого сентября 2023 года 1693515599
		# через api vk вызываем статистику постов
		response = requests.get('https://api.vk.com/method/wall.get',
		params={'access_token': TOKEN_USER,
        	'v': VERSION,
        	'domain': DOMAIN,
			'offset': i*100,
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
else:
	for domain in domains:
		date =  time.time()
		i = 0
		while date > 1693515599: #парсинг с первого сентября 2023 года 1693515599
			response = requests.get('https://api.vk.com/method/wall.get',
			params={'access_token': TOKEN_USER,
        		'v': VERSION,
        		'domain': domain,
				'offset': i*100,
        		'count': 100,
        		'filter': str('owner')})

			data = response.json()['response']['items']
			print("получено 100 записей")
			for j in range(100):
				date = data[j]['date']
				#print(i*100+j, time.ctime(date)) #, data[i*100+j]['text'])
				array.append( [i*100+j,time.ctime(date),data[j]['id'], data[j]['text']]) 
			i+=1
			pd.DataFrame(array,columns= ['i', 'time', 'id', 'text']).to_csv("parse-data.csv", index=False)


