#!/usr/bin/env python
"""fritz box api calls for python"""
import requests
import hashlib
import xml.etree.ElementTree as ET
import re
import logging
logger = logging.getLogger(__name__)

USERNAME = 'YOUR FRITZ USERNAME HERE'
PASSWORD = 'YOUR SECRET PASSWORD HERE'
DOMAIN = 'YOUR FRITZ IP/HOSTNAME HERE'

class Frytz(object):
    """class for interaction with the FRITZ!Box(R)"""

    def __init__(self, domain='fritz.box', password='', username=''):
        self.domain = 'http://' + domain
        self.base = '{}/fon_num/fonbook_list.lua'.format(self.domain)
        self.headers = {'content-type': "application/x-www-form-urlencoded"}
        self.username = username
        self.password = password
        self.sid = self._get_sid()
        logging.basicConfig(level=logging.INFO)

    def _get_sid(self):
        """
        gets a sesion id

        see [1] for details

        [1] http://www.avm.de/de/Extern/files/session_id/AVM_Technical_Note_-_Session_ID.pdf
        """
        response = requests.get('{}/login_sid.lua'.format(self.domain))
        tree = ET.fromstring(response.content)
        for one in tree.findall('Challenge'):
            challenge = one.text
        md5sum = hashlib.md5((challenge + "-" + self.password).encode('utf-16LE'))
        md5sum = md5sum.hexdigest()

        fresponse = challenge + '-' + md5sum
        #parameter = "&login:command/response={}".format(fresponse)
        response = requests.get(
            '{}/login_sid.lua?username={}&response={}'.format(self.domain, self.username, fresponse),
            headers=self.headers
        )
        # we are looking for something like this:
        # <SID>0123456789abcdef</SID>
        match = re.search(r'\<SID\>([^<]+)\</SID\>', response.text)
        if match:
            sid = match.groups()[0]
        else:
            logger.error('could not get sid')
            logger.error('response was:')
            logger.error(response.content)
            raise Exception('could not get sid')
        logger.debug('SID:', sid)
        return sid

    def dial(self, number):
        """dial number

        pick up the default phone
        """
        url = self.base
        data = ('{post_base}&sid={sid}&dial={number}')
        data = data.format(post_base=self.base, number=number, sid=self.sid)
        response = requests.post(url, data=data, headers=self.headers)
        if response.status_code != 200:
            logger.error(response.text)
        else:
            logger.info(response.text)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        print('usage: frytz.py +492219876543')
    else:
        frytz = Frytz(password=PASSWORD, username=USERNAME, domain=DOMAIN)
        frytz.dial(sys.argv[1])
