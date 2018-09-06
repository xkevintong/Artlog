from bs4 import BeautifulSoup

f = open('scratch.txt', 'w', encoding='utf8')

soup = BeautifulSoup(open('smol.html', encoding='utf8'), 'html.parser')

message_group = soup.find('div', {'id' : 'messageGroup'})

msgs = message_group.find_all('div', class_='msg')

num_divs = 0

for i, msg in enumerate(msgs):
	for div in msg.find_all('div', recursive=False):
		num_divs += 1
		f.write(div.prettify())

print(i+1)
print(num_divs)