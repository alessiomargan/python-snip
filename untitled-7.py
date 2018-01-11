from __future__ import print_function
"""
A very simple 'animation' of a 3D plot
"""
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import time


def generate(X, Y, phi):
    R = np.sqrt(X**2 + Y**2)
    return np.cos(2 * np.pi * X + phi) * R

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

xs = np.linspace(-1, 1, 16)
ys = np.linspace(-1, 1, 8)
X, Y = np.meshgrid(xs, ys)
Z = generate(X, Y, 0.0)

wframe = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                         rstride=1, cstride=1,
                         linewidth=0,
                         antialiased=False)

fig.colorbar(wframe, shrink=0.5, aspect=10)

tstart = time.time()
for phi in np.linspace(0, 360 / 2 / np.pi, 100):

    oldcol = wframe

    Z = generate(X, Y, phi)
    #wframe = ax.plot_wireframe(X, Y, Z, rstride=2, cstride=2)
    wframe = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                             rstride=1, cstride=1,
                             linewidth=0,
                             antialiased=False)
    
    # Remove old line collection before drawing
    if oldcol is not None:
        ax.collections.remove(oldcol)

    plt.pause(.005)

print('FPS: %f' % (100 / (time.time() - tstart)))