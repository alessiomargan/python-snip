#! /usr/bin/python
# -*- coding: utf-8 -*-

#!/usr/bin/env python

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort
from collections import defaultdict

vdata = defaultdict(list)

ESCAPE      = '\xF0'
MASK        = '\xAA'

PKT_BEGIN   = '\x24' # $
PKT_END     = '\x23' # #
CR          = '\x0D' # '\r'
LF          = '\x0A' # '\n'

def unescape_data(data, chk=False):

    _data = ''
    _unescape_next_byte = False
    _unmask_next_byte =  False
    
    for c in data :
        if _unescape_next_byte:
            _unescape_next_byte = False
            if c == MASK :
                _unmask_next_byte = True
                continue

        elif _unmask_next_byte :
            _unmask_next_byte = False
            c = chr(ord(c) ^ ord(MASK))

        elif c == ESCAPE:
            _unescape_next_byte = True
            continue

        _data += c
    if chk :
        _data = data[:-1]
    
    return _data

class ABC_Protocol(Protocol):
    
    __buffer = ''
    MAX_LENGTH = 16384

    def __init__(self, **kwargs) :
        pass
    
    def dataReceived(self, data): 
        
        self.__buffer = self.__buffer + unescape_data(data)
        try : 
            raw_packet, self.__buffer = self.__buffer.split('\r\n', 1)
        except ValueError :
            return
        print raw_packet
        try :
            id,val = raw_packet.strip().split(':')
            vdata[id].append(val.split())
        except Exception, e:
            print e
            
    def sendData(self, data):
        
        return self.transport.write(data) 
    
    
        
if __name__ == '__main__':

    import sys
    from optparse import OptionParser
    from twisted.python import log
    from twisted.internet import reactor
    import csv
    
    parser = OptionParser()
    parser.add_option("-d", "--device", action="store", type="string", dest="serial_port", default='/dev/ttyUSB0')
    parser.add_option("-s", "--speed", action="store", type="int", dest="speed", default=57600)
    (options, args) = parser.parse_args()
    
    serial_port = options.serial_port
    speed = options.speed
        
    #log.startLogging(sys.stdout)
    SerialPort(ABC_Protocol(), serial_port, reactor, timeout = 1.0, baudrate=speed)
    reactor.run()
    print 'exit reactor'

    for k,v in vdata.items() :
        w = csv.writer(open(k+'.csv', 'w'),delimiter=' ')
        w.writerows(v)
    

