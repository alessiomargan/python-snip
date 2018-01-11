#! /usr/bin/env python

import zmq
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import datetime
import threading
import operator
from collections import defaultdict

from zmq_sub import zmq_sub_option, ZMQ_sub, json_cb, protobuf_cb

fig = plt.figure()

ax1 = fig.add_subplot(511, xlim=(0,5000), ylim=(-3, 3))
ax2 = fig.add_subplot(512, xlim=(0,5000), ylim=(-10, 10))
ax3 = fig.add_subplot(513, xlim=(0,5000), ylim=(-30, 30))
ax4 = fig.add_subplot(514, xlim=(0,5000), ylim=(900, 1100))
#ax5 = fig.add_subplot(515, xlim=(0,5000), ylim=(20, 400))
ax5 = fig.add_subplot(515, xlim=(0,5000), ylim=(-250, 250))

line, = ax1.plot([], [], lw=2, label='link_pos')
lin2, = ax1.plot([], [], lw=2, label='ref_fb')
lin3, = ax1.plot([], [], lw=2, label='motor_pos')

lin4, = ax3.plot([], [], lw=2, label='torque')

lin5, = ax2.plot([], [], lw=2, label='link_vel')
lin6, = ax2.plot([], [], lw=2, label='motor_vel')

lin7, = ax4.plot([], [], lw=2, label='rtt')

lin8, = ax5.plot([], [], lw=2, label='temp')

ax1.legend()
ax2.legend()
ax3.legend()
ax4.legend()

lines = [
    line,
    lin2,
    lin3,
    lin4,
    lin5,
    lin6,
    lin7,
    lin8
]

plot_data = defaultdict(list)
global ths

#!!!!
key_prefix = 'Motor_id_1'
#key_prefix = 'Test_pos_1'
key_prefix_2 = 'Motor_id_103'
key_prefix_3 = 'Motor_id_104'

'''
('Motor_id_4',
 {'aux': 0.0,
  'fault': 0,
  'link_pos': 0.31863078474998474,
  'link_vel': -0.0476837158203125,
  'motor_pos': 0.31815823912620544,
  'motor_vel': -0.0476837158203125,
  'op_idx_ack': 0,
  'rtt': 993,
  'temperature': 45,
  'torque': -0.7925033569335938})
'''

class ZMQ_sub_buffered(ZMQ_sub) :

    def __init__(self, **kwargs):

        #draw_event_freq_ms = kwargs.pop('draw_event_freq_ms',100)
        #self.fire_event = datetime.timedelta(milliseconds=draw_event_freq_ms)
        self.elapsed = datetime.timedelta()
        self.buffered = defaultdict(list)
        self.lock_buff = threading.RLock()
        ZMQ_sub.__init__(self, **kwargs)
        self.callback = self.on_rx

    def on_rx(self, id, data, signals):
        ''' '''
        with self.lock_buff :
            #id, data_dict = json_cb(id, data, signals)
            id, data_dict = protobuf_cb(id, data, signals)
            self.buffered[id].append(data_dict)
        self.elapsed += self.msg_loop

        return id,data_dict

    def next(self):
        '''  '''
        data = defaultdict(list)
        with self.lock_buff :
            for id in self.buffered.iterkeys():
                #print '>>', id, len(self.buffered[id])
                for d in self.buffered[id] :
                    for k, v in d.items() :
                        data[id+'_'+k].append(v)
            # clean buffered data
            self.buffered = defaultdict(list)
        return data


def init():
    
    for l in lines :
        l.set_data([], [])
    return lines
    
def animate(i):

    new_data = th.next()
    for k in plot_data.iterkeys() :
        plot_data[k].extend(new_data[k])
        plot_data[k] = plot_data[k][-5000:]

    x = np.arange(len(plot_data[key_prefix+'_link_pos']))
    
    y = np.array(plot_data[key_prefix+'_link_pos'])
    line.set_data(x, y)
    y = np.array(plot_data[key_prefix+'_aux'])
    lin2.set_data(x, y)
    y = np.array(plot_data[key_prefix+'_motor_pos'])
    lin3.set_data(x, y)
    y = np.array(plot_data[key_prefix+'_torque'])
    lin4.set_data(x, y)
    y = np.array(plot_data[key_prefix+'_motor_vel'])
    lin5.set_data(x, y)
    y = np.array(plot_data[key_prefix+'_link_vel'])
    lin6.set_data(x, y)
    
    y = np.array(plot_data[key_prefix+'_rtt'])
    lin7.set_data(x, y)
    y = np.array(plot_data[key_prefix+'_temperature'])
    y = np.array(map(operator.sub, plot_data[key_prefix+'_motor_pos'], plot_data[key_prefix+'_link_pos']))
    
    #x = np.arange(len(plot_data[key_prefix_2+'_link_pos']))
    #y = np.array(plot_data[key_prefix_2+'_torque'])
    lin8.set_data(x, y)
    
    return lines

if __name__ == '__main__' :
    
    
    dict_opt = zmq_sub_option()
    th = ZMQ_sub_buffered(**dict_opt)
    
    ani = animation.FuncAnimation(fig, animate, init_func=init, interval=50, blit=True)
    plt.show()
    
    print "Set thread event ...."
    th.stop()
