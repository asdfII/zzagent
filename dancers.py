# -*- coding: utf-8 -*-

import os
import sys
import time
if sys.version_info[0] == 3:
    import socketserver as SocketServer
    import configparser as ConfigParser
    import queue as Queue
else:
    import SocketServer
    import ConfigParser
    import Queue

from zzagent.daemons import Daemon
from zzagent.utils import get_time


class BaseDaemon(Daemon):
    def run(self):
        print(self.__class__.__name__.rstrip('Daemon') + ' starts.')
        while True:
            time.sleep(0.1)


class ServerDaemon(Daemon):
    def __init__(self, pidfile='/tmp/zzserver.pid',
        stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        Daemon.__init__(self, pidfile,
            stdin=os.devnull, stdout=os.devnull, stderr=os.devnull)
        self.stdin = stdin
        self.stdout = '/var/log/zzserver.log'
        self.stderr = '/var/log/zzserver.log'
    
    def run(self):
        import threading
        from zzagent.inits import create_server_ini
        from zzagent.models import (Server, RPCServer, HttpServer,
            PathDispatcher)
        from zzagent.costumes import (home_page, exec_command,
            exec_config, init_environ, test_page, zz_tasks)
        
        os.chdir(os.path.expanduser('~'))
        config = ConfigParser.ConfigParser()
        config.read(create_server_ini())
        host = config.get('server', 'host')
        port = config.get('server', 'port')
        
        server = Server(host, int(port))
        s1 = threading.Thread(target=server.run)
        s1.daemon = True
        s1.start()
        print('[%s]: %s starts.' % (
            get_time(), self.__class__.__name__.rstrip('Daemon')))
        
        rpc_server = RPCServer((host, int(port)-1))
        rs = threading.Thread(target=rpc_server.serve_forever)
        rs.daemon = True
        rs.start()
        print('[%s]: RPCapi enabled.' % get_time())
        
        # Register routes and methods
        dispatcher = PathDispatcher()
        dispatcher.register('GET', '/', home_page)
        dispatcher.register('GET', '/test_page', test_page)
        dispatcher.register('GET', '/exec_command', exec_command)
        dispatcher.register('GET', '/exec_config', exec_config)
        dispatcher.register('GET', '/init_environ', init_environ)
        
        http_server = HttpServer(host, int(port)-2, zz_tasks)
        hs = threading.Thread(target=http_server.serve_forever)
        hs.daemon = True
        hs.start()
        print('[%s]: HTTPapi enabled.' % get_time())
        
        while True:
            time.sleep(0.1)
    
    def clean(self):
        with open('/var/log/zzlist', 'ab+') as f:
            f.truncate()


class ClientDaemon(Daemon):
    def __init__(self, pidfile='/tmp/zzclient.pid',
        stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        Daemon.__init__(self, pidfile,
            stdin=os.devnull, stdout=os.devnull, stderr=os.devnull)
        self.pidfile = pidfile
        self.stdin = stdin
        self.stdout = '/var/log/zzclient.log'
        self.stderr = '/var/log/zzclient.log'
    
    def run(self):
        import threading
        from zzagent.inits import create_client_ini
        from zzagent.models import Client
        
        os.chdir(os.path.expanduser('~'))
        config = ConfigParser.ConfigParser()
        config.read(create_client_ini())
        server_host = config.get('client', 'server_host')
        server_port = config.get('client', 'server_port')
        
        client = Client(server_host, int(server_port))
        c1 = threading.Thread(target=client.run)
        c1.daemon = True
        c1.start()
        print('[%s]: %s starts.' % (
            get_time(), self.__class__.__name__.rstrip('Daemon')))
        
        pid = os.getpid()
        while True:
            time.sleep(0.1)
            if c1.isAlive() == False:
                import signal
                print('[%s]: Client stopped.' % get_time())
                time.sleep(0.1)
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                os.kill(pid, signal.SIGTERM)
                #~ sys.exit(1)


class ManagerDaemon(Daemon):
    def __init__(self, pidfile='/tmp/zzmanager.pid',
        stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        Daemon.__init__(self, pidfile,
            stdin=os.devnull, stdout=os.devnull, stderr=os.devnull)
        self.stdin = stdin
        #~ self.stdout = '/var/log/zzmanager.log'
        #~ self.stderr = '/var/log/zzmanager.log'
    
    def list(self):
        from zzagent.models import PeersList
        print('List connections details:')
        print('-------------------------')
        for i in PeersList.peers:
            print i
    
    def execute(self, connections, command, args=None):
        pass
        #~ print('%r will execute the command %r with %r' % (
            #~ connections, command, args)
        #~ )
