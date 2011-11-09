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
"""

SQLAlchemy-based storage backend for key-retrieval.

"""

import urlparse

from zope.interface import implements

from sqlalchemy import (String, Text, Column, Table, MetaData, create_engine)

from keyretrieval.storage import IKeyRetrievalStorage


metadata = MetaData()
tables = []

# Table mapping userids to stored key data.
#
keydata = Table("keydata", metadata,
    Column("userid", String(64), primary_key=True),
    Column("data",  Text, nullable=False),
)
tables.append(keydata)


class SQLKeyRetrievalStorage(object):
    """IKeyRetrievalStorage implemented on top of an SQL database."""

    implements(IKeyRetrievalStorage)

    def __init__(self, sqluri, pool_size=100, pool_recycle=60,
                 reset_on_return=True, create_tables=False,
                 pool_max_overflow=10, no_pool=False,
                 pool_timeout=30, **kwds):
        self.sqluri = sqluri
        self.driver = urlparse.urlparse(sqluri).scheme
        # Create the engine pased on database type and given parameters.
        # SQLite engines are forced to use default pool options.
        if no_pool or self.driver == 'sqlite':
            sqlkw = {}
        else:
            sqlkw = {'pool_size': int(pool_size),
                     'pool_recycle': int(pool_recycle),
                     'pool_timeout': int(pool_timeout),
                     'max_overflow': int(pool_max_overflow)}
            if self.driver.startswith("mysql") or self.driver == "pymsql":
                sqlkw['reset_on_return'] = reset_on_return
        sqlkw['logging_name'] = 'sqlstore'
        self._engine = create_engine(sqluri, **sqlkw)
        # Bind the tables to the engine, creating if necessary.
        for table in tables:
            table.metadata.bind = self._engine
            if create_tables:
                table.create(checkfirst=True)
        self.engine_name = self._engine.name

    def execute(self, query, *args, **kwds):
        # XXX: copy safe_execute logic from server-storage
        return self._engine.execute(query, *args, **kwds)

    def get(self, userid):
        query = "SELECT data FROM keydata WHERE userid = :userid"
        row = self.execute(query, userid=userid).fetchone()
        if row is None:
            raise KeyError(userid)
        return row[0]

    def set(self, userid, data):
        # First try an update.  If that fails, do an insert.
        query = "UPDATE keydata SET data = :data WHERE userid = :userid"
        res = self.execute(query, userid=userid, data=data)
        if res.rowcount == 0:
            query = "INSERT INTO keydata VALUES (:userid, :data)"
            self.execute(query, userid=userid, data=data)

    def delete(self, userid):
        query = "DELETE FROM keydata WHERE userid = :userid"
        res = self.execute(query, userid=userid)
        if res.rowcount == 0:
            raise KeyError(userid)
