

import urllib.request
import xml.etree.ElementTree

import pss_core as core
import utility as util

base_url = f'http://{core.get_production_server()}/'
ASSET_DOWNLOAD_URL = 'http://datxcu1rnppcg.cloudfront.net/'

# ---------- Sprite handling ----------
def request_new_sprites_sheet():
    get_sprites_url = f'{base_url}/FileService/ListSprites2'
    data = urllib.request.urlopen(get_sprites_url).read()
    return data.decode()


def get_sprites_dict(raw_text):
    result = {}
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        for cc in c:
            for ccc in cc:
                if ccc.tag != 'Sprite':
                    continue
                sprite_id = ccc.attrib['SpriteId']
                result[sprite_id] = ccc.attrib
    return result


def request_new_sprites_dict():
    raw_text = request_new_sprites_sheet()
    result = get_sprites_dict(raw_text)
    return result


def get_sprite_from_id(sprite_id):
    sprites = request_new_sprites_dict()
    result = None
    if sprite_id in sprites.keys():
        result = sprites[sprite_id]
    return result


# ---------- File handling ----------
def request_new_files_sheet():
    get_files_url = f'{base_url}/FileService/ListFiles3'
    data = urllib.request.urlopen(get_files_url).read()
    return data.decode()


def get_files_dict(raw_text):
    result = {}
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        for cc in c:
            for ccc in cc:
                if ccc.tag != 'File':
                    continue
                file_id = ccc.attrib['Id']
                result[file_id] = ccc.attrib
    return result


def request_new_files_dict():
    raw_text = request_new_files_sheet()
    result = get_files_dict(raw_text)
    return result


def get_file_from_id(file_id):
    files = request_new_files_dict()
    result = None
    if file_id in files.keys():
        result = files[file_id]
    return result


def get_file_from_sprite_id(sprite_id):
    sprite = get_sprite_from_id(sprite_id)
    file_id = sprite['ImageFileId']
    result = get_file_from_id(file_id)
    return result


def get_download_url_for_sprite_id(sprite_id):
    file = get_file_from_sprite_id(sprite_id)
    file_name = file['AwsFilename']
    result = f'{ASSET_DOWNLOAD_URL}{file_name}'
    return result