# -*- coding: utf-8 -*-

import os
import sys
import socket
import time
import datetime

STATUS_LIST = {
    '0': 'successful',
    '1': 'failed',
    '2': 'running',
    '3': 'unknown'
}


def is_windows():
    import platform
    
    os_arch = False
    if platform.system() == 'Windows':
        os_arch = True
    return os_arch


def serial_encrypt(obj):
    if sys.version_info[0] == 3:
        try:
            import _pickle as pickle
        except:
            import pickle
    else:
        try:
            import cPickle as pickle
        except:
            import pickle
    
    pickle_obj = pickle.dumps(obj)
    return pickle_obj


def serial_decrypt(obj):
    if sys.version_info[0] == 3:
        try:
            import _pickle as pickle
        except:
            import pickle
    else:
        try:
            import cPickle as pickle
        except:
            import pickle
    
    pickle_obj = pickle.loads(obj)
    return pickle_obj


def get_time():
    dt = datetime.datetime.now()
    tm = dt.strftime("%Y-%m-%d %H:%M:%S")
    return tm


def get_timestamp():
    dt = datetime.datetime.now()
    ts = dt.strftime("%Y%m%d%H%M%S%f")
    if is_windows:
        rnd = str(int(time.time()))
        ts = ts[:-3] + rnd[-3:]
    return ts


def get_ip_address(host='8.8.8.8', port=80, matchini=False):
    if sys.version_info[0] == 3:
        import configparser as ConfigParser
    else:
        import ConfigParser
    from zzagent.inits import cliini
    
    if os.path.exists(cliini) and matchini == True:
        config = ConfigParser.ConfigParser()
        config.read(cliini)
        host = config.get('client', 'server_host')
        port = config.get('client', 'server_port')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((host, int(port)))
    ip_address = sock.getsockname()[0]
    sock.close()
    return ip_address


def empty_socket(sock):
    input = [sock]
    while True:
        inputready, o, e = select.select(input,[],[], 0.0)
        if len(inputready) == 0:
            break
        for s in inputready:
            s.recv(1)
