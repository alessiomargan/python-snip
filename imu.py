#!/usr/bin/python

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort
from twisted.internet.task import LoopingCall

import struct
import operator
import StringIO
import pprint
import json
import time
import datetime

class dec_enc(struct.Struct):

    def __init__(self):
        
        self.__dict__.update(dict.fromkeys(self._fields_))
        fmt = self._byte_order_ + self._format_
        struct.Struct.__init__(self, fmt)
        self._buf = StringIO.StringIO()
        
    def encode(self):

        self._buf.seek(0)  #= StringIO.StringIO()
        buf.write(self.pack(*[getattr(self, k) for k in self._fields_]))  
        return buf.getvalue()

    def decode(self, data, offset=0):

        _data = data[offset:]
        buf = _data if hasattr(_data, 'read') else StringIO.StringIO(_data)
        for k,v in zip(self._fields_, self.unpack(buf.read(self.size))) :
            setattr(self, k, v)
        
    def toDict(self, all_fields=True):
        
        return dict((k,v)
                    for k,v in self.__dict__.iteritems()
                    if k in self._fields_ and (not k.startswith('_') or all_fields) )

    def __str__(self):
        
        return str(self.toDict())

# ##############################################################################
#
# ##############################################################################

class dec_enc_chk(dec_enc):

    def decode(self, data, offset=0):
        
        dec_enc.decode(self, data, offset=offset)
        try : assert(sum(map(ord,data[:-2])) == self._chk)
        except AttributeError : pass

class C2_pkt(dec_enc_chk):

    _fields_ = ('_cmd',
                'acc_x', 'acc_y', 'acc_z',
                'gyr_x', 'gyr_y', 'gyr_z',
                '_ts', '_chk')
    _format_ = 'BffffffIH'
    _byte_order_ = '>'
    _byte_cmd = 0xC2
    
    def __init__(self):
        dec_enc.__init__(self)

class CB_pkt(dec_enc_chk):

    _fields_ = ('_cmd',
                'acc_x', 'acc_y', 'acc_z',
                'gyr_x', 'gyr_y', 'gyr_z',
                'mag_x', 'mag_y', 'mag_z',
                '_ts', '_chk')
    _format_ = 'BfffffffffIH'
    _byte_order_ = '>'
    _byte_cmd = 0xCB
    
    def __init__(self):
        dec_enc.__init__(self)
    
class CE_pkt(dec_enc_chk):

    _fields_ = ('_cmd',
                'Roll', 'Pitch', 'Yaw',
                '_ts', '_chk')
    _format_ = 'BfffIH'
    _byte_order_ = '>'
    _byte_cmd = 0xCE
    
    def __init__(self):
        dec_enc.__init__(self)
    
class DF_pkt(dec_enc_chk):

    _fields_ = ('_cmd',
                'quat_0', 'quat_1', 'quat_2', 'quat_3',
                '_ts', '_chk')
    _format_ = 'BffffIH'
    _byte_order_ = '>'
    _byte_cmd = 0xDF
    
    def __init__(self):
        dec_enc.__init__(self)

# ##############################################################################
#
# ##############################################################################

def print_hex(data):
    
    print "<%d> %s" % (len(data), map(lambda x: hex(ord(x)), data))

def to_buff(byte_list):
    
    return ''.join(map(lambda x: chr(x), byte_list))
                       
                       
class IMU_Protocol(Protocol):
    
    __buffer = ''
    MAX_LENGTH = 16384

    def __init__(self, **kwargs) :
        
        self.packet_map = {
            # Acceleration, Angular Rate (0xC2) 
            chr(0xC2): C2_pkt,
            # Acceleration, Angular Rate & Magnetometer Vector (0xCB) 
            chr(0xCB): CB_pkt,
            # Euler Angles (0xCE)
            chr(0xCE): CE_pkt,
            # Quaternion (0xDF)
            chr(0xDF): DF_pkt,
        }            
        self.FSM = {
            # Communications Settings (0xD9)
            '0'      : [0xD9,0xC3,0x55]+[0x1]+[0x1]+[0x0,0xE,0x10,0x0]+[0x2,0x0],
            # Sampling Settings (0xDB) 20 bytes
            chr(0xD9): [0xDB,0xA8,0xB9]+[0x1]+[0x0,0x0]+[0x10,0x3]+[0x0]*12,
            chr(0xDB): [CB_pkt._byte_cmd],
            chr(0xCB): [CE_pkt._byte_cmd],
            chr(0xCE): [DF_pkt._byte_cmd],
            chr(0xDF): [CB_pkt._byte_cmd],
            
        }
        
    def connectionMade(self):
        ''' Called when a connection is made '''
        print 'connectionMade'
        
        self.sendData(to_buff(self.FSM['0']))
        self.t1 = datetime.datetime.now()
        self.cnt = 0
        self.avg_elap = datetime.timedelta(seconds=0)
        
    def dataReceived(self, data): 
        global zpub
        if data[0] not in self.packet_map.keys() :
            print_hex(data)
            time.sleep(1)
        else :
            self.cnt += 1
            elapsed = datetime.datetime.now() - self.t1 
            self.avg_elap += elapsed
            pkt = self.packet_map[data[0]]()
            pkt.decode(data)
            self.t1 = datetime.datetime.now()
            print elapsed
            print pkt.toDict(all_fields=False)
            # publish json data
            zpub.send_multipart(['uStrain',json.dumps(pkt.toDict(all_fields=False))])
        
        time.sleep(0.1)
        self.sendData(to_buff(self.FSM[data[0]]))
        
    def sendData(self, data):
        
        return self.transport.write(data) 
    
    
        
if __name__ == '__main__':

    import sys
    from twisted.python import log
    from twisted.internet import reactor
    import zmq
    
    log.startLogging(sys.stdout)
    
    protocol = IMU_Protocol()
    #SerialPort(protocol, '/dev/ttyACM0', reactor, baudrate=921600)
    SerialPort(protocol, '/dev/ttyS0', reactor, baudrate=115200)

    context = zmq.Context()
    zpub = context.socket(zmq.PUB)
    zpub.setsockopt(zmq.LINGER, 1)
    zpub.setsockopt(zmq.HWM, 10)
    zpub.bind("tcp://*:5550")
    print 'IMU publisher bind to port 5550' 
    
    reactor.run()
    print 'avg _elap', protocol.avg_elap / protocol.cnt
    print 'exit reactor'

    
