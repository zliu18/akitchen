# coding = utf-8
# usr/bin/env python

'''
Author: Chuck
Email: zliu18@gmail.com

date: 16/08/2020 3:13 PM
desc:
'''

import csv
import json
import os
import string
from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.parse import quote
import requests
import shutil
from datetime import datetime
import time
from multiprocessing import Pool
from concurrent.futures import ProcessPoolExecutor
import random

domain = 'https://p.ak2.co/'

search_api = 'https://p.ak2.co/api/v2/index?id={}&device_id='
# 0 = legacy_code, 1 = page number
search_api2 = 'https://p.ak2.co/api/v2/index_detail/{0}?page={1}&device_id='

# 0 = legacy id
search_api3 = 'https://p.ak2.co/api/recipes/{}'

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36(KHTML, like Gecko)"
                         " Chrome", "Accept": "text/html,application/xhtml+xml,application/xml;q = 0.9, image "
                                              "/ webp, * / *;q = 0.8"}
categories = []
recipes_legacies = list()
chefs = list()

save_legacy_path = 'data/legacy/json/'
save_recipe_path = 'data/recipe/json/'
save_detail_path = 'data/detail/json/'
chef_avatar = 'data/avatar'
recipe_images = 'data/images'

recipes_legacy_file = 'recipes_legacy.csv'
urls_file = 'data/urls.csv'


class Category:
    def __init__(self, code, name, selected='False', legacy=None, total=0):
        self.code = code
        self.name = name
        self.selected = selected
        self.legacy = legacy
        self.total = total


class Recipe:
    def __init__(self, code, legacy, title, description, image_url, chef):
        self.code = code
        self.legacy = legacy
        self.title = title
        self.description = description
        self.image_url = image_url
        self.chef = chef


class Chef:
    def __init__(self, code, name, title, avatar_url, description):
        self.code = code
        self.name = name
        self.title = title
        self.avatar_url = avatar_url
        self.description = description


def create_csv(filename):
    with open(filename, 'w') as creator:
        csv_write = csv.writer(creator)
        csv_head = ['code', 'name', 'selected', 'legacy', 'total']
        csv_write.writerow(csv_head)


def read_csv(filename):
    global categories
    categories.clear()
    with open(filename, 'r', encoding='utf-8') as reader:
        csv_reader = csv.DictReader(reader)
        for row in csv_reader:
            categories.append(Category(row['code'], row['name'], row['selected'], row['legacy']))


def write_csv(filename, rows):
    writer = csv.writer(open(filename, 'w', encoding='utf-8'))
    writer.writerow(['code', 'name', 'selected', 'legacy', 'total'])
    for row in rows:
        code = row.code
        name = row.name
        selected = row.selected
        legacy = row.legacy
        total = row.total
        writer.writerow([code, name, selected, legacy, total])


def write_legacy_csv(filename, rows):
    writer = csv.writer(open(filename, 'w', encoding='utf-8'))
    writer.writerow(['code', 'legacy', 'title', 'description', 'image_url', 'chef'])
    for row in rows:
        code = row.code
        legacy = row.legacy
        title = row.title
        description = row.description
        image_url = row.image_url
        chef = row.chef
        writer.writerow([code, legacy, title, description, image_url, chef])


def write_chef_csv(filename, rows):
    writer = csv.writer(open(filename, 'w', encoding='utf-8'))
    writer.writerow(['code', 'name', 'title', 'avatar_url', 'description'])
    for row in rows:
        code = row.code
        name = row.name
        title = row.title
        description = row.description
        avatar_url = row.avatar_url
        writer.writerow([code, name, title, avatar_url, description])


def get_page(url):
    global headers
    response = requests.get(url, headers=headers)
    # content = response.content.decode('utf-8')
    return response.json()


def read_from_json(filename):
    # print(filename)
    with open(filename, 'r', encoding='utf-8') as f:
        s = f.read()
        dict_data = json.loads(json.dumps(eval(s)))
        return dict_data


def parse_json(raw_data):
    global categories
    rows = raw_data['data']['tabs']
    legacy = raw_data['data']['contents']
    for row in rows:
        code = row['id']
        name = row['name']
        selected = str(row['current']).capitalize()
        c = get_category_by_code(code)
        if c is not None:
            if (c.selected is None or c.selected == 'False') and selected == 'True':
                c.selected = 'True'
                c.legacy = str(legacy[0]['id'])
        else:
            if selected.__eq__('True'):
                c = Category(code, name, selected, legacy[0]['id'])
            else:
                c = Category(code, name)
            categories.append(c)


def get_category_by_code(code):
    global categories
    for c in categories:
        if c.code == code:
            return c
    return None


def generate_base_data():
    global categories
    filename = 'data.json'
    csv_filename = 'data.csv'
    create_csv(csv_filename)
    read_csv(csv_filename)
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)
        parse_json(data)
    # write_csv(csv_filename, categories)

    for category in categories:
        if str(category.selected).title() == 'False':
            parse_json(get_page(search_api.format(category.code)))

    write_csv(csv_filename, categories)


def parse_details(json_data):
    dict_data = json_data
    print('total: ' + str(dict_data['data']['total']))
    print('current_page : ', str(dict_data['data']['current_page']))
    print('last_page :', str(dict_data['data']['last_page']))
    return {'total': dict_data['data']['total'], 'current_page': dict_data['data']['current_page'],
            'last_page': dict_data['data']['last_page']}


def get_img(img_url):
    global headers
    # response = requests.get(img_url, headers = headers)
    # req = Request(urllib.parse.urlencode(img_url))
    # req.headers = headers
    response = urlopen(quote(img_url, safe=string.printable))
    if response.getcode() == 200:
        return response.read()
    else:
        return None


def save_img(file_name, resource):
    # 图片不是文本文件，以二进制格式写入，所以是html.content
    with open(file_name, "wb") as f:
        f.write(resource)
        f.close()


def save_json(file_name, contents):
    with open(file_name, "w", encoding='utf-8') as file:
        file.write(contents)


def crawl_legacy_detail(file_name):
    global categories
    read_csv(file_name)
    for category in categories:
        page = 1
        if category.legacy is not None:
            print('start {} : '.format(category.name))
            while True:
                print('第{}页'.format(str(page)))
                # fetch page
                data = get_page(search_api2.format(category.legacy, page))
                save_json(save_legacy_path + '{}-{}.json'.format(category.name, str(page).zfill(2)), str(data))
                page_info = parse_details(data)
                if page_info['current_page'] == page_info['last_page']:
                    category.total = page_info['total']
                    print('end {} : '.format(category.name))
                    break
                else:
                    page = page + 1
    write_csv(file_name, categories)


def parse_legacy_page(data):
    global chefs
    global recipes_legacies
    chef_ids = set()
    recipe_ids = set()

    for c in chefs:
        chef_ids.add(c.code)
    for r in recipes_legacies:
        recipe_ids.add(r.code)

    contents = data['data']['contents']
    legacy = data['data']['id']
    for content in contents:
        raw_chef = content['chef']
        chef = Chef(raw_chef['id'], raw_chef['name'], raw_chef['title'], raw_chef['avatar_url'],
                    raw_chef['description'])
        recipe = Recipe(content['id'], legacy, content['title'], content['short_description'],
                        content['image_url'], chef.code)
        if chef.code not in chef_ids:
            chefs.append(chef)
            chef_ids.add(chef.code)
        if recipe.code not in recipe_ids:
            recipes_legacies.append(recipe)
            recipe_ids.add(recipe.code)


def deal_legacy_recipes():
    global chefs
    global recipes_legacies
    json_files = os.listdir(save_legacy_path)
    for file in json_files:
        if not file.startswith('推荐'):
            data = read_from_json(os.path.join(save_legacy_path, file))
            parse_legacy_page(data)
    write_legacy_csv('data/legacy.csv', sorted(recipes_legacies, key=lambda x: (x.legacy, x.code)))
    write_chef_csv('data/chef.csv', sorted(chefs, key=lambda x: (x.code)))


def grab_chef_avatar():
    with open('data/chef.csv', 'r', encoding='utf-8') as reader:
        csv_reader = csv.DictReader(reader)
        for row in csv_reader:
            url = row['avatar_url']
            print(row['code'] + " " + row['avatar_url'])

            a = urlparse(url)
            basename = os.path.basename(a.path)
            if basename is not None and len(basename) > 0:
                # print(a.path)  # Output: /kyle/09-09-201315-47-571378756077.jpg
                # print(os.path.basename(a.path))
                # response = get_img(url)
                response = requests.get(quote(url, safe=string.printable))
                save_file_name = os.path.join('data/user/avatar/' + os.path.basename(a.path))
                save_img(save_file_name, response.content)


def crawl_recipe():
    with open('data/legacy.csv', 'r', encoding='utf-8') as reader:
        csv_reader = csv.DictReader(reader)
        if not os.path.exists(save_recipe_path):
            os.makedirs(save_recipe_path)
        for row in csv_reader:
            code = row['code']
            data = get_page(search_api3.format(code))
            filename = '{} - {}'.format(code, row['title'])
            print(filename)
            save_json(save_recipe_path + filename + '.json', str(data))


def deal_with_recipes():
    json_files = os.listdir(save_recipe_path)
    i = 0
    j = 0
    for file in json_files:
        if os.path.isfile(save_recipe_path + "/" + file) \
                and os.path.splitext(save_recipe_path + "/" + file)[1] == '.json':
            data = read_from_json(os.path.join(save_recipe_path, file))
            parse_recipe(data)
            i = i + 1
            # print(i)


def parse_media_url(url):
    a = urlparse(url)
    basename = os.path.basename(a.path)
    basedir = os.path.dirname(a.path)
    if not os.path.exists(recipe_images + basedir):
        os.makedirs(recipe_images + basedir, exist_ok=True)
    if not os.path.exists(urls_file):
        with open(urls_file, 'a', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['path', 'name', 'url'])
    writer = csv.writer(open(urls_file, 'a', encoding='utf-8'))
    writer.writerow([recipe_images + basedir, basename, url])


def parse_preparations(items):
    urls = list()
    for item in items:
        url = item['url']
        if urlparse(url).scheme in {'https', 'http'}:
            urls.append(url)
    return urls


def parse_steps(steps):
    urls = list()
    for step in steps:
        contents = step['content']
        for content in contents:
            if content['type'] in {'image', 'video'}:
                url = content['content']
                print(url)
                urls.append(url)
    return urls


def parse_key_prompts(key_prompts):
    urls = list()
    # for prompt in key_prompts:
    #     print(prompt)
    return urls


def parse_introductions(introductions):
    urls = list()
    # for introduction in introductions:
    #     print(introduction)
    return urls


def parse_suggestions(suggestions):
    urls = list()
    # for suggestion in suggestions:
    #     print(suggestion)
    return urls


def parse_recipe(data):
    urls = list()
    url = data['data']['image_url']
    urls.append(url)
    preparations = data['data']['preparations']
    if len(preparations) > 0:
        urls.extend(parse_preparations(preparations))
    steps = data['data']['static_steps']
    if len(steps) > 0:
        urls.extend(parse_steps(steps))
    # key_prompts = data['data']['key_prompt']
    # if len(key_prompts) > 0:
    #     urls.append(parse_key_prompts(key_prompts))
    # introductions = data['data']['introduction']
    # if len(introductions) > 0:
    #     urls.append(parse_introductions(introductions))
    # suggestions = data['data']['suggestions']
    # if len(suggestions):
    #     urls.append(parse_suggestions(suggestions))
    for url in urls:
        parse_media_url(url)
    return len(urls)


def deal_with_urls():
    tasks = []
    # start = time.time();

    with open('data/missing_urls0.csv', 'r', encoding='utf-8') as reader:
        csv_reader = csv.DictReader(reader)
        for row in csv_reader:
            tasks.append({'path': row['path'],
                          'name': row['name'],
                          'url': row['url']})
    reader.close()
    # for file in files:
    #     time.sleep(0.1)
    #     print(file['url'])
    # print(time.time() - start)
    return tasks


def deal_with_task(task):
    start_time = time.time()
    response = requests.get(quote(task['url'], safe=string.printable))
    save_file_name = os.path.join(task['path'], task['name'])
    save_img(save_file_name, response.content)
    print(save_file_name + ' is saved')


def deal_with_wrong_filenames():
    all_tasks = deal_with_urls()
    for task in all_tasks:
        current_filename = os.path.join(task['path'] + task['name'])
        correct_filename = os.path.join(task['path'], task['name'])

        if os.path.exists(current_filename):
            shutil.move(current_filename, correct_filename)


def readfile(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        i = 1
        for line in lines:
            texts = line.split('        ')
            print(texts[1])
            i = i + 1

        f.close


if __name__ == '__main__':
    # data = get_page('https://p.ak2.co/api/v2/index?code=9&device_code=')
    # deal_legacy_recipes()
    # grab_chef_avatar()
    # crawl_recipe()
    # deal_with_recipes()
    start = datetime.now()
    # dd/mm/YY H:M:S
    # dt_string = start.strftime("%d-%m-%Y %H:%M:%S")
    # print('All tasks started at ' + dt_string)
    # tasks = deal_with_urls()
    # pool = Pool(processes=4)
    # pool.map(deal_with_task, tasks)
    # pool.close()
    # pool.join()
    # now = datetime.now()
    # # dd/mm/YY H:M:S
    # dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
    # print('All tasks are completed at ' + dt_string + ' cost {}'.format(now - start))
    # deal_with_wrong_filenames()
    # readfile('ps1.txt')
    list1 = ['a', 'b', 'c', 'd', 'e', 'a', 'c']
    list1 = list(dict.fromkeys(list1))
    print(random.choice(list1))

