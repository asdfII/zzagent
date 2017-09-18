# -*- coding: utf-8 -*-

import os


def create_dirpath(role=None):
    dirpath = os.path.join(os.path.expanduser('~'), '.zzagent')
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    if role == 'server':
        serverpath = os.path.join(dirpath, 'server')
        if not os.path.exists(serverpath):
            os.mkdir(serverpath)
        dirpath = serverpath
    elif role == 'client':
        clientpath = os.path.join(dirpath, 'client')
        if not os.path.exists(clientpath):
            os.mkdir(clientpath)
        dirpath = clientpath
    return dirpath


def create_server_ini(host='localhost'):
    srvini = os.path.join(os.path.expanduser('~'), '.zzserver.ini')
    if not os.path.exists(srvini):
        with open(srvini, 'wb+') as f:
            f.truncate()
            f.write('[server]\n')
            f.write('host = %s\n' % host)
            f.write('port = 9999\n')
            f.write('backlog = 5\n')
            f.write('timeout = 10\n')
            f.write('serverpath = %s\n' % create_dirpath('server'))
    return srvini


def create_client_ini(host='localhost'):
    cliini = os.path.join(os.path.expanduser('~'), '.zzclient.ini')
    if not os.path.exists(cliini):
        with open(cliini, 'wb+') as f:
            f.truncate()
            f.write('[client]\n')
            f.write('server_host = %s\n' % host)
            f.write('server_port = 9999\n')
            f.write('timeout = 30\n')
            f.write('clientpath = %s\n' % create_dirpath('client'))
    return cliini
