# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is keyretrieval.
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Ryan Kelly (rkelly@mozilla.com)
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import unittest

from pyramid import testing
from pyramid.httpexceptions import (HTTPNotFound,
                                    HTTPUnsupportedMediaType,
                                    HTTPLengthRequired,
                                    HTTPRequestEntityTooLarge)

from keyretrieval.views import get_key, put_key, delete_key
from keyretrieval.storage import IKeyRetrievalStorage
from keyretrieval.storage.sql import SQLKeyRetrievalStorage


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        storage = SQLKeyRetrievalStorage("sqlite://", create_tables=True)
        self.config.registry.registerUtility(storage, IKeyRetrievalStorage)

    def tearDown(self):
        testing.tearDown()

    def test_get_put_delete_cycle(self):
        # Initially there should be no data
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        self.assertRaises(HTTPNotFound, get_key, request)
        # Put some data.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        request.body = "TEST"
        request.content_length = 4
        request.content_type = "text/plain"
        res = put_key(request)
        self.assertEquals(res.status_int, 204)
        # Now we can retrieve it.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        res = get_key(request)
        self.assertEquals(res.status_int, 200)
        self.assertEquals(res.body, "TEST")
        # But only by using the correct username.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user2"}
        self.assertRaises(HTTPNotFound, get_key, request)
        # Delete the data.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        res = delete_key(request)
        self.assertEquals(res.status_int, 204)
        # And now it's gone.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        self.assertRaises(HTTPNotFound, get_key, request)
        # We can't delete it again.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        self.assertRaises(HTTPNotFound, delete_key, request)

    def test_put_with_binary_data(self):
        # Putting binary data should fail.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        request.body = "\x00" * 4
        request.content_length = 4
        request.content_type = "image/jpeg"
        self.assertRaises(HTTPUnsupportedMediaType, put_key, request)
        # Sending any text type will succeed.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        request.body = '{ "hello": "world" }'
        request.content_length = len(request.body)
        request.content_type = "text/json"
        res = put_key(request)
        self.assertEquals(res.status_int, 204)
        # But it's gonna come back as text/plain.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        res = get_key(request)
        self.assertEquals(res.status_int, 200)
        self.assertEquals(res.body, '{ "hello": "world" }')
        self.assertEquals(res.content_type, "text/plain")

    def test_length_limiting_of_uploads(self):
        # If the content-length is too big, it gets rejected.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        request.body = "WAREZ" * 1024 * 1024
        request.content_length = len(request.body)
        request.content_type = "text/plain"
        self.assertRaises(HTTPRequestEntityTooLarge, put_key, request)
        # And you can't just cheat by not sending content-length.
        request = testing.DummyRequest()
        request.matchdict = {"username": "user1"}
        request.body = "WAREZ" * 1024 * 1024
        request.content_length = None
        request.content_type = "text/plain"
        self.assertRaises(HTTPLengthRequired, put_key, request)
