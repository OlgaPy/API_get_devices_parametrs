#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'PykhovaOlga'
import cx_Oracle

class Ora:
    def __init__(self) -> None:
        """
        A class for easy connection to the oracle database through the context manager.
        :return: None
        """
        self.path_config = '/home/equipment/EQ-scripts/equipment.conf'
        self.configParse()
        self.request_devices = """With arm_address as (SELECT  av.obj_id device_id,
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
                                    WHERE guid = '75C0F3733B084DBDAC604167D298B2F5'
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
                                                            and ga.unified_house_id = '<house_id>'
              """
        self.request_adresses = """SELECT av.obj_id device_id, av.value_raw house_id
                        FROM os_usr.dev_attr_values av 
                        WHERE av.attr_id = 2 AND av.VALUE_RAW LIKE '%<house>%'"""

    def __enter__(self) -> cx_Oracle.connect:
        """
        Establishes a connection to the oracle database. Returns the db_connect

        :return: self.db_connection: cx_Oracle.connect
        """
        self.db_connection = cx_Oracle.connect(
            self.config['oracle']['ora_user'],
            self.config['oracle']['ora_pass'],
            f"{self.config['oracle']['ora_host']}/{self.config['oracle']['ora_sid']}")
        return self.db_connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes the connection to the oracle database.

        :return: None
        :raises: Exception
        """
        self.db_connection.close()
        if exc_val:
            raise Exception(exc_val)

    def configParse(self) -> None:
        config = open(self.path_config).readlines()
        self.config = {}
        for row in config:
            row = row.strip()
            if not row.startswith('#') and row != '':
                if row.startswith('['):
                    section = row[1:-1]
                    if section not in self.config:
                        self.config[section.lower()] = {}
                if '\t' in row:
                    items = row.split('\t')
                    self.config[section.lower()].update(
                        {items[0].strip().lower(): items[-1].strip()}
                    )
                if '  ' in row:
                    items = row.split('  ')
                    self.config[section.lower()].update(
                        {items[0].strip().lower(): items[-1].strip()}
                    )
                elif '=' in row:
                    items = row.split('=')
                    self.config[section.lower()].update(
                        {items[0].strip().lower(): items[-1].strip()}
                    )
