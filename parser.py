from bs4 import BeautifulSoup

links = open('links.txt', 'w', encoding='utf8')
fb_page = open('fb_page.txt', 'w', encoding='utf8')
scratch = open('scratch.txt', 'w', encoding='utf8')

soup = BeautifulSoup(open('tini.html', encoding='utf8'), 'html.parser')

message_group = soup.find('div', {'id' : 'messageGroup'})

msgs = message_group.find_all('div', class_='msg')

num_divs = 0

for i, msg in enumerate(msgs):
	for div in msg.find_all('div', recursive=False):
		num_divs += 1
		scratch.write(div.prettify())

		# Check for class="touchable _4qxt" 's href, which should be most links?
		if div.find(class_='touchable _4qxt') is not None:
			links.write(div.find(class_='touchable _4qxt')['href'] + '\n')


		# Check for FB page links

		# Check for images

		# Everything else should go in some Misc. section

print(i+1)
print(num_divs)

