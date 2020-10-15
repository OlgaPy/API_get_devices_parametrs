#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'PykhovaOlga'

import os
os.environ["NLS_LANG"] = "Russian.AL32UTF8" #не убирать! это чтоб кириллицу в запросах нормально обрабатывал
import cgi
import cgitb;cgitb.enable()
import cx_Oracle
import re
import json


def connect(config):
    db_connection = None
    db_connection = cx_Oracle.connect(
        config['oracle']['ora_user'],
        config['oracle']['ora_pass'],
        '%s/%s' % (config['oracle']['ora_host'], config['oracle']['ora_sid'])
    )
    db_cursor = db_connection.cursor()
    return db_cursor, db_connection

def configParse(path='/home/equipment/EQ-scripts/equipment.conf'):
    config = open(path).readlines()
    config_dict = {}
    for row in config:
        row = row.strip()
        if not row.startswith('#') and row != '':
            if row.startswith('['):
                section = row[1:-1]
                if section not in config_dict:
                    config_dict[section.lower()] = {}
            if '\t' in row:
                items = row.split('\t')
                config_dict[section.lower()].update(
                    {items[0].strip().lower(): items[-1].strip()}
                )
            if '  ' in row:
                items = row.split('  ')
                config_dict[section.lower()].update(
                    {items[0].strip().lower(): items[-1].strip()}
                )
            elif '=' in row:
                items = row.split('=')
                config_dict[section.lower()].update(
                    {items[0].strip().lower(): items[-1].strip()}
                )
    return config_dict

def parse_responce(response):
    part_result_dict = {}
    re_model = re.compile("(?P<model>DEV(?P<num>\d+)(Марка:\s+|)(?P<name>.*?)\,\s+)", re.MULTILINE| re.DOTALL) # DEV + num + ' ' + name
    re_ip = re.compile("(IP:\s+(?P<ip>\S+)\s+)", re.MULTILINE| re.DOTALL) #ip replace(',', '')
    re_ifaddr_v4 = re.compile("(?P<ipv4_address>((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3})(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\S*))", re.MULTILINE |re.DOTALL)
    re_mac = re.compile("(MAC:\s+(?P<mac>\S+)(\s+|$))", re.MULTILINE| re.DOTALL) # mac #todo replace(',', '')
    re_address = re.compile("(Адрес:\s+(?P<address>.*?)(\s+IP|$))", re.MULTILINE| re.DOTALL) #address



    for element in response:
        one_device = {'model': '',
                      'ip': '',
                      'address': house,
                      'MAC': ''
                      }

        founds_model = re_model.search(element[1])
        if founds_model is not None:
            model = 'DEV' + founds_model.group('num') + ' ' + founds_model.group('name')
            one_device['model'] = model

        founds_ip = re_ifaddr_v4.search(element[1])
        if founds_ip is not None:
            ip = founds_ip.group('ipv4_address')
            ip = ip.replace(",", "")
            one_device['ip'] = ip

        founds_address = re_address.search(element[1])
        if founds_address is not None:
            address = founds_address.group('address')
            one_device['address'] = address


        founds_mac = re_mac.search(element[1])
        if founds_mac is not None:
            mac = founds_mac.group('mac')
            mac = mac.replace(",", "")
            one_device['MAC'] = mac
        part_result_dict[element[0]] = one_device
    return part_result_dict

#---------------START---------------------------
result_dict = {'unifie_houseid':{}}
# print("Content-Type: text/html")
print("Content-Type: application/json")
print("") #Не убирать, без этого не работает!

house = ""
house_id = ""
arguments = cgi.FieldStorage()

for param in arguments.keys():
    if param == 'house':
        house = arguments[param].value
        result_dict['natural_address'][house] = {}
    elif param == 'house_id':
        house_id = arguments[param].value
        result_dict['unifie_houseid'][house_id] = {}



config = configParse()
db_cursor, db_connection = connect(config)
if house != '':
    response = db_cursor.execute("SELECT av.obj_id device_id, av.value_raw house_id FROM os_usr.dev_attr_values av WHERE av.attr_id = 2 AND av.VALUE_RAW LIKE '%" + house +"%'").fetchall()
    result_dict['natural_address'][house] = parse_responce(response)
    js = json.dumps(result_dict, ensure_ascii=False) #ключ не убирать! это чтоб кириллицу в ответах нормально обрабатывал
if house_id != '':
    request = """With arm_address as (SELECT  av.obj_id device_id,
                                        av.value_raw house_id
                                    FROM os_usr.dev_attr_values av
                                    WHERE  av.attr_id = 3),
                                    swithes as (SELECT device_type_id
                                    FROM os_eqm.device_types
                                    WHERE device_class IN
                                    (
                                        SELECT device_class_id
                                    FROM os_eqm.device_classes
                                    WHERE guid IN
                                    (
                                    SELECT obj_guid
                                    FROM os_lib.objects_in_nav_categories
                                    WHERE nav_cat_id in
                                    (
                                    SELECT nav_cat_id
                                    FROM nav_categories
                                    WHERE guid = '75C0F3733B084DBDAC604167D298B2F5' --  Eiiiooaoi?u
                                    )
                                    )
                                    ))
                                    SELECT d.device_id,
                                           na.net_address,
                                           dt.name,
                                           trim(os_usr.ertel_utils.get_prop_str(d.device_id,'MAC_ADRES_USTROJSTVA')) 
                                           mac_sw
                                    FROM os_usr.geo_addresses ga,
                                                              os_eqm.net_addresses na,
                                                                                   arm_address arm ,
                                                                                               device_types  dt,
                                                                                                             devices d,
                                                                                                                     swithes sw
                                    WHERE  arm.house_id = ga.house_id
                                                          and arm.device_id = d.device_id
                                                                              and na.device_id = d.device_id and na.is_management = '1'
                                    AND dt.device_type_id = d.device_type
                                                            and dt.device_type_id in sw.device_type_id
                                                            and ga.unified_house_id = '<uni_houseid>'
              """

    request = request.replace("<uni_houseid>", str(house_id))
    response = db_cursor.execute(request).fetchall()
    count_dev = 0
    one_device = {}
    for element in response:
        one_device[count_dev] = {'device_id' : element[0],
                                 'ip' : element[1],
                                 'model' : element[2],
                                 'MAC' : element[3]
                                 }
        count_dev += 1
    result_dict['unifie_houseid'][house_id] = one_device
    print result_dict
    # js = json.dumps(result_dict, ensure_ascii=False)
else:
    js = json.dumps(result_dict, ensure_ascii=False) #ключ не убирать! это чтоб кириллицу в ответах нормально обрабатывал

