import requests
import argparse
import time
import pandas as pd


TOKEN_USER = "" #токен пользователя
VERSION = 5.131 # используемая версия апи
domains = []
array = []

#================================ Аргументы командной строки ===================================#
parser = argparse.ArgumentParser(description="Парсер постов из сообществ в ВК")  
parser.add_argument("communities", help="Файл .txt с cсылками на сообщества в ВК. Каждая ссылка с новой строки, без дополнительных символов.")  
format_string = "%H:%M:%S#%d.%m.%Y"

parser.add_argument(
    '--start_time',
    type=str,
    default="00:00:00#10.07.2025",
    help='Время появления поста в сети, начиная с которого проводится парсинг (default: 00:00:00#10.07.2025)'
)

parser.add_argument(
    '--finish_time',
    type=str,
    default=time.strftime(format_string, time.localtime(time.time())),
    help='Время появления поста в сети, завершая которым проводится парсинг (default: текущее время)'
)

args = parser.parse_args()
#еревод времени в секнды с начала эпохи
st_time = int(time.mktime(time.strptime(args.start_time, format_string)))
fn_time = int(time.mktime(time.strptime(args.finish_time, format_string)))
#print(int(st_time))
#print(int(fn_time))

#============================= импорт доменов =========================================#
domains = []
with open(args.communities, "r") as file:
    #выделение домена сообщества из ссылок в файле
    for string in file.readlines():
        domains.append(string.replace("https://vk.com/", "").replace("\n", ""))
    #print(domains)

#============================== Парсинг ================================================#
#добавить условие на fn_time
for domain in domains:
	date = time.time()
	i = 0
	while date > st_time: #парсинг с первого сентября 2023 года 1693515599
		response = requests.get('https://api.vk.com/method/wall.get',
		params={'access_token': TOKEN_USER,
       		'v': VERSION,
       		'domain': domain,
			'offset': i*100,
       		'count': 100,
       		'filter': str('owner')})
		data = response.json()#['response']['items']
		if 'error' in data.keys(): 
			print (data['error'])



		data = data['response']['items']
		print("получено 100 записей")
		for j in range(100):
			date = data[j]['date']
			#print(i*100+j, time.ctime(date)) #, data[i*100+j]['text'])
			if date< fn_time:
				array.append( [i*100+j,time.ctime(date),data[j]['id'], data[j]['text'], domain]) 
			else:
				break
		i+=1
		pd.DataFrame(array,columns= ['i', 'time', 'id', 'text', 'domain']).to_csv("parse-data.csv", index=False)
		if date> fn_time: break

print("Парсинг постов завершён. Данные сохранены в файл 'parse-data.csv'")


