# -*- coding: utf-8 -*-

import argparse
import os
import sys
import time
import atexit
import signal
import logging


class Daemon(object):
    def __init__(self, pidfile,
        stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        self.pidfile = pidfile
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
    
    def daemonize(self):
        if self.fork() != 0:
            os.waitpid(0, 0)
            time.sleep(0.1)
            return
        
        if self.fork() != 0:
            sys.exit(0)
        
        self.detach_env
        
        sys.stdout.flush()
        sys.stderr.flush()
        
        self.attach_stream('stdin', mode='rb')
        self.attach_stream('stdout', mode='ab')
        self.attach_stream('stderr', mode='ab')
        
        self.create_pidfile()
        
        self.run()
        sys.exit(0)
    
    def attach_stream(self, name, mode):
        stream = open(getattr(self, name), mode)
        os.dup2(stream.fileno(), getattr(sys, name).fileno())
    
    def detach_env(self):
        os.chdir('/')
        os.umask(0)
        os.setsid()
    
    def fork(self):
        try:
            return os.fork()
        except OSError as e:
            sys.stderr.write('Fork failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)
    
    def create_pidfile(self):
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'wb+').write('%s\n' % pid)
    
    def delpid(self):
        os.remove(self.pidfile)
    
    def get_pid(self):
        try:
            pf = open(self.pidfile, 'rb')
            pid = int(pf.read().strip())
            pf.close()
        except (IOError, TypeError):
            pid = None
        return pid
    
    def start(self):
        pid = self.get_pid()
        if pid:
            message = 'Daemon already running with pidfile %s.\n'
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        self.daemonize()
    
    def stop(self, silent=False):
        pid = self.get_pid()
        if not pid:
            if not silent:
                message = 'Daemon not running without pidfile %s.\n'
                sys.stderr.write(message % self.pidfile)
            return
        
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                else:
                    sys.stdout.write(str(err))
                    sys.exit(1)
        finally:
            self.clean()
    
    def restart(self):
        self.stop(silent=True)
        self.start()
    
    def run(self):
        raise NotImplementedError
    
    def clean(self):
        pass
