import os, re, requests
from pprint import pprint
from bs4 import BeautifulSoup


BASE_URL = 'http://image-net.org'
WORD_LIST_URL = BASE_URL + '/api/text/imagenet.sbow.obtain_synset_wordlist'
QUERYSET = ['cat', 'dog']


#ГОТОВЫЙ БЛОК - ПОЛУЧЕНИЕ ID IMG
'''pattern_cat = re.compile(' '+QUERYSET[0])
pattern_dog = re.compile(' '+QUERYSET[1])

print("get page text...")
page = requests.get(WORD_LIST_URL).text

print("page text is received!")

soup = BeautifulSoup(page, 'html.parser')
links = soup.find_all('a')

print("Generate links")
cat_links = [re.findall(r'n\d+', link.get('href'))[0] for link in links if pattern_cat.findall(link.contents[0])]
dog_links = [re.findall(r'n\d+', link.get('href'))[0] for link in links if pattern_dog.findall(link.contents[0])]'''
# КОНЕЦ ГОТОВОГО БЛОКА


'''word_list_file = open('word_list.txt', 'at')
for link in cat_links:
    word_list_file.write(link)

word_list_file.close

pprint(cat_links)
print("--------------------------")
pprint(dog_links)'''

# http://www.image-net.org/api/text/imagenet.synset.geturls?wnid=n02123394
# ГОТОВЫЙ БЛОК - ПОЛУЧЕНИЕ СПИСКА УРЛОВ IMG
cat_links_url = BASE_URL + '/api/text/imagenet.synset.geturls?wnid={0}'.format('n02509815')
cat_page = requests.get(cat_links_url).text
soup = BeautifulSoup(cat_page, 'html.parser')
cat_img_urls = soup.getText().split('\r\n')[:-1]
pprint(cat_img_urls)
# КОНЕЦ ГОТОВОГО БЛОКА
