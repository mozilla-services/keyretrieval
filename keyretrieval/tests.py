import unittest

from pyramid import testing
from pyramid.httpexceptions import (HTTPNotFound,
                                    HTTPUnsupportedMediaType,
                                    HTTPLengthRequired,
                                    HTTPRequestEntityTooLarge)

from keyretrieval.views import get_key, put_key, delete_key


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

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
