Net2Host
========

You will need redis on your linux correlation host and bro

Alternatively see the docker-elk repo which will build a test system using compose

Conf directory Files:
=====================

net2Host.conf:
 Net2Host Configuration
 File Paths for Log files ETC

nxlog-linux-config:
 Configuration for recieving NX log information from windows.   Should be possible to use syslog instead if you wish.

nxlog-window-config:
 NX log configuration for Windows.   This takes windows events and forwards them to windows.


Processes
==========
 bro-ssl-read.py: This read data from bro SSL logs and populates redis database
                 - ./bro-ssl-read.py start

 host-read.py:  This reads data from file created by NXlog on linux machine and populates Redis data
                 - ./host-read.py start

 correlate.py:   This checks redis database and correlates logs. Still a more work to do here.

 process-stdin.py:  Use this utility to run daemon process and except input on standard input.  
                    - e.g.: ./process-stdin bro-ssl-read
