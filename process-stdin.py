#!/usr/bin/env python
import sys
import importlib
import os
import configparser
import logging
from helperFunctions import *

if len(sys.argv)!=2:
   print("2 args requiredi: " + sys.argv[1] + " <process name>")

appname = sys.argv[1] 
i=importlib.import_module(appname)

configuration=readConfigToDict(appname)

loggerName=configuration['appname'] + " logger"

setupLogger(loggerName,configuration)

processing=i.dataProcess(configuration,loggerName)

for l in sys.stdin:
    processing.process(l)
