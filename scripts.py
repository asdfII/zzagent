# -*- coding: utf-8 -*-

import argparse
import sys


def zzserver():
    from zzagent.dancers import ServerDaemon
    daemon = ServerDaemon()
    
    parser = argparse.ArgumentParser(
        description='ServerDaemon runner',
        epilog='That\'s all folks.')
    try:
        parser.add_argument(
            'operation',
            metavar='Usage: {} [start|stop|restart|status]'.format(sys.argv[1]),
            type=str,
            help='Operation with daemon. Accepts any of these values: \
                start, stop, restart, status',
            choices=['start', 'stop', 'restart', 'status'])
        args = parser.parse_args()
        operation = args.operation
    except IndexError as e:
        print(e)
        sys.exit(1)
    
    if operation == 'start':
        print('Starting daemon')
        daemon.start()
        pid = daemon.get_pid()
        if not pid:
            print('Unable run daemon')
        else:
            print('Daemon is running with pid %d' % pid)
    elif operation == 'stop':
        print('Stoping daemon')
        daemon.stop()
    elif operation == 'restart':
        print('Restarting daemon')
        daemon.restart()
    elif operation == 'status':
        pid = daemon.get_pid()
        if not pid:
            print('Daemon isn\'t running')
        else:
            print('Daemon is running with pid %d' % pid)
    sys.exit(0)


def zzclient():
    from zzagent.dancers import ClientDaemon
    daemon = ClientDaemon()
    
    parser = argparse.ArgumentParser(
        description='ClientDaemon runner',
        epilog='That\'s all folks.')
    try:
        parser.add_argument(
            'operation',
            metavar='Usage: {} [start|stop|restart|status]'.format(sys.argv[1]),
            type=str,
            help='Operation with daemon. Accepts any of these values: \
                start, stop, restart, status',
            choices=['start', 'stop', 'restart', 'status'])
        args = parser.parse_args()
        operation = args.operation
    except IndexError as e:
        print(e)
        sys.exit(1)
    
    if operation == 'start':
        print('Starting daemon')
        daemon.start()
        pid = daemon.get_pid()
        if not pid:
            print('Unable run daemon')
        else:
            print('Daemon is running with pid %d' % pid)
    elif operation == 'stop':
        print('Stoping daemon')
        daemon.stop()
    elif operation == 'restart':
        print('Restarting daemon')
        daemon.restart()
    elif operation == 'status':
        pid = daemon.get_pid()
        if not pid:
            print('Daemon isn\'t running')
        else:
            print('Daemon is running with pid %d' % pid)
    sys.exit(0)


def zzmanager():
    from zzagent.dancers import ManagerDaemon
    daemon = ManagerDaemon()
    
    if len(sys.argv) < 2:
        print('Usage: list|execute')
        sys.exit(0)
    if sys.argv[1] == 'list':
        daemon.list()
    elif sys.argv[1] == 'execute':
        daemon.execute(sys.argv[2], sys.argv[3])
    sys.exit(0)
