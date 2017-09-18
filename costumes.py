# -*- coding: utf-8 -*-

import time

from zzagent.utils import get_timestamp
from zzagent.models import HttpServer, plist


def zz_running():
    return '{"status": 2, "desc": "running"}'


def zz_worker(s):
    for i in plist.send_queue:
        if i.has_key('exec_config'):
            data = i['exec_config']
            ret = s.exec_config(data)
            plist.recv_queue.append({
                'data': data,
                'ret': ret
            })
            plist.send_queue.remove({'exec_config': i['exec_config']})
        elif i.has_key('init_environ'):
            data = i['init_environ']
            ret = s.init_environ(data)
            plist.recv_queue.append({
                'data': data,
                'ret': ret
            })
            plist.send_queue.remove({'init_environ': i['init_environ']})
        elif i.has_key('send_file'):
            data = i['send_file']
            ret = s.send_file(data)
            plist.recv_queue.append({
                'data': data,
                'ret': ret
            })
            plist.send_queue.remove({'send_file': i['send_file']})
        time.sleep(0.1)
        print '----send_queue:', plist.send_queue
        print '----recv_queue:', plist.recv_queue


def zz_tasks(environ, start_response):
    import os, json, threading, ConfigParser
    from urllib import unquote
    from urlparse import parse_qs
    from xmlrpclib import ServerProxy, Fault, ProtocolError
    config = ConfigParser.ConfigParser()
    config.read(os.path.join(os.path.expanduser('~'), '.zzserver.ini'))
    host = config.get('server', 'host')
    s = ServerProxy('http://%s:9998/rpc' % host)
    
    t = threading.Thread(target=zz_worker, args=(s,))
    t.daemon = True
    t.start()
    
    path = environ['PATH_INFO']
    method = environ['REQUEST_METHOD']
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(status, headers)
    
    if method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
        request_body = environ['wsgi.input'].read(request_body_size)
        d = json.loads(request_body)
        
        if d.has_key('exec_config'):
            t = threading.Thread(target=zz_running)
            t.daemon = True
            t.start()
            t.join()
            plist.send_queue.append(
                {'exec_config': d['exec_config']}
            )
        elif d.has_key('init_environ'):
            t = threading.Thread(target=zz_running)
            t.daemon = True
            t.start()
            t.join()
            plist.send_queue.append(
                {'init_environ': d['init_environ']}
            )
        elif d.has_key('send_file'):
            t = threading.Thread(target=zz_running)
            t.daemon = True
            t.start()
            t.join()
            plist.send_queue.append(
                {'send_file': d['send_file']}
            )
        time.sleep(0.1)
        print 'post----send_queue:', plist.send_queue
        print 'post----recv_queue:', plist.recv_queue
        return '{"status": 0, "desc": "successful"}'
        #~ return '{"status": 2, "desc": "running"}'
    else:
        request_body = environ['QUERY_STRING']
        d = json.loads(unquote(request_body))
        
        if d.has_key('exec_config'):
            for i in plist.recv_queue:
                if i['data'] == d['exec_config']:
                    results = i['ret']
                    plist.recv_queue.remove(i)
        elif d.has_key('init_environ'):
            for i in plist.recv_queue:
                if i['data'] == d['init_environ']:
                    results = i['ret']
                    plist.recv_queue.remove(i)
        elif d.has_key('send_file'):
            for i in plist.recv_queue:
                if i['data'] == d['send_file']:
                    results = i['ret']
                    plist.recv_queue.remove(i)
        else:
            results = {"status": 2, "desc": "running"}
        print 'get----send_queue:', plist.send_queue
        print 'get----recv_queue:', plist.recv_queue
        try:
            return json.dumps(results)
        except:
            return '{"status": 2, "desc": "running"}'


def home_page(environ, start_response):
    response_body = [
        '%s: %s' % (key, value) for key, value in sorted(environ.items())
    ]
    response_body = '\n'.join(response_body)
    
    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(response_body)))
    ]
    start_response(status, response_headers)
    return [response_body]


def test_page(environ, start_response):
    path = environ['PATH_INFO']
    method = environ['REQUEST_METHOD']
    if method == 'POST':
        request_body_size = int(environ.get('CONTENT_LENGTH', '0'))
        request_body = environ['wsgi.input'].read(request_body_size)
        try:
            response_body = str(request_body)
        except:
            response_body = "error"
        status = '200 OK'
        headers = [('Content-type', 'text/html')]
        start_response(status, headers)
        return [response_body]
    else:
        request_body_size = int(environ['CONTENT_LENGTH'])
        #~ request_body = environ['wsgi.input'].read(request_body_size)
        status = '200 OK'
        headers = [('Content-type', 'text/html'),
                    ('Content-Length', str(len(response_body)))]
        start_response(status, headers)
        return [response_body]


def exec_command(environ, start_response):
    path = environ['PATH_INFO']
    method = environ['REQUEST_METHOD']
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    if method == 'POST':
        start_response(status, headers)
        return ['post %s' % data]
    else:
        start_response(status, headers)
        return ['get %s' % data]


def exec_config(environ, start_response):
    path = environ['PATH_INFO']
    method = environ['REQUEST_METHOD']
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    if method == 'POST':
        start_response(status, headers)
        return ['post %s' % data]
    else:
        start_response(status, headers)
        return ['get %s' % data]


def init_environ(environ, start_response):
    path = environ['PATH_INFO']
    method = environ['REQUEST_METHOD']
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    if method == 'POST':
        start_response(status, headers)
        return ['post %s' % data]
    else:
        start_response(status, headers)
        return ['get %s' % data]
