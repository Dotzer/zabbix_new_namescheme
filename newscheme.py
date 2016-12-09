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

yes = set(['yes', 'y'])


# Get group data from parameter
def get_group_name(grpnum):
    grpdata = zapi.hostgroup.get(output="extend", groupids=grpnum)
    print 'Do you want to use custom or default name for group or skip it?'
    print 'default : "' + grpdata[0]['name'] + ', " (y,yes/skip/*)'
    choice = raw_input().lower()
    if choice in yes:
        print "Type in your custom name (Don't forget comma and space):"
        group_name = raw_input()
    elif choice == 'skip':
        group_name = ''
    else:
        print "Leaving it default."
        group_name = grpdata[0]['name'] + ', '
    return group_name


# form new names for selected group
def form_new_names(grpnum):
    out_list = []
    # Filing list out_list with names and host ids
    for host_list in zapi.host.get(output="extend",
                                   groupids=grpnum):
        host_id = host_list['hostid']
        group_check = zapi.host.get(output='hostid',
                                    selectGroups='groupid',
                                    hostids=host_id)
        name = host_list['name'].split(',', 1)
        for host_int in zapi.hostinterface.get(output="extend",
                                               hostids=host_id,
                                               filter={'type': 2}):
            ip = host_int['ip']
        hhost_new = ip
        if (len(name) == 1 or name[1].strip() == ''):
            hname_new = grpname + 'неизв ' + str(host_id)
        else:
            hname_new = grpname + name[1].strip()
        if len(group_check[0]['groups']) == 1:
            out_list.append([host_id, hhost_new, hname_new])
        else:
            # if user wants, script can ignore hosts with > 1 group
            print ('Host "' + host_list['name'] +
                   '" has more than one group bound to it.')
            print 'Rewrite anyways? [y,yes,ye/*]:'
            choice = raw_input().lower()
            if choice in yes:
                print "This one will be changed."
                out_list.append([host_id, hhost_new, hname_new])
            else:
                print "Ignoring it."
    return out_list


def check_name_list(in_list):
    name_list = []
    for list_ind in range(0, len(in_list)):
        name_list.append(in_list[list_ind][2])
    dups = [item for item, count in collections.Counter(name_list).items()
            if count > 1]
    return dups

if len(sys.argv) == 2:
    grp = sys.argv[1]
    grpname = get_group_name(grp)
    new_list = form_new_names(grp)
    z = check_name_list(new_list)
    if len(z) > 0:
        print 'Not applying changes because there are duplicates in names:'
        for dup in z[0:len(z)]:
            print dup
    else:
        for x in range(0, len(new_list)):
            print ('hostid = ' + new_list[x][0] +
                   '\nhostname = ' + new_list[x][1] +
                   '\nvisiblename = ' + '"' + new_list[x][2] + '"')
        print "Do you want to deploy changes?(y,yes/*):"
        deploy = raw_input().lower()
        if deploy in yes:
            print "Deploying changes"
            for x in range(0, len(new_list)):
                zapi.host.update(hostid=new_list[x][0],
                                 host=new_list[x][1],
                                 name=new_list[x][2])
else:
    print 'Not enough, or too many arguments (' + str(len(sys.argv)-1) + ')'
