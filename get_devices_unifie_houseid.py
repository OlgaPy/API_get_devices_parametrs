#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'PykhovaOlga'

import os

os.environ["NLS_LANG"] = "Russian.AL32UTF8"  # для корректной обработки кириллицы в запросах
import cgi
import cgitb

cgitb.enable()
import re
import json
from act_db import Ora


def parse_responce(response: tuple) -> dict:
    devices = {}
    re_model = re.compile("(?P<model>DEV(?P<num>\d+)(Марка:\s+|)(?P<name>.*?)\,\s+)",
                          re.MULTILINE | re.DOTALL)  # DEV + num + ' ' + name
    re_ip = re.compile("(IP:\s+(?P<ip>\S+)\s+)", re.MULTILINE | re.DOTALL)  # ip replace(',', '')
    re_ifaddr_v4 = re.compile(
        "(?P<ipv4_address>((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3})(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\S*))",
        re.MULTILINE | re.DOTALL)
    re_mac = re.compile("(MAC:\s+(?P<mac>\S+)(\s+|$))", re.MULTILINE | re.DOTALL)  # mac
    re_address = re.compile("(Адрес:\s+(?P<address>.*?)(\s+IP|$))", re.MULTILINE | re.DOTALL)  # address

    for element in response:
        one_device = {'model': '',
                      'ip': '',
                      'address': house,
                      'MAC': ''
                      }

        founds_model = re_model.search(element[1])
        if founds_model is not None:
            model = f"DEV{founds_model.group('num')} {founds_model.group('name')}"
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
        devices[element[0]] = one_device
    return devices


# ---------------START---------------------------
adresses_h = {'unifie_houseid': {}}
print("Content-Type: application/json")
print("")  # Не убирать, без этого не работает!

house = ""
house_id = ""
arguments = cgi.FieldStorage()

for param in arguments.keys():
    if param == 'house':
        house = arguments[param].value
        adresses_h['natural_address'][house] = {}
    elif param == 'house_id':
        house_id = arguments[param].value
        adresses_h['unifie_houseid'][house_id] = {}

with Ora() as conn:
    db_cursor = conn.cursor()
    if house != '':
        request_adresses = conn.request_adresses.replace('<house>', house)
        response_addr = db_cursor.execute().fetchall()
        adresses_h['natural_address'][house] = parse_responce(response_addr)
        js = json.dumps(adresses_h,
                        ensure_ascii=False)  # ключ для корректной обработки кириллицы в ответах
    if house_id == '':
        js = json.dumps(adresses_h,
                        ensure_ascii=False)  # ключ для корректной обработки кириллицы в ответах

    request_devices = conn.request_devices.replace('<house_id>', house_id)

    response = db_cursor.execute(request_devices).fetchall()

count_dev = 0
one_device = {}
for element in response:
    one_device[count_dev] = {'device_id': element[0],
                             'ip': element[1],
                             'model': element[2],
                             'MAC': element[3]
                             }
    count_dev += 1
adresses_h['unifie_houseid'][house_id] = one_device
print(adresses_h)
