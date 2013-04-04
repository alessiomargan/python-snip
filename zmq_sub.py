#!/usr/bin/python

import threading
import time, datetime
import pprint
import zmq
import json
from collections import defaultdict
from optparse import OptionParser


import sys
sys.path.append('/usr/local/src/COMAN_shared/utils/python')
import board_data_type
import policy_maps

JSON_PUB_PORT = 6666 
TEXT_PUB_PORT = 6667 
CSTRUCT_PUB_PORT = 6668 

#DEFAULT_ZMQ_PUB = 'tcp://carm-deb.local:6666'
#DEFAULT_ZMQ_PUB = 'tcp://ccub-deb-test.local:6666'
DEFAULT_ZMQ_PUB = 'tcp://localhost:%d'%CSTRUCT_PUB_PORT
#DEFAULT_ZMQ_PUB = 'tcp://wheezy-i386-test.local:%d'%CSTRUCT_PUB_PORT

POLLER_TIMEOUT = 3


def default_cb(id, data):
    
    pprint.pprint((id,data))

def json_cb(id, data):
    
    pprint.pprint(id,json.loads(data))
    
def cstruct_cb(id,data):
    ''' broadcast policy MUST match the one set for DSP board !!!! '''
    policy = 'Position|Velocity|Torque|PID_err|PID_out|Current|Tendon_tor|Faults|Height|Hip_pos|Target_pos|Lin_enc_pos|Lin_enc_raw|Delta_tor|Lin_enc_vel'
    bcast_data = board_data_type.data_factory(policy, policy_maps.bigLeg_policy_map)
    bcast_data.decode(data)    
    data_dict = bcast_data.toDict(all_fields=False)
    pprint.pprint((id, data_dict))


cb_map = {'default_cb': default_cb,
          'json_cb':    json_cb,
          'cstruct_cb': cstruct_cb,
          }


class ZMQ_sub(threading.Thread) :
    ''' read data from a zmq publisher '''
    
    def __init__(self, **kwargs):

        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.stop_event.clear()
        
        self.zmq_context = kwargs.get('zmq_context')
        self.zmq_pub = kwargs.get('zmq_pub')
        self.zmq_msg_sub = kwargs.get('zmq_msg_sub')
        self.signals = kwargs.get('signals')        
        self.callback = cb_map[kwargs.get('cb', 'default_cb')]
        
        assert(self.zmq_context)
        self.subscriber = self.zmq_context.socket(zmq.SUB)
        for msg in self.zmq_msg_sub :
            self.subscriber.setsockopt(zmq.SUBSCRIBE, msg)
        self.subscriber.connect(self.zmq_pub)
        print 'Connect to Data publisher %s' % self.zmq_pub 

        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)

        self.msg_loop = datetime.timedelta()
        # start thread activity .... start by user !!!!
        self.start()


    def run(self):
        ''' poll on sockets '''

        print "...start thread activity"
        previous = datetime.datetime.now()

        while not self.stop_event.is_set():
            
            socks = dict(self.poller.poll(POLLER_TIMEOUT))

            if self.subscriber in socks and socks[self.subscriber] == zmq.POLLIN:
                now = datetime.datetime.now()
                self.msg_loop = now - previous
                previous = now
                #print self.msg_loop
                try :
                    id, data = self.subscriber.recv_multipart()
                except Exception, e :
                    print e
                    continue
                
                self.callback(id, data)
                
            else :
                print datetime.datetime.now(), "poller timeout"

        print "thread Exit ..."


    def stop(self):
        ''' '''
        self.stop_event.set()
       

def zmq_sub_option():
    
    parser = OptionParser()
    parser.add_option("--zmq-pub", action="store", type="string", dest="zmq_pub", default=DEFAULT_ZMQ_PUB)
    parser.add_option("--zmq-msg-sub", action="store", type="string", dest="zmq_msg_sub", default="")
    parser.add_option("--signals", action="store", type="string", dest="signals", default="")
    parser.add_option("--cb", action="store", type="string", dest="cb", default="default_cb")
    (options, args) = parser.parse_args()
    opts_as_dict = vars(options)
    return opts_as_dict
    
    
if __name__ == '__main__' :
    
    import sys
    import csv
    
    dict_opt = zmq_sub_option()

    # one ctx for each process
    dict_opt['zmq_context'] = zmq.Context()
    dict_opt['zmq_msg_sub'] = dict_opt['zmq_msg_sub'].split(',')
    dict_opt['signals'] = dict_opt['signals'].split(',')    
    
    th = ZMQ_sub(**dict_opt)
    try : sys.__stdin__.readline()
    except KeyboardInterrupt : pass
    print "Set thread event ...."
    th.stop()
