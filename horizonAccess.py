#!/usr/bin/env python
# coding: utf-8

"""This simple module allows to retrieve information about books
checked out in the library using Dynix Horizon software. Only basic
functionality is provided.

Usage example:
import horizonAccess
l = horizonAccess.Library('LIBRARY_URL_ENDING_IN.jsp', 'ID', 'PASSWORD')
l.mybooks()

Author: Wiktor Gołgowski <wgolgowski@gmail.com>
License: WTFPL <http://www.wtfpl.net>
"""

from __future__ import print_function, unicode_literals

"""Make urllib work under Python 2 and 3.
See [http://python3porting.com/noconv.html]
"""
try:
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
except ImportError:
    from urllib2 import urlopen, Request
    from urllib import urlencode

import xml.etree.ElementTree as ET


class Library:
    def __init__(self, url, idnum, code, debug=False):

        """
        Keyword Arguments:
        url   -- base URL of the library,
        idnum -- ID number,
        code  -- access code.
        """
        self.debug = debug
        self.baseUrl = url
        self.idnum = idnum
        self.code = code
        self.authorized = False
        self.session = ''

    def auth(self):
        """
        Creates new session with provided credentials.
        """
        # Get session ID:
        resp = urlopen(self.baseUrl + '?auth=true&GetXML=true')
        tree = ET.fromstring(resp.read())
        sessid = tree.find('session').text
        if self.debug:
            print('Session ID: %s' % sessid)

        # Authorize:
        params = {
            'session': sessid,
            'sec1': self.code,
            'sec2': self.idnum,
        }

        data = urlencode(params)
        req = Request(self.baseUrl + '?GetXML=true',
                      data.encode('ascii'))
        resp = urlopen(req)
        xx = resp.read()
        tree = ET.fromstring(xx)
        auth = tree.find('security/auth').text
        if auth == 'true':
            if self.debug:
                print('Authorized.')
            self.session = sessid
            self.authorized = True
            return True
        else:
            if self.debug:
                print('Authorization failed.')
            self.authorized = False
            return False

    def mybooks(self):
        """
        Returns a dictionary consisting of error code (0 if success) and a
        list of borrowed books. Every book is a tuple with name, due
        date, checkout date and number of prolongates.

        """
        retval = {'status': 0, 'books': []}
        if not self.authorized and not self.auth():
            if self.debug:
                print('Cannot authorize. Check your URL/credentials.')
            retval['status'] = 1
            return retval
        else:
            params = {
                'session': self.session,
                'menu': 'account',
                'submenu': 'itemsout'
            }
            req = Request(self.baseUrl + '?GetXML=true',
                          urlencode(params).encode('ascii'))
            resp = urlopen(req)
            myparser = ET.XMLParser(encoding="utf-8")
            tree = ET.fromstring(resp.read(), parser=myparser)
            auth = tree.find('security/auth').text
            if auth != 'true':
                if self.debug:
                    print('Request failed: not authenticated (timeout?).')
                retval['status'] = 2
                return retval
            else:
                books = tree.find('itemsoutdata')
                blist = []
                for book in books.findall('itemout'):
                    blist.append((book.find('disptitle').text,
                                  book.find('duedate').text,
                                  book.find('ckodate').text,
                                  book.find('numrenewals').text))
                retval['books'] = blist
                return retval
