#! /usr/bin/env python3

"""
('NoNe@Motor_id_123',
 {'aux': 0.0,
  'board_temp': 41.0,
  'fault': 0,
  'link_pos': -0.12549510598182678,
  'link_vel': 0.0,
  'motor_pos': -0.1254965364933014,
  'motor_temp': 33.0,
  'motor_vel': 0.0,
  'op_idx_ack': 0,
  'rtt': 990,
  'temperature': 8489,
  'torque': -4.564897060394287})
"""

import sys
import operator
import numpy as np
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec

from zmq_sub import zmq_sub_option, ZMQ_sub_buffered

gPlot_data = defaultdict(list)  # type: defaultdict[Any, list]
global th

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

#lin10, = ax6.plot([], [], lw=2, label='p_err')
#lin11, = ax6.plot([], [], lw=2, label='v_err')

ax1.legend()
ax2.legend()
ax3.legend()
ax4.legend()
ax5.legend()
ax6.legend()

lines = [
    lin1,
#    lin2,
    lin3,
    lin4,
    lin5,
    lin6,
    lin7,
    lin8,
    lin9,
#    lin10,
#    lin11,
]

var_names = (
    '_link_pos',
#    '_ref_pos',
    '_motor_pos',
    '_torque',
    '_link_vel',
    '_motor_vel',
    '_rtt',
    '_motor_temp',
    '_board_temp',
#    '_p_err',
)

def init():

    for l in lines:
        l.set_data([], [])
    return lines


def animate(i):

    new_data = th.next()
    for k in gPlot_data.keys():
        gPlot_data[k].extend(new_data[k])
        gPlot_data[k] = gPlot_data[k][-5000:]

    x = np.arange(len(gPlot_data[th.key_prefix+'_link_pos']))

    for name, lin in zip(var_names, lines):
        y = np.array(gPlot_data[th.key_prefix + name])
        lin.set_data(x, y)

    return lines


if __name__ == '__main__' :

    dict_opt = zmq_sub_option(sys.argv[1:])
    th = ZMQ_sub_buffered(**dict_opt)
    th.start()

    ani = animation.FuncAnimation(fig, animate, init_func=init, interval=50, blit=True)
    plt.show()
    
    print("Set thread event ....")
    th.stop()
