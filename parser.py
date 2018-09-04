from bs4 import BeautifulSoup

soup = BeautifulSoup(open('tini.html', encoding='utf8'), 'html.parser')

message_group = soup.find('div', {'id' : 'messageGroup'})

msgs = message_group.find_all('div', class_='msg')

for msg in msgs:
	print (msg.prettify())