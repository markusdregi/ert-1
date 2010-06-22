import matplotlib.figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


import datetime
import time
from erttypes import time_t
import numpy
from widgets.util import print_timing
from  pages.plot.plotdata import PlotData
import widgets
from matplotlib.dates import AutoDateLocator
from PyQt4.QtCore import SIGNAL
import os

from plotconfig import PlotConfig
from plotter import Plotter
import matplotlib.lines
import matplotlib.text
from PyQt4.QtGui import QFrame, QInputDialog, QSizePolicy

class PlotView(QFrame):
    """PlotPanel shows available plot result files and displays them"""
#    blue = (56/255.0, 108/255.0, 176/255.0)
#    yellow = (255/255.0, 255/255.0, 153/255.0)
#    orange = (253/255.0, 192/255.0, 134/255.0)
#    purple = (190/255.0, 174/255.0, 212/255.0)
#    green = (127/255.0, 201/255.0, 127/255.0)

    red = (255/255.0, 26/255.0, 28/255.0)
    blue = (55/255.0, 126/255.0, 184/255.0)
    green = (77/255.0, 175/255.0, 74/255.0)
    purple = (152/255.0, 78/255.0, 163/255.0)
    orange = (255/255.0, 127/255.0, 0/255.0)

#    plot_color = (128/255.0, 177/255.0, 211/255.0)
#    selected_color = (190/255.0, 186/255.0, 218/255.0)
#    history_color = (253/255.0, 180/255.0, 98/255.0)
#    refcase_color = (179/255.0, 222/255.0, 105/255.0)

#    plot_color = (55/255.0, 126/255.0, 184/255.0)
#    selected_color = (152/255.0, 78/255.0, 163/255.0)
#    #history_color = (255/255.0, 127/255.0, 0/255.0)
#    history_color = (228/255.0, 26/255.0, 28/255.0)
#    #history_color = (255/255.0, 255/255.0, 51/255.0)
#    #refcase_color = (77/255.0, 175/255.0, 74/255.0)
#    refcase_color = (166/255.0, 86/255.0, 40/255.0)
#
    plot_color = (55/255.0, 126/255.0, 200/255.0)
    selected_color = (152/255.0, 78/255.0, 163/255.0)
    history_color = (255/255.0, 127/255.0, 0/255.0)
    #refcase_color = (190/255.0, 0/255.0, 0/255.0)
    refcase_color = (0/255.0, 200/255.0, 0/255.0)



    def __init__(self):
        """Create a PlotPanel"""
        QFrame.__init__(self)


        self.data = PlotData()
        self.data.x_data_type = "number"

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.fig = matplotlib.figure.Figure(dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        #self.canvas.draw = print_timing(self.canvas.draw)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xlim()

        self.selected_lines = []
        self.annotations = []


        self.mousehandler = MouseHandler(self)

        self.xminf = 0.0
        self.xmaxf = 1.0
        self.plot_path = "."

        self.observation_plot_config = PlotConfig("Observation", color = self.history_color, zorder=10)
        self.refcase_plot_config = PlotConfig("Refcase", visible=False, color = self.refcase_color, zorder=10)
        self.std_plot_config = PlotConfig("Error", linestyle=":", visible=False, color = self.history_color, zorder=10)
        self.plot_config = PlotConfig("Members", color = self.plot_color, alpha=0.125, zorder=1, picker=2)
        self.selected_plot_config = PlotConfig("Selected members", color = self.selected_color, alpha=0.5, zorder=8, picker=2)
        self.errorbar_plot_config = PlotConfig("Errorbars", visible=False, color = self.history_color, alpha=0.5, zorder=10)

        self.plot_configs = [self.plot_config,
                             self.selected_plot_config,
                             self.refcase_plot_config,
                             self.observation_plot_config,
                             self.std_plot_config,
                             self.errorbar_plot_config]

        self.plotter = Plotter()


    def configureLine(self, line, plot_config):
        line.set_color(plot_config.color)
        line.set_alpha(plot_config.alpha)
        line.set_zorder(plot_config.z_order)
        line.set_linestyle(plot_config.style)

    def toggleLine(self, line):
        if line in self.selected_lines:
            plot_config = self.plot_config
            self.selected_lines.remove(line)
        else:
            plot_config = self.selected_plot_config
            self.selected_lines.append(line)

        self.configureLine(line, plot_config)

        self.emit(SIGNAL('plotSelectionChanged(array)'), self.selected_lines)
        self.canvas.draw()


    #@print_timing
    @widgets.util.may_take_a_long_time
    def drawPlot(self):
        self.axes.cla()
        self.lines = []

        name = self.data.getName()
        key_index = self.data.getKeyIndex()

        if not key_index is None:
            name = "%s (%s)" % (name, key_index)

        self.axes.set_title(name)

        if self.data.hasInvertedYAxis() and not self.axes.yaxis_inverted():
            self.axes.invert_yaxis()
        elif not self.data.hasInvertedYAxis() and self.axes.yaxis_inverted():
            self.axes.invert_yaxis()
                

        for annotation in self.annotations:
            self.axes.add_artist(annotation)

        selected_members = []

        for selected_line in self.selected_lines:
            selected_members.append(selected_line.get_gid())

        self.selected_lines = []

        for member in self.data.x_data.keys():
            x, y, x_std, y_std = self.setupData(self.data.x_data[member], self.data.y_data[member])


            if member in selected_members:
                plot_config = self.selected_plot_config
                selected = True
            else:
                plot_config = self.plot_config
                selected = False

            if self.data.getXDataType() == "time":
                line = self.plotter.plot_date(self.axes, plot_config, x, y)
            else:
                line = self.plotter.plot(self.axes, plot_config, x, y)

            if selected:
                self.selected_lines.append(line)

            line.set_gid(member)
            self.lines.append(line)


        if not self.data.obs_x is None and not self.data.obs_y is None:
            x, y, x_std, y_std = self.setupData(self.data.obs_x, self.data.obs_y, self.data.obs_std_x, self.data.obs_std_y)

            if self.data.getXDataType() == "time":
                self.plotter.plot_date(self.axes, self.observation_plot_config, x, y)
            else:
                self.plotter.plot(self.axes, self.observation_plot_config, x, y)

            if (not self.data.obs_std_x is None or not self.data.obs_std_y is None):
                if self.std_plot_config.is_visible:
                    if self.data.getXDataType() == "time":
                        if not y_std is None:
                            self.plotter.plot_date(self.axes, self.std_plot_config, x, y - y_std)
                            self.plotter.plot_date(self.axes, self.std_plot_config, x, y + y_std)
                        elif not x_std is None:
                            self.plotter.plot_date(self.axes, self.std_plot_config, x - x_std, y)
                            self.plotter.plot_date(self.axes, self.std_plot_config, x + x_std, y)
                    else:
                        if not y_std is None:
                            self.plotter.plot(self.axes, self.std_plot_config, x, y - y_std)
                            self.plotter.plot(self.axes, self.std_plot_config, x, y + y_std)
                        elif not x_std is None:
                            self.plotter.plot(self.axes, self.std_plot_config, x - x_std, y)
                            self.plotter.plot(self.axes, self.std_plot_config, x + x_std, y)

                if  self.errorbar_plot_config.is_visible:
                    self.plotter.plot_errorbar(self.axes, self.errorbar_plot_config, x, y, x_std, y_std)

           
        if not self.data.refcase_x is None and not self.data.refcase_y is None and self.refcase_plot_config.is_visible:
            x, y, x_std, y_std = self.setupData(self.data.refcase_x, self.data.refcase_y)

            if self.data.getXDataType() == "time":
                self.plotter.plot_date(self.axes, self.refcase_plot_config, x, y)

                
        self.xlimits = self.axes.get_xlim()
        #self.axes.set_xlim(xlim[0] - 30, xlim[1] + 30)

        if self.data.getXDataType() == "time":
            #years = matplotlib.dates.YearLocator()   # every year
            #months = matplotlib.dates.MonthLocator()  # every month
            #yearsFmt = matplotlib.dates.DateFormatter('%b %y')
            yearsFmt = matplotlib.dates.DateFormatter('%b \'%Y')
            #monthFmt = matplotlib.dates.DateFormatter('%b')
            #self.axes.xaxis.set_major_locator(years)
            self.axes.xaxis.set_major_formatter(yearsFmt)
            self.fig.autofmt_xdate()
            #self.axes.xaxis.set_minor_locator(months)
            #self.axes.xaxis.set_minor_formatter(monthFmt)
            #self.axes.xaxis.set_major_locator(AutoDateLocator())
            #self.axes.xaxis.set_minor_locator(AutoDateLocator())

        #number_formatter = matplotlib.ticker.FormatStrFormatter("%f")
        number_formatter = matplotlib.ticker.ScalarFormatter(useOffset=False)
        number_formatter.set_scientific(True)
        #number_formatter.set_powerlimits((5, -5))

        self.axes.yaxis.set_major_formatter(number_formatter)
        self.setXViewFactors(self.xminf, self.xmaxf, False)

        self.canvas.draw()

    def setupData(self, x, y, std_x = None, std_y = None):
        if self.data.getXDataType() == "time":
            x = [t.datetime() for t in x]

        if not std_x is None:
            std_x = numpy.array(std_x)

        if not std_y is None:
            std_y = numpy.array(std_y)
        
        x = numpy.array(x)
        y = numpy.array(y)

        return x, y, std_x, std_y

        
    def resizeEvent(self, event):
        QFrame.resizeEvent(self, event)
        self.canvas.resize(event.size().width(), event.size().height())

    def setData(self, data):
        self.data = data

    def setXViewFactors(self, xminf, xmaxf, draw=True):
        self.xminf = xminf
        self.xmaxf = xmaxf

        if self.data.getXDataType() == "time":
            x_min = self.convertDate(self.data.x_min)
            x_max = self.convertDate(self.data.x_max)

            if not x_min is None and not x_max is None:
                range = x_max - x_min
                self.axes.set_xlim(x_min + xminf * range - 60, x_min + xmaxf * range + 60)
        else:
            x_min = self.data.x_min
            x_max = self.data.x_max
            
            if not x_min is None and not x_max is None:
                range = x_max - x_min
                self.axes.set_xlim(x_min + xminf * range - range*0.05, x_min + xmaxf * range + range*0.05)

        if draw:
            self.canvas.draw()

    def convertDate(self, ert_time):
        if ert_time is None:
            ert_time = time_t(0)
            
        return matplotlib.dates.date2num(ert_time.datetime())

    def save(self):
        if not os.path.exists(self.plot_path):
            os.makedirs(self.plot_path)
            
        path = self.plot_path + "/" + self.axes.get_title()
        self.fig.savefig(path + ".png", dpi=300, format="png")
        self.fig.savefig(path + ".pdf", dpi=300, format="pdf")

    def setPlotPath(self, plot_path):
        self.plot_path = plot_path

    def clearSelection(self):
        for line in self.selected_lines:
            self.configureLine(line, self.plot_config)

        self.selected_lines = []

        self.emit(SIGNAL('plotSelectionChanged(array)'), self.selected_lines)
        self.canvas.draw()

    def displayToolTip(self, event):
        if not self.data is None and not event.xdata is None and not event.ydata is None:
            if self.data.getXDataType() == "time":
                date = matplotlib.dates.num2date(event.xdata)
                self.setToolTip("x: %s y: %04f" % (date.strftime("%d/%m-%Y"), event.ydata))
            else:
                self.setToolTip("x: %04f y: %04f" % (event.xdata, event.ydata))
        else:
            self.setToolTip("")

class MouseHandler:

    def __init__(self, plot_view):
        self.plot_view = plot_view
        self.fig = plot_view.fig
        self.axes = plot_view.axes


        plot_view.fig.canvas.mpl_connect('button_press_event', self.on_press)
        plot_view.fig.canvas.mpl_connect('button_release_event', self.on_release)
        plot_view.fig.canvas.mpl_connect('pick_event', self.on_pick)
        plot_view.fig.canvas.mpl_connect('motion_notify_event', self.motion_notify_event)

        self.button_position = None
        self.artist = None

    def on_press(self, event):
        if event.button == 3 and self.artist is None and not event.xdata is None and not event.ydata is None:
            label, success = QInputDialog.getText(self.plot_view, "New label", "Enter label:")

            if success and not str(label).strip() == "":
                coord = (event.xdata, event.ydata)
                arrow = dict(arrowstyle="->", connectionstyle="arc3,rad=.2")
                annotation = self.axes.annotate(str(label), coord, xytext=None, xycoords='data', textcoords='data', arrowprops=arrow, picker=1)
                self.plot_view.annotations.append(annotation)
                self.plot_view.canvas.draw()

    def on_release(self, event):
        self.button_position = None
        self.artist = None

    def on_pick(self, event):
        if isinstance(event.artist, matplotlib.lines.Line2D) and event.mouseevent.button == 1:
            self.plot_view.toggleLine(event.artist)
        elif isinstance(event.artist, matplotlib.text.Annotation) and event.mouseevent.button == 1:
            self.artist = event.artist
            self.button_position = (event.mouseevent.x, event.mouseevent.y)
        elif isinstance(event.artist, matplotlib.text.Annotation) and event.mouseevent.button == 3:
            self.artist = event.artist
            self.axes.texts.remove(event.artist)
            self.plot_view.annotations.remove(event.artist)
            self.plot_view.canvas.draw()

    def motion_notify_event(self, event):
        if self.artist is None:
            self.plot_view.displayToolTip(event)
        elif isinstance(self.artist, matplotlib.text.Annotation):
            if not event.xdata is None and not event.ydata is None:
                self.artist.xytext = (event.xdata, event.ydata)
                self.plot_view.canvas.draw()


