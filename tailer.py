from daemon import Daemon
import json
import pprint
import sys
import traceback
import os.path
import time    
import logging
import pickle
import signal

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
        logger.debug(tempPosInfo)
        pickle.dump(tempPosInfo, open( self.savePos, "wb" ))
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
            posInfo=pickle.load(open(self.savePos, "rb"))


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

    if 'start' == args[2]:
        try:
            daemon.start()
        except SystemExit:
            pass
        except:
            logger.error(sys.exc_info())
            logger.error(traceback.format_exc())
            pass

    elif 'nodaemon' == args[2]:
        print('Starting without daemon')
        signal.signal(signal.SIGTERM, daemon.sigtermhandler)
        signal.signal(signal.SIGINT, daemon.sigtermhandler)
        daemon.run()

    elif 'stop' == args[2]:
        print("Stopping ...")
        daemon.stop()

    elif 'restart' == args[2]:
        print("Restaring ...")
        daemon.restart()

    elif 'status' == args[2]:
        try:
            pf = file(CONFSTORE['pidfile'],'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None

        if pid:
            print('%s is running as pid %s' % (CONFSTORE['appname'], pid))
        else:
            print('%s is not running.' % CONFSTORE['appname'])

    else:
        print("Unknown command")
        sys.exit(2)

    sys.exit(0)

