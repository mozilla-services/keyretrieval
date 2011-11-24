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

from pyramid.security import Allow
from pyramid.response import Response
from pyramid.httpexceptions import (HTTPNotFound,
                                    HTTPUnsupportedMediaType,
                                    HTTPLengthRequired,
                                    HTTPRequestEntityTooLarge)

from cornice import Service

from keyretrieval.storage import IKeyRetrievalStorage


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
    store = request.registry.getUtility(IKeyRetrievalStorage)
    try:
        key = store.get(username)
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
    store = request.registry.getUtility(IKeyRetrievalStorage)
    store.set(username, request.body)
    return Response(status=204)


@user_key.delete(permission="edit")
def delete_key(request):
    """Delete any uploaded key-retrieval information."""
    username = request.matchdict["username"]
    store = request.registry.getUtility(IKeyRetrievalStorage)
    try:
        store.delete(username)
    except KeyError:
        raise HTTPNotFound()
    else:
        return Response(status=204)
