#!/usr/bin/env python

import logging
import os
import re
import requests
import time
import sys

from bs4 import BeautifulSoup
from influxdb import InfluxDBClient

class YggTorrentException(RuntimeError):
    pass

class YggTorrent(object):
    RE_BYTES = re.compile(r'(?P<value>\d+(?:\.\d+)?)(?P<unit>[bMGT]?o)')
    RE_RATIO = re.compile(r'(?P<value>\d+(?:\.\d+)?)')
    UNITS = ('o', 'Mo', 'Go', 'To')

    def __init__(self, domain, username, password):
        self._domain = domain
        self._username = username
        self._password = password
        self._cookies = None

    def _request(self, method, subdomain, uri, payload=None):
        url = 'https://{}.{}/{}'.format(
            subdomain,
            self._domain,
            uri.lstrip('/'),
        )
        return requests.request(
            method,
            url,
            data=payload,
            cookies=self._cookies)

    def _post(self, subdomain, uri, payload):
        return self._request('POST', subdomain, uri, payload)

    def _get(self, subdomain, uri):
        return self._request('GET', subdomain, uri)

    def _convert_bytes(self, string):
        logging.debug('Converting "%s" to bytes', string)

        m = self.RE_BYTES.match(string)

        if not m:
            raise YggTorrentException('Unable to convert "{}" to bytes'.format(string))

        unit = m.group('unit')

        if unit not in self.UNITS:
            raise YggTorrentException('Invalid unit found: "{}"'.format(unit))

        unit_index = self.UNITS.index(unit)
        value = float(m.group('value'))
        
        return value * (1024 ** unit_index) * 1.0

    def _convert_ratio(self, string):
        logging.debug('Converting "%s" to float', string)

        m = self.RE_RATIO.match(string)

        if not m:
            raise YggTorrentException('Unable to convert "{}" to float'.format(string))

        value = float(m.group('value'))
        
        return value * 1.0

    def login(self):
        res = self._post(
            'www',
            '/user/login',
            {
                'id': self._username,
                'pass': self._password,
            }
        )

        if not res.ok:
            raise YggTorrentException('Unable to login to YggTorrent!')

        self._cookies = res.cookies

    def logout(self):
        self._cookies = None
        self._get('www2', '/user/logout')

    def get_ratio(self):
        res = self._get('www2', '/user/account')

        if not res.ok:
            raise YggTorrentException('Not logged in')

        parser = BeautifulSoup(res.text, 'html.parser')

        return (
            self._convert_bytes(
                parser.find('td', text='Qtt uploadée').parent.find('strong').text.strip()
            ),
            self._convert_bytes(
                parser.find('td', text='Qtt téléchargée').parent.find('strong').text.strip()
            ),
            self._convert_ratio(
                parser.find('td', text='Ratio').parent.find('a').text.strip()
            ),
        )

def update(ygg):
    try:
        ygg.login()
    except YggTorrentException as e:
        logging.error('Unable to login to YggTorrent: %s', e)
        logging.exception(e)
        return False

    ratio = ygg.get_ratio()
    points = []

    points.append({
        'measurement': 'yggtorrent_download',
        'tags': {
            'username': os.getenv('YGGTORRENT_USER'),
        },
        'fields': {
            'value': ratio[0],
        }
    })

    points.append({
        'measurement': 'yggtorrent_upload',
        'tags': {
            'username': os.getenv('YGGTORRENT_USER'),
        },
        'fields': {
            'value': ratio[1],
        }
    })

    points.append({
        'measurement': 'yggtorrent_ratio',
        'tags': {
            'username': os.getenv('YGGTORRENT_USER'),
        },
        'fields': {
            'value': ratio[2],
        }
    })

    try:
        client = InfluxDBClient(
            host=os.getenv('INFLUXDB_HOST'),
            port=os.getenv('INFLUXDB_PORT'),
            username=os.getenv('INFLUXDB_USER'),
            password=os.getenv('INFLUXDB_PASS'),
            database=os.getenv('INFLUXDB_BASE'),
            timeout=os.getenv('INFLUXDB_TIMEOUT', 10),
        )
        client.write_points(points)

        logging.info('Written {} point(s) to InfluxDB.'.format(
            len(points)
        ))
    except Exception as e:
        logging.error('Unable to write {} point(s) to InfluxDB'.format(
            len(points),
        ))
        logging.exception(e)
        return False

    try:
        ygg.logout()
    except Exception:
        pass
    finally:
        return True

def usage():
    print('You need to define following environment variables:')
    print(' - YGGTORRENT_DOMAIN')
    print(' - YGGTORRENT_USER')
    print(' - YGGTORRENT_PASS')
    print(' - INFLUXDB_HOST')
    print(' - INFLUXDB_PORT')
    print(' - INFLUXDB_USER')
    print(' - INFLUXDB_PASS')
    print(' - INFLUXDB_BASE')

if '__main__' == __name__:
    # Check environment variables
    for env_name in [
        'YGGTORRENT_DOMAIN',
        'YGGTORRENT_USER',
        'YGGTORRENT_PASS',
        'INFLUXDB_HOST',
        'INFLUXDB_PORT',
        'INFLUXDB_USER',
        'INFLUXDB_PASS',
        'INFLUXDB_BASE',
    ]:
        if os.getenv(env_name) is None:
            usage()
            sys.exit(1)

    # Configure logging
    logging_level = int(os.getenv('LOG_LEVEL', logging.INFO))
    logging.basicConfig(level=logging_level, format='[%(asctime)s] (%(levelname)s) %(message)s')

    # Initialize YggTorrent client
    ygg = YggTorrent(
        os.getenv('YGGTORRENT_DOMAIN'),
        os.getenv('YGGTORRENT_USER'),
        os.getenv('YGGTORRENT_PASS'),
    )

    # Main loop
    while True:
        if not update(ygg):
            logging.warning('Unable to update data')
        time.sleep(int(os.getenv('LOOP_DELAY', 1)) * 60)
