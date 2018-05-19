#!/usr/bin/env python
from daemon import Daemon
import json
import pprint
import sys
import os.path
import time    
import logging

CONFSTORE = None

logger = None

processing = None

class tailer(Daemon):

    def getInode(self,filename):
        global logger

        if not os.path.exists(filename):
            return None
        else:
            return os.stat(filename)[1]

    def sigtermhandler(self, signum, frame):
        global logger

        tempPosInfo=dict()
        tempPosInfo['inode']=self.fileInode
        tempPosInfo['offset']=self.fh.tell()
        self.fh.seek(0,0)
        tempPosInfo['firstLine']=self.fh.readline()
        self.fh.close()
        logger.debug(pprint.pprint(tempPosInfo))
        with open(self.savePos, 'w') as outfile:
            json.dump(tempPosInfo, outfile)
        self.daemon_alive = False
        sys.exit()

    def run(self):
        global logger
        global processing
 
        logger.debug('Run function started')

        self.fileInode=None
        self.fh=None
        self.savePos=CONFSTORE['statestore']

        posInfo=None

        if os.path.isfile(self.savePos):
            posInfo=json.load(open(self.savePos))


        while True:
            if os.path.isfile(CONFSTORE['tailfile']):
                if self.fileInode!=self.getInode(CONFSTORE['tailfile']):
                    if self.fh!=None:
                        if not self.fh.closed:
                            self.fh.close()
                    self.fileInode=self.getInode(CONFSTORE['tailfile'])
                    self.fh=open(CONFSTORE['tailfile'])
                    if posInfo!=None:
                        if posInfo['inode']==self.fileInode:
                            if self.fh.readline() == posInfo['firstLine']:
                                self.fh.seek(posInfo['offset'],0)
                            posInfo=None
                fileLine=self.fh.readline()
                while fileLine:
                    logger.debug(fileLine)
                    processing.process(fileLine)
                    fileLine=self.fh.readline()
                    
                time.sleep(0.1)
            else:
                time.sleep(1)

def programControl(args,conf,loggerName,p):
    global CONFSTORE
    global logger
    global processing

    processing=p

    CONFSTORE = conf
   
    logger=logging.getLogger(loggerName)
    logger.debug(loggerName + " program control begun")
 
    daemon = tailer(CONFSTORE['pidfile'])
    
    if len(args) == 2:

        if 'start' == args[1]:
            try:
                daemon.start()
            except:
                logger.info('daemon failed to start')
                pass

        elif 'stop' == args[1]:
            print "Stopping ..."
            daemon.stop()

        elif 'restart' == args[1]:
            print "Restaring ..."
            daemon.restart()

        elif 'status' == args[1]:
            try:
                pf = file(CONFSTORE['pidfile'],'r')
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None
            except SystemExit:
                pid = None

            if pid:
                print '%s is running as pid %s' % (CONFSTORE['appname'], pid)
            else:
                print '%s is not running.' % CONFSTORE['appname']

        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart|status|stdin <normalisation schema>" % args[0]
        sys.exit(2)
