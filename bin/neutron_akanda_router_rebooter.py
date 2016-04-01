#!/usr/bin/env python

import os
import sys

from neutronclient.v2_0 import client as neutronclient
nc = neutronclient.Client(username=os.getenv('OS_USERNAME'),
                   password=os.getenv('OS_PASSWORD'),
                   tenant_name=os.getenv('OS_TENANT_NAME'),
                   auth_url=os.getenv('OS_AUTH_URL'))

from novaclient.v1_1 import client as novaclient
novac = novaclient.Client(os.getenv('OS_USERNAME'),
                      os.getenv('OS_PASSWORD'),
                      os.getenv('OS_TENANT_NAME'),
                      os.getenv('OS_AUTH_URL')
                      )
from keystoneclient.v2_0 import client
keystone = client.Client(username=os.getenv('OS_USERNAME'),
                         password=os.getenv('OS_PASSWORD'),
                         tenant_name=os.getenv('OS_TENANT_NAME'),
                         auth_url=os.getenv('OS_AUTH_URL')
                         )
glance_endpoint = keystone.service_catalog.get_endpoints('image').get('image')[0].get('internalURL')
## HACKITY HACK HACK HACK
if ( glance_endpoint.endswith('/v2') or glance_endpoint.endswith('/v1') ) :
  glance_endpoint = glance_endpoint.rsplit('/', 1)[0]

print "Found a glance endpoint at {}".format(glance_endpoint)

for tenant in keystone.tenants.list():
  if tenant.name == 'service':
    svc_tenant = tenant.id
    break

if not svc_tenant:
  print "can't find service tenant, bailing"
  sys.exit(0)

token = keystone.auth_token

from glanceclient import Client as glanceclient
gc = glanceclient('1', endpoint=glance_endpoint, token=token)

router_images = []

servers = {}

for server in novac.servers.list(True, {'all_tenants': 1}):
  ## Skip anything that doesn't look like a router instance 
  router = 0
  try:
    image_id = server.image.get('id')
  except AttributeError:
    image_id = False
  if image_id:
    gc.images.get(image_id)
    try:
      image = gc.images.get(image_id)
    except:
      print "can't find image with id of " + image_id
      
    else:
      if image.name.startswith('akanda') and image.owner == svc_tenant:
        router = 1

  if router == 1:
    servers[server.name] = server


for router in nc.list_routers().get('routers'):
  nova_name = "ak-" + router.get('id')
  if nova_name in servers:
    print "Rebooting " + nova_name
    servers[nova_name].reboot(reboot_type='HARD')
