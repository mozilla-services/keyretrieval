from pyramid.exceptions import Forbidden
from pyramid.security import authenticated_userid, Allow
from pyramid.response import Response
from pyramid.httpexceptions import (HTTPNoContent, HTTPNotFound,
                                    HTTPUnsupportedMediaType,
                                    HTTPLengthRequired,
                                    HTTPRequestEntityTooLarge)

from cornice import Service

# Mapping from usernames to uploaded key data.
# Eventually this will live in a configurable backend store.
_USER_KEYS = {}


def user_key_acl(request):
    """Access control for user_keys service.

    The matched username is allows to view and edit; no-one else is
    allow to do anything at all.
    """
    username = request.matchdict["username"]
    return [(Allow, username, "view"), (Allow, username, "edit")]


user_key = Service(name="user_key", path="/{username}", acl=user_key_acl)


@user_key.get(permission="view")
def get_key(request):
    """Returns the uploaded key-retrieval information."""
    username = request.matchdict["username"]
    try:
        key = _USER_KEYS[username]
    except KeyError:
        raise HTTPNotFound()
    else:
        return Response(key, content_type="text/plain")


@user_key.put(permission="edit")
def put_key(request):
    """Uploads new key-retrieval information."""
    # Validate that the request is text/<something>
    if request.content_type:
        if not request.content_type.startswith("text/"):
            raise HTTPUnsupportedMediaType()
    # Validate that the request is not too big
    if request.content_length is None:
        raise HTTPLengthRequired()
    if request.content_length > 8 * 1024:
        raise HTTPRequestEntityTooLarge()
    # Store the uploaded data.
    username = request.matchdict["username"]
    _USER_KEYS[username] = request.body
    return Response(status=204)


@user_key.delete(permission="edit")
def delete_key(request):
    """Delete any uploaded key-retrieval information."""
    username = request.matchdict["username"]
    try:
        del _USER_KEYS[username]
    except KeyError:
        raise HTTPNotFound()
    else:
        return Response(status=204)
