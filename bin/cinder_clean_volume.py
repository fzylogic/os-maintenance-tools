#!/usr/bin/env python

import os
from cinderclient.v1 import client

cinder_db_conn = os.getenv('CINDER_DB_CONNECTION')

cc = client.Client(os.getenv('OS_USERNAME'), os.getenv('OS_PASSWORD'), os.getenv('OS_TENANT_NAME'), os.getenv('OS_AUTH_URL'), service_type='volume')
volumes = []

for vol in cc.volumes.list(True, {'all_tenants': '1'}):
  if vol.status in ('error', 'error_deleting'):
    print vol.id + " " + vol.status
    volumes.append(vol)

dialog = "Delete all errored volumes? (Y/N)"
try: 
  confirm = raw_input(dialog)
except NameError: 
  confirm = input(dialog)

if ( confirm.lower() == 'y' ):
  for vol in volumes:
    print "Deleting " + vol.id
    if not vol.force_delete():
      print "Error Deleting " + vol.id
