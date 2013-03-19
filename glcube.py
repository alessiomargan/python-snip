#!/usr/bin/env python

"""Draw a cube on the screen. every frame we orbit
the camera around by a small amount and it appears
the object is spinning. note i've setup some simple
data structures here to represent a multicolored cube,
we then go through a semi-unopimized loop to draw
the cube points onto the screen. opengl does all the
hard work for us. :]
"""

import pygame
from pygame.locals import *

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    print OpenGL.__version__
    import OpenGLContext.quaternion as quat
except Exception, e :
    print e
    
    print ('The GLCUBE example requires PyOpenGL')
    raise ImportError

import math

#some simple data for a colored cube
#here we have the 3D point position and color
#for each corner. then we have a list of indices
#that describe each face, and a list of indieces
#that describes each edge


CUBE_POINTS = (
    (0.5, -0.5, -0.5),  (0.5, 0.5, -0.5),
    (-0.5, 0.5, -0.5),  (-0.5, -0.5, -0.5),
    (0.5, -0.5, 0.5),   (0.5, 0.5, 0.5),
    (-0.5, -0.5, 0.5),  (-0.5, 0.5, 0.5)
)

#colors are 0-1 floating values
CUBE_COLORS = (
    (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 0),
    (1, 0, 1), (1, 1, 1), (0, 0, 1), (0, 1, 1)
)

CUBE_QUAD_VERTS = (
    (0, 1, 2, 3), (3, 2, 7, 6), (6, 7, 5, 4),
    (4, 5, 1, 0), (1, 5, 7, 2), (4, 0, 3, 6)
)

CUBE_EDGES = (
    (0,1), (0,3), (0,4), (2,1), (2,3), (2,7),
    (6,3), (6,4), (6,7), (5,1), (5,4), (5,7),
)



def drawcube():
    "draw the cube"
    allpoints = zip(CUBE_POINTS, CUBE_COLORS)

    glBegin(GL_QUADS)
    for face in CUBE_QUAD_VERTS:
        for vert in face:
            pos, color = allpoints[vert]
            glColor3fv(color)
            glVertex3fv(pos)
    glEnd()
    
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    for line in CUBE_EDGES:
        for vert in line:
            pos, color = allpoints[vert]
            #glColor3fv(color)
            glVertex3fv(pos)

    glEnd()

AXES_POINTS = (
    (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
)

#colors are 0-1 floating values
AXES_COLORS = (
    (1, 1, 1), (1, 0, 0), (0, 1, 0), (0, 0, 1),
)

def drawaxes():
    "draw axes"
    allpoints = zip(AXES_POINTS, AXES_COLORS)

    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    for line in [(0,1),(0,2),(0,3)]:
        for vert in line:
            pos, color = allpoints[vert]
            glColor3fv(color)
            glVertex3fv(pos)
    glEnd()

def drawline(pt,color=(1,1,1)):
    "draw line"

    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    for vert in [(0,0,0),tuple(pt)]:
        glColor3fv(color)
        glVertex3fv(vert)
    glEnd()

    
def init_scene():
    #initialize pygame and setup an opengl display
    pygame.init()
    pygame.display.set_mode((640,480), OPENGL|DOUBLEBUF)
    glEnable(GL_DEPTH_TEST)        #use our zbuffer
    #setup the camera
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45.0,640/480.0,0.1,100.0)    #setup lens
    glTranslatef(0.0, 0.0, -3.0)                #move back
    #glRotatef(25, 0, 1, 1)                       #orbit higher
        

def event():
    #check for quit'n events
    event = pygame.event.poll()
    return event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE)

def draw_scene_quat(q) :
    #clear screen and move camera
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    
    drawaxes()
    
    glPushMatrix()
    rmat =  quat.Quaternion(list(q)).matrix()
    #print rmat
    glMultMatrixf(rmat)
    drawcube()
    glPopMatrix()
    
    pygame.display.flip()
    #pygame.time.wait(1)

    return 1

def draw_scene_vect(v) :
    #clear screen and move camera
    #glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    #glMatrixMode(GL_MODELVIEW)
    
    drawaxes()
    for pt,c in v :
        drawline(pt,c)
    '''
    glPushMatrix()
    glRotatef(v[0], 1, 0, 0)                    
    glRotatef(v[1], 0, 1, 0)                    
    glRotatef(v[2], 0, 0, 1)                    
    drawcube()
    glPopMatrix()
    '''
    
    pygame.display.flip()
    #pygame.time.wait(1)

    return 1


if __name__ == '__main__': 
    
    ang = 1
    init_scene()
    while not event():
        draw_scene_vect((ang,1,1))
        ang +=1
