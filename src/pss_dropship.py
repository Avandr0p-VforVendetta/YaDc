#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# ----- Packages ------------------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import datetime
import pss_core as core
import pss_prestige as p
import pss_research as rs
import utility as util
import xml.etree.ElementTree


base_url = 'http://{}/'.format(core.get_production_server())

DROPSHIP_TEXT_PART_KEYS = ['News', 'Crew', 'Merchant', 'Shop', 'Sale', 'Reward']


# ----- Utilities --------------------------------
def request_id2item():
    url = base_url + 'ItemService/ListItemDesigns2?languageKey=en'
    raw_text = core.get_data_from_url(url)
    id2item = core.xmltree_to_dict3(raw_text, 'ItemDesignId')
    # item_lookup = mkt.parse_item_designs(raw_text)
    # df_items = mkt.rtbl2items(item_lookup)
    return id2item


def request_dropship():
    url = base_url + 'SettingService/GetLatestVersion2?languageKey=en'
    raw_text = core.get_data_from_url(url)
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        # c.tag == 'GetLatestSetting'
        for cc in c:
            # cc.tag == 'Setting'
            d = cc.attrib
    return d


# ----- Text Processing --------------------------
def get_dropshipcrew_txt(d, ctbl):
    common_crew = ctbl[d['CommonCrewId']]
    hero_crew = ctbl[d['HeroCrewId']]
    common_rarity = common_crew['Rarity']
    hero_rarity = hero_crew['Rarity']
    txt = '**Dropship Crew**'
    txt += '\nCommon Crew: {} (Rarity: {})'.format(
        common_crew['CharacterDesignName'],
        common_rarity)
    if common_rarity in ['Unique', 'Epic', 'Hero', 'Special', 'Legendary']:
        txt += ' - any unique & above crew that costs minerals is probably worth buying (just blend it if you don\'t need it)!'
    txt += '\nHero Crew: {} (Rarity: {})'.format(
        hero_crew['CharacterDesignName'],
        hero_rarity)
    return txt


def get_merchantship_txt(d, id2item):
    cargo_items = d['CargoItems'].split('|')
    cargo_prices = d['CargoPrices'].split('|')
    txt = '**Merchant Ship**'
    for i, item in enumerate(cargo_items):
        item_id, qty = item.split('x')
        cost = cargo_prices[i].split(':')
        txt += '\n{} x {}: {} {}'.format(
            id2item[item_id]['ItemDesignName'], qty,
            cost[1], cost[0])
    return txt


def get_item_text(item):
    txt = "{} (Rarity = {}, Enhancement = {} {})".format(
        item['ItemDesignName'],
        item['Rarity'],
        item['EnhancementValue'],
        item['EnhancementType'])
    return txt


def get_character_text(char):
    collection = char['CollectionDesignId']
    if collection == '0':
        collection = 'None'
    if collection in p.collections.keys():
        collection = p.collections[collection]['CollectionName']
    ability = char['SpecialAbilityType']
    if ability in p.specials_lookup.keys():
        ability = p.specials_lookup[ability]
    txt = "{} (Rarity - {}, Ability - {}, Collection - {})".format(
        char['CharacterDesignName'], char['Rarity'], ability, collection)
    return txt


def is_within_daterange(start_date, end_date, test_date='now',
                        fmt='%Y-%m-%dT%H:%M:%S'):
    # Example:
    # is_within_daterange('2018-09-03T00:00:00', '2018-09-04T00:00:00')
    start_date = datetime.datetime.strptime(start_date, fmt)
    end_date = datetime.datetime.strptime(end_date, fmt)
    if test_date == 'now':
        test_date = datetime.datetime.now()
    return (test_date > start_date) and (test_date < end_date)


def get_sale_text(d, id2item, ctbl):
    if is_within_daterange(d['SaleStartDate'], d['SaleEndDate']) is False:
        return None

    if d['SaleType'] == 'Item':
        sale_item = id2item[d['SaleArgument']]
        txt = "**Sale**\n{}".format(get_item_text(sale_item))
    elif d['SaleType'] == 'Character':
        sale_item = ctbl[d['SaleArgument']]
        txt = "**Sale**\n{}".format(get_character_text(sale_item))
    elif d['SaleType'] == 'Bonus':
        txt = "**Sale**\n{}% Bonus".format(d['SaleArgument'])
    elif d['SaleType'] == 'None':
        return None
    else:
        txt = '**Sale**'
        txt += '\nSaleType: {}'.format(d['SaleType'])
        txt += '\nSaleArgument: {}'.format(d['SaleArgument'])
        return txt
    return txt


def get_shop_item_text(d, id2item, ctbl, id2roomname):
    if d['LimitedCatalogType'] == 'Item':
        sale_item = id2item[d['LimitedCatalogArgument']]
        txt = "**Shop**\n{}".format(get_item_text(sale_item))
    elif d['LimitedCatalogType'] == 'Character':
        sale_item = ctbl[d['LimitedCatalogArgument']]
        txt = "**Shop**\n{}".format(get_character_text(sale_item))
    elif d['LimitedCatalogType'] == 'Room':
        sale_item = id2roomname[d['LimitedCatalogArgument']]
        txt = "**Shop**\n{}".format(sale_item)
    return txt


def get_shop_item_cost(d):
    txt = """Cost: {} {}, Can own (max): {}""".format(
        d['LimitedCatalogCurrencyAmount'],
        d['LimitedCatalogCurrencyType'],
        d['LimitedCatalogMaxTotal'])
    return txt


def get_dailyrewards_txt(d, id2item):
    items = d['DailyItemRewards'].split('|')
    txt = '**Daily Rewards**'
    txt += '\n{} {}'.format(d['DailyRewardArgument'], d['DailyRewardType'])
    for i, item in enumerate(items):
        item_id, qty = item.split('x')
        txt += '\n{} x {}'.format(
            id2item[item_id]['ItemDesignName'], qty)
    return txt


def get_limited_catalog_txt(d, id2item, ctbl, id2roomname):
    expiry_date = datetime.datetime.strptime(
        d['LimitedCatalogExpiryDate'], '%Y-%m-%dT%H:%M:%S')
    if datetime.datetime.now() > expiry_date:
        return None

    if d['LimitedCatalogType'] == 'Item':
        sale_item = id2item[d['LimitedCatalogArgument']]
    elif d['LimitedCatalogType'] == 'Character':
        sale_item = ctbl[d['LimitedCatalogArgument']]
    elif d['LimitedCatalogType'] == 'Room':
        sale_item = d['LimitedCatalogArgument']
    txt = '{}, {}'.format(
        get_shop_item_text(d, id2item, ctbl, id2roomname),
        get_shop_item_cost(d))
    return txt


def get_dropship_text():
    text_parts = get_dropship_text_parts()
    text_parts_keys = text_parts.keys()
    txt = ''
    for text_part_expected in DROPSHIP_TEXT_PART_KEYS:
        if text_part_expected in text_parts_keys and text_parts[text_part_expected] != None:
            txt += '{}\n\n'.format(text_parts[text_part_expected])             
    return txt


def update_and_get_auto_daily_text():
    utc_now = util.get_utcnow()
    text_parts_api = get_dropship_text_parts()
    text_parts_db = db_get_dropship_text_parts()
    updated = db_try_update_dropship_text(text_parts_api, utc_now)
    if updated:
        txt = ''
        for text_part_expected in DROPSHIP_TEXT_PART_KEYS:
            if text_part_expected in text_parts_keys and text_parts[text_part_expected] != None:
                txt += '{}\n\n'.format(text_parts[text_part_expected]) 
        return txt
    else:
        return None


def get_dropship_text_parts():
    id2item = request_id2item()
    ctbl, tbl_i2n, tbl_n2i, rarity = p.get_char_sheet()
    rooms = rs.get_room_designs()
    id2roomname = rs.create_reverse_lookup(rooms, 'RoomDesignId', 'RoomName')
    
    result = {}

    if 'News' in d.keys():
        result['News'] = d['News']
    result['Crew'] = get_dropshipcrew_txt(d, ctbl)
    result['Merchant'] = get_merchantship_txt(d, id2item)
    result['Shop'] = get_limited_catalog_txt(d, id2item, ctbl, id2roomname)
    result['Sale'] = get_sale_text(d, id2item, ctbl)
    result['Reward'] = get_dailyrewards_txt(d, id2item)
    
    return result


def db_get_dropship_text_parts():
    result = []
    rows = db_select_any_from('dropship')
    if len(rows) > 0:
        temp = {}
        for row in rows:
            result[row[0]] = result[row[1]]
    return result

    
def db_try_update_dropship_text(text_parts, utc_now):
    updated = False
    for text_parts_key in text_parts.keys():
        query_select = 'SELECT * FROM dropship WHERE partid = \'{}\''.format(text_parts_key)
        results = core.db_fetchall(query_select)
        if len(results) == 0:
            updated = True
            success = db_try_insert_dropship_text(text_parts_key, text_parts[text_parts_key], utc_now)
            if success == False:
                print('[] Could not insert dropship text for part \'{}\' into db'.format(text_parts_key))
        elif:
            db_value = results[0]
            if db_value != text_parts[text_parts_key]:
                updated = True
                success = db_try_update_dropship_text(text_parts_key, text_parts[text_parts_key], utc_now)
                if success == False:
                    print('[] Could not update dropship text for part \'{}\''.format(text_parts_key))
    return updated

                
def db_try_insert_dropship_text(partid, text, utc_now):
    timestamp = utc_now.strftime('%Y-%m-%d %H:%M:%S')
    query_insert = 'INSERT INTO dropship VALUES (\'{}\', \'{}\', TIMESTAMP \'{}\')'.format(partid, text, timestamp);
    result = core.db_try_execute(query_insert)
    return result
    

def db_try_update_dropship_text(partid, text, utc_now):
    timestamp = utc_now.strftime('%Y-%m-%d %H:%M:%S')
    query_update = 'UPDATE dropship SET text = \'{}\', modifydate = TIMESTAMP {} WHERE partid = \'{}\''.format(text, timestamp, partid)
    result = core.db_try_execute(query_update)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        'Daily Rewards & Dropship API')
    parser.add_argument('--raw', action='store_true',
        help='Show the raw data only')
    args = parser.parse_args()

    if args.raw is True:
        d = request_dropship()
        print(d)
    else:
        txt = get_dropship_text()
        print(txt)
