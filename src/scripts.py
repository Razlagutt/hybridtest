"""scripts.py"""
import os
import ssl
import re
from pprint import pprint
import shutil
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient


def get_wnid(base_url, queryset):
    """Функция возвращает словарь wnid-списков рассортированных по категориям, заданным в queryset.

    base_url - адрес ресурса для получения картинок
    queryset - список запросов категорий картинок

    """
    # Url wnid-списков всех категорий картинок
    word_list_url = base_url + '/api/text/imagenet.sbow.obtain_synset_wordlist'
    # Паттерны, по которым будут отбираться wnid-списки
    pattern_cat = re.compile(' ' + queryset[0])
    pattern_dog = re.compile(' ' + queryset[1])
    # Получаем wnid-список всех категорий картинок
    print('Получаем wnid-список всех категорий картинок')
    word_list = requests.get(word_list_url).text
    soup = BeautifulSoup(word_list, 'html.parser')
    # Из wnid-списка забираем тег а
    links = soup.find_all('a')
    # Создаем и возвращаем словарь wnid-списков рассортированных по категориям
    word_net_dict = {queryset[0]: [re.findall(r'n\d+', link.get('href'))[0] for link in links if
                                   pattern_cat.findall(link.contents[0])],
                     queryset[1]: [re.findall(r'n\d+', link.get('href'))[0] for link in links if
                                   pattern_dog.findall(link.contents[0])]}
    return word_net_dict


def download_img(word_net_dict, base_url):
    """Функция возвращает словарь картинок, рассортированных по категориям и wnid.

    base_url - адрес ресурса для получения картинок
    WNID_DICT - словарь wnid-списков рассортированных по категориям

    """
    # Словарь картинок
    images_dict = {}
    # Текщая директория приложения
    base_dir = os.path.dirname(__file__)
    # Директория для временного хранения, загруженных картинок
    downloads_dir = os.path.join(base_dir, 'tmp')
    # Обход словаря wnid-списков рассортированных по категориям
    for category, wnid_list in word_net_dict.items():
        # Если в директории tmp нет поддиректории с именем категории, то создать ее
        if not os.path.exists(os.path.join(downloads_dir, category)):
            os.mkdir(os.path.join(downloads_dir, category))
        # Получаем путь к поддиректории с названием текущей категории
        category_tmp_dir = os.path.join(downloads_dir, category)
        # Ключу category словаря imgs_dict создаем ссылку на пустой словарь
        images_dict[category] = []
        # Обход wnid-списка
        for wnid in wnid_list:
            # По wnid-списку получаем список url картинок
            print('По wnid-списку получаем список url картинок:', wnid)
            img_urls = base_url + '/api/text/imagenet.synset.geturls?wnid={0}'.format(wnid)
            img_urls_page = requests.get(img_urls).text
            soup = BeautifulSoup(img_urls_page, 'html.parser')
            img_urls_list = soup.getText().split('\r\n')[:-1]
            # Количество картинок
            img_count = len(img_urls_list)
            # Обход элентов списка url картинок
            for img_url in img_urls_list:
                try:
                    # Получаем url картинки
                    print('Получаем url картинки:', img_url)
                    get_url = requests.get(img_url)
                    # Задаем имя картинке
                    img_name = '{0}.jpg'.format(wnid + str(img_count))
                    print('Задаем имя картинке:', img_name)
                    # Скачиваем картинку в tmp директорию
                    print('Скачиваем картинку в tmp директорию', img_name)
                    get_img = open(os.path.join(category_tmp_dir, img_name), "wb")
                    get_img.write(get_url.content)
                    get_img.close()
                    # Добавляем в словарь картинку
                    print('Добавляем в словарь картинку')
                    images_dict[category].append(os.path.join(category_tmp_dir, img_name))
                    print('Картинка в словаре:')
                    pprint(images_dict)
                    print('\n')
                    # Учитываем количество скаченных картинок
                    img_count -= 1
                except ssl.SSLError:
                    pprint('Certificate verify failed (_ssl.c:645)')
                except requests.exceptions.SSLError:
                    pprint('Max retries exceeded with url...')
                except requests.exceptions.ConnectionError:
                    pprint('Connection aborted. Remote end closed connection without response.')
    return images_dict


def sort_img(from_tmp_dict):
    """Функция сортирует картинки по каталогам: /data/train/cat,
    /data/train/dog, /data/test/cat, /data/test/dog и
    записывает данные в базу данных.

    from_tmp_dict - словарь картинок, рассортированных по категориям

    """
    # Текщая директория приложения
    base_dir = os.path.dirname(__file__)
    # Получение полного пути к директории data/test и data/train
    test_path = os.path.join(base_dir, 'data/test')
    train_path = os.path.join(base_dir, 'data/train')
    # Создаем клиента для работы с базой данных
    client = MongoClient()
    # Подключаемся к базе данных
    database = client["local"]
    # Получаем коллекцию данных в базе
    coll = database["img_catalog"]
    # Обход словаря картинок, рассортированных по категориям
    for category, img_files_list in from_tmp_dict.items():
        # Считаем количество картинок в категории
        img_count = len(img_files_list)
        # Считаем сколько из них нужно переместить в test_path
        img_files_into_test = round(img_count * .2)
        # Получаем путь к каждой картинке
        for img_file in img_files_list:
            # Если не все картинки перемещены в директорию test_path, то
            if img_files_into_test > 0:
                # Получаем подиректорию в директории test_path с именем category
                if not os.path.exists(os.path.join(test_path, category)):
                    os.mkdir(os.path.join(test_path, category))
                dst_path = os.path.join(test_path, category)
                # Перемещаем картинку в директорию dst_path
                shutil.move(img_file, dst_path)
                # Учитываем, что файл перемещен
                img_files_into_test -= 1
                # Создаем документ для записи данных в базу
                data = {'category': category, 'path': dst_path}
                # Записываем сведения о картинке в базу данных
                coll.insert_one(data)
            # Иначе, если все необходимые картинки перенесены в test_path, то
            else:
                # Получаем поддиректорию в директории train_path с именем category
                if not os.path.exists(os.path.join(train_path, category)):
                    os.mkdir(os.path.join(train_path, category))
                dst_path = os.path.join(train_path, category)
                # Перемещаем картинку в директорию dst_path
                shutil.move(img_file, dst_path)
                # Создаем документ для записи данных в базу
                data = {'category': category, 'path': dst_path}
                # Записываем сведения о картинке в базу данных
                coll.insert_one(data)


if __name__ == '__main__':
    BASE_URL = 'http://image-net.org'
    WORD_NET_IDS = get_wnid(BASE_URL, ['cat', 'dog'])
    IMAGES_DICT = download_img(WORD_NET_IDS, BASE_URL)
    sort_img(IMAGES_DICT)
