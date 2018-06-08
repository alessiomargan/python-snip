#! /usr/bin/env python

import sys
import operator
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec

import datetime
import threading
from collections import defaultdict

from zmq_sub import zmq_sub_option, ZMQ_sub_buffered

fig = plt.figure()
gs = gridspec.GridSpec(4, 3)

ax1 = fig.add_subplot(gs[0, :], xlim=(0, 5000), ylim=(-3, 3))
ax2 = fig.add_subplot(gs[1, :], xlim=(0, 5000), ylim=(-10, 10))
ax3 = fig.add_subplot(gs[2, :], xlim=(0, 5000), ylim=(-60, 60))
ax4 = fig.add_subplot(gs[3, 0], xlim=(0, 5000), ylim=(900, 1100))
ax5 = fig.add_subplot(gs[3, 1], xlim=(0, 5000), ylim=(20, 90))
ax6 = fig.add_subplot(gs[3, 2], xlim=(0, 5000), ylim=(0, 0.1))

lin1, = ax1.plot([], [], lw=2, label='link_pos')
lin2, = ax1.plot([], [], lw=2, label='ref_fb')
lin3, = ax1.plot([], [], lw=2, label='motor_pos')

lin4, = ax3.plot([], [], lw=2, label='torque')

lin5, = ax2.plot([], [], lw=2, label='link_vel')
lin6, = ax2.plot([], [], lw=2, label='motor_vel')

lin7, = ax4.plot([], [], lw=2, label='rtt')

lin8, = ax5.plot([], [], lw=2, label='mT')
lin9, = ax5.plot([], [], lw=2, label='bT')

lin10, = ax6.plot([], [], lw=2, label='p_err')
#lin11, = ax6.plot([], [], lw=2, label='v_err')

ax1.legend()
ax2.legend()
ax3.legend()
ax4.legend()
ax5.legend()
ax6.legend()

lines = [
    lin1,
    lin2,
    lin3,
    lin4,
    lin5,
    lin6,
    lin7,
    lin8,
    lin9,
    lin10,
#    lin11,
]

plot_data = defaultdict(list)
global th


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



def init():
    
    for l in lines:
        l.set_data([], [])
    return lines


def animate(i):

    new_data = th.next()
    for k in plot_data.iterkeys():
        plot_data[k].extend(new_data[k])
        plot_data[k] = plot_data[k][-5000:]

    x = np.arange(len(plot_data[th.key_prefix+'_link_pos']))
    
    y = np.array(plot_data[th.key_prefix+'_link_pos'])
    lin1.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_aux'])
    lin2.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_motor_pos'])
    lin3.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_torque'])
    lin4.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_motor_vel'])
    lin5.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_link_vel'])
    lin6.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_rtt'])
    lin7.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_board_temp'])
    lin8.set_data(x, y)
    y = np.array(plot_data[th.key_prefix+'_motor_temp'])
    lin9.set_data(x, y)

    y = np.absolute(np.array(map(operator.sub, plot_data[th.key_prefix+'_aux'], plot_data[th.key_prefix+'_motor_pos'])))
    lin10.set_data(x, y)
#    y = np.absolute(np.array(map(operator.sub, plot_data[key_prefix+'_link_vel'], plot_data[key_prefix+'_motor_vel'])))
#    lin10.set_data(x, y)

    # x = np.arange(len(plot_data[key_prefix_2+'_link_pos']))
    # y = np.array(plot_data[key_prefix_2+'_torque'])

    return lines

if __name__ == '__main__' :

    dict_opt = zmq_sub_option(sys.argv[1:])
    th = ZMQ_sub_buffered(**dict_opt)
    th.start()

    ani = animation.FuncAnimation(fig, animate, init_func=init, interval=50, blit=True)
    plt.show()
    
    print ("Set thread event ....")
    th.stop()
