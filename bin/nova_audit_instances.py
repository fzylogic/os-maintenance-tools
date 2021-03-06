#!/usr/bin/env python

import argparse
import libvirt
import os
import socket
import sys
import time

parser = argparse.ArgumentParser(description='Nova Auditor')
parser.add_argument('--clean', action='store_true', default=False, help='auto-clean orphans')
parser.add_argument('--quiet', action='store_true', default=False, help='lose the chit-chat')
parser.add_argument('--hypervisor', action='append', default=[], help='specify a hypervisor to check')
args = parser.parse_args()


connection_template = os.getenv('NOVA_LIBVIRT_CONNECTION_TEMPLATE')

graphite_enabled = os.getenv('GRAPHITE_ENABLED')
if graphite_enabled == 'yes':
  graphite_host = os.getenv('GRAPHITE_HOST')
  graphite_port = os.getenv('GRAPHITE_PORT')
  graphite_prefix = os.getenv('GRAPHITE_PREFIX')

from novaclient.v1_1 import client
nc = client.Client(os.getenv('OS_USERNAME'), os.getenv('OS_PASSWORD'), os.getenv('OS_TENANT_NAME') , os.getenv('OS_AUTH_URL'), service_type="compute")
hosts = []
metrics = dict()

nova_servers = dict()

def ship_metric(name, value, timestamp=time.time()):
  if graphite_enabled == 'yes':
    sock = socket.socket()
    sock.settimeout(5)
    sock.connect( (graphite_host, graphite_port) )
    print "%s %s %d" % (graphite_prefix + name, value, timestamp)
    sock.send("%s %s %d\n" % (STATS_PREFIX + name, value, timestamp))
    sock.close()

def add_server(server):
  name = s._info['OS-EXT-SRV-ATTR:instance_name']
  hypervisor = s._info['OS-EXT-SRV-ATTR:hypervisor_hostname']
  if hypervisor not in nova_servers:
    nova_servers[hypervisor] = dict()
  nova_servers[hypervisor][name] = s

for s in nc.servers.list(True, {'all_tenants': '1'}):
  add_server(s)

for s in nc.servers.list(True, {'all_tenants': '1', 'deleted': '1'}):
  add_server(s)

if args.hypervisor:
  hosts = args.hypervisor
else:
  for hv in nc.hypervisors.list():
    hosts.append(hv.hypervisor_hostname)

for hypervisor in hosts:
  if not args.quiet:
    print 'Auditing {}'.format(hypervisor)
  try:
    conn = libvirt.open(connection_template.replace('$host', hypervisor))
  except:
    print "Connection to {} failed".format(hypervisor)
    conn = False
  if conn:
    for id in conn.listDomainsID():
      dom = conn.lookupByID(id)
      infos = dom.info()
      if hypervisor in nova_servers:
        if dom.name() not in nova_servers[hypervisor]:
          uuid = dom.UUIDString()
          if not args.quiet:
            print "name: {}, id: {} not found in first check of nova on {}".format(dom.name(), id, hypervisor)
          try:
            if nc.servers.get(uuid):
              if not args.quiet:
                print "name: {}, id: {} APPEARED after second check of nova on {}".format(dom.name(), id, hypervisor)
              continue
          except:
            pass
          if args.clean:
            print "auto-cleaning %s" % dom.name()
            try:
              dom.destroy()
              metrics['unknown_strays'] += 1
            except libvirt.libvirtError:
              pass
        else:
          if nova_servers[hypervisor][dom.name()].status == 'DELETED':
            if not args.quiet:
              print "{} supposed to be deleted on {}".format(dom.name(), hypervisor)
            if args.clean:
              print "auto-cleaning %s" % dom.name()
              try:
                dom.destroy()
                metrics['deleted_strays'] += 1
              except libvirt.libvirtError:
                pass
  
for metric in metrics:
  ship_metrics(metric, metrics[metric])
