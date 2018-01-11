#!/usr/bin/python

import threading
import time, datetime
import pprint
import zmq
import json
from collections import defaultdict
from optparse import OptionParser

import numpy as np

#import sys
#sys.path.append('/home/amargan/work/code/COMAN_shared/utils/python')
#import board_data_type
#import policy_maps

import sys
sys.path.append('/home/amargan/work/code/ecat_dev/ecat_master_advr/build/protobuf')
import ecat_pdo_pb2
from protobuf_to_dict import protobuf_to_dict

JSON_PUB_PORT = 6666 
TEXT_PUB_PORT = 6667 
CSTRUCT_PUB_PORT = 6668 

def zmq_pub_gen(hostname, port_range):
    def gen() :
        for e in port_range :
            yield 'tcp://%s:%d,'%(hostname,e)    
    return "".join(gen())[:-1]



#DEFAULT_ZMQ_PUB = 'tcp://carm-deb.local:6666'
#DEFAULT_ZMQ_PUB = 'tcp://ccub-deb-test.local:6666'
#DEFAULT_ZMQ_PUB = 'tcp://localhost:%d'%CSTRUCT_PUB_PORT
#DEFAULT_ZMQ_PUB = 'tcp://wheezy-i386-test.local:%d'%CSTRUCT_PUB_PORT
#DEFAULT_ZMQ_PUB = 'tcp://localhost:5555'
#DEFAULT_ZMQ_PUB = 'ipc:///tmp/6969'
#DEFAULT_ZMQ_PUB = 'tcp://coman-linux.local:%d'%CSTRUCT_PUB_PORT
#DEFAULT_ZMQ_PUB = 'tcp://amargan-desktop.local:9601'
#DEFAULT_ZMQ_PUB = 'tcp://coman-disney.local:9001,tcp://coman-disney.local:9002,tcp://coman-disney.local:9003'
#DEFAULT_ZMQ_PUB = zmq_pub_gen('coman-disney.local', [9008])
#DEFAULT_ZMQ_PUB = zmq_pub_gen('coman-disney.local', range(9001,9038))
#DEFAULT_ZMQ_PUB = zmq_pub_gen('coman-disney.local', [9034,9035,9036,9037])
#DEFAULT_ZMQ_PUB = zmq_pub_gen('coman-disney.local', [9037])
#DEFAULT_ZMQ_PUB = zmq_pub_gen('localhost', [9547,9548])
#DEFAULT_ZMQ_PUB = zmq_pub_gen('localhost', range(9801,9804))
#DEFAULT_ZMQ_PUB = zmq_pub_gen('com-exp.local', range(9500,9600))
#DEFAULT_ZMQ_PUB = zmq_pub_gen('com-exp.local', [9501,10103,10104])
DEFAULT_ZMQ_PUB = zmq_pub_gen('com-exp.local', range(9671,9674))

POLLER_TIMEOUT = 1000


def default_cb(id, data, signals):
    
    if len(signals) :
        raise BaseException("signals filter NOT supported")
    pprint.pprint(id,data)

def json_cb(id, data, signals):
    
    json_dict =	json.loads(data)
    if len(signals) :
        try : json_dict = { key : json_dict[key] for key in signals if json_dict.has_key(key) }
        except KeyError : json_dict = {}
    pprint.pprint((id, json_dict))
    return id,json_dict

def protobuf_cb(id, data, signals):
    
    def filter_dict(key, dict_to_filter):
        if len(signals) :
            filter_dict = dict_to_filter[key]
            try : filter_dict = { key : filter_dict[key] for key in signals if filter_dict.has_key(key) }
            except KeyError : filter_dict = {}
            return filter_dict
        else :
            return pb_dict[key]
        
        
    rx_pdo = ecat_pdo_pb2.Ec_slave_pdo()
    rx_pdo.ParseFromString(data)
    pb_dict = protobuf_to_dict(rx_pdo)
    #print pb_dict
    
    if rx_pdo.type == rx_pdo.RX_XT_MOTOR :
        # motor pdo56 byte
        pb_dict = filter_dict('motor_xt_rx_pdo',pb_dict)

    elif rx_pdo.type == rx_pdo.RX_MOTOR :
        pb_dict = filter_dict('motor_rx_pdo',pb_dict)

    elif rx_pdo.type == rx_pdo.RX_FT6 :
        pb_dict = filter_dict('ft6_rx_pdo',pb_dict)
        
    elif rx_pdo.type == rx_pdo.RX_FOOT_SENS :
        pb_dict = filter_dict('footWalkman_rx_pdo',pb_dict)

    elif rx_pdo.type == rx_pdo.RX_SKIN_SENS :
        pb_dict = filter_dict('skin_rx_pdo',pb_dict)
        
        a = np.array(pb_dict['forceXY'])
        #a = np.array([1 if z > 5 else 0 for z in pb_dict['forceXY']] )
        b = np.reshape(a,(8,3))
        c = b.transpose()
        print c
        
    elif rx_pdo.type == rx_pdo.RX_MC_HAND :
        pb_dict = filter_dict('mcHand_rx_pdo',pb_dict)

    #pprint.pprint((id, pb_dict))
    return id, pb_dict

def cstruct_cb(id,data,signals):
    pass

'''    
def cstruct_cb(id,data):

    policy = 'Position|Velocity|Torque|PID_out|PID_err|Link_pos|Target_pos|TempTarget_pos'
    bcast_data = board_data_type.data_factory(policy, policy_maps.mc_policy_map) # bigLeg_policy_map)
    bcast_data.decode(data) 
    # do some scaling
    bcast_data.Position /= 1e2
    bcast_data.Target_pos /= 1e2
    bcast_data.TempTarget_pos /= 1e2
    
    data_dict = bcast_data.toDict(all_fields=False)
    #pprint.pprint((id, data_dict))
    return id, data_dict
'''

cb_map = {'default_cb': default_cb,
          'json_cb':    json_cb,
          'cstruct_cb': cstruct_cb,
          'protobuf_cb': protobuf_cb,
          }


class ZMQ_sub(threading.Thread) :
    ''' read data from a zmq publisher '''
    
    def __init__(self, **kwargs):

        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.msg_id_ts = defaultdict(list)
        
        self.zmq_context = kwargs.get('zmq_context')
        self.zmq_pub = kwargs.get('zmq_pub')
        self.zmq_msg_sub = kwargs.get('zmq_msg_sub')
        self.signals = kwargs.get('signals')        
        self.callback = cb_map[kwargs.get('cb', 'default_cb')]
        
        assert(self.zmq_context)
        self.subscriber = self.zmq_context.socket(zmq.SUB)
        for msg in self.zmq_msg_sub :
            self.subscriber.setsockopt(zmq.SUBSCRIBE, msg)
        for pub in self.zmq_pub :
            self.subscriber.connect(pub)
        print 'Connect to Data publisher %s' % self.zmq_pub 

        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)
        
        # start thread activity .... start by user !!!!
        self.start()


    def run(self):
        ''' poll on sockets '''

        print "...start thread activity"
        start_time = datetime.datetime.now()
        previous = datetime.datetime.now()
        self.msg_loop = datetime.timedelta()
        
        while not self.stop_event.is_set():
            
            socks = dict(self.poller.poll(POLLER_TIMEOUT))

            if self.subscriber in socks and socks[self.subscriber] == zmq.POLLIN:
                now = datetime.datetime.now()
                self.msg_loop = now - previous
                previous = now
                try :
                    id, data = self.subscriber.recv_multipart()
                    self.msg_id_ts[id].append((self.msg_loop,now-start_time))
                except Exception, e :
                    print e
                    continue
                
                self.callback(id, data, self.signals)
                
            else :
                print datetime.datetime.now(), socks, "poller timeout"

        print "thread Exit ..."


    def stop(self):
        ''' '''
        self.stop_event.set()
       

def zmq_sub_option():
    
    parser = OptionParser()
    parser.add_option("--zmq-pub", action="store", type="string", dest="zmq_pub", default=DEFAULT_ZMQ_PUB)
    parser.add_option("--zmq-pub-gen-host", action="store", type="string", dest="zmq_pub_gen_host", default="")
    parser.add_option("--zmq-pub-gen-port", action="store", type="string", dest="zmq_pub_gen_port", default="")
    parser.add_option("--zmq-msg-sub", action="store", type="string", dest="zmq_msg_sub", default="")
    parser.add_option("--signals", action="store", type="string", dest="signals", default="")
    parser.add_option("--cb", action="store", type="string", dest="cb", default="default_cb")
    (options, args) = parser.parse_args()
    dict_opt = vars(options)

    # one ctx for each process
    dict_opt['zmq_context'] = zmq.Context()
    gen_pub_zmq = zmq_pub_gen(dict_opt['zmq_pub_gen_host'],
                              [int(x) for x in dict_opt['zmq_pub_gen_port'].split(',') if len(dict_opt['zmq_pub_gen_port']) ])
    print gen_pub_zmq
    if len(gen_pub_zmq) :
        dict_opt['zmq_pub'] = gen_pub_zmq
    dict_opt['zmq_pub'] = dict_opt['zmq_pub'].split(',')
    dict_opt['zmq_msg_sub'] = dict_opt['zmq_msg_sub'].split(',')
    dict_opt['signals'] = dict_opt['signals'].split(',') if len(dict_opt['signals']) else []   
    
    return dict_opt
    
    
if __name__ == '__main__' :
    
    import sys
    import csv 
    import operator
    
    dict_opt = zmq_sub_option()
    
    th = ZMQ_sub(**dict_opt)
    try : sys.__stdin__.readline()
    except KeyboardInterrupt : pass
    print "Set thread event ...."
    th.stop()

    for k in th.msg_id_ts.iterkeys() :
        pprint.pprint((k, th.msg_id_ts[k][:10]))
        #print reduce(operator.add ,(ts for ts in th.msg_id_ts[k]))
