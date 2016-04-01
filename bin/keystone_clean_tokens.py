#!/usr/bin/env python

from datetime import datetime
import os
from sqlalchemy import create_engine, MetaData, Table

keystone_db_conn = os.getenv('KEYSTONE_DB_CONNECTION')

engine = create_engine(keystone_db_conn, echo=True)
conn = engine.connect()
metadata = MetaData()
token = Table(
    'token',
    metadata,
    autoload=True,
    autoload_with=engine
)

conn.execute(token.delete(token.c.expires<=datetime.now()))
