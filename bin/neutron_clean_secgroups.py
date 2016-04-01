#!/usr/bin/env python

import sys          # reads command-line args
import os

broken_n_sgroups = []
known_tids = []

from neutronclient.v2_0 import client as neutronclient
nc = neutronclient.Client(username=os.getenv('OS_USERNAME'),
                   password=os.getenv('OS_PASSWORD'),
                   tenant_name=os.getenv('OS_TENANT_NAME'),
                   auth_url=os.getenv('OS_AUTH_URL'))


from keystoneclient.v2_0 import client as kclient
keystone = kclient.Client(username=os.getenv('OS_USERNAME'),
                         password=os.getenv('OS_PASSWORD'),
                         tenant_name=os.getenv('OS_TENANT_NAME'),
                         auth_url=os.getenv('OS_AUTH_URL')
                         )
for tenant in keystone.tenants.list():
  known_tids.append(tenant.id)

security_groups = nc.list_security_groups()
for n_sgroup in security_groups.get('security_groups'):
  tid = n_sgroup.get('tenant_id')
  if tid not in known_tids:
    print "stray sgroup %s (tenant %s DNE)" % (n_sgroup.get('id'), tid)

