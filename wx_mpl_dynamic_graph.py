#!/usr/bin/python
import os
import pprint
import random
import sys
import wx
import wx.lib.newevent
(UpdateIoEvent, EVT_UPDATE_IO) = wx.lib.newevent.NewEvent()


# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#
sys.path.insert(0,'/usr/local/lib/python2.6/dist-packages/')

import matplotlib
print matplotlib.__version__
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.axes3d import Axes3D
from matplotlib.backends.backend_wxagg import \
     FigureCanvasWxAgg as FigCanvas, \
     NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab

# #################################################################

class DataGenFake() :

    def __init__(self, **kwargs):
        pass

    def next(self):
        data = []
        return data

# #################################################################

class DataGenRandom() :

    def __init__(self, **kwargs):
        pass

    def next(self):
        data = []
        return data


# #################################################################
'''
import ioModel

class DataGen(ioModel.Log_model) :

    def __init__(self, **kwargs):
        ioModel.Log_model.__init__(self, **kwargs)
        self.buffered = []

    def set(self, data):
        ret = ioModel.Log_model.set(self, data)
        if ret :
            self.buffered.append(self)
            evt = UpdateIoEvent(board_id=self.board_id)
            try : wx.PostEvent(wx.GetApp().GetTopWindow(), evt)
            except : pass
        return ret

    def next(self):
        data = []
        print len(self.buffered)
        for b in self.buffered :
            v = b._serialize_analog('ain',4)
            data.extend(v)
            self.buffered = []
        if not len(data) :
            return []
        return data
'''
# #################################################################

import threading
import time, datetime
import zmq
import json
from collections import defaultdict

class DataGenZMQ(threading.Thread) :
    ''' read json data from a zmq publisher '''

    def __init__(self, **kwargs):

        threading.Thread.__init__(self)
        self.buffered = defaultdict(list)
        self.lock_buff = threading.RLock()
        self.stop_event = threading.Event()
        self.stop_event.clear()
        
        zmq_context = kwargs.pop('zmq_context')
        zmq_pub = kwargs.pop('zmq_pub')
        self.zmq_msg_sub = kwargs.pop('zmq_msg_sub',[])
        self.draw_event_freq_ms = kwargs.pop('draw_event_freq_ms',100)

        assert(zmq_context)
        self.subscriber = zmq_context.socket(zmq.SUB)
        for msg in self.zmq_msg_sub :
            self.subscriber.setsockopt(zmq.SUBSCRIBE, msg)
        self.subscriber.connect(zmq_pub)
        print 'Connect to Data publisher %s' % zmq_pub 

        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)

        # start thread activity
        self.start()


    def run(self):
        ''' poll on sockets '''

        previous = datetime.datetime.now()
        elapsed = datetime.timedelta()
        fire_event = datetime.timedelta(milliseconds=self.draw_event_freq_ms)

        while not self.stop_event.is_set():
            
            socks = dict(self.poller.poll())

            if self.subscriber in socks and socks[self.subscriber] == zmq.POLLIN:
                now = datetime.datetime.now()
                msg_loop = now - previous
                elapsed += msg_loop
                previous = now
                #print msg_loop
                try :
                    id, message = self.subscriber.recv_multipart()
                except ValueError :
                    continue
                with self.lock_buff :
                    self.buffered[id].append(json.loads(message))
                if elapsed > fire_event :
                    #print self.buffered
                    #print elapsed, fire_event
                    elapsed = datetime.timedelta()
                    evt = UpdateIoEvent(id=id)
                    try : wx.PostEvent(wx.GetApp().GetTopWindow(), evt)
                    except : pass

        print "thread Exit ..."


    def stop(self):
        ''' '''
        self.stop_event.set()
       

    def next(self):
        '''  '''
        data = defaultdict(list)
        with self.lock_buff :
            #if len(self.buffered) :
            for id in self.buffered.iterkeys():
                for d in self.buffered[id] :
                    for k, v in d.items() :
                        data[id+'_'+k].append(v)
            if set(self.buffered.keys()) == set(self.zmq_msg_sub) :
                self.buffered = defaultdict(list)
        return data



# ###############################################################

class Plot():

    def __init__(self, axes, **kwargs):

        self._axes = axes 
        self._length = 0
        self._ymin = sys.maxint
        self._ymax = -sys.maxint-1

        self._max_samples = kwargs.get('max_samples')
        _zmq_msg_sub = kwargs.get('zmq_msg_sub',[])
        _signals = kwargs.get('signals',[])

        # dict of samples list
        # self._data[k] = [samples]
        self._data = defaultdict(list)
        for m in _zmq_msg_sub :
            for s in _signals :
                self._data[m+'_'+s]

        _color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        color_iterator = iter(_color)

        self._plot = dict()
        for k,l in self._data.iteritems() :
            self._plot[k] = self._axes.plot(l, linewidth=1,
                                            color=color_iterator.next(),
                                            label=k)[0]
        fp = matplotlib.font_manager.FontProperties(size=8)
        self._axes.legend(loc=2, prop=fp)


    def draw(self):

        for k,_plot in self._plot.iteritems() :
            _plot.set_xdata(np.arange(len(self._data[k])))
            _plot.set_ydata(np.array(self._data[k]))

    def set_data(self, new_data):
        ''' 
        '''
        for k in self._data.iterkeys() :
            self._data[k].extend(new_data[k])
            self._data[k] = self._data[k][-self._max_samples:]
            # ?!?!? 
            if len(self._data[k]):
                self._length = max(len(self._data[k]), self._length)
                self._ymin = min(round(min(self._data[k]),0)-1, self._ymin)
                self._ymax = max(round(max(self._data[k]),0)+1, self._ymax)

    def __len__(self):

        return self._length 

    def minmax(self):

        return self._ymin, self._ymax


class BoundControlBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a 
        manual mode with an associated value.
    """
    def __init__(self, parent, ID, label, initval):
        wx.Panel.__init__(self, parent, ID)

        self.value = initval

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.radio_auto = wx.RadioButton(self, -1, 
                                         label="Auto", style=wx.RB_GROUP)
        self.radio_manual = wx.RadioButton(self, -1,
                                           label="Manual")
        self.manual_text = wx.TextCtrl(self, -1, 
                                       size=(70,-1),
                                       value=str(initval),
                                       style=wx.TE_PROCESS_ENTER)

        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)

        manual_box = wx.BoxSizer(wx.HORIZONTAL)
        manual_box.Add(self.radio_manual, flag=wx.ALIGN_CENTER_VERTICAL)
        manual_box.Add(self.manual_text, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(self.radio_auto, -1, wx.ALL, 2)
        sizer.Add(manual_box, -1, wx.ALL, 2)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_update_manual_text(self, event):
        self.manual_text.Enable(self.radio_manual.GetValue())

    def on_text_enter(self, event):
        self.value = self.manual_text.GetValue()

    def is_auto(self):
        return self.radio_auto.GetValue()

    def manual_value(self):
        return self.value



class GraphFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Dynamic matplotlib graph'

    def __init__(self, **kwargs):
        wx.Frame.__init__(self, None, -1, self.title)

        self.kwargs = kwargs

        zmq_context = kwargs.get('zmq_context')

        # start with null data generator 
        self.datagen = DataGenFake()
        self.data = self.datagen.next()

        self.paused = False

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        # 
        self.Bind(EVT_UPDATE_IO, self.on_redraw_timer)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_close, m_exit)

        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        self.xmin_control = BoundControlBox(self.panel, -1, "X min", 0)
        self.xmax_control = BoundControlBox(self.panel, -1, "X max", 50)
        self.ymin_control = BoundControlBox(self.panel, -1, "Y min", 0)
        self.ymax_control = BoundControlBox(self.panel, -1, "Y max", 100)

        self.pause_button = wx.Button(self.panel, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.cb_grid = wx.CheckBox(self.panel, -1, 
                                   "Show Grid",
                                   style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)

        self.cb_xlab = wx.CheckBox(self.panel, -1, 
                                   "Show X labels",
                                   style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_xlab, self.cb_xlab)        
        self.cb_xlab.SetValue(True)

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.cb_xlab, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.xmax_control, border=5, flag=wx.ALL)
        self.hbox2.AddSpacer(24)
        self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)

        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
        self.dpi = 100
        params = matplotlib.figure.SubplotParams(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.001, hspace=0.1)
        self.fig = Figure((3.0, 3.0), dpi=self.dpi, subplotpars=params)

        gs = matplotlib.gridspec.GridSpec(1, 1)
        gs.update(wspace=0.1)

        self.axes = self.fig.add_subplot(gs[0, :]) #221
        self.axes.set_axis_bgcolor('black')
        #self.axes.set_title('Data', size=12)

        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series

        self.plot = Plot(self.axes, **self.kwargs)

        """
        self.f_plot_old = []
        self.f_axes = self.fig.add_subplot(gs[1, 0], projection='3d')
        self.f_axes.autoscale(False)
        self.f_axes.set_xlim(-15,15)
        self.f_axes.set_ylim(-15,15)
        self.f_axes.set_zlim(-15,15)
        self.f_plot_old.append(self.f_axes.plot_wireframe([0,1], [0,1], [0,1]))

        self.t_axes = self.fig.add_subplot(gs[1, 1], projection='3d')
        self.t_axes.autoscale(False)
        self.t_axes.set_xlim(-15,15)
        self.t_axes.set_ylim(-15,15)
        self.t_axes.set_zlim(-15,15)
        self.t_plot_old = self.t_axes.plot_wireframe([0,1], [0,1], [0,1])
        """

    def draw_plot(self):
        """ Redraws the plot
        """
        # when xmin is on auto, it "follows" xmax to produce a 
        # sliding window effect. therefore, xmin is assigned after
        # xmax.
        #
        data_length =  len(self.plot)

        if self.xmax_control.is_auto():
            xmax = data_length if data_length > 50 else 50
        else:
            xmax = int(self.xmax_control.manual_value())

        if self.xmin_control.is_auto():            
            xmin = xmax - self.kwargs.get('max_samples')/2
        else:
            xmin = int(self.xmin_control.manual_value())

        # for ymin and ymax, find the minimal and maximal values
        # in the data set and add a mininal margin.
        # 
        # note that it's easy to change this scheme to the 
        # minimal/maximal value in the current display, and not
        # the whole data set.
        #
        if self.ymin_control.is_auto():
            ymin = self.plot.minmax()[0]
        else:
            ymin = int(self.ymin_control.manual_value())

        if self.ymax_control.is_auto():
            ymax = self.plot.minmax()[1]
        else:
            ymax = int(self.ymax_control.manual_value())

        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=ymin, upper=ymax)

        # anecdote: axes.grid assumes b=True if any other flag is
        # given even if b is set to False.
        # so just passing the flag into the first statement won't
        # work.
        #
        if self.cb_grid.IsChecked():
            self.axes.grid(True, color='gray')
        else:
            self.axes.grid(False)

        # Using setp here is convenient, because get_xticklabels
        # returns a list over which one needs to explicitly 
        # iterate, and setp already handles this.
        #  
        pylab.setp(self.axes.get_xticklabels(), 
                   visible=self.cb_xlab.IsChecked())

        self.plot.draw()
        self.canvas.draw()

    def on_pause_button(self, event):
        self.paused = not self.paused

    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

    def on_cb_grid(self, event):
        self.draw_plot()

    def on_cb_xlab(self, event):
        self.draw_plot()

    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"

        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)

    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        #
        if not self.paused:
            data = self.datagen.next()
            self.plot.set_data(data)

            '''
            while len(self.f_plot_old) :
                p = self.f_plot_old.pop()
                p.remove()
            plot_old = self.f_axes.plot_wireframe([0, data['ft_xyz_mod_1_1_fx'][-1]],
                                                  [0, data['ft_xyz_mod_1_1_fy'][-1]],
                                                  [0, data['ft_xyz_mod_1_1_fz'][-1]])
            self.f_plot_old.append(plot_old)
            plot_old = self.f_axes.plot_wireframe([0, data['ft_xyz_mod_1_1_fx'][-1]],
                                                  [0, data['ft_xyz_mod_1_1_fy'][-1]],
                                                  [15, 15],
                                                  colors='r')
            self.f_plot_old.append(plot_old)
            plot_old = self.f_axes.plot_wireframe([0, data['ft_xyz_mod_1_1_fx'][-1]],
                                                  [15, 15],
                                                  [0, data['ft_xyz_mod_1_1_fz'][-1]],
                                                  colors='g')
            self.f_plot_old.append(plot_old)
            plot_old = self.f_axes.plot_wireframe([-15, -15],
                                                  [0, data['ft_xyz_mod_1_1_fy'][-1]],
                                                  [0, data['ft_xyz_mod_1_1_fz'][-1]],
                                                  colors='c')
            self.f_plot_old.append(plot_old)

            self.t_plot_old.remove()
            self.t_plot_old = self.t_axes.plot_wireframe([0, data['ft_xyz_mod_1_1_tx'][-1]],
                                                         [0, data['ft_xyz_mod_1_1_ty'][-1]],
                                                         [0, data['ft_xyz_mod_1_1_tz'][-1]])
            '''
        self.draw_plot()


    def on_close(self, event):

        self.datagen.stop()
        self.Destroy()


    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)

    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')


def main_twisted():

    from twisted.internet import wxreactor
    wxreactor.install()
    from twisted.internet import reactor    

    app = wx.PySimpleApp()
    frame = GraphFrame()
    frame.Show(True)

    # data generator
    datagen = DataGen(**{'board_id':int('0x740',16)})
    frame.datagen = datagen

    reactor.registerWxApp(app)
    kwargs = {'models':[datagen],
              'addr':'10.255.32.76',
              'mcast_grp': '239.1.1.2',
              'port':5260}
    protocol = MulticastServerUDP(**kwargs)
    reactor.listenMulticast(protocol.port, protocol, maxPacketSize=65536)
    SerialPort(ABC_Protocol(), '/dev/ttyUSB0', reactor, baudrate=57600)
    reactor.run(installSignalHandlers=0)
    print 'exit reactor ... exit app'


def main_zmq():

    import zmq
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--zmq-pub", action="store", type="string", dest="zmq_pub", default="tcp://localhost:5555")
    parser.add_option("--zmq-msg-sub", action="store", type="string", dest="zmq_msg_sub", default="")
    parser.add_option("--signals", action="store", type="string", dest="signals", default="")
    parser.add_option("--max-samples", action="store", type="int", dest="max_samples", default=2000)
    parser.add_option("--draw-event-freq-ms", action="store", type="int", dest="draw_event_freq_ms", default=100)
    (options, args) = parser.parse_args()
    dict_opt = vars(options)

    context = zmq.Context(1)

    dict_opt['zmq_context'] = context
    dict_opt['zmq_msg_sub'] = options.zmq_msg_sub.split(',')
    dict_opt['signals'] = options.signals.split(',')
    print dict_opt

    app = wx.PySimpleApp() 
    frame = GraphFrame(**dict_opt)
    frame.Show(True)

    # data generator
    datagen = DataGenZMQ(**dict_opt)
    frame.datagen = datagen

    app.MainLoop()

    for id in datagen.buffered.iterkeys():
        print id, len(datagen.buffered[id])
       

if __name__ == '__main__':


    main_zmq()

    print "Good bye ... cruel world !!"        
