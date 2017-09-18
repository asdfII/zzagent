# -*- coding: utf-8 -*-

import os
import sys
import time
import socket
import threading
import multiprocessing
import Queue
import subprocess
import json
import pickle
import platform
import ConfigParser
import ssl
import cgi
import traceback
from random import random
from urlparse import parse_qs
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from wsgiref.simple_server import make_server, WSGIRequestHandler

from zzagent.inits import create_server_ini, create_client_ini
from zzagent.utils import (is_windows, get_time, get_timestamp,
    serial_encrypt, serial_decrypt, STATUS_LIST)
        
server_config = ConfigParser.ConfigParser()
server_config.read(create_server_ini())
client_config = ConfigParser.ConfigParser()
client_config.read(create_client_ini())
SERVERPATH = server_config.get('server', 'serverpath')
CLIENTPATH = client_config.get('client', 'clientpath')

RECV_SAFEMODE = 0
RECV_BUFSIZE = 4096

proc_shell = is_windows()


class PeersList(object):
    try:
        with open('/var/log/zzlist', 'rb+') as f:
            peers = eval(f.readline().strip('\n'))
    except:
        peers = []
    conns_dict = {}
    results_list = []
    send_queue = []
    recv_queue = []
    temp_queue = []


plist = PeersList()


class Server(object):
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.bind((host, int(port)))
        self.sock.listen(5)
        self.connections = []
    
    def handler(self, c, a):
        while True:
            try:
                print('[%s]: Server is getting data from %s:%s.' % (
                    get_time(), a[0], a[1]))
                try:
                    data = c.recv(RECV_BUFSIZE)
                except:
                    if plist.results_list.has_key(a[0]):
                        plist.results_list[a[0]].append({
                            'info': 'Failed on receiving deserialized data.',
                            'return': 1
                        })
                    else:
                        plist.results_list.append({a[0]: [{
                            'info': 'Failed on receiving deserialized data.',
                            'return': 1
                        }]})
                
                if not data:
                    self.connections.remove(c)
                    plist.conns_dict.pop(a[0])
                    plist.peers.remove(a[0])
                    c.close()
                    with open('/var/log/zzlist', 'ab+') as f:
                        f.truncate()
                        f.write(str(plist.peers)+'\n')
                    print('[%s]: %s:%s disconnected.' % (
                        get_time(), a[0], a[1]))
                    break
                
                print('[%s]: Server received serialized data from %s:%s.' % (
                    get_time(), a[0], a[1]))
                
                try:
                    real_data = serial_decrypt(data)
                    print('[%s]: Server deserialized data %r from %s:%s.' % (
                        get_time(), real_data, a[0], a[1]))
                    plist.results_list.append(real_data)
                except:
                    # Handling if failed to deserialize data
                    print('[%s]: Server failed to deserialize data from %s:%s.' \
                        % (get_time(), a[0], a[1]))
                    plist.results_list.append(data)
                
                # Deduplicate data
                [i for n, i in enumerate(plist.results_list) 
                    if i not in plist.results_list[n+1:]]
            except Exception as e:
                self.connections.remove(c)
                plist.conns_dict.pop(a[0])
                plist.peers.remove(a[0])
                c.close()
                with open('/var/log/zzlist', 'ab+') as f:
                    f.truncate()
                    f.write(str(plist.peers)+'\n')
                print('[%s]: %s:%s disconnected abnormally with %s.' % (
                    get_time(), a[0], a[1], str(e)))
                break
            time.sleep(0.1)
    
    def _update_zzlist(self):
        # Update /var/log/zzlist continuously
        with open('/var/log/zzlist', 'ab+') as f:
            f.truncate()
            f.write(str(plist.peers)+'\n')
        time.sleep(0.1)
    
    def run(self):
        while True:
            c, a = self.sock.accept()
            self.connections.append(c)
            plist.conns_dict[a[0]] = c
            plist.peers.append(a[0])
            print('[%s]: %s:%s connected.' % (get_time(), a[0], a[1]))
            
            c_handler = threading.Thread(target=self.handler, args=(c, a))
            c_handler.daemon = True
            c_handler.start()
            
            u_handler = threading.Thread(target=self._update_zzlist)
            u_handler.daemon = True
            u_handler.start()


class Client(object):
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
    
    def handler(self):
        return
    
    def run(self, counter=0):
        # TODO: Client should be only receive tasks, need to use mq.
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_host, int(self.server_port)))
            self.addr = self.sock.getsockname()
            client_connected = True
            counter = 0
        except:
            client_connected = False
            time.sleep(3+random())
            counter += 1
            #~ if counter < 100:
            if counter < 10:
                if counter % 2 == 0:
                    print('[%s]: Client is reconnecting(%d).' % (
                        get_time(), counter))
                self.run(counter)
            else:
                print('[%s]: Client will stop with some retries.' % get_time())
                sys.exit(1)
        
        while client_connected:
            # TODO: multiple processes maybe broken. Need handler to handle.
            r_handler = threading.Thread(target=self.handler)
            r_handler.daemon = True
            r_handler.start()
            
            print('[%s]: Client is getting data.' % get_time())
            data = self.sock.recv(RECV_BUFSIZE)
            time.sleep(0.1)
            #~ print('[%s]: Client got data %r.' % (get_time(), data))
            
            if not data:
                #~ break
                print('[%s]: Client is restarting with no data.' % get_time())
                self.run(counter)
            else:
                try:
                    task_job = serial_decrypt(data)
                    print('[%s]: Client deserialized data.' % get_time())
                    time.sleep(0.5)
                except:
                    plist.results_list.append({self.addr[0]: {
                        'return': 1,
                        'info': 'Failed to deserialize data.'
                    }})
                    task_job = ''
                finally:
                    time.sleep(0.1)
            
            if not task_job:
                #~ break
                print('[%s]: Client is restarting with no task job.' \
                    % get_time())
                self.run(counter)
            else:
                if task_job.has_key('task') and not task_job.has_key('script'):
                    if task_job['task'] == 'send_file':
                        results = {self.addr[0]: []}
                        for i in task_job['task_args']:
                            try:
                                for fn, fc in i.iteritems():
                                    with open(os.path.join(
                                        CLIENTPATH, fn), 'wb+') as f:
                                        f.write(fc)
                                time.sleep(1)
                                results[self.addr[0]].append({
                                    'return': 0,
                                    'info': 'Received %s from server.' % fn
                                })
                            except:
                                time.sleep(0.1)
                                results[self.addr[0]].append({
                                    'return': 1,
                                    'info': 'Failed to create/write %s.' % fn
                                })
                        #~ task_job['task_args'] = ''
                        task_command = False
                        cmdb_init = False
                    else:
                        if task_job['task_args']:
                            task_command = task_job['task'] \
                                + task_job['task_args']
                        else:
                            task_command = task_job['task']
                    cmdb_init = False
                elif not task_job.has_key('task') and task_job.has_key('script'):
                    if os.path.splitext(task_job['script'])[-1] == '.py':
                        run_script = 'python' + ' ' + os.path.join(
                            CLIENTPATH, task_job['script'])
                    elif os.path.splitext(task_job['script'])[-1] == '.sh':
                        run_script = 'sh' + ' ' + os.path.join(
                            CLIENTPATH, task_job['script'])
                    else:
                        run_script = task_job['script']
                    
                    if task_job['argv']:
                        task_command = run_script.strip('\r\n').split() \
                            + task_job['argv'].strip('\r\n').split()
                    else:
                        task_command = run_script.strip('\r\n').split()
                    cmdb_init = True
                elif task_job.has_key('commands'):
                    task_command = ('bash /data/config/gitpull.sh %s %s' % (
                        task_job['project'],
                        task_job['commit']
                    )).strip('\r\n').split()
                    cmdb_init = False
                else:
                    cmdb_init = False
                    break
                
                if task_command and not cmdb_init:
                    try:
                        proc = subprocess.Popen(task_command,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=proc_shell)
                        (res, err) = proc.communicate()
                    except Exception as e:
                        res = ''
                        err = str(e)
                    res = res.strip('\r\n')
                    err = err.strip('\r\n')
                    try:
                        res_json = json.loads(res)
                        res_is_json = True
                    except:
                        res_is_json = False
                    try:
                        err_json = json.loads(err)
                        err_is_json = True
                    except:
                        err_is_json = False
                    time.sleep(0.1)
                    
                    if res and not err:
                        results = {self.addr[0]: {
                            'return': 0,
                            'info': res
                        }}
                        if res_is_json:
                            results[self.addr[0]]['return'] = res_json['status']
                    elif not res and err:
                        results = {self.addr[0]: {
                            'return': 1,
                            'info': err
                        }}
                        if err_is_json:
                            results[self.addr[0]]['return'] = err_json['status']
                    
                    if len(serial_encrypt(results)) > RECV_BUFSIZE:
                        if RECV_SAFEMODE == 1:
                            results = {self.addr[0]: {
                                'return': 1,
                                'info': 'Safemode protectd from long length returned.'
                            }}
                        else:
                            results = {self.addr[0]: {
                                'return': 3,
                                'info': 'Results have too many characters.'
                            }}
                elif task_command and cmdb_init:
                    try:
                        proc = subprocess.Popen(task_command,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=proc_shell)
                        (res, err) = proc.communicate()
                    except Exception as e:
                        res = ''
                        err = str(e)
                    res = res.strip('\r\n')
                    err = err.strip('\r\n')
                    
                    try:
                        res_json = json.loads(res)
                        res_is_json = True
                    except:
                        res_is_json = False
                    try:
                        err_json = json.loads(err)
                        err_is_json = True
                    except:
                        err_is_json = False
                    time.sleep(0.1)
                    
                    if res and not err:
                        results = {self.addr[0]: {
                            'return': 0,
                            'info': res,
                            'script': task_job['script'],
                            'argv': task_job['argv']
                        }}
                        if res_is_json:
                            results[self.addr[0]]['return'] = res_json['status']
                    elif not res and err:
                        results = {self.addr[0]: {
                            'return': 1,
                            'info': err,
                            'script': task_job['script'],
                            'argv': task_job['argv']
                        }}
                        if err_is_json:
                            results[self.addr[0]]['return'] = err_json['status']
                    
                    if len(serial_encrypt(results)) > RECV_BUFSIZE:
                        if RECV_SAFEMODE == 1:
                            results = {self.addr[0]: {
                                'return': 1,
                                'info': 'Safemode protectd from long length returned.',
                                'script': task_job['script'],
                                'argv': task_job['argv']
                            }}
                        else:
                            results = {self.addr[0]: {
                                'return': 3,
                                'info': 'Results have too many characters.',
                                'script': task_job['script'],
                                'argv': task_job['argv']
                            }}
            
            try:
                print('[%s]: Get data %r.' % (get_time(), results))
                self.sock.sendall(serial_encrypt(results))
                time.sleep(0.1)
            except:
                print('[%s]: Connection lost.' % get_time())
                if task_command and not cmdb_init:
                    plist.results_list.append({self.addr[0]: {
                        'return': 1,
                        'info': 'Connection lost.'
                    }})
                elif task_command and cmdb_init:
                    plist.results_list.append({self.addr[0]: {
                        'return': 1,
                        'info': 'Connection lost.',
                        'script': task_job['script'],
                        'argv': task_job['argv']
                    }})
                time.sleep(random())
                print('[%s]: Client is restarting with some error occurred.' \
                    % get_time())
                self.run(counter)


class RPCRequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/rpc', '/RPC2')
    
    def log_message(self, format, *args):
        sys.stderr.write("[%s]: %s - - %s\n" % (
            get_time(), self.address_string(), format%args))


class RPCServer(object):
    _rpc_methods_ = [
        'get_funclist', 'func_register', 'func_unregister',
        'get', 'set', 'delete', 'exists', 'keys',
        'get_hostname', 'get_peers', 'send_file',
        'exec_command', 'exec_config', 'init_environ'
    ]
    
    def __init__(self, address):
        self._data = {}
        self._serv = SimpleXMLRPCServer(address,
            requestHandler=RPCRequestHandler, allow_none=True)
        for name in self._rpc_methods_:
            self._serv.register_function(getattr(self, name))
        self._func = {}
    
    def get_funclist(self):
        return self._rpc_methods_
    
    def func_register(self, func_name, func_body):
        self._func[func_name] = func_body
        self._rpc_methods_.append(func_name)
    
    def func_unregister(self, func_name):
        self._rpc_methods_.remove(func_name)
    
    def get(self, name):
        return self._data[name]
    
    def set(self, name, value):
        self._data[name] = value
    
    def delete(self, name):
        del self._data[name]
    
    def exists(self, name):
        return name in self._data
    
    def keys(self):
        return list(self._data)
    
    def get_hostname(self):
        return socket.gethostname(), time.ctime()
    
    def get_peers(self):
        return plist.peers
    
    def _get_results_list(self, hosts):
        while len(plist.results_list) != len(hosts):
            time.sleep(0.1)
    
    def send_file(self, data):
        hosts = data[0]
        files = data[1]
        tid = get_timestamp()
        serverfiles = os.listdir(SERVERPATH)
        task_job = {
            'tid': tid,
            'task': 'send_file',
            'task_args': [],
            'results_list': []
        }
        
        for file in files:
            if file in serverfiles:
                filepath = os.path.join(SERVERPATH, file)
                with open(filepath, 'rb') as f:
                    content = f.read()
                time.sleep(0.5)
                task_job['task_args'].append({file: content})
            else:
                print('[%s]: No such file(%s).' % (get_time(), file))
        
        for host in hosts:
            if host in plist.conns_dict.keys():
                plist.conns_dict[host].sendall(serial_encrypt(task_job))
            else:
                plist.results_list.append({host: 'No such connection.'})
        
        t = threading.Thread(target=self._get_results_list, args=(hosts,))
        t.daemon = True
        t.start()
        t.join()
        task_job['results_list'] = plist.results_list
        print('[%s]: Got results: %r.' % (get_time(), plist.results_list))
        plist.results_list = []
        return(task_job)
    
    def exec_command(self, hosts, task, task_args=''):
        # TODO: Maybe need a lock
        tid = get_timestamp()
        task_job = {
            'tid': tid,
            'task': task.strip('\r\n').split(),
            'task_args': task_args.strip('\r\n').split(),
            'results_list': [],
            'results': {
                'success_list': [],
                'failure_list': []
            },
            'retcode': 2
        }
        
        for host in hosts:
            if host in plist.conns_dict.keys():
                plist.conns_dict[host].sendall(serial_encrypt(task_job))
                time.sleep(0.1)
            else:
                plist.results_list.append({host: {
                    'return': 1,
                    'info': 'No such connection.'
                }})
        
        t = threading.Thread(target=self._get_results_list, args=(hosts,))
        t.daemon = True
        t.start()
        t.join()
        task_job['results_list'] = plist.results_list
        plist.results_list = []
        task_job = json.loads(json.dumps(task_job))
        
        retlist = []
        for i in task_job['results_list']:
            for k, v in i.iteritems():
                if i[k]['return'] == 0:
                    task_job['results']['success_list'].append(k)
                else:
                    task_job['results']['failure_list'].append(k)
                retlist.append(i[k]['return'])
        
        retset = set(retlist)
        if 1 in retset:
            task_job['retcode'] = 1
        elif 3 in retset:
            task_job['retcode'] = 1
        else:
            task_job['retcode'] = 0
        return(task_job)
    
    def exec_config(self, data):
        '''
        data = {
            'project': u'acl_qa',
            'commands': u'nodesend',
            'sid': u'201708281218-test_post',
            'ip': [u'192.168.171.2'],
            'commit': u'4c724c36140b18b0eb3fbc9d72994040492a556f',
            'id': u'43'
        }
        '''
        task_job = data.copy()
        task_job.pop('ip')
        task_job['results_list'] = []
        task_job['results'] = {
            'success_list': [],
            'failure_list': []
        }
        task_job['status'] = 2
        task_job['desc'] = STATUS_LIST[str(task_job['status'])]
        
        for host in data['ip']:
            if host in plist.conns_dict.keys():
                plist.conns_dict[host].sendall(serial_encrypt(task_job))
                time.sleep(0.1)
            else:
                plist.results_list.append({host: {
                    'return': 1,
                    'info': 'No such connection.'
                }})
        
        t = threading.Thread(target=self._get_results_list, args=(data['ip'],))
        t.daemon = True
        t.start()
        t.join()
        task_job['results_list'] = plist.results_list
        plist.results_list = []
        task_job = json.loads(json.dumps(task_job))
        
        retlist = []
        for i in task_job['results_list']:
            for k, v in i.iteritems():
                if i[k]['return'] == 0:
                    task_job['results']['success_list'].append(k)
                else:
                    task_job['results']['failure_list'].append(k)
                retlist.append(i[k]['return'])
        
        for i in ['project', 'commands', 'sid', 'commit', 'id',
            'results_list', 'results']:
            task_job.pop(i)
        
        retset = set(retlist)
        if 1 in retset:
            task_job['status'] = 1
        elif 3 in retset:
            task_job['status'] = 1
        else:
            task_job['status'] = 0
        task_job['desc'] = STATUS_LIST[str(task_job['status'])]
        return(task_job)
    
    def init_environ(self, data):
        task_job = {
            'sid': data[0],
            'status': 2,
            'results_list': [],
            'results': {
                'success_list': [],
                'failure_list': []
            },
        }
        task_job['desc'] = STATUS_LIST[str(task_job['status'])]
        
        task_list = []
        for i in xrange(1, len(data)):
            if data[i]['commands'] == 'init':
                task_list.extend(data[i]['exec'])
        task_list = sorted(task_list,
            key=lambda k: (k['priority'], k['ip']),
            reverse=True)
        print('[%s]: Generated %d task(s): %r.' % (
            get_time(), len(task_list), task_list))
        
        for i in task_list:
            if i['ip'] in plist.conns_dict.keys():
                print('[%s]: Server is sending task: %r.' % (get_time(), i))
                plist.conns_dict[i['ip']].sendall(serial_encrypt(i))
                time.sleep(0.1)
            else:
                print('No such connection.')
                plist.results_list.append({i['ip']: {
                    'return': 1,
                    'info': 'No such connection.',
                    'script': i['script'],
                    'argv': i['argv']
                }})
        
        t = threading.Thread(target=self._get_results_list, args=(task_list,))
        t.daemon = True
        t.start()
        t.join()
        task_job['results_list'] = plist.results_list
        plist.results_list = []
        task_job = json.loads(json.dumps(task_job))
        
        script_list = []
        success_list = []
        fail_list = []
        task_job['results'] = {}
        print('[%s]: Fixing data of task job if omitted.' % get_time())
        for i in task_job['results_list']:
            for k, v in i.iteritems():
                if not v.has_key('script'):
                    v['script'] = 'unknown'
                    v['argv'] = 'unknown'
                    i[k] = v
                if v['script'] not in script_list:
                    script_list.append(v['script'])
        print('[%s]: Fixed data of task job if omitted.' % get_time())
        
        for i in script_list:
            task_job['results'][i] = {'success_list': [], 'fail_list': []}
        
        retlist = []
        for i in task_job['results_list']:
            for k, v in i.iteritems():
                if v['return'] == 0:
                    task_job['results'][v['script']]['success_list'].append(k)
                else:
                    task_job['results'][v['script']]['fail_list'].append(k)
                retlist.append(i[k]['return'])
        
        retset = set(retlist)
        if 1 in retset:
            task_job['status'] = 1
        elif 3 in retset:
            task_job['status'] = 1
        else:
            task_job['status'] = 0
        task_job['desc'] = STATUS_LIST[str(task_job['status'])]
        task_job.pop('results_list')
        return(task_job)
    
    def serve_forever(self):
        self._serv.serve_forever()


class PathDispatcher(object):
    def __init__(self):
        self.pathmap = {}
    
    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        params = cgi.FieldStorage(environ['wsgi.input'], environ=environ)
        method = environ['REQUEST_METHOD']
        environ['params'] = {key: params.getvalue(key) for key in params}
        handler = self.pathmap.get((method, path), self.notfound_404)
        return handler(environ, start_response)
    
    def register(self, method, path, function):
        self.pathmap[method, path] = function
        return function
    
    def notfound_404(self, environ, start_response):
        status = '404 Not Found'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [b'Not Found']


class HTTPRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write("[%s]: %s - - %s\n" % (
            get_time(), self.address_string(), format%args))


class HttpServer(object):
    def __init__(self, host, port, app):
        self._serv = make_server(
            host, port, app,
            handler_class=HTTPRequestHandler)
    
    def serve_forever(self):
        self._serv.serve_forever()
