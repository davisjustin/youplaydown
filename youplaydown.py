import os
import time
import shutil
import urllib
import argparse
from bs4 import BeautifulSoup
from urllib.request import urlopen


url_downloader = 'http://keepvid.com'

parser = argparse.ArgumentParser()
parser.add_argument('-q', '--quality', dest='quality', help='Video quality.(0-Min, 1-Max)')
parser.add_argument('-u', '--url', dest='url', help='Url for video playlist.')
parser.add_argument('-i', '--index', dest='index',
                    help='Specify starting & ending index 4 the playlist (<from> or <from>-<to>).')
args = parser.parse_args()


def check_inp_params(force=False):
    if args.quality is None or args.url is None or force is True:
        if args.url is None:
            args.url = input('enter url:')
        if args.quality is None:
            args.quality = input('enter quality:')
        if args.index is None:
            if input('specify index? (y)').lower() == 'y':
                args.index = input('<start>-<end> (enter 0 for default/auto)')
        return False
    else:
        return True


def get_page(url):
    for i in range(3):
        try:
            page = urlopen(url)
            print('got page')
            return page
        except():
            print('failed\nretrying in 3secs')
            time.sleep(3)
    return False


def check_file_io(folder, file_list):
    temp_dir = 'temp-' + folder
    os.mkdir(temp_dir)
    fail_name_list = []
    for file_name in file_list:
        try:
            temp_file = open(os.path.join(temp_dir, file_name), 'w')
            temp_file.close()
        except():
            fail_list.append(file_name)
    shutil.rmtree(temp_dir)

    if len(fail_name_list) == 0:
        return True

    print('Error writing file names:')
    for f in fail_name_list:
        print(f)
    return False


def clean_nm(cl):
    cl = cl.replace('\n', '')
    cl = cl.replace('\t', '')
    cl = cl.replace('\\', '')
    cl = cl.replace('/', '-')
    cl = cl.replace('*', '-')
    cl = cl.replace(':', '-')
    cl = cl.replace('?', '')
    cl = cl.replace('<', '(')
    cl = cl.replace('>', ')')
    cl = cl.replace('|', '!')

    if cl[:1].isspace():
        start = 1
        while cl[:start].isspace():
            start += 1
        start -= 1
        cl = cl[start:]
    if cl[-1:].isspace():
        end = -1
        while cl[end:].isspace():
            end -= 1
        end += 1
        cl = cl[:end]

    return cl


# needs error handling implemented
def dwl_file(file_url):
    open_link = urlopen(file_url)

    meta = str(open_link.info()).split()
    byte_size = int(meta[1 + meta.index('Content-Length:')])

    gear = -1
    total = 0
    data_blocks = []
    while True:
        block = open_link.read(1024)
        data_blocks.append(block)
        total += len(block)
        hash_sym = ((50 * total) // byte_size)
        if gear < int(total / byte_size * 50):
            gear = int(total / byte_size * 50)
            print("[{}{}] {}% | \t{}/{}Kb".format('#' * hash_sym, ' ' * (50 - hash_sym), int(total / byte_size * 100),
                                                  int(total / 1024), int(byte_size / 1024)))

        if not len(block):
            break

    data = b''.join(data_blocks)
    open_link.close()
    return data


# ############################# START

# check and/or get input params
while True:
    if check_inp_params():
        break

args.url = 'https://www.youtube.com/playlist?list=PLQVvvaa0QuDc_owjTbIY4rbgXOFkUYOUB'

# get the playlist page
print('getting playlist page...')
play_page = get_page(args.url)
if play_page is False:
    print('failed to retrieve playlist page')
    exit(0)

# scrape off the unwanted code
play_page = BeautifulSoup(play_page, 'html.parser')
play_page = play_page.find("div", {"class": "branded-page-v2-body"})

# get the playlist title and video title
dir_name = play_page.find("h1", {"class": "pl-header-title"}).text
dir_name = clean_nm(dir_name)

vdo_names_obj = play_page.findAll('a', {'class': 'pl-video-title-link'})
vdo_names = []
vdo_links = []
for x in vdo_names_obj:
    vdo_names.append(clean_nm(x.text))
    vdo_links.append('https://www.youtube.com' + x['href'])

# create dir & check names (if its ok to save them by the given names)
if not check_file_io(dir_name, vdo_names):
    exit(0)

# parse index vars if any
start_index = 0
end_index = 0
if args.index is not None:
    if '-' in args.index:
        start_index, end_index = args.index.split('-')
    else:
        start_index = args.index
    start_index = int(start_index)
    end_index = int(end_index)

index_num = 0
fail_list = []
for link in vdo_links:              # each video link from playlist page
    index_num += 1

    if end_index != 0:              #
        if index_num > end_index:   #
            break                   #
    if index_num < start_index:     #
        continue                    #
    # ############################# # checking loop bounds

    req_url = url_downloader + '/?' + urllib.parse.urlencode({'url': link})
    kv_page = get_page(req_url)
    if kv_page is False:
        print("could'nt download video page:{}".format(vdo_names[index_num - 1]))
        fail_list.append(vdo_names[index_num - 1])
        continue

    kv_page = BeautifulSoup(kv_page, 'html.parser')
    kv_page = kv_page.find('div', {'class': 'd-info'})
    kv_page_li = kv_page.findAll('li')

    did_download = False            # FLAG ###
    for li in kv_page_li:
        if 'MP4' in li.find('a').text and 'Only' not in li.find('b').text and args.quality in li.find('b').text:
            file_data = dwl_file(li.find('a')['href'])
            with open(os.path.join(dir_name, vdo_names[index_num - 1]), 'wb') as f:
                f.write(file_data)
            did_download = True

    if not did_download:
        print("could'nt download video :{}".format(vdo_names[index_num - 1]))
        fail_list.append(vdo_names[index_num - 1])
        continue

print('download done!')
if len(fail_list) != 0:
    print("Couldn't download file(s):")
    for nm in fail_list:
        print(nm)

print('done!')
