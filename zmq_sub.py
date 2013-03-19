#! /usr/bin/env python

import sys, os
import zmq
import json
import datetime
import time
import threading
import pprint
import numpy
import math
import itertools
from collections import defaultdict
try : from view.UI_event import trig_ZMQ_data
except : pass

#DEFAULT_ZMQ_PUB = 'tcp://localhost:5555'
#DEFAULT_ZMQ_PUB = 'tcp://carm-deb.local:6666'
#DEFAULT_ZMQ_PUB = 'tcp://10.255.32.203:6666'
#DEFAULT_ZMQ_PUB = 'tcp://ccub-deb-test.local:6666'
DEFAULT_ZMQ_PUB = 'tcp://localhost:6666'

hiris_vars = defaultdict(list)

# ##############################################################
#
try: 
    import glcube
    
    def vect_norm(v):
        return numpy.array(v) / numpy.linalg.norm(v)
    
    def draw_gl_init(*args):
        global th
        glcube.init_scene()
        th.callback = draw_gl_cube
        
    def draw_gl_cube(*args):
    
        id, data = args
    
        if id == 'uStrain':
            for k,v in data.items() :
                hiris_vars[k].append(v)
            
                
        elif id == 'hiris':
            for var_as_dict in data['_payload']['_vars'] :
                # !!! 
                hiris_vars[var_as_dict['name']].append(var_as_dict['_value']/1000.0)
    
            
        try :
            imu_quat = [hiris_vars[var_name][-1] for var_name in "quat_0 quat_1 quat_2 quat_3".split()]
            glcube.draw_scene_quat(imu_quat)
        except IndexError :
            # not enought data ....
            print '... retry'
    
        try :
            imu_mag =  [hiris_vars[var_name][-1] for var_name in "mag_x mag_y mag_z".split()]
            imu_gyr =  [hiris_vars[var_name][-1] for var_name in "gyr_x gyr_y gyr_z".split()]
            imu_acc =  [hiris_vars[var_name][-1] for var_name in "acc_x acc_y acc_z".split()]
        except IndexError :
            # not enought data ....
            print '... retry'
            return
        
        print "M:", vect_norm(imu_mag)
        print "G:", vect_norm(imu_gyr)
        print "A:", vect_norm(imu_acc)
        print "Q:", imu_quat
    
        
        #glcube.draw_scene_vect([(vect_norm(imu_mag),(1,0,1)),
        #                        (vect_norm(imu_gyr),(0,1,1)),
        #                        (vect_norm(imu_acc),(1,1,0))])
        
        #print datetime.datetime.now()

except ImportError, e : print e

# ##############################################################

import sys
sys.path.append('/usr/local/src/COMAN_shared/utils/python')
import board_data_type
import policy_maps

def test_cb(*args):

    id,data = args
    policy = 'Position|Tendon_tor|Lin_enc_raw|Delta_tor|Lin_enc_vel'
    bcast_data = board_data_type.data_factory(policy, policy_maps.bigLeg_policy_map)
    bcast_data.decode(data)    
    data_dict = bcast_data.toDict(all_fields=False)
    pprint.pprint((id,data_dict))
    
    
def hiris_var_cb(*args):

    id, data = args
    #values = [var_as_dict['_value'] for var_as_dict in data['_payload']['_vars']]
    #print values
    #print numpy.linalg.norm(values)
    for var_as_dict in data['_payload']['_vars'] :
        hiris_vars[var_as_dict['name']].append(var_as_dict['_value'])
        
    [hiris_vars[var_name][:-1] for var_name in "quat_0 quat_1 quat_2 quat_3".split()]
        

def default_cb(*args):
    
    id,data = args
    data = json.loads(data)
    pprint.pprint((id,data))

def text_cb(*args):
    
    id,data = args
    print id,data
    
    
class zmq_sub(threading.Thread):

    def __init__(self, *args, **kwargs):

        threading.Thread.__init__(self)
        self.ev = threading.Event()
        self.ev.clear()
        
        self.zmq_context = kwargs.get('zmq_context')
        self.zmq_pub = kwargs.get('zmq_pub', DEFAULT_ZMQ_PUB)
        self.zmq_msg_sub = kwargs.get('zmq_msg_sub', '')
        self.signals = kwargs.get('signals', '')

        self.callback = cb_map[kwargs.get('cb', 'default_cb')] 
        
        # Connect our subscriber socket
        self.subscriber = self.zmq_context.socket(zmq.SUB)
        for msg in self.zmq_msg_sub.split(',') :
            self.subscriber.setsockopt(zmq.SUBSCRIBE, msg)
        self.subscriber.connect(self.zmq_pub)
        
        
    def run(self):
    
        prev = datetime.datetime.now()
        while not self.ev.is_set():
    
            #time.sleep(0.001)
            try : id,data = self.subscriber.recv_multipart(zmq.NOBLOCK)
            #try : id,data = self.subscriber.recv_multipart()
            except ValueError : continue
            except zmq.ZMQError, e : 
                #print e
                #time.sleep(1)
                continue
            
            self.callback(id, data) 
            
            now = datetime.datetime.now()
            elap = now - prev
            prev = now
            print elap
            #print id , data
    

    
if __name__ == '__main__' :
    
    import sys
    from optparse import OptionParser
    import csv
    
    cb_map = {'default_cb': default_cb,
              'text_cb': text_cb,
              'test_cb': test_cb} 
    
    
    parser = OptionParser()
    parser.add_option("--zmq-pub", action="store", type="string", dest="zmq_pub", default=DEFAULT_ZMQ_PUB)
    parser.add_option("--zmq-msg-sub", action="store", type="string", dest="zmq_msg_sub", default="")
    parser.add_option("--signals", action="store", type="string", dest="signals", default="")
    parser.add_option("--cb", action="store", type="string", dest="cb", default="default_cb")
    (options, args) = parser.parse_args()
    dict_opt = vars(options)

    # one ctx for each process
    dict_opt['zmq_context'] = zmq.Context()
    
    th = zmq_sub(**dict_opt)
    th.start()
    try : sys.__stdin__.readline()
    except KeyboardInterrupt : pass
    print "Set thread event ...."
    th.ev.set()
        
    w = csv.writer(open('M.csv', 'w'),delimiter=' ')
    w.writerows(itertools.izip(hiris_vars['mag_x'],hiris_vars['mag_y'],hiris_vars['mag_z']))    
    w = csv.writer(open('G.csv', 'w'),delimiter=' ')
    w.writerows(itertools.izip(hiris_vars['gyr_x'],hiris_vars['gyr_y'],hiris_vars['gyr_z']))    
    w = csv.writer(open('A.csv', 'w'),delimiter=' ')
    w.writerows(itertools.izip(hiris_vars['acc_x'],hiris_vars['acc_y'],hiris_vars['acc_z']))    
        
