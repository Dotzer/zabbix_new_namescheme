#!/usr/bin/python
# -*- coding: utf-8 -*

# Initialzing base data
import codecs
import base64
import sys
import collections
from pyzabbix import ZabbixAPI
# Setting default text encoding to UTF-8
reload(sys)
sys.setdefaultencoding('utf-8')
# Importing password data
passfile = open('/home/dotza/python/base/password', 'r')
passw = passfile.readlines()
passw = base64.b64decode(passw[0].rstrip())
# Initializing ZabbixAPI
zapi = ZabbixAPI("http://monitor.st65.ru")
zapi.login("i.kim", passw)
print "Connected to Zabbix API Version %s" % zapi.api_version()
# Get group data from parameter
grp = sys.argv[1]
grpdata = zapi.hostgroup.get(output="extend", groupids=grp)
grpname = grpdata[0]['name']
print grp + '     ' + grpname
# Initializing variables
unk = 0
out_list = []
name_list = []
yes = set(['yes', 'y', 'ye'])
# Filing list out_list with names and host ids
for host_list in zapi.host.get(output="extend",
                               groupids=grp):
    host_id = host_list['hostid']
# Check if host hast more than 1 group
    group_check = zapi.host.get(output='hostid',
                                selectGroups='groupid',
                                hostids=host_id)
    name = host_list['name'].split(',', 1)
    for host_int in zapi.hostinterface.get(output="extend",
                                           hostids=host_id,
                                           filter={'type': 2}):
        ip = host_int['ip']
    hhost_new = ip
    if len(name) > 1:
        hname_new = grpname + ',' + name[1]
    else:
        hname_new = grpname + ' неизв ' + unk + ' ' + ip
        unk += 1
    if len(group_check[0]['groups']) == 1:
        out_list.append([host_id, hhost_new, hname_new])
        name_list.append(hname_new)
    else:
        # if user wants, script can ignore hosts with > 1 group
        print ('Host ' + host_list['name'] +
               ' has more than one group bound to it.')
        print 'Rewrite anyways? [y,yes,ye/*]:'
        choice = raw_input().lower()
        if choice in yes:
            print "Okay, this one will be changed."
            out_list.append([host_id, hhost_new, hname_new])
            name_list.append(hname_new)
        else:
            print "Okay, ignoring it."
# Checking for duplicate names in output list
z = [item for item, count in collections.Counter(name_list).items()
     if count > 1]
if len(z) > 0:
    print 'Not applying changes because there are duplicates in names:'
    for dup in z[0:len(z)]:
        print dup
else:
    print 'No duplicates in names.'
    for x in range(0, len(out_list)):
        # Applying changes
        print ('hostid = ' + out_list[x][0] +
               '\nhostname = ' + out_list[x][1] +
               '\nvisiblename = ' + out_list[x][2])
        zapi.host.update(hostid=out_list[x][0],
                         host=out_list[x][1],
                         name=out_list[x][2])
