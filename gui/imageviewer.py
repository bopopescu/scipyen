# -*- coding: utf-8 -*-
'''
Image viewer: designed for viewing vigra arrays (primarily)
Based on GraphicsView Qt framework
Supports cursors defined in pictgui module.
Dependencies:
python >= 3.4
PyQt5
vigra built python 3)
boost C++ libraries built against python 3 (for building vigra against python3)
numpy (for python 3)
quantities (for python 3)
matplotlib for colormaps & colors

'''

# NOTE: 2017-05-25 08:47:01
# TODO:
# 1. colormap editor
# 
# 2. remember last applied colormap or rather make a default colormap configurable
# 
# 3. cursors:
#
# 3.1. really constrain the movement of cursors within the image boundaries; -- DONE
# 
# 3.2. implement edit cursor properties dialog
# 
# 3.3. streamline cursor creation from a neo.Epoch -- check if they support
#      spatial units, not just time -- it apparently DOES WORK:
# 
#      epc = neo.Epoch(times=[15, 20, 25], durations=[5, 5, 5], labes=["r0", "r1", "r2"], units=pq.um, name="SpineROIs")
# 
# 
# 3.4  implement the reverse operation of generating an epoch from an array of 
#      cursors
#
# 3.5 for 3.3 and 3.4 be mindful that we can have epochs in BOTH directions, in
#      an image -- I MIGHT contemplate "epochs" in the higher dimensions, for where 
#      this makes sense
# 
# 
# 4. ROIs: probably the best approach is to inherit from QGraphicsObject, see GraphicsObject
# 

# KISS = Keep It Simple, Stupid !

#### BEGIN core python modules
from __future__ import print_function
import sys, os, numbers, traceback, inspect, threading, warnings
import weakref, copy
from collections import ChainMap, namedtuple, defaultdict
from enum import Enum, IntEnum

#### END core python modules

#### BEGIN 3rd party modules
import numpy as np
import quantities as pq
import pyqtgraph as pgraph
import neo
import vigra
#import vigra.pyqt 
import matplotlib as mpl
from matplotlib import cm, colors

try:
    import cmocean # some cool palettes/luts
except:
    pass

from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Q_ENUMS, Q_FLAGS, pyqtProperty
from PyQt5.uic import loadUiType as __loadUiType__

#### END 3rd party modules

#### BEGIN pict.core modules
from core import utilities
from core.utilities import safeWrapper
from core import strutils as strutils
from core import datatypes as dt
#from core import neo
#from core import metaclass_solver
#### END pict.core modules

#### BEGIN pict.iolib modules
from iolib import pictio as pio
#### END pict.iolib modules

#### BEGIN pict.gui modules
from .scipyenviewer import ScipyenViewer, ScipyenFrameViewer

from . import signalviewer as sv
from . import pictgui as pgui
from . import custom_colormaps as customcm
from . import quickdialog
#### END pict.gui modules

mpl.rcParams['backend']='Qt5Agg'

#__viewer_info__ = {"alias": "iv", "class": "ImageViewer"}


# NOTE: 2017-06-22 14:22:00 added custom color maps
customcm.register_custom_colormaps()


colormaps = cm.cmap_d.copy() # now this has all mpl and custom colormaps

# NOTE: 2019-03-26 09:54:59
# add a "None" colormap NOW (actually, map it to "gray")
colormaps["None"] = cm.cmap_d["gray"]

try:
    colormaps.update(cmocean.cm.cmap_d)
except:
    pass

#colormapnames = [n for n in colormaps.keys()]
#colormapnames.sort()
#colormapnames.insert(0, "None") #prepend None to remove any applied colormap


if sys.version_info[0] >= 3:
    xrange = range

__module_path__ = os.path.abspath(os.path.dirname(__file__))

#print(__module_path__)

#import qimage2ndarray 
#from qimage2ndarray import gray2qimage, array2qimage, alpha_view, rgb_view, byte_view

# don't use this yet, until we fully understand how to deal with VigraQt colormap
#mechanism from Python side
Ui_EditColorMapWidget, QWidget = __loadUiType__(os.path.join(__module_path__,"editcolormap2.ui"))

#Ui_ItemsListDialog, QDialog = __loadUiType__(os.path.join(__module_path__,'itemslistdialog.ui'))

# used for ImageWindow and ImageWindow, below
Ui_ImageViewerWindow, QMainWindow = __loadUiType__(os.path.join(__module_path__,'imageviewer.ui'))

Ui_GraphicsImageViewerWidget, QWidget = __loadUiType__(os.path.join(__module_path__,'graphicsimageviewer.ui'))

Ui_AxisCalibrationDialog, QDialog = __loadUiType__(os.path.join(__module_path__, "axescalibrationdialog.ui"))

Ui_TransformImageValueDialog, QDialog = __loadUiType__(os.path.join(__module_path__,"transformimagevaluedialog.ui"))

####don't use this yet, until we fully understand how to deal with VigraQt colormap
####mechanism from Python side
class ColorMapEditor(QWidget, Ui_EditColorMapWidget):
 def __init__(self, parent = None):
   super(ColorMapEditor, self).__init__(parent);
   self.setupUi(self);
   self.colormapeditor = VigraQt.ColorMapEditor(EditColorMapWidget);
   self.colormapeditor.setObjectName(_fromUtf8("ColorMapEditor"));
   self.verticalLayout.addWidget(self.colormapeditor);

    
class ComplexDisplay(Enum):
    """
    """
    real  = 1
    imag  = 2
    dual  = 3
    abs   = 4
    mod   = 4
    phase = 5
    arg   = 5
    
class IntensityCalibrationLegend(pgraph.graphicsItems.GraphicsWidget.GraphicsWidget):
    def __init__(self, image):
        GraphicsWidget.__init__(self)
        if not isinstance(image, vigra.VigraArray):
            raise TypeError("Expectign a VigraArray; got %s instead" % type(image).__name__)
        
        #if 
        
        w = image.width
        h = image.height
        self.layout = QtGui.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setSpacing(0)
        self.vb = pgraph.ViewBox(parent=self)
        self.vb.setMaximumWidth(w)
        self.vb.setMinimumWidth(w)
        self.vb.setMaximumHeight(h)
        self.vb.setMinimumHeight(h)
        self.axis = AxisItem('left', linkView=self.vb, maxTickLength=-10, parent=self)
        self.layout.addItem(self.vb, 0, 0)
        self.layout.addItem(self.axis, 0, 1)
        
        
class ImageBrightnessDialog(QDialog, Ui_TransformImageValueDialog):
    """
    """
    signalAutoRange             = pyqtSignal(name="signalAutoRange")
    signalDefaultRange          = pyqtSignal(name="signalDefaultRange")
    signalApply                 = pyqtSignal(name="signalApply")
    signalFactorValueChanged    = pyqtSignal(float, name="signalFactorValueChanged")
    signalMinRangeValueChanged  = pyqtSignal(float, name="signalMinRangeValueChanged")
    signalMaxRangeValueChanged  = pyqtSignal(float, name="signalMaxRangeValueChanged")
    
    
    
    def __init__(self, parent=None, title=None):
        super(ImageBrightnessDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.factorLabel.setText("Brightness")
        
        if title is None:
            self.setWindowTitle("Adjust Brightness")
        else:
            self.setWindowTitle("Adjust Brightness for %s" % title)
            
        
        self.autoRangePushButton.clicked.connect(self.slot_requestAutoRange)
        self.defaultRangePushButton.clicked.connect(self.slot_requestDefaultRange)
        self.applyPushButton.clicked.connect(self.slot_requestApplyToData)
        self.factorSpinBox.valueChanged[float].connect(self.slot_sendNewFactorValue)
        self.rangeMinSpinBox.valueChanged[float].connect(self.slot_sendNewRangeMinValue)
        self.rangeMaxSpinBox.valueChanged[float].connect(self.slot_sendNewRangeMaxValue)
        
    @pyqtSlot()
    def slot_requestAutoRange(self):
        self.signalAutoRange.emit()
        
    @pyqtSlot()
    def slot_requestDefaultRange(self):
        self.signalDefaultRange.emit()
    
    @pyqtSlot()
    def slot_requestApplyToData(self):
        self.signalApply.emit()
        
    @pyqtSlot(float)
    def slot_sendNewFactorValue(self, val):
        self.signalFactorValueChanged.emit(val)
        
    @pyqtSlot(float)
    def slot_sendNewRangeMinValue(self, val):
        self.signalMinRangeValueChanged.emit(val)
        
    @pyqtSlot(float)
    def slot_sendNewRangeMaxValue(self, val):
        self.signalMaxRangeValueChanged.emit(val)
        
    @pyqtSlot(float)
    def slot_newFactorValueReceived(self, val):
        self.factorSpinBox.setValue(val)
        
    @pyqtSlot(float)
    def slot_newMinRangeValueReceived(self, val):
        self.rangeMinSpinBox.setValue(val)
        
    @pyqtSlot(float)
    def slot_newMaxRangeValueReceived(self, val):
        self.rangeMaxSpinBox.setValue(val)
        
    

class AxesCalibrationDialog(QDialog, Ui_AxisCalibrationDialog):
    def __init__(self, image, pWin=None, parent=None):
        super(AxesCalibrationDialog, self).__init__(parent)
        
        self.arrayshape=None
        self._data_=None
        
        if isinstance(image, vigra.AxisTags):
            self.axistags = image
            self._data_ = None
            
        elif isinstance(image, vigra.VigraArray):
            self.axistags = image.axistags
            self.arrayshape = image.shape
            self._data_ = image
            
        else:
            raise TypeError("A VigraArray instance was expected; got %d instead" % (type(image).__name__))
        
        #self._data_ = image
        
        self.resolution = 1.0
        self.origin = 0.0
        self.units = dt.pixel_unit
        
        self.selectedAxisIndex = 0
        
        self.axisMetaData = dict()
        
        for axisInfo in self.axistags:
            self.axisMetaData[axisInfo.key]["calibration"] = dt.AxisCalibration(axisInfo)
                
            self.axisMetaData[axisInfo.key]["description"] = dt.AxisCalibration.removeCalibrationFromString(axisInfo.description)

        self.units          = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].units
        self.origin         = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].origin
        self.resolution     = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].resolution
        self.description    = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["description"]
        
        self._configureGUI_()
        
    def _configureGUI_(self):
        self.setupUi(self)
        
        self.setWindowTitle("Calibrate axes")
        
        self.axisIndexSpinBox.setMaximum(len(self.axistags) -1)
        
        self.axisIndexSpinBox.setValue(self.selectedAxisIndex)
        
        if self.arrayshape is None:
            self.axisInfoLabel.setText("Axis key: %s, type: %s" % (self.axistags[self.selectedAxisIndex].key, dt.defaultAxisTypeName(self.axistags[self.selectedAxisIndex])))
        else:
            self.axisInfoLabel.setText("Axis key: %s, type: %s, length: %d" % (self.axistags[self.selectedAxisIndex].key, dt.defaultAxisTypeName(self.axistags[self.selectedAxisIndex]), self.arrayshape[self.selectedAxisIndex]))
            
        self.unitsLineEdit.setClearButtonEnabled(True)
        
        self.unitsLineEdit.undoAvailable = True
        
        self.unitsLineEdit.redoAvailable = True
        
        self.unitsLineEdit.setText(self.units.__str__().split()[1])
        
        #self.unitsLineEdit.setValidator(dt.UnitsStringValidator())
        
        self.unitsLineEdit.editingFinished.connect(self.slot_unitsChanged)
        
        #self.unitsLineEdit.returnPressed.connect(self.slot_unitsChanged)
        
        self.axisIndexSpinBox.valueChanged[int].connect(self.slot_axisIndexChanged)
        
        self.originSpinBox.setValue(self.origin)
        
        self.originSpinBox.valueChanged[float].connect(self.slot_originChanged)
        
        self.resolutionRadioButton.setDown(True)
        
        self.resolutionRadioButton.toggled[bool].connect(self.slot_resolutionChecked)
        
        self.resolutionSpinBox.setValue(self.resolution)
        
        self.resolutionSpinBox.setReadOnly(True)
        
        self.pixelsDistanceRadioButton.toggled[bool].connect(self.slot_pixelsDistanceChecked)
        
        self.calibratedDistanceRadioButton.toggled[bool].connect(self.slot_calibratedDistanceChecked)
        
        self.resolutionSpinBox.valueChanged[float].connect(self.slot_resolutionChanged)
        
        self.pixelsDistanceSpinBox.valueChanged[int].connect(self.slot_pixelDistanceChanged)
        
        self.calibratedDistanceSpinBox.valueChanged[float].connect(self.slot_calibratedDistanceChanged)
        
        #self.axisDescriptionEdit.setUndoRedoEnabled(True)
        
        self.axisDescriptionEdit.plainText = self.description
        
        self.axisDescriptionEdit.textChanged.connect(self.slot_descriptionChanged)
        
    def updateFieldsFromAxis(self):
        self.units          = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].units
        self.origin         = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].origin
        self.resolution     = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].resolution
        self.description    = self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["description"]

        if self.arrayshape is None:
            self.axisInfoLabel.setText("Axis key: %s, type: %s" % (self.axistags[self.selectedAxisIndex].key, dt.defaultAxisTypeName(self.axistags[self.selectedAxisIndex])))
        else:
            self.axisInfoLabel.setText("Axis key: %s, type: %s, length: %d" % (self.axistags[self.selectedAxisIndex].key, dt.defaultAxisTypeName(self.axistags[self.selectedAxisIndex]), self.arrayshape[self.selectedAxisIndex]))
            
        self.unitsLineEdit.setText(self.units.__str__().split()[1])
        self.originSpinBox.setValue(self.origin)
        self.resolutionSpinBox.setValue(self.resolution)
        
        if self.resolutionRadioButton.isChecked():
            self.calibratedDistanceSpinBox.setValue(self.resolution * self.pixelsDistanceSpinBox.value())
            
        else:
            self.slot_resolutionChanged(self.resolution)
    
        self.axisDescriptionEdit.clear()
        self.axisDescriptionEdit.plainText = self.description
        
    @pyqtSlot(int)
    @safeWrapper
    def slot_axisIndexChanged(self, value):
        self.selectedAxisIndex = value
        self.updateFieldsFromAxis()
        #self.slot_generateCalibration()
        
    @pyqtSlot()
    @safeWrapper
    def slot_unitsChanged(self):
        try:
            self.units = eval("1*%s" % (self.unitsLineEdit.text()), pq.__dict__)
            #print("%s --> %s" % (self.unitsLineEdit.text(),self.units))
        except:
            pass
            #print("Try again!")
        
        self.slot_generateCalibration()

    @pyqtSlot(bool)
    @safeWrapper
    def slot_resolutionChecked(self, value):
        self.resolutionSpinBox.setReadOnly(value)
        self.pixelsDistanceSpinBox.setReadOnly(not value)
        self.calibratedDistanceSpinBox.setReadOnly(not value)
    
    @pyqtSlot(bool)
    @safeWrapper
    def slot_pixelsDistanceChecked(self, value):
        self.pixelsDistanceSpinBox.setReadOnly(value)
        self.resolutionSpinBox.setReadOnly(not value)
        self.calibratedDistanceSpinBox.setReadOnly(not value)
        
    @pyqtSlot(bool)
    @safeWrapper
    def slot_calibratedDistanceChecked(self, value):
        self.calibratedDistanceSpinBox.setReadOnly(value)
        self.pixelsDistanceSpinBox.setReadOnly(not value)
        self.resolutionSpinBox.setReadOnly(value)
    
    @pyqtSlot()
    @safeWrapper
    def slot_generateCalibration(self):
        self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].units = \
            eval("1*%s" % (self.unitsLineEdit.text()), pq.__dict__)
        
        self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].origin = \
            self.origin
        
        self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["calibration"].resolution = \
            self.resolution
        
        self.axisMetaData[self.axistags[self.selectedAxisIndex].key]["description"] = \
            self.description
        
        
    
    @pyqtSlot(float)
    @safeWrapper
    def slot_originChanged(self, value):
        self.origin = value
        
        self.slot_generateCalibration()


    @pyqtSlot(float)
    @safeWrapper
    def slot_resolutionChanged(self, value):
        if self.pixelsDistanceRadioButton.isChecked(): # calculate distance in pixels
            self.pixelsDistanceSpinBox.setValue(int(self.calibratedDistanceSpinBox.value() // value))
            
        elif self.calibratedDistanceRadioButton.isChecked(): # calculate calibrated distance
            self.calibratedDistanceSpinBox.setValue(value * self.pixelsDistanceSpinBox.value())
            
        self.resolution = value
        
        self.slot_generateCalibration()

    @pyqtSlot(int)
    @safeWrapper
    def slot_pixelDistanceChanged(self, value):
        if self.resolutionRadioButton.isChecked(): # calculate resolution
            self.resolutionSpinBox.setValue(self.calibratedDistanceSpinBox.value() / value)
            
            self.resolution = self.resolutionSpinBox.value()
            
        elif self.calibratedDistanceRadioButton.isChecked(): # calculate calibrated distance
            self.calibratedDistanceSpinBox.setValue(self.resolutionSpinBox.value() * value)
    
        self.slot_generateCalibration()
        
    @pyqtSlot(float)
    @safeWrapper
    def slot_calibratedDistanceChanged(self, value):
        if self.resolutionRadioButton.isChecked(): # calculate resolution
            self.resolutionSpinBox.setValue(value / self.pixelsDistanceSpinBox.value())
            
            self.resolution = self.resolutionSpinBox.value()
            
        elif self.pixelsDistanceSpinBox.isChecked(): # calculate pixels distance
            self.pixelsDistanceSpinBox.setValue(int(value // self.resolutionSpinBox.value()))
        
        self.slot_generateCalibration()
        
    @pyqtSlot()
    @safeWrapper
    def slot_descriptionChanged(self):
        self.description = self.axisDescriptionEdit.toPlainText()
        self.slot_generateCalibration()

    def calculateResolution(self, pixels=None, distance=None):
        if pixels is None:
            pixels = self.pixelsDistanceSpinBox.value()
            
        if distance is None:
            distance = self.calibratedDistanceSpinBox.value()
            
        self.resolution = distance / pixels
        
        self.resolutionSpinBox.setValue(self.resolution)

        self.slot_generateCalibration()
        
        

class GraphicsImageViewerScene(QtWidgets.QGraphicsScene):
    signalMouseAt = pyqtSignal(int,int,name="signalMouseAt")
    
    signalMouseLeave = pyqtSignal()
    
    #signalDeselectGraphics = pyqtSignal()

    def __init__(self, gpix=None, rect = None, **args):
        if rect is not None:
            super(GraphicsImageViewerScene, self).__init__(rect = rect, **args)
            
        else:
            super(GraphicsImageViewerScene, self).__init__(**args)
            
        self.__gpixitem__ = None
        
        self.graphicsItemDragMode=False

        #self._contextMenu = QtWidgets.QMenu("Scene Menu", super())
        
        #self._addCursorAction = self._contextMenu.addAction("Add cursor")
        #self._addCursorAction.triggered.connect(self._slotAddCursor)
        
        
    ####
    # public methods
    ####
    
    @property
    def rootImage(self):
        return self.__gpixitem__
    
    @rootImage.setter
    def rootImage(self, gpix):
        if gpix is None:
            return
        
        if self.__gpixitem__ is not None:
            super().removeItem(self.__gpixitem__)
            
        nItems = len(self.items())
        
        super().addItem(gpix)
        
        if nItems > 0:
            gpix.setZValue(-nItems-1)
            
        self.setSceneRect(gpix.boundingRect())
        gpix.setVisible(True)
        self.__gpixitem__ = gpix
        #self.__gpixitem__.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        
    def clear(self):
        super(GraphicsImageViewerScene, self).clear()
        self.__gpixitem__ = None
        
    def setRootImage(self, gpix):
        #print("scene setRootImage: %s" % gpix)
        self.rootImage=gpix
        
    def addItem(self, item, picAsRoot=True):
        #print("scene addItem %s" % item)
        if isinstance(item, QtWidgets.QGraphicsPixmapItem) and picAsRoot:
            self.rootImage = item
        else:
            super().addItem(item)
            item.setVisible(True)
            
    def mouseMoveEvent(self, evt):
        """Emits signalMouseAt(x,y) if event position is inside the scene.
        """
        
        if self.__gpixitem__ is None:
            return
        
        if self.sceneRect().contains(evt.scenePos().x(), evt.scenePos().y()):
            self.signalMouseAt.emit(int(evt.scenePos().x()), int(evt.scenePos().y()))
            
        else:
            self.signalMouseLeave.emit()
            
        super().mouseMoveEvent(evt)
        evt.accept()
        
    def mousePressEvent(self, evt):
        super().mousePressEvent(evt)
        evt.accept()
        
        
    def mouseReleaseEvent(self, evt):
        super().mouseReleaseEvent(evt)
        evt.accept()
        
    def hoverMoveEvent(self, evt):
        if self.__gpixitem__ is None:
            return
        
        super().event(evt)
        
        if self.sceneRect().contains(evt.pos().x(), evt.pos().y()):
            self.signalMouseAt.emit(int(evt.pos().x()), int(evt.pos().y()))
            
    def wheelEvent(self, evt):
        evt.ignore()
        
#"class" ImageGraphicsView(QtWidgets.QGraphicsView):
    #"""
    #TODO contemplate this to customize the graphicsivew in the GraphicsImageViewerWidget
    #(_imageGraphicsView member)
    #"""
    #"def" __init__(*args, **kwargs):
        #super(ImageGraphicsView, self).__init__(*args, **kwargs)
        
        
        
class GraphicsImageViewerWidget(QWidget, Ui_GraphicsImageViewerWidget):
    """
    A simple image view widget based on Qt5 graphics view framework
    
    The widget does not own the data but a pixmap copy of it; therefore data values 
    under the cursors must be received via signal/slot mechanism from the parent window.
    Signals from the underlying scene are exposed as public APIand shoul be connected
    to appropriate slots in the container window
    """
    
    # NOTE: 2017-03-23 13:55:36
    # While in C++ I had subclassed the QGraphicsView to a custom derived class
    # in python/PyQt5 I cannot "promote" the QGraphicsView widget in the
    # UI class to this derived class
    # TODO Therefore the functionality of said derived class must be somehow 
    # implemented here
    
    # TODO add functionality from ExtendedImageViewer class
    
    
    ####
    # signals
    ####
    signalMouseAt             = pyqtSignal(int, int, name="signalMouseAt")
    signalCursorAt            = pyqtSignal(str, list, name="signalCursorAt")
    signalZoomChanged         = pyqtSignal(float, name="signalZoomChanged")
    signalCursorPosChanged    = pyqtSignal(str, "QPointF", name="signalCursorPosChanged")
    signalCursorLinkRequest   = pyqtSignal(pgui.GraphicsObject, name="signalCursorLinkRequest")
    signalCursorUnlinkRequest = pyqtSignal(pgui.GraphicsObject, name="signalCursorUnlinkRequest")
    signalCursorAdded         = pyqtSignal(object, name="signalCursorAdded")
    signalCursorChanged       = pyqtSignal(object, name="signalCursorChanged")
    signalCursorRemoved       = pyqtSignal(object, name="signalCursorRemoved")
    signalCursorSelected      = pyqtSignal(object, name="signalCursorSelected")
    signalRoiAdded            = pyqtSignal(object, name="signalRoiAdded")
    signalRoiChanged          = pyqtSignal(object, name="signalRoiChanged")
    signalRoiRemoved          = pyqtSignal(object, name="signalRoiRemoved")
    signalRoiSelected         = pyqtSignal(object, name="signalRoiSelected")
    signalGraphicsDeselected  = pyqtSignal()
    
    ####
    # constructor
    ####
    
    def __init__(self, img=None, parent=None, imageViewer=None):
        super(GraphicsImageViewerWidget, self).__init__(parent=parent)
        self._configureGUI_()
        
        self.__zoomVal__ = 1.0
        self._minZoom__ = 0.1
        self.__maxZoom__ = 100
        
        self.__escape_pressed___ = False
        self.__mouse_pressed___ = False
        
        self.__last_mouse_click_lmb__ = None
        
        self.__interactiveZoom__ = False
        
        self.__defaultCursorWindow__ = 10.0
        self.__defaultCursorRadius__ = 0.5

        self.__cursorWindow__ = self.__defaultCursorWindow__
        self.__cursorRadius__ = self.__defaultCursorRadius__

        # NOTE: 2017-08-10 13:45:17
        # make separate dictionaries for each roi type -- NOT a chainmap!
        self.__graphicsObjects__ = dict([(k.value, dict()) for k in pgui.GraphicsObjectType])
        
        # grab dictionaries for cursor types in a chain map
        cursorTypeInts = [t.value for t in pgui.GraphicsObjectType if \
            t.value < pgui.GraphicsObjectType.allCursorTypes]
        
        self.__cursors__ = ChainMap() # almost empty ChainMap
        self.__cursors__.maps.clear() # make sure it is empty
        
        for k in cursorTypeInts:    # now chain up the cursor dictionaries
            self.__cursors__.maps.append(self.__graphicsObjects__[k])
        
        # do the same for roi types
        roiTypeInts = [t.value for t in pgui.GraphicsObjectType if \
            t.value > pgui.GraphicsObjectType.allCursorTypes]
        
        self.__rois__ = ChainMap()
        self.__rois__.maps.clear()
        
        # NOTE: 2017-11-28 22:25:33
        # maps attribute is a list !!!
        # would ChainMap.new_child() be more appropriate, below?
        for k in roiTypeInts:
            self.__rois__.maps.append(self.__graphicsObjects__[k])

        #### NOTE: 2017-11-26 22:53:12
        ####
        #### not needed anymore: coordinate linking between instances of 
        #### GraphicsObject of the same type is now handled by the instances
        #### themselves
        #self._linkedCrosshairCursors = []
        #self._linkedHorizontalCursors = []
        #self._linkedVerticalCursors = []
        #self._linkedRois = []
        
        self.selectedCursor = None
        
        #self.__rois__ = dict()
        
        self.selectedRoi = None
        
        # NOTE: 2017-06-27 23:10:05
        # hack to get context menu working for non-selected cursors
        self._cursorContextMenuSourceId = None 
        
        
        self.__scene__ = GraphicsImageViewerScene(parent=self)
        self.__scene__.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)
        
        self._imageGraphicsView.setScene(self.__scene__)
        
        #NOTE: 2017-03-25 22:31:12
        # this is unnecessary: just connect the signal from the scene to the 
        # container of this widget direcly (we get access to the scene by calling self.scene())
        #self.__scene__.signalMouseAt[int,int].connect(self._reportPixelValueAtMousePosInWidget)
        
        if img is not None:
            if isinstance(img, QtGui.QImage):
                self.__scene__.rootImage = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(img))
                
            elif isinstance(img, QtGui.QPixmap):
                self.__scene__.rootImage = QtWidgets.QGraphicsPixmapItem(img)

        self.__image_viewer__ = imageViewer
    ####
    # private methods
    ####
    
    def _configureGUI_(self):
        self.setupUi(self)
        self._imageGraphicsView.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self._imageGraphicsView.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self._topLabel.clear()
        
    def _zoomView(self, val):
        self._imageGraphicsView.resetTransform()
        self._imageGraphicsView.scale(val, val)
        self.__zoomVal__ = val
        self.signalZoomChanged[float].emit(self.__zoomVal__)
        
    def _cursorEditor(self, crsId=None):
        if len(self.__cursors__) == 0:
            return
        
        if crsId is None:
            cselectDlg = pgui.ItemsListDialog(self, sorted([cId for cId in self.__cursors__.keys()]), "Select cursor")
            
            a = cselectDlg.exec_()
            
            if a == QtWidgets.QDialog.Accepted:
                crsId = cselectDlg.selectedItemText
            else:
                return
        
        cursor = self.__cursors__[crsId]
        
        cursor_type = cursor.objectType
        
        cDict = self.__graphicsObjects__[cursor_type]
        
        d = quickdialog.QuickDialog(self, "Edit cursor %s" % cursor.name)
        #d = vigra.pyqt.quickdialog.QuickDialog(self, "Edit cursor %s" % cursor.name)
        d.promptWidgets = list()
        
        namePrompt = quickdialog.StringInput(d, "New label:")
        #namePrompt = vigra.pyqt.quickdialog.StringInput(d, "New label:")
        namePrompt.variable.setClearButtonEnabled(True)
        namePrompt.variable.redoAvailable=True
        namePrompt.variable.undoAvailable=True
        namePrompt.setText(cursor.ID)
        
        d.promptWidgets.append(namePrompt)
        
        showsPositionCheckBox = quickdialog.CheckBox(d, "Label shows position")
        #showsPositionCheckBox = vigra.pyqt.quickdialog.CheckBox(d, "Label shows position")
        showsPositionCheckBox.setChecked(cursor.labelShowsPosition)
        
        
        d.promptWidgets.append(showsPositionCheckBox)
        
        showsOpaqueLabel = quickdialog.CheckBox(d, "Opaque label")
        #showsOpaqueLabel = vigra.pyqt.quickdialog.CheckBox(d, "Opaque label")
        showsOpaqueLabel.setChecked(not cursor.hasTransparentLabel)
        
        d.promptWidgets.append(showsOpaqueLabel)
        
        if cursor.isVerticalCursor:
            promptX = quickdialog.FloatInput(d, "X coordinate (pixels):")
            #promptX = vigra.pyqt.quickdialog.FloatInput(d, "X coordinate (pixels):")
            promptX.variable.setClearButtonEnabled(True)
            promptX.variable.redoAvailable=True
            promptX.variable.undoAvailable=True
            promptX.setValue(cursor.x)
            d.promptWidgets.append(promptX)
        
            promptXWindow = quickdialog.FloatInput(d, "Horizontal window size (pixels):")
            #promptXWindow = vigra.pyqt.quickdialog.FloatInput(d, "Horizontal window size (pixels):")
            promptXWindow.variable.setClearButtonEnabled(True)
            promptXWindow.variable.redoAvailable=True
            promptXWindow.variable.undoAvailable=True
            promptXWindow.setValue(cursor.xwindow)
            d.promptWidgets.append(promptXWindow)
            
        elif cursor.isHorizontalCursor:
            promptY = quickdialog.FloatInput(d, "Y coordinate (pixels):")
            #promptY = vigra.pyqt.quickdialog.FloatInput(d, "Y coordinate (pixels):")
            promptY.variable.setClearButtonEnabled(True)
            promptY.variable.redoAvailable=True
            promptY.variable.undoAvailable=True
            promptY.setValue(cursor.y)
            d.promptWidgets.append(promptY)
            
            promptYWindow = quickdialog.FloatInput(d, "Vertical window size (pixels):")
            #promptYWindow = vigra.pyqt.quickdialog.FloatInput(d, "Vertical window size (pixels):")
            promptYWindow.variable.setClearButtonEnabled(True)
            promptYWindow.variable.redoAvailable=True
            promptYWindow.variable.undoAvailable=True
            promptYWindow.setValue(cursor.ywindow)
            d.promptWidgets.append(promptYWindow)
            
        else:
            promptX = quickdialog.FloatInput(d, "X coordinate:")
            #promptX = vigra.pyqt.quickdialog.FloatInput(d, "X coordinate:")
            promptX.variable.setClearButtonEnabled(True)
            promptX.variable.redoAvailable=True
            promptX.variable.undoAvailable=True
            promptX.setValue(cursor.x)
            d.promptWidgets.append(promptX)
            
            promptXWindow = quickdialog.FloatInput(d, "Horizontal window size:")
            #promptXWindow = vigra.pyqt.quickdialog.FloatInput(d, "Horizontal window size:")
            promptXWindow.variable.setClearButtonEnabled(True)
            promptXWindow.variable.redoAvailable=True
            promptXWindow.variable.undoAvailable=True
            promptXWindow.setValue(cursor.xwindow)
            d.promptWidgets.append(promptXWindow)
            
            promptY = quickdialog.FloatInput(d, "Y coordinate:")
            #promptY = vigra.pyqt.quickdialog.FloatInput(d, "Y coordinate:")
            promptY.variable.setClearButtonEnabled(True)
            promptY.variable.redoAvailable=True
            promptY.variable.undoAvailable=True
            promptY.setValue(cursor.y)
            d.promptWidgets.append(promptY)
            
            promptYWindow = quickdialog.FloatInput(d, "Vertical window size:")
            #promptYWindow = vigra.pyqt.quickdialog.FloatInput(d, "Vertical window size:")
            promptYWindow.variable.setClearButtonEnabled(True)
            promptYWindow.variable.redoAvailable=True
            promptYWindow.variable.undoAvailable=True
            promptYWindow.setValue(cursor.ywindow)
            d.promptWidgets.append(promptYWindow)
                
        
        framesWhereVisible = quickdialog.StringInput(d, "Visible frames:")
        #framesWhereVisible = vigra.pyqt.quickdialog.StringInput(d, "Visible frames:")
        framesWhereVisible.setToolTip("Enter comma-separated list of visible frames, the keyword 'all', or 'range(start,[stop,[step]]')")
        framesWhereVisible.setWhatsThis("Enter comma-separated list of visible frames, the keyword 'all', or 'range(start,[stop,[step]]')")
        
        if len(cursor.frameVisibility)==0:
            framesWhereVisible.setText("all")
            
        else:
            b = ""
            if len(cursor.frameVisibility):
                for f in cursor.frameVisibility[:-1]:
                    if f is None:
                        continue
                    
                    b += "%d, " % f
                    
                f = cursor.frameVisibility[-1]
                
                if f is not None:
                    b += "%d" % cursor.frameVisibility[-1]
                    
            if len(b.strip()) == 0:
                b = "all"
                
            framesWhereVisible.setText(b)

        d.promptWidgets.append(framesWhereVisible)
        
        linkToFramesCheckBox = quickdialog.CheckBox(d, "Link position to frame number")
        #linkToFramesCheckBox = vigra.pyqt.quickdialog.CheckBox(d, "Link position to frame number")
        
        #linkToFramesCheckBox.setChecked( not cursor.backend.hasCommonState)
        linkToFramesCheckBox.setChecked( len(cursor.backend.states) > 1)
        
        d.promptWidgets.append(linkToFramesCheckBox)
        
        for w in d.promptWidgets:
            #if not isinstance(w, vigra.pyqt.quickdialog.CheckBox):
            if not isinstance(w, quickdialog.CheckBox):
                w.variable.setClearButtonEnabled(True)
                w.variable.redoAvailable=True
                w.variable.undoAvailable=True

        if d.exec() == QtWidgets.QDialog.Accepted:
            old_name = cursor.name
            
            newName = namePrompt.text()
            
            if newName is not None and len(newName.strip()) > 0:
                if newName != old_name:
                    if newName in cDict:
                        QtWidgets.QMessageBox.critical(self, "Cursor name clash", "A cursor named %s already exists" % newName)
                        return
                    
            if cursor.isVerticalCursor:
                cursor.x = promptX.value()
                cursor.xwindow = promptXWindow.value()
                
            elif cursor.isHorizontalCursor:
                cursor.y = promptY.value()
                cursor.ywindow = promptYWindow.value()

            else:
                cursor.x = promptX.value()
                cursor.y = promptY.value()
                cursor.xwindow = promptXWindow.value()
                cursor.ywindow = promptYWindow.value()
        
            cursor.labelShowsPosition = showsPositionCheckBox.selection()
            
            cursor.setTransparentLabel(not showsOpaqueLabel.selection())
            
            
            newFrames = []
            
            txt = framesWhereVisible.text()
            
            #print("txt", txt)
            
            #print("GraphicsImageViewerWidget._cursorEditor imageViewer:", self.__image_viewer__)
            
            if len(txt.strip()) == 0:
                newFrames = []
                
            elif txt.strip().lower() == "all":
                if self.__image_viewer__ is not None:
                    #print("GraphicsImageViewerWidget._cursorEditor imageViewer.nFrames:", self.__image_viewer__.nFrames)
                    
                    newFrames = [f for f in range(self.__image_viewer__.nFrames)]
                    
                else:
                    newFrames = []
                
            elif txt.find("range") == 0:
                val = eval(txt)
                
                newFrames = [f for f in val]
                
            elif txt.find(":") > 0:
                try:
                    newFrames = [int(f_) for f_ in txt.split(":")]
                    if len(newFrames) > 3:
                        newFrames = []
                        
                    else:
                        newFrames = range(*newFrames)
                        
                except Exception as e:
                    traceback_print_exc()
                    
            else:
                try:
                    newFrames = [int(f_) for f_ in txt.split(",")]
                    
                except Exception as e:
                    traceback.print_exc()
                    
            #print(newFrames)
                    
            linkToFrames = linkToFramesCheckBox.selection()
            
            #print(linkToFrames)
            
            if linkToFrames:
                cursor.frameVisibility = newFrames
                
                cursor.__backend__.linkFrames(newFrames)
                
            else:
                # no frame linking required
                cursor.frameVisibility = []
            
            cursor.__backend__.name = newName
            
            if old_name != cursor.name:
                cDict = self.__graphicsObjects__[cursor.objectType]
                cDict.pop(old_name, None)
                cDict[cursor.name] = cursor
                
            self.signalCursorChanged.emit(cursor.backend)

        self._cursorContextMenuSourceId = None
        
    def buildROI(self):
        """Interactively builds a new ROI.
        """
        #print("buildROI")
        params = None
        pos = QtCore.QPointF(0,0)
        
        p = self.parent()

        while p is not None and not isinstance(p, ImageViewer):
            p = p.parent()
            
        if p is not None and isinstance(p, ImageViewer):
            frame = p.currentFrame
            
        else:
            frame = 0

        newROI = pgui.GraphicsObject(params, 
                                pos=pos,
                                objectType=pgui.GraphicsObjectType.allShapeTypes,
                                visibleFrames=[],
                                label=None,
                                currentFrame=frame,
                                parentWidget=self)
        
        self.__scene__.addItem(newROI)
        
        newROI.signalROIConstructed.connect(self.slot_newROIConstructed)
        
        return newROI

    def createNewRoi(self, params=None, roiType=None, label=None,
                     frame=None, pos=None, movable=True, 
                     editable=True, frameVisibility=[], 
                     showLabel=True, labelShowsPosition=True,
                     autoSelect=False, parentWidget=None):
        """
        """
        if self.__scene__.rootImage is None:
            return
        
        if parentWidget is None:
            if isinstance(self.__image_viewer__, ImageViewer):
                parentWidget = self.__image_viewer__
            else:
                parentWidget = self
            
        if roiType is None or params is None:
            self.buildROI()
            
        rTypeStr = ""
        
        if isinstance(params, pgui.PlanarGraphics):
            if params.type & pgui.GraphicsObjectType.allShapeTypes:
                roiType = params.type
                
            else:
                raise TypeError("Cannot build a ROI with this PlanarGraphics type: %s" % params.type)
            
            
        if roiType & pgui.GraphicsObjectType.point:
            rTypeStr = "p"
        elif roiType & pgui.GraphicsObjectType.line:
            rTypeStr = "l"
        elif roiType & pgui.GraphicsObjectType.rectangle:
            rTypeStr = "r"
        elif roiType & pgui.GraphicsObjectType.ellipse:
            rTypeStr = "e"
        elif roiType & pgui.GraphicsObjectType.polygon:
            rTypeStr = "pg"
        elif roiType & (pgui.GraphicsObjectType.path | pgui.GraphicsObjectType.polyline):
            rTypeStr = "pt"
        else:
            return
        
        if frame is None:
            if isinstance(parentWidget, ImageViewer):
                frame = parentWidget.currentFrame
            else:
                frame = 0
                
        nFrames = 1
                
        if isinstance(parentWidget, ImageViewer):
            nFrames = parentWidget.nFrames
            
            if frame < 0 :
                frame = nFrames
                
            if frame >= nFrames:
                frame = nFrames-1
                
        if frameVisibility is None:
            if isinstance(params, pgui.PlanarGraphics) and params.type & pgui.GraphicsObjectType.allShapeTypes:
                if not isinstance(params, pgui.Path):
                    frameVisibility = params.frameIndices
                    
                else:
                    frameVisibility = []
                
                if len(frameVisibility) == 1 and frameVisibility[0] is None:
                    frameVisibility.clear()
                    
            else:
                frameVisibility = [f for f in range(nFrames)]
            
        else:
            if not isinstance(params, pgui.Path):
                if not isinstance(frameVisibility, (tuple, list)) or not all([isinstance(f, int) for f in frameVisibility]):
                    raise TypeError("frame visibility must be specified as a list of ints or an empty list, or None; got %s instead" % frameVisibility)
                
                elif len(frameVisibility) == 0:
                    frameVisibility = [0]
            
        if isinstance(roiType, int):
            rDict = self.__graphicsObjects__[roiType]
            
        else:
            rDict = self.__graphicsObjects__[roiType.value]
            
        if label is None or (isinstance(label, str) and len(label) == 0):
            if isinstance(params, pgui.PlanarGraphics) and (isinstance(params.name, str) and len(params.name) > 0):
                tryName = params.name
                if tryName in rDict.keys():
                    tryName = utilities.counterSuffix(tryName, [s for s in rDict.keys()])
                    
                roiId = tryName
                
            else:
                roiId = "%s%d" % (rTypeStr, len(rDict))
            
        elif isinstance(label, str) and len(label):
            roiId = "%s%d" % (label, len(rDict))
                
        if roiId in rDict.keys():
            roiId += "%d" % len(rDict)
        
        if pos is not None and not isinstance(pos, (QtCore.QPoint, QtCore.QPointF)):
            raise TypeError("pos must be a QPoint or QPointF; got %s instead" % (type(pos).__name__))
        
        if pos is None:
            pos = QtCore.QPointF(0,0)
            
        if parentWidget is None:
            parentWidget = self
            
        #print("GraphicsImageViewerWidget.createNewRoi params %s" % params)
        #print("GraphicsImageViewerWidget.createNewRoi frameVisibility %s" % frameVisibility)
        
        roi = pgui.GraphicsObject(parameters            = params,
                                    pos                 = pos,
                                    objectType          = roiType,
                                    currentFrame        = frame,
                                    visibleFrames       = frameVisibility, 
                                    label               = roiId, 
                                    showLabel           = showLabel,
                                    labelShowsPosition  = labelShowsPosition,
                                    parentWidget        = parentWidget)
        
        roi.canMove = movable
        roi.canEdit = editable
        
        if isinstance(parentWidget, ImageViewer) and not parentWidget.guiClient:
            parentWidget.frameChanged[int].connect(roi.slotFrameChanged)
            
        if autoSelect:
            for r in self.__rois__.values():
                r.setSelected(False)
                
            roi.setSelected(True)

        self.__scene__.addItem(roi)

        roi.signalPosition.connect(self.slot_reportCursorPos)
        roi.selectMe[str, bool].connect(self.slot_setSelectedRoi)
        roi.requestContextMenu.connect(self.slot_graphicsObjectMenuRequested)
        roi.signalBackendChanged[object].connect(self.slot_roiChanged)
        
        rDict[roiId] = roi
        
        self.scene.update(self.scene.sceneRect().x(), \
                          self.scene.sceneRect().y(), \
                          self.scene.sceneRect().width(), \
                          self.scene.sceneRect().height())
        
        self.signalRoiAdded.emit(roi.backend)
        
        return roi
        
    def createNewCursor(self, cType, window=None, radius=None, pos=None, movable=True, 
                        editable=True, frame=None,  label=None, frameVisibility=[],
                        showLabel=True, labelShowsPosition = True, 
                        autoSelect=False, parentWidget = None):
        """
        
        cType: int or one of the pictgui.GraphicsObjectType cursor type enum values, 
            or a pictgui.Cursor object
        
        When cType is an int or GraphicsObjecType enum value, then the keyword
            parameters are used for constructing a pictgui.GraphicsObject 
            representation of a pictgui.Cursor

        When cType is a pictgui.Cursor object, keyword parameters given may
            override the Cursor's own values.
        
            NOTE: pictgui.Cursor objects can have both width and height None. 
            When this happens, the width/height will be taken from the scene 
            geometry.
        
            The Cursor window (in x or y direction) can be None for vertical or 
            horizontal cursors, respectively. It can be overridden by the "window" 
            keyword parameter here (default is the default _cursorWindow value 
            in GraphicsImageViewerWidget).
        
            By design, neither xwindow nor ywindow can be None in crosshair and 
            point cursors.
            
            NOTE: special attention should be given to the "name" attribute of
            the cursor object, which is also used to assign the ID of the 
            graphics object. 
            
        
        
        """
        if self.__scene__.rootImage is None:
            return
        
        if parentWidget is None:
            if isinstance(self.__image_viewer__, ImageViewer):
                parentWidget = self.__image_viewer__
            else:
                parentWidget = self
            
        if window is None:
            window = self.__cursorWindow__
            
        if radius is None:
            radius = self.__cursorRadius__
            
        if frame is None:
            if isinstance(parentWidget, ImageViewer):
                frame = parentWidget.currentFrame
            else:
                frame = 0
                
        nFrames = 1
                
        if isinstance(parentWidget, ImageViewer):
            nFrames = parentWidget.nFrames
            
            if frame < 0 :
                frame = nFrames
                
            if frame >= nFrames:
                frame = nFrames-1
                
        if isinstance(cType, pgui.Cursor): # construct from a pgui.Cursor
            # builds a GUI cursor for a backend PlanarGraphics object (a pictgui.Cursor)
            # this comes with its own coordinates, but we allow these to be
            # overridden here by this constructor's optional "pos" parameter
            cDict = self.__graphicsObjects__[cType.type.value]
            
            valx = np.floor(self.__scene__.rootImage.boundingRect().center().x())
            valy = np.floor(self.__scene__.rootImage.boundingRect().center().y())
            
            if cType.xwindow is None:
                cType.xwindow = window
    
            if cType.ywindow is None:
                cType.ywindow = window
                
            if isinstance(pos, (tuple, list)) and \
                len(pos) == 2 and all([isinstance(a, (numbers.Real, pq.Quantity)) for a in pos]):
                cType.x = pos[0]
                cType.y = pos[1]
            
            elif isinstance(pos, (QtCore.QPoint, QtCore.QPointF)):
                cType.x = pos.x()
                cType.y = pos.y()
        
            else:
                # no pos specified -- unlikely but anyhow...
                if cType.x is None or cType.y is None:
                    # just in case the PlanarGraphics object x or y are not set
                    if len(cDict) > 0:
                        # find a suitable position so we don't land on previous objects
                        if cType.type & pgui.GraphicsObjectType.vertical_cursor or \
                            cType.type & pgui.GraphicsObjectType.crosshair_cursor or \
                                cType.type & pgui.GraphicsObjectType.point_cursor:
                            
                            max_x = max([o.x for o in cDict.values()])
                            min_x = min([o.x for o in cDict.values()])
                            
                            valx = (self.__scene__.rootImage.boundingRect().width() + max_x) / 2
                            
                        if cType.type & pgui.GraphicsObjectType.horizontal_cursor or \
                            cType.type & pgui.GraphicsObjectType.crosshair_cursor or \
                                cType.type & pgui.GraphicsObjectType.point_cursor:
                        
                            max_y = max([o.y for o in cDict.values()])
                            valy = (self.__scene__.rootImage.boundingRect().height() + max_y) / 2
                            
                    if cType.x is None:
                        cType.x = valx
                        
                    if cType.y is None:
                        cType.y = valy
                    
            if cType.width is None:
                cType.width = self.__scene__.sceneRect().width()
                
            if cType.height is None:
                cType.height = self.__scene__.sceneRect().height()
            
            if cType.radius is None:
                cType.radius = self.__cursorRadius__
                
            if isinstance(label, str) and len(label) > 0:
                crsId = label
                
            else:
                tryName = cType.name
                if tryName in cDict.keys():
                    tryName = utilities.counterSuffix(tryName, [s for s in cDict.keys()])
                    
                crsId = tryName
                
            if crsId in self.__cursors__.keys():
                crsId +="%d" % len(cDict)
                
            if frameVisibility is None:
                if len(cType.frameIndices) == 0:
                    frameVisibility = [f for f in range(nFrames)]
                    
                else:
                    frameVisibility = cType.frameIndices
                
            else:
                if isinstance(frameVisibility, (tuple, list)):
                    if len(frameVisibility):
                        if len(frameVisibility) == 1 and frameVisibility[0] is None:
                            frameVisibility.clear()
                            
                        else:
                            if not all([isinstance(f, int) for f in frameVisibility]):
                                raise TypeError("frameVisibility expected to be a sequence of int, an empty sequence, the sequence [None], or just None; got %s instead" % frameVisibility)
                            
                    else:
                        frameVisibility = [0]
                            
                else:
                    raise TypeError("frame visibility must be specified as a list of ints or an empty list, or None; got %s instead" % frameVisibility)
                
            cursor = pgui.GraphicsObject(parameters             = cType,
                                            currentFrame        = frame,
                                            visibleFrames       = frameVisibility,
                                            label               = crsId,
                                            showLabel           = showLabel,
                                            labelShowsPosition  = labelShowsPosition,
                                            parentWidget        = parentWidget)
            
            #print("ImageViewer.createNewCursor cursor.backend", cursor.__backend__)
            
        else:              # parametric c'tor :
            # NOTE: 2018-09-28 10:20:29
            # cType is a GraphicsObjecType enum value
            cTypeStr = ""
            
            if cType & pgui.GraphicsObjectType.vertical_cursor:
                cTypeStr = "v"

            elif cType & pgui.GraphicsObjectType.horizontal_cursor:
                cTypeStr = "h"

            elif cType & pgui.GraphicsObjectType.point_cursor:
                cTypeStr = "p"

            elif cType & pgui.GraphicsObjectType.crosshair_cursor:
                cTypeStr = "c"

            else:
                return
            
            # NOTE: 2018-09-28 10:21:32
            # because it can be an enum value or an int resulted from
            # logical OR between several enum values, 
            # see NOTE: 2018-09-28 10:20:29
            if isinstance(cType, int):
                cDict = self.__graphicsObjects__[cType]
                
            else:
                cDict = self.__graphicsObjects__[cType.value]
            
            if label is None or (isinstance(label, str) and len(label) == 0):
                crsId = "%s%d" % (cTypeStr, len(cDict))
                
            elif instance(label, str) and len(label):
                crsId = "%s%d" % (label, len(cDict))
                
            else:
                raise TypeError("label expected to be a non-empty str or None; got %s instead" % type(name).__name__)
                
            #print(pos)
                
            if isinstance(pos, (tuple, list)) and \
                len(pos) == 2 and all([isinstance(a, (numbers.Real, pq.Quantity)) for a in pos]):
                point = QtCore.QPointF(pos[0], pos[1])
                    
            elif isinstance(pos, (QtCore.QPoint, QtCore.QPointF)):
                point = QtCore.QPointF(pos)
            
            else:
                # no pos specified
                
                # NOTE: 2018-09-28 11:20:32
                # cursor() is reimplemented as access method for a pictgui.Cursor!
                # must use the superclass instance method
                currentTopLabelText = self._topLabel.text()
                
                self._topLabel.setText(currentTopLabelText + " Double-click left mouse button for cursor position")
                
                #currentCursor = super(GraphicsImageViewerWidget, self).cursor()
                currentCursor = self._imageGraphicsView.viewport().cursor()
                
                #print("currentCursor shape:", currentCursor.shape())
                
                self._imageGraphicsView.viewport().setCursor(QtCore.Qt.CrossCursor)
                #self.setCursor(QtCore.Qt.CrossCursor)
                
                mouseEventFilters = [pgui.MouseEventSink(c) for c in cDict.values()]
                
                if len(cDict) > 0:
                    # install mouse event filter for all other cursors
                    for ck, c in enumerate(cDict.values()):
                        c.installEventFilter(mouseEventFilters[ck])
                    
                while not self.__escape_pressed___ and not self.__mouse_pressed___:
                    QtCore.QCoreApplication.processEvents()
                    
                self.__escape_pressed___ = False
                self.__mouse_pressed___  = False
                
                if len(cDict) > 0:
                    for ck, c in enumerate(cDict.values()):
                        c.removeEventFilter(mouseEventFilters[ck])
                
                self._imageGraphicsView.viewport().setCursor(currentCursor)
                
                self._topLabel.setText(currentTopLabelText)
                
                if isinstance(self.__last_mouse_click_lmb__, (QtCore.QPoint, QtCore.QPointF)):
                    point = QtCore.QPointF(self.__last_mouse_click_lmb__)
                    
                else:
                
                    valx = np.floor(self.__scene__.rootImage.boundingRect().center().x())
                    valy = np.floor(self.__scene__.rootImage.boundingRect().center().y())
                    
                    if len(cDict) > 0:
                        # find a suitable position so we don't land on previous objects
                        if cType & pgui.GraphicsObjectType.vertical_cursor or \
                            cType & pgui.GraphicsObjectType.crosshair_cursor or \
                                cType & pgui.GraphicsObjectType.point_cursor:
                            
                            max_x = max([o.x for o in cDict.values()])
                            valx = (self.__scene__.rootImage.boundingRect().width() + max_x) / 2
                            
                        if cType & pgui.GraphicsObjectType.horizontal_cursor or \
                            cType & pgui.GraphicsObjectType.crosshair_cursor or \
                                cType & pgui.GraphicsObjectType.point_cursor:
                        
                            max_y = max([o.y for o in cDict.values()])
                            valy = (self.__scene__.rootImage.boundingRect().height() + max_y) / 2
                            
                    point = QtCore.QPointF(valx, valy)
            
            if not self.__scene__.sceneRect().contains(point) or point == QtCore.QPointF(0,0):
                point.setX(np.floor(self.__scene__.rootImage.boundingRect().center().x()))
                point.setY(np.floor(self.__scene__.rootImage.boundingRect().center().y()))
                
            width = self.__scene__.sceneRect().width()
            height = self.__scene__.sceneRect().height()
            
            if frameVisibility is None:
                frameVisibility = []
                
            elif isinstance(frameVisibility, (tuple, list)):
                if len(frameVisibility):
                    if len(frameVisibility) == 1 and frameVisibility[0] is None:
                        frameVisibility.clear()
                        
                    else:
                        if not all([isinstance(f, int) for f in frameVisibility]):
                            raise TypeError("frameVisibility expected a sequence of int, [], or [None], or just None; got %s instead" % frameVisibility)
                        
                
            cursor = pgui.GraphicsObject(parameters = (width, height, window, window, radius),
                                            pos                 = point, 
                                            objectType          = cType,
                                            currentFrame        = frame,
                                            visibleFrames       = frameVisibility, 
                                            label               = crsId,
                                            showLabel           = showLabel,
                                            labelShowsPosition  = labelShowsPosition,
                                            parentWidget        = parentWidget)
            
        cursor.canMove = movable
            
        if isinstance(parentWidget, ImageViewer) and not parentWidget.guiClient:
            parentWidget.frameChanged[int].connect(cursor.slotFrameChanged)
            
        self.__scene__.addItem(cursor)

        if autoSelect:
            for c in self.__cursors__.values():
                c.setSelected(False)
                
            cursor.setSelected(True)
            
        cursor.signalPosition.connect(self.slot_reportCursorPos)
        cursor.selectMe[str, bool].connect(self.slot_setSelectedCursor)
        cursor.requestContextMenu.connect(self.slot_graphicsObjectMenuRequested)
        cursor.signalBackendChanged.connect(self.slot_cursorChanged)
        
        cDict[crsId] = cursor
        
        self.scene.update(self.scene.sceneRect().x(), \
                          self.scene.sceneRect().y(), \
                          self.scene.sceneRect().width(), \
                          self.scene.sceneRect().height())
        
        #if len(cursor.frameVisibility)==0 or cursor.currentFrame in cursor.frameVisibility:
            #cursor.show()
            
        if cursor.__backend__.hasStateForFrame(cursor.currentFrame):
            cursor.show()
            
        self.signalCursorAdded.emit(cursor.backend)
        
        return cursor
    
    def clear(self):
        """Clears the contents of the viewer.
        
        Removes all cursors, rois and image data and clears the 
        underlying scene.
        
        """
        for d in self.__graphicsObjects__.values():
            d.clear()
            
        for d in self.__cursors__.values():
            d.clear()
            
        self.selectedCursor = None
        self.selectedRoi = None
        self._cursorContextMenuSourceId = None 
        
        self.__scene__.clear()
    
    ####
    # slots
    ####
    
    @pyqtSlot(int, str)
    @safeWrapper
    def slot_newROIConstructed(self, roiType, roiName):
        sender = self.sender()
        
        # see NOTE: 2018-09-25 23:06:55
        #sigBlock = QtCore.QSignalBlocker(sender)
        
        if roiType & pgui.GraphicsObjectType.point:
            rTypeStr = "p"
            
        elif roiType & pgui.GraphicsObjectType.line:
            rTypeStr = "l"
            
        elif roiType & pgui.GraphicsObjectType.rectangle:
            rTypeStr = "r"
            
        elif roiType & pgui.GraphicsObjectType.ellipse:
            rTypeStr = "e"
            
        elif roiType & pgui.GraphicsObjectType.polygon:
            rTypeStr = "pg"
            
        elif roiType & pgui.GraphicsObjectType.path:
            rTypeStr = "pt"
            
        elif roiType == 0:
            sender.signalROIConstructed.disconnect()
            self.__scene__.removeItem(sender)
            return
        else:
            return
        
        sender.signalPosition.connect(self.slot_reportCursorPos)
        sender.selectMe.connect(self.slot_setSelectedRoi)
        sender.requestContextMenu.connect(self.slot_graphicsObjectMenuRequested)
        
        rDict = self.__graphicsObjects__[roiType]
        
        roiId = "%s%d" % (rTypeStr, len(rDict))
        sender.name=roiId
        
        rDict[roiId] = sender
        
        self.selectedRoi = sender
        
    @pyqtSlot(object)
    @safeWrapper
    def slot_cursorChanged(self, obj):
        self.signalCursorChanged.emit(obj)
        
    @pyqtSlot(object)
    @safeWrapper
    def slot_roiChanged(self, obj):
        self.signalRoiChanged.emit(obj)
        
    @pyqtSlot(float)
    @safeWrapper
    def slot_zoom(self, val):
        self._zoomView(val)
        
    @pyqtSlot(float)
    @safeWrapper
    def slot_relativeZoom(self, val):
        newZoom = self.__zoomVal__ + val
        
        if newZoom < self._minZoom__:
            newZoom = self._minZoom__
        elif newZoom > self.__maxZoom__:
            newZoom = self.__maxZoom__
                
        self._zoomView(newZoom)
        
    @pyqtSlot()
    @safeWrapper
    def slot_editAnyCursor(self):
        self._cursorEditor()
        
        return
    
    @pyqtSlot()
    @safeWrapper
    def slot_editSelectedCursor(self):
        if self.selectedCursor is not None:
            self._cursorEditor(self.selectedCursor.ID)
            
        return
                    
    @pyqtSlot()
    @safeWrapper
    def slot_editCursor(self):
        if self._cursorContextMenuSourceId is not None and self._cursorContextMenuSourceId in self.__cursors__.keys():
            self._cursorEditor(self._cursorContextMenuSourceId)
            
        return
    
    def propagateCursorState(self):
        if self._cursorContextMenuSourceId is not None and self._cursorContextMenuSourceId in self.__cursors__.keys():
            cursor = self.__cursors__[self._cursorContextMenuSourceId]
            
            if cursor.__backend__.hasHardFrameAssociations and cursor.__backend__.hasStateForCurrentFrame:
                cursor.__backend__.propagateFrameState(cursor.__backend__.currentFrame, cursor.__backend__.frameIndices)
                cursor.__backend__.updateFrontends()
                
        
    
    @pyqtSlot()
    @safeWrapper
    def slot_editRoi(self):
        # TODO: select a roi fromt the list then bring up a ROI edit dialog
        pass
    
    @pyqtSlot()
    @safeWrapper
    def slot_editRoiProperties(self): # to always work on selected ROI
        # TODO bring up a ROI edit dialog
        # this MUST have a checkbox to allow shape editing when OK-ed
        pass

    @pyqtSlot()
    @safeWrapper
    def slot_editRoiShape(self): # to always work on selected ROI!
        if self.selectedRoi is not None:
            self.selectedRoi.editMode = True
            # press RETURN in editMode to turn editMode OFF
        

    @pyqtSlot(str, QtCore.QPoint)
    @safeWrapper
    def slot_graphicsObjectMenuRequested(self, crsId, pos):
        if crsId in self.__cursors__.keys() and self.__cursors__[crsId].objectType & pgui.GraphicsObjectType.allCursorTypes:
            self._cursorContextMenuSourceId = crsId 
            
            cm = QtWidgets.QMenu("Cursor Menu", self)
            crsEditAction = cm.addAction("Edit properties for %s cursor" % crsId)
            crsEditAction.triggered.connect(self.slot_editCursor)
            
            crsPropagateStateToAllFrames = cm.addAction("Propagate current state to all frames")
            crsPropagateStateToAllFrames.triggered.connect(self.propagateCursorState)
            
            crsLinkCursorAction = cm.addAction("Link...")
            crsUnlinkCursorAction = cm.addAction("Unlink...")
            crsRemoveAction = cm.addAction("Remove %s cursor" % crsId)
            crsRemoveAction.triggered.connect(self.slot_removeCursor)
            cm.exec(pos)
            
        elif crsId in self.__rois__.keys() and self.__rois__[crsId].objectType & pgui.GraphicsObjectType.allObjectTypes:
            self._roiContextMenuSourceId = crsId
            
            cm = QtWidgets.QMenu("ROI Menu", self)
            crsEditAction = cm.addAction("Edit properties for %s ROI" % crsId)
            crsEditAction.triggered.connect(self.slot_editRoi)
            
            pathEditAction = cm.addAction("Edit path for %s" % crsId)
            pathEditAction.triggered.connect(self.slot_editRoiShape)
            
            crsLinkCursorAction = cm.addAction("Link...")
            crsUnlinkCursorAction = cm.addAction("Unlink...")
            crsRemoveAction = cm.addAction("Remove %s ROI" % crsId)
            crsRemoveAction.triggered.connect(self.slot_removeRoi)
            cm.exec(pos)

    
            
    @pyqtSlot(str, bool)
    @safeWrapper
    def slot_setSelectedCursor(self, cId, sel):
        """To keep track of what cursor is selected, 
        independently of the underlying graphics view fw.
        """
        if len(self.__cursors__) == 0 or cId not in self.__cursors__.keys():
            self.selectedCursor = None
            self.signalGraphicsDeselected.emit()
            return
        
        if sel:
            self.selectedCursor = self.__cursors__[cId]
            
            self.signalCursorSelected.emit(self.selectedCursor.backend)
            
        else:
            self.selectedCursor = None
            self.signalGraphicsDeselected.emit()
            
    @pyqtSlot(str, bool)
    @safeWrapper
    def slot_setSelectedRoi(self, rId, sel):
        if len(self.__rois__) == 0 or rId not in self.__rois__.keys():
            self.selectedRoi = None
            self.signalGraphicsDeselected.emit()
            return
        
        if sel:
            self.selectedRoi = self.__rois__[rId]
            self.signalCursorSelected.emit(self.selectedRoi.backend)
            
        else:
            self.selectedRoi = None
            self.signalGraphicsDeselected.emit()
            
    @pyqtSlot()
    @safeWrapper
    def slot_newHorizontalCursor(self):
        self.createNewCursor(pgui.GraphicsObjectType.horizontal_cursor)
        
    @pyqtSlot()
    @safeWrapper
    def slot_newPointCursor(self):
        self.createNewCursor(pgui.GraphicsObjectType.point_cursor)
    
    @pyqtSlot()
    @safeWrapper
    def slot_newVerticalCursor(self):
        self.createNewCursor(pgui.GraphicsObjectType.vertical_cursor)
    
    @pyqtSlot()
    @safeWrapper
    def slot_newCrosshairCursor(self):
        self.createNewCursor(pgui.GraphicsObjectType.crosshair_cursor)
    
    @pyqtSlot(str)
    @safeWrapper
    def slot_selectCursor(self, crsId):
        if crsId in self.__cursors__.keys():
            self.slot_setSelectedCursor(crsId, True)
      
    @pyqtSlot()
    @safeWrapper
    def slot_receiveCursorUnlinkRequest(self):
        pass
    
    @pyqtSlot()
    @safeWrapper
    def slot_receiveCursorLinkRequest(self):
        pass
    
    @pyqtSlot(int, str, "QPointF")
    @safeWrapper
    def slot_reportCursorPos(self, cType, crsId, pos):
        obj = self.__cursors__.get(crsId, None)
        if obj is not None:
            if cType & pgui.GraphicsObjectType.vertical_cursor:
                self.signalCursorAt[str, list].emit(crsId, \
                    [np.floor(pos.x()), None, obj.xwindow])
                
            elif cType & pgui.GraphicsObjectType.horizontal_cursor:
                self.signalCursorAt[str, list].emit(crsId, \
                    [None, np.floor(pos.y()), self.__cursors__[crsId].ywindow])
                
            elif cType & (pgui.GraphicsObjectType.crosshair_cursor | pgui.GraphicsObjectType.point_cursor):
                self.signalCursorAt[str, list].emit(crsId, \
                    [np.floor(pos.x()), np.floor(pos.y()), self.__cursors__[crsId].xwindow, self.__cursors__[crsId].ywindow])
                        
    @pyqtSlot()
    @safeWrapper
    def slot_removeCursors(self):
        if len(self.__cursors__) == 0:
            return
        
        cursors = [c for c in self.__cursors__.values()]
                
        for crs in cursors:
            self.scene.removeItem(crs)
            
            if crs in crs.backend.frontends:
                crs.backend.frontends.remove(crs)
            
        cursorTypeInts = [t.value for t in pgui.GraphicsObjectType if \
            t.value < pgui.GraphicsObjectType.allCursorTypes]
        
        for k in cursorTypeInts:
            self.__graphicsObjects__[k].clear()
            
        self.selectedCursor = None
        
        self.__cursors__.clear()
        
        self.update(self._imageGraphicsView.childrenRegion())
        self.scene.update(self.scene.sceneRect().x(), \
                          self.scene.sceneRect().y(), \
                          self.scene.sceneRect().width(), \
                          self.scene.sceneRect().height())
        
    @pyqtSlot()
    @safeWrapper
    def slot_removeSelectedCursor(self):
        if self.selectedCursor is None:
            return
        
        self.slot_removeCursorByName(self.selectedCursor.name)
        
    @pyqtSlot()
    @safeWrapper
    def slot_removeCursor(self):
        if len(self.__cursors__) == 0:
            return
        
        if self._cursorContextMenuSourceId is not None and self._cursorContextMenuSourceId in self.__cursors__.keys():
            self.slot_removeCursorByName(self._cursorContextMenuSourceId)
        
    @pyqtSlot(str)
    @safeWrapper
    def slot_removeCursorByName(self, crsId):
        #if isinstance(self.__image_viewer__, ImageViewer):
            #print("GraphicsImageViewerWidget of %s slot_removeCursorByName %s" % (self.__image_viewer__.windowTitle(), crsId))
        #else:
            #print("GraphicsImageViewerWidget slot_removeCursorByName %s" % crsId)
            
        if len(self.__cursors__) == 0:
            return
        
        if crsId in self.__cursors__.keys():
            cursor = self.__cursors__[crsId]
            
            self.scene.removeItem(cursor)
            
            if self.selectedCursor == cursor:
                self.selectedCursor = None
            
            if isinstance(cursor.objectType, pgui.GraphicsObjectType):
                cType = cursor.objectType.value
                
            else:
                cType = cursor.objectType

            #removed_cursor = self.__graphicsObjects__[cType].pop(crsId, None)
            self.__graphicsObjects__[cType].pop(crsId, None)
            
            if cursor in cursor.backend.frontends:
                cursor.backend.frontends.remove(cursor)

            self.signalCursorRemoved.emit(cursor.backend)
            
            #del cursor
            #del removed_cursor
            
        self.update(self._imageGraphicsView.childrenRegion())
        
        self.scene.update(self.scene.sceneRect().x(), \
                          self.scene.sceneRect().y(), \
                          self.scene.sceneRect().width(), \
                          self.scene.sceneRect().height())
        
    @pyqtSlot()
    @safeWrapper
    def slot_removeRois(self):
        if len(self.__rois__) == 0 :
            return
        
        rois = [r for r in self.__rois__.values()]
        
        for roi in rois:
            self.scene.removeItem(roi)
            
            if roi in roi.backend.frontends:
                roi.backend.frontends.remove(roi)
            
        roiTypeInts = [t.value for t in pgui.GraphicsObjectType if \
            t.value > pgui.GraphicsObjectType.allCursorTypes]
        
        for k in roiTypeInts:
            self.__graphicsObjects__[k].clear()
            
        self.__rois__.clear()
        
        self.selectedRoi = None
        
        self.update(self._imageGraphicsView.childrenRegion())
        self.scene.update(self.scene.sceneRect().x(), \
                          self.scene.sceneRect().y(), \
                          self.scene.sceneRect().width(), \
                          self.scene.sceneRect().height())
        
    @pyqtSlot()
    @safeWrapper
    def slot_removeSelectedRoi(self):
        if self.selectedRoi is None:
            return
        
        self.slot_removeRoiByName(self.selectedRoi.name)
        
    @pyqtSlot(str)
    @safeWrapper
    def slot_removeRoiByName(self, roiId):
        #print("GraphicsImageViewerWidget slot_removeRoiByName %s" % roiId)
        if len(self.__rois__) == 0:
            return
        
        if roiId in self.__rois__.keys():
            roi = self.__rois__[roiId]
            
            self.scene.removeItem(roi)
            
            if self.selectedRoi == roi:
                self.selectedRoi = None
            
            if isinstance(roi.objectType, pgui.GraphicsObjectType):
                rType = roi.objectType.value
                
            else:
                rType = roi.objectType

            #removed_roi = self.__graphicsObjects__[rType].pop(roiId, None)
            self.__graphicsObjects__[rType].pop(roiId, None)
            
            if roi in roi.backend.frontends:
                roi.backend.frontends.remove(roi)
            
            self.signalRoiRemoved.emit(roi.backend)
            
            #del roi
            #del removed_roi
            
        self.update(self._imageGraphicsView.childrenRegion())
        
        self.scene.update(self.scene.sceneRect().x(), \
                          self.scene.sceneRect().y(), \
                          self.scene.sceneRect().width(), \
                          self.scene.sceneRect().height())

    @pyqtSlot()
    @safeWrapper
    def slot_removeRoi(self):
        if len(self.__rois__) == 0:
            return
        
        if self._roiContextMenuSourceId is not None and self._roiContextMenuSourceId in self.__rois__.keys():
            self.slot_removeRoiByName(self._roiContextMenuSourceId)
        
    @safeWrapper
    def hasRoi(self, roiId):
        """Tests for existence of a GraphicsObject roi with given id or name (label).
        
        Parameters:
        ===========
        roiId: str: the roi Id or roi Name (label)
        """
        if not isinstance(roiId, str):
            raise TypeError("Expecting a str; got %s instead" % type(roiId).__name__)
        
        if len(self.__rois__) == 0:
            return False
        
        if not roiId in self.__rois__.keys():
            roi_id_Label = [(rid, r.name) for (rid, r) in self.__rois__.items() if r.name == roiId]
            
            return len(roi_id_Label) > 0
            
        else:
            return True
        
   ####
    # properties
    ####
    
    @property
    def minZoom(self):
        return self._minZoom__
    
    @minZoom.setter
    def minZoom(self, val):
        self._minZoom__ = val
        
    #@pyqtProperty(float)
    @property
    def maxZoom(self):
        return self.__maxZoom__
    
    @maxZoom.setter
    def maxZoom(self, val):
        self.__maxZoom__ = val
        

    @property
    def scene(self):
        return self.__scene__
    
    @property
    def graphicsview(self):
        return self._imageGraphicsView
    
    @property
    def cursors(self):
        return self.__cursors__
    
    @property
    def imageViewer(self):
        return self.__image_viewer__
    
    @property
    def rois(self):
        return self.__rois__
    
    @property
    def graphicsObjects(self):
        return self.__graphicsObjects__
    
    @safeWrapper
    def roi(self, value):
        """Returns the GraphicsObject with specified ID or name (label) or None if this does not exist.
        
        Parameters:
        ===========
        roiId: str: the roi Id or Name (label)
        """
        if not isinstance(value, str):
            raise TypeError("Expecting a str; got %s instead" % type(value).__name__)
        
        #print("current rois: ", self.__rois__)
        
        if len(self.__rois__):
            if value in self.__rois__.keys():
                return self.__rois__[value]
            
            else:
                roi_id_Label = [(r, rid, r.label) for (rid, r) in self.__rois__.items() if r.label == value]
                #print("roi",  roi_id_Label[0])
                #print("roi id %s" % rid)
                #print("roi label " , roi_id_Label[0].label)
                if len(roi_id_Label):
                    return [self.__rois__[i[0]] for i in roi_id_Label]
    
    ####
    # public methods
    ####
    
    #def showImageLabel(self, val):
        #self._imageNameLabel.setVisible(val)
        
    @safeWrapper
    def cursor(self, value):
        """Returns the GraphicsObject cursor with specified ID or name (label) or None if this does not exist.
        
        Parameters:
        ===========
        value: str: the cursor Id or Name (label)
        """
        
        if len(self.__cursors__):
            if not isinstance(value, str):
                raise TypeError("Expecting a str; gt %s instead" % type(value).__name__)
            
            if value in self.__cursors__.keys():
                return self.__cursors__[value]
            
            #else:
                #crsId_Label = [(c, cid, c.name) for (cid, c) in self.__cursors__.items() if c.label == value]
                
                #if len(crsId_Label):
                    #return [c[0] for c in crsId_Label]
            
    @safeWrapper
    def hasCursor(self, crsid):
        """Tests for existence of a GraphicsObject cursor with given id or label.
        
        Parameters:
        ===========
        roiId: str: the roi Id or roi Name (label)
        """
        
        if not isinstance(crsid, str):
            raise TypeError("Expecting a str; got %s instead" % type(crsid).__name__)
        
        if len(self.__cursors__) == 0:
            return False
        
        if not crsid in self.__cursors__.keys():
            cid_label = [(cid, c.label) for (cid, c) in self.__cursors__.items() if c.label == crsid]
            
            return len(cid_label) > 0
        
        else:
            return True
    
    def setMessage(self, s):
        pass
    
    def wheelEvent(self, evt):
        if evt.modifiers() and QtCore.Qt.ShiftModifier:
            step = 1
            #if evt.modifiers() and QtCore.Qt.ControlModifier and QtCore.Qt.ShiftModifier:
                #step = 10
                
            #print("wheel event angle delta x: ", evt.angleDelta().x(), " y: ", evt.angleDelta().y())
                
            nDegrees = evt.angleDelta().y()*step/8
            
            nSteps = nDegrees / 15
            
            zoomChange = nSteps * 0.1
            
            self.slot_relativeZoom(zoomChange)
        #else:
        evt.accept()

    def timerEvent(self, evt):
        evt.ignore()
        
    def keyPressEvent(self, evt):
        #print("keyPresEvent in GraphicsImageViewerWidget: ", evt)
        if evt.key() == QtCore.Qt.Key_Escape:
            self.__escape_pressed___ = True
            
        #else:
            #self.__escape_pressed___ = False
            
        evt.accept()
        #evt.ignore()
        
    @safeWrapper
    def mousePressEvent(self, evt):
        #print("mousePressEvent in GraphicsImageViewerWidget: ", evt)
        self.__mouse_pressed___ = True
        
        if evt.button() == QtCore.Qt.LeftButton:
            self.__last_mouse_click_lmb__ = evt.pos()
            #self.__escape_pressed___ = True
            
        elif evt.button() == QtCore.Qt.RightButton:
            self.__last_mouse_click_lmb__ = None
            #self.__escape_pressed___ = True
        
        evt.accept()
    
    @safeWrapper
    def mouseReleaseEvent(self, evt):
        #print("mouseReleaseEvent in GraphicsImageViewerWidget: ", evt)
        self.__mouse_pressed___ = True
        
        if evt.button() == QtCore.Qt.LeftButton:
            self.__last_mouse_click_lmb__ = evt.pos()
            #self.__escape_pressed___ = True
            
        elif evt.button() == QtCore.Qt.RightButton:
            self.__last_mouse_click_lmb__ = None
            #self.__escape_pressed___ = True
        
        evt.accept()
    
    def setImage(self, img):
        self.view(img)
        
    def view(self, a):
        if isinstance(a, QtGui.QPixmap):
            self.__scene__.rootImage = QtWidgets.QGraphicsPixmapItem(a)
            #self.__scene__.setRootImage(QtWidgets.QGraphicsPixmapItem(a))
            
        elif isinstance(a, QtGui.QImage):
            self.__scene__.rootImage = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(a))
            #self.__scene__.setRootImage(QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(a)))
            
        else:
            return
        
        #print(a)
        
        #self._imageGraphicsView.ensureVisible(self.__scene__.getRootImage().boundingRect(),0,0)
        
        #print("scene Rect: ", self.__scene__.sceneRect())
        #print("image bounding rect: ", self.__scene__.getRootImage().boundingRect())
        
        #if self.parentWidget() is None:
            ##self.adjustSize()
            #self.resize(self.__scene__.sceneRect().width(), self.__scene__.sceneRect().height())
            ##self.setVisible(True)
        ##else:
            ##self.parentWidget().resize(self.__scene__.sceneRect().width(), self.__scene__.sceneRect().height())
            
        #self._imageGraphicsView.setGeometry(self.__scene__.sceneRect().toAlignedRect())
        #self._imageGraphicsView.centerOn(QtCore.QPointF(self.__scene__.rootImage.boundingRect().left() ,self.__scene__.rootImage.boundingRect().top()))


    def interactiveZoom(self):
        self.__interactiveZoom__ = not self.__interactiveZoom__
    
    def setBackground(self, brush):
        self.__scene__.setBackground(brush)
        
    def setTopLabelText(self, value):
        self._topLabel.setText(value)
        
    #def setBottomLabelText(self, value):
        #self._bottomLabel.setText(value)
        
    def clearTopLabel(self):
        self._topLabel.clear()
        
    #def clearBottomLabel(self):
        #self._bottomLabel.clear()
        
    def clearLabels(self):
        self.clearTopLabel()
        #self.clearBottomLabel()
        
class ImageViewer(ScipyenFrameViewer, Ui_ImageViewerWindow):
    closeMe                 = pyqtSignal(int)
    
    signal_graphicsObjectAdded      = pyqtSignal(object, name="signal_graphicsObjectAdded")
    signal_graphicsObjectChanged    = pyqtSignal(object, name="signal_graphicsObjectChanged")
    signal_graphicsObjectRemoved    = pyqtSignal(object, name="signal_graphicsObjectRemoved")
    signal_graphicsObjectSelected   = pyqtSignal(object, name="signal_graphicsObjectSelected")
    signal_graphicsObjectDeselected = pyqtSignal(name="signal_graphicsObjectDeselected")
    
    # TODO 2019-11-01 22:41:39
    # implement viewing of Kernel2D, numpy.ndarray with 2 <= ndim <= 3
    # list and tuple of 2D VigraArray 2D, Kernel2D, 2D numpy.ndarray, QImage, QPixmap
    supported_types = (vigra.VigraArray, vigra.filters.Kernel2D, np.ndarray, 
                       QtGui.QImage, QtGui.QPixmap, tuple, list) 
    
    view_action_name = "Image"
    
    # image = the image (2D or volume, or up to 5D (but with up to 3 spatial
    #           dimensions e.g., xyztc, etc))
    # title = name of image data to be displayed on the view's label -- defaults to "image ID"
    # 
    # normalize = boolean or (min,max) or None
    #
    # gamma = None (for now)
    #
    # "colortable" = singleton or list of colortables or None
    #
  
    def __init__(self, data: (vigra.VigraArray, vigra.filters.Kernel2D, np.ndarray, QtGui.QImage, QtGui.QPixmap, tuple, list) = None,
                 parent: (QtWidgets.QMainWindow, type(None)) = None, 
                 pWin: (QtWidgets.QMainWindow, type(None))= None, ID:(int, type(None)) = None,
                 win_title: (str, type(None)) = None, doc_title: (str, type(None)) = None,
                 frame:(int, type(None)) = None, 
                 displayChannel = None, normalize: (bool, ) = False, gamma: (float, ) = 1.0, 
                 *args, **kwargs):
        super().__init__(data=data, parent=parent, pWin=pWin, ID=ID, win_title=win_title, doc_title=doc_title, frame=frame, *args, *kwargs)

        #self._configureGUI_()
        
        self.imageNormalize             = None
        self.imageGamma                 = None
        self.colorMap                   = None
        self.prevColorMap               = None
        self.colorTable                 = None
        self.colorbar                   = None
        self._colorbar_width_           = 20
        
        #self._separateChannels           = False
        
        self.cursorsColor               = None
        self.roisColor                  = None
        
        self.sharedCursorsColor         = None
        self.sharedRoisColor            = None
        
        #self._defaultCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)
        
        #self.fallbackCursorsColor       = pgui.GraphicsObject.defaultColor
        #self.fallbackRoisColor          = pgui.GraphicsObject.defaultColor
        
        if displayChannel is None:
            self._displayedChannel_      = "all"
            
        else:
            if isinstance(displayChannel, str):
                if displayChannel.lower().strip()!="all":
                    raise ValueError("When a str, displayChannel must be 'all'; got %s instead" % displayChannel)
                
            elif isinstance(displayChannel, int):
                if displayChannel < 0:
                    raise ValueError("When an int, display channel must be >= 0")
                
            self._displayedChannel_ = displayChannel
                
                
        #self.isComplex                 = False
        #self.nChannels                 = 1
        #self._current_frame_index_      = 0
        #self._number_of_frames_         = 1
        self.tStride                    = 0
        self.zStride                    = 0
        self.frameAxisInfo              = None
        self.userFrameAxisInfo          = None
        self.widthAxisInfo              = None # this is "visual" width which may not be on a spatial axis "x"
        self.heightAxisInfo             = None # this is "visual" height which may not be on a spatial axis "y"
        #self.frameIterator              = None # ??? FIXME what's this for ???
        self._currentZoom_            = 0
        #self.complexDisplay            = ComplexDisplay.real # one of "real", "imag", "dual" "abs", "phase" (cmath.phase), "arg"
        self._currentFrameData_       = None
        
        # QGraphicsLineItems -- outside the roi/cursor GraphicsObject framework!
        self._scaleBarColor_             = QtGui.QColor(255, 255, 255)
        self._xScaleBar_                 = None
        self._xScaleBarTextItem_         = None
        self._yScaleBar_                 = None
        self._yScaleBarTextItem_         = None
        self._scaleBarTextPen_           = QtGui.QPen(QtCore.Qt.SolidLine)
        self._scaleBarPen_               = QtGui.QPen(QtGui.QBrush(self._scaleBarColor_, 
                                                                  QtCore.Qt.SolidPattern),
                                                     2.0,
                                                     cap = QtCore.Qt.RoundCap,
                                                     join = QtCore.Qt.RoundJoin)
        
        self.settings                   = QtCore.QSettings()
        
        self._display_horizontal_scalebar_ = True
        self._display_vertical_scalebar_   = True
        
        self._showsScaleBars_            = True
        
        self._showsIntensityCalibration_ = False
        
        self._scaleBarOrigin_            = (0, 0)
        self._scaleBarLength_            = (10,10)
        
        # NOTE 2019-03-18 12:54:14
        # TODO
        #self._cursors_color_
        #self._rois_color_

        #self._load_settings_()
        
        if isinstance(data, ImageViewer.supported_types) or any([t in type(data).mro() for t in ImageViewer.supported_types]):
            self.setData(data, doc_title=self._docTitle_)
        
    ####
    # properties
    ####
    
    @property
    def currentFrame(self):
        return self._current_frame_index_
    
    @currentFrame.setter
    def currentFrame(self, val):
        """
        Emits self.frameChanged signal when not a guiClient
        """
        if not isinstance(val, int) or val >= self._number_of_frames_ or val < 0: 
            return
        
        # NOTE: 2018-09-25 23:06:55
        # recipe to block re-entrant signals in the code below
        # cleaner than manually docinenctign and re-connecting
        # and also exception-safe
        
        signalBlockers = [QtCore.QSignalBlocker(widget) for widget in \
            (self.framesQSpinBox, self.framesQSlider)]
        
        #self.framesQSpinBox.valueChanged[int].disconnect()
        #self.framesQSlider.valueChanged[int].disconnect()

        self.framesQSpinBox.setValue(val)
        self.framesQSlider.setValue(val)

        self._current_frame_index_ = val
        #print("ImageViewer %s currentFrame: " % self.windowTitle(), self._current_frame_index_)

        self.displayFrame()

        if type(self._scipyenWindow_).__name__ == "ScipyenWindow":
            # updates the graphics items positions from their backend store
            # ONLY is this is an independent window (ie. it is not a client
            # to some other app e.g. LSCaT)
            #
            # when a client to such app, it falls to that app to manage the 
            # graphics items' backends (i.e., to set the index of their current 
            # frame) followed by the backends' responsibility to update
            # their frontends
            #
            for obj_dict in self.graphicsObjects().values():
                for obj in obj_dict.values():
                    if obj.backend.currentFrame != self._current_frame_index_: # check to avoid race conditions and recurrence
                        obj.backend.currentFrame = self._current_frame_index_
                    
            self.frameChanged.emit(self.currentFrame)
        
        #self.framesQSpinBox.valueChanged.connect(self.slot_setFrameNumber)
        #self.framesQSlider.valueChanged.connect(self.slot_setFrameNumber)
        
        # NOTE: 2018-05-21 20:59:18
            
    
    @property
    def cursors(self):
        return self.viewerWidget.cursors
    
    @safeWrapper
    def cursor(self, value):
        """Returns a GraphicsObject cursor with specified ID or name (label).
        
        Parameters:
        ===========
        value: str: the cursor Id or roi Name (label)
        """
        return self.viewerWidget.cursor(value)

    @safeWrapper
    def hasCursor(self, value):
        """Tests for existence of a GraphicsObject cursor with specified ID or name (label).
        
        Parameters:
        ===========
        value: str: the cursor Id or roi Name (label)
        """
        return self.viewerWidget.hasCursor(value)
    
    @property
    def rois(self):
        return self.viewerWidget.rois
    
    @safeWrapper
    def roi(self, roiId):
        """Returns a GraphicsObject roi with specified ID or name (label).
        
        Parameters:
        ===========
        roiId: str: the roi Id or roi Name (label)
        """
        return self.viewerWidget.roi(roiId)
        
    @safeWrapper
    def hasRoi(self, roiId):
        """Tests for existence of a GraphicsObject roi with specified ID or name (label).
        
        Parameters:
        ===========
        roiId: str: the roi Id or roi Name (label)
        """
        return self.viewerWidget.hasRoi(roiId)
    
    @property
    def colorBarWidth(self):
        return self._colorbar_width_
    
    @colorBarWidth.setter
    def colorBarWidth(self, value):
        if not isinstance(value, int):
            raise TypeError("Expecting an int; got %s instead" % type(value).__name__)
        
        if value <= 0:
            raise ValueError("Expecting a strictly positive value (>=0); got %d instead" % value)
        
        self._colorbar_width_ = value
    
    @property
    def viewer(self):
        return self.viewerWidget
    
    @property
    def scene(self):
        """A reference to viewerWidget's QGraphicsScene.
        """
        return self.viewer.scene
    
    
    @property
    def selectedRoi(self):
        """A reference to the selected ROI
        """
        return self.viewer.selectedRoi
    
    @property
    def selectedCursor(self):
        """A reference to the selected cursor
        """
        return self.viewer.selectedCursor
    
    ####
    # slots
    ####
    
    # helper for export slots
    
    def _export_scene_helper_(self, file_format):
        if not isinstance(file_format, str) or file_format.strip().lower() not in ("svg", "tiff", "png"):
            raise ValueError("Unsupported export file format %s" % file_format)
        
        if file_format.strip().lower() == "svg":
            file_filter = "Scalable Vector Graphics Files (*.svg)"
            caption_suffix = "SVG"
            
        elif file_format.strip().lower() == "tiff":
            file_filter = "TIFF Files (*.tif)"
            caption_suffix = "TIFF"
            qimg_format = QtGui.QImage.Format_ARGB32
            
        elif file_format.strip().lower() == "png":
            file_filter = "Portable Network Graphics Files (*.png)"
            caption_suffix = "PNG"
            qimg_format = QtGui.QImage.Format_ARGB32
            
        else:
            raise ValueError("Unsupported export file format %s" % file_format)
        
        if self._scipyenWindow_ is not None:
            targetDir = self._scipyenWindow_.currentDir
            
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                caption="Export figure as %s" % caption_suffix,
                                                                filter = file_filter,
                                                                directory = targetDir)
            
        else:
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                caption="Export figure as %s" % caption_suffix,
                                                                filter = file_filter)
            
        if len(fileName) == 0:
            return
        
        if file_format.strip().lower() == "svg":
            generator = QtSvg.QSvgGenerator()
            generator.setFileName(fileName)
            
            generator.setSize(QtCore.QSize(int(self.viewerWidget.scene.width()), 
                                           int(self.viewerWidget.scene.height())))
            
            generator.setViewBox(QtCore.QRect(0, 0, 
                                              int(self.viewerWidget.scene.width()),
                                              int(self.viewerWidget.scene.height())))
            
            generator.setResolution(300)
            
            #font = QtGui.QFont("sans-serif", pointSize = 4)
            font = QtGui.QGuiApplication.font()
            
            painter = QtGui.QPainter()
            painter.begin(generator)
            painter.setFont(font)
            self.viewerWidget.scene.render(painter)
            painter.end()
        
        else:
            out = QtGui.QImage(int(self.viewerWidget.scene.width()), 
                               int(self.viewerWidget.scene.height()),
                               qimg_format)
            
            out.fill(QtCore.Qt.black)
            
            painter = QtGui.QPainter(out)
            self.viewerWidget.scene.render(painter)
            painter.end()
            out.save(fileName, file_format.strip().lower(), 100)
    
    @pyqtSlot()
    @safeWrapper
    def slot_exportSceneAsPNG(self):
        if self._data_ is None:
            return
        
        self._export_scene_helper_("png")
        
    @pyqtSlot()
    @safeWrapper
    def slot_exportSceneAsSVG(self):
        if self._data_ is None:
            return
        
        self._export_scene_helper_("svg")
        
    @pyqtSlot()
    @safeWrapper
    def slot_exportSceneAsTIFF(self):
        if self._data_ is None:
            return
        
        self._export_scene_helper_("tiff")
        
    @pyqtSlot()
    @safeWrapper
    def slot_saveTIFF(self):
        if self._data_ is None:
            return
        
        if self._scipyenWindow_ is not None:
            targetDir = self._scipyenWindow_.currentDir
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                caption="Save image data as TIFF", 
                                                                filter="TIFF Files (*.tif)",
                                                                directory=targetDir)
        else:
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                caption="Save image data as TIFF", 
                                                                filter="TIFF Files (*.tif)")
        
        if len(fileName) == 0:
            return
        
        #if image
        
        pio.saveImageFile(self._data_, fileName)
        
    
    @pyqtSlot()
    @safeWrapper
    def slot_editCursor(self):
        self.viewerWidget.slot_editAnyCursor()
    
    @pyqtSlot()
    @safeWrapper
    def slot_editSelectedCursor(self):
        self.viewerWidget.slot_editSelectedCursor()
    
    @pyqtSlot()
    @safeWrapper
    def slot_removeCursors(self):
        self.viewerWidget.slot_removeCursors()

    @pyqtSlot()
    @safeWrapper
    def slot_removeSelectedCursor(self):
        self.viewerWidget.slot_removeSelectedCursor()
    
    @pyqtSlot()
    @safeWrapper
    def slot_removeRois(self):
        self.viewerWidget.slot_removeRois()
        
    @pyqtSlot(str)
    @safeWrapper
    def slot_removeRoi(self, roiId):
        self.viewerWidget.slot_removeRoiByName(roiId)

    @pyqtSlot()
    @safeWrapper
    def slot_removeSelectedRoi(self):
        self.viewerWidget.slot_removeSelectedRoi()
    
    @pyqtSlot()
    @safeWrapper
    def slot_zoomIn(self):
        self._currentZoom_ +=1
        self.viewerWidget.slot_zoom(2**self._currentZoom_)
        
    @pyqtSlot()
    @safeWrapper
    def slot_zoomOriginal(self):
        self._currentZoom_ = 0
        self.viewerWidget.slot_zoom(2**self._currentZoom_)
        
    @pyqtSlot()
    @safeWrapper
    def slot_refreshDataDisplay(self):
        self.displayFrame()
        #if self._scipyenWindow_ is None:
            #return
        
        #if self._data_var_name_ is not None and self._data_var_name_ in self._scipyenWindow_.workspace.keys():
            #self.setData(self._scipyenWindow_.workspace[self._data_var_name_], doc_title=self._data_var_name_)

        
    @pyqtSlot()
    @safeWrapper
    def slot_zoomOut(self):
        self._currentZoom_ -=1
        self.viewerWidget.slot_zoom(2**self._currentZoom_)
        
    @pyqtSlot(bool)
    @safeWrapper
    def slot_selectZoom(self):
        self.viewerWidget.interactiveZoom()
        
    @pyqtSlot(bool)
    @safeWrapper
    def slot_displayColorBar(self, value):
        if value:
            self._setup_color_bar_()
            
        else:
            if self.colorbar is not None:
                self.viewerWidget.scene.removeItem(self.colorbar)
                
    def _setup_color_bar_(self):
        #try:
            #import qimage2ndarray as q2a
        #except:
            #traceback.print_exc()
            #return
        
        
        if isinstance(self._data_, vigra.VigraArray):
            self._currentFrameData_, _ = self._generate_frame_view_(self._displayedChannel_)
            
            imax = self._currentFrameData_.max()
            imin = self._currentFrameData_.min()
            
            imin, imax = sorted((imin, imax))
            
            image_range = abs(imax - imin)
            
            bar_x = self._currentFrameData_.shape[0]
            bar_height = self._currentFrameData_.shape[1]
            
            
            if image_range == 0:
                return
            
            bar_column = np.linspace(self._currentFrameData_.max(), 
                                    self._currentFrameData_.min(),
                                    bar_height)
            
            # 1) prepare a gradient image:
            
            bar_image = vigra.VigraArray(np.concatenate([bar_column[:,np.newaxis] for k in range(self._colorbar_width_)], 
                                                        axis=1).T,
                                        axistags = vigra.VigraArray.defaultAxistags("xy"))
            
            if self.colorMap is None or self._currentFrameData_.channels > 1:
                bar_qimage = bar_image.qimage(normalize = self.imageNormalize)
                
            else:
                bar_qimage = self._applyColorTable_(bar_image).qimage(normalize = self.imageNormalize)
                    
                    
            if self.colorbar is None:
                self.colorbar =  QtWidgets.QGraphicsItemGroup()
                
                self.viewerWidget.scene.addItem(self.colorbar)
                #self.colorbar.setPos(bar_x, 0)
                    
            else:
                for item in self.colorbar.childItems():
                    self.colorbar.removeFromGroup(item)
                    
                #self.colorbar.setPos(bar_x, 0)
                    
                
            cbar_pixmap_item = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(bar_qimage))
            cbar_pixmap_item.setPos(bar_x, 0)
            
            # 2) draw a rect around the gradient image
            cbar_rect = QtWidgets.QGraphicsRectItem(bar_x, 0, self._colorbar_width_, bar_height)
            cbar_rect.setPen(pgraph.mkPen(pgraph.mkColor("k")))
            
            # 3) calculate ticks (thanks to Luke Campagnola, author of pyqtgraph)
            
            # 3.a) tick spacing
            
            optNTicks = max(2., np.log(bar_height))
            
            optTickSpc = image_range/optNTicks
            
            #print("optTickSpc", optTickSpc)
            
            max_p10_spacing = 10 ** np.floor(np.log10(optTickSpc))
            
            #print("max_p10_spacing", max_p10_spacing)
            
            intervals = np.array([1., 2., 10, 20., 100.]) * max_p10_spacing
            
            #print("intervals", intervals)
            
            minorIndex = 0
            
            while intervals[minorIndex+1] <= optTickSpc:
                minorIndex += 1
                
            #print("minorIndex", minorIndex)
                
            # each element is a tuple (spacing, offset)
            levels = [(intervals[minorIndex+2], 0),
                      (intervals[minorIndex+1], 0)]
            
            #print("levels", levels)
            
            minSpc = min(bar_height/20., 30.)
            
            #print("minSpc", minSpc)
            
            maxNTicks = bar_height / minSpc
            
            #print("maxNTicks", maxNTicks)
            
            if image_range / intervals[minorIndex] <= maxNTicks:
                levels.append((intervals[minorIndex], 0))
                
            #print("levels", levels)
            
            tick_values = np.array([])
            
            # will have tuple of (spacing, sequence of tick values)
            ticks = []
                
            for k in range(len(levels)):
                spacing, offset = levels[k]
                
                start = np.ceil((imin-offset)/spacing) * spacing + offset
                
                nticks = int((imax-start) / spacing) + 1
                
                values = np.arange(nticks) * spacing + start
                
                values = list(filter(lambda x: all(np.abs(tick_values-x) > spacing * 0.01), values) )
                
                tick_values = np.concatenate([tick_values, values])
                
                ticks.append( (spacing, values))
                
            #print(ticks)
            
            final_tick_values = ticks[-1][1]
            
            tick_strings = ["%d" % value for value in final_tick_values]
            #print("tick_strings", tick_strings)
            
            tick_y_positions = [(bar_height - ((value -imin) * bar_height) / image_range) for value in final_tick_values]
            
            #print("tick_y_positions", tick_y_positions)
            
            tick_labels_width = []
            
            font = QtGui.QGuiApplication.font()
            
            font_metrics = QtGui.QFontMetrics(font)
            
            tick_lines = []
            tick_labels = []
            
            for k, tick_y in enumerate(tick_y_positions):
                tick_line = QtWidgets.QGraphicsLineItem(bar_x, tick_y, self._colorbar_width_ + bar_x, tick_y)
                tick_line.setPen(pgraph.mkPen(pgraph.mkColor("k")))
                
                
                tick_text = QtWidgets.QGraphicsTextItem(tick_strings[k])
                tick_text.setFont(font)
    
                font_rect = font_metrics.boundingRect(tick_strings[k])
                ##print("fRect", fRect)
                #tick_labels_width.append(fRect.width())
                
                tick_labels_width.append(font_rect.width())# * 1.1)
                
                tick_text.setPos(self._colorbar_width_ + bar_x, tick_y + font_rect.y())
                
                tick_lines.append(tick_line)
                tick_labels.append(tick_text)
                
                
            back_rect = QtWidgets.QGraphicsRectItem(bar_x, 0, (self._colorbar_width_ + max(tick_labels_width))*1.2, bar_height)
            back_rect.setPen(pgraph.mkPen(pgraph.mkColor("w")))
            back_rect.setBrush(pgraph.mkBrush("w"))
            #back_rect.setZValue(-1)
            
            self.colorbar.addToGroup(back_rect)
            self.colorbar.addToGroup(cbar_pixmap_item)
            self.colorbar.addToGroup(cbar_rect)
            
            for k,l in enumerate(tick_lines):
                self.colorbar.addToGroup(l)
                self.colorbar.addToGroup(tick_labels[k])
                
            
            
        elif isinstance(self._data_, (QtGui.QImage, QtGui.QPixmap)):
            # TODO/FIXME figure out how to get the image min and max from a QImage!
            #if isinstance(self._data_, QtGui.QImage):
                #if image.depth() == 24:
                    #pass
            #bar_height = self._data_.height()
            #bar_x = self._data_.width()
            
            return
            
            
        else:
            return
        
            
            
        
    @pyqtSlot(bool)
    @safeWrapper
    def slot_displayScaleBar(self, value):
        """
        """
        if value:
            if self._data_ is None:
                return
            
            xcal = None
            ycal = None
            
            x_units = dt.pixel_unit
            y_units = dt.pixel_unit
            
            if isinstance(self._data_, vigra.VigraArray):
                w = self._data_.shape[0]
                h = self._data_.shape[1]
                
                if self.frameAxisInfo is not None:
                    if isinstance(self.frameAxisInfo, tuple) and len(self.frameAxisInfo) == 2:
                        ndx1 = self._current_frame_index_ // self._data_.shape[self._data_.axistags.index(self.frameAxisInfo[0].key)]
                        ndx0 = self._current_frame_index_ - ndx1 * self._data_.shape[self._data_.axistags.index(self.frameAxisInfo[0].key)]
                        
                        img = self._data_.bindAxis(self.frameAxisInfo[0].key,ndx0).bindAxis(self.frameAxisInfo[1].key,ndx1)
                        
                    else:
                        img = self._data_.bindAxis(self.frameAxisInfo.key, self._current_frame_index_)
                        
                else:
                    img = self._data_
                    
                xcal = dt.AxisCalibration(img.axistags[0])
                ycal = dt.AxisCalibration(img.axistags[1])
                
                x_units = xcal.getUnits(img.axistags[0])
                y_units = ycal.getUnits(img.axistags[1])
                
            elif isinstance(self._data_, (QtGui.QImage, QtGui.QPixmap)):
                w = self._data_.width()
                h = self._data_.height()
                
            else:
                return # shouldn't really get here
        
            def_x       = self._scaleBarOrigin_[0] # in pixels!
            def_x_len   = self._scaleBarLength_[0]
            
            if xcal is not None:
                def_x       = float(xcal.getCalibratedAxialDistance(def_x, img.axistags[0]).magnitude)
                def_x_len   = float(xcal.getCalibratedAxialDistance(def_x_len, img.axistags[0]).magnitude)
                
            #print("def_x", def_x)
            #print("def_x_len", def_x_len)
            
            def_y       = self._scaleBarOrigin_[1] # in pixels!
            def_y_len   = self._scaleBarLength_[1]
            
            if ycal is not None:
                def_y       = float(ycal.getCalibratedAxialDistance(def_y, img.axistags[1]).magnitude)
                def_y_len   = float(ycal.getCalibratedAxialDistance(def_y_len, img.axistags[1]).magnitude)
            
            #print("def_y", def_y)
            #print("def_y_len", def_y_len)
            
            dlg = quickdialog.QuickDialog(self, "Display scale bars")
            #dlg = vigra.pyqt.quickdialog.QuickDialog(self, "Display scale bars")
            
            display_group = quickdialog.HDialogGroup(dlg)
            #display_group = vigra.pyqt.quickdialog.HDialogGroup(dlg)
            
            show_x = quickdialog.CheckBox(display_group, "Horizontal")
            #show_x = vigra.pyqt.quickdialog.CheckBox(display_group, "Horizontal")
            show_x.setToolTip("Show horizontal scalebar")
            show_x.setChecked(self._display_horizontal_scalebar_)
            
            show_y = quickdialog.CheckBox(display_group, "Vertical")
            #show_y = vigra.pyqt.quickdialog.CheckBox(display_group, "Vertical")
            show_y.setToolTip("Show vertical scalebar")
            show_y.setChecked(self._display_vertical_scalebar_)
            
            x_prompt = quickdialog.FloatInput(dlg, "X coordinate (in %s)" % x_units)
            #x_prompt = vigra.pyqt.quickdialog.FloatInput(dlg, "X coordinate (in %s)" % x_units)
            x_prompt.variable.setClearButtonEnabled(True)
            x_prompt.variable.redoAvailable = True
            x_prompt.variable.undoAvailable = True
            x_prompt.setValue(def_x)
            
            y_prompt = quickdialog.FloatInput(dlg, "Y coordinate (in %s)" % y_units)
            #y_prompt = vigra.pyqt.quickdialog.FloatInput(dlg, "Y coordinate (in %s)" % y_units)
            y_prompt.variable.setClearButtonEnabled(True)
            y_prompt.variable.redoAvailable = True
            y_prompt.variable.undoAvailable = True
            y_prompt.setValue(def_y)
            
            x_len_prompt = quickdialog.FloatInput(dlg, "Length on X axis (in %s)" % x_units)
            #x_len_prompt = vigra.pyqt.quickdialog.FloatInput(dlg, "Length on X axis (in %s)" % x_units)
            x_len_prompt.variable.setClearButtonEnabled(True)
            x_len_prompt.variable.redoAvailable = True
            x_len_prompt.variable.undoAvailable = True
            x_len_prompt.setValue(def_x_len)
            
            y_len_prompt = quickdialog.FloatInput(dlg, "Length on Y axis (in %s)" % y_units)
            #y_len_prompt = vigra.pyqt.quickdialog.FloatInput(dlg, "Length on Y axis (in %s)" % y_units)
            y_len_prompt.variable.setClearButtonEnabled(True)
            y_len_prompt.variable.redoAvailable = True
            y_len_prompt.variable.undoAvailable = True
            y_len_prompt.setValue(def_y_len)
            
            if dlg.exec() == QtWidgets.QDialog.Accepted:
                self._display_horizontal_scalebar_ = show_x.selection()
                self._display_vertical_scalebar_ = show_y.selection()
                
                if xcal is not None:
                    cal_x       = x_prompt.value() * xcal.getUnits(img.axistags[0].key)
                    cal_x_len   = x_len_prompt.value() * xcal.getUnits(img.axistags[0].key)
                    
                    x           = xcal.getDistanceInSamples(cal_x, img.axistags[0].key)
                    x_len       = xcal.getDistanceInSamples(cal_x_len, img.axistags[0].key)
                    
                else:
                    x           = int(x_prompt.value())
                    x_len       = int(x_len_prompt.value())
                    
                    cal_x       = x
                    cal_x_len   = y_len
                    
                #print("x", x)
                #print("x_len", x_len)
                    
                if ycal is not None:
                    cal_y       = y_prompt.value() * ycal.getUnits(img.axistags[1].key)
                    cal_y_len   = y_len_prompt.value() * ycal.getUnits(img.axistags[1].key)
                    
                    y           = ycal.getDistanceInSamples(cal_y, img.axistags[1].key)
                    y_len       = ycal.getDistanceInSamples(cal_y_len, img.axistags[1].key)
                    
                else:
                    y           = int(y_prompt.value())
                    y_len       = int(y_len_prompt.value())
                    
                    cal_y       = y
                    cal_y_len   = y_len
                    
                #print("y", y)
                #print("y_len", y_len)
                    
                self._scaleBarOrigin_ = (x, y)
                self._scaleBarLength_ = (x_len, y_len)
                
                self.showScaleBars(calibrated_length = (cal_x_len, cal_y_len))
            
        else:
            if self._xScaleBar_ is not None:
                self._xScaleBar_.setVisible(False)
                
            if self._yScaleBar_ is not None:
                self._yScaleBar_.setVisible(False)
            
    def _setup_channels_display_actions_(self):
        if isinstance(self._data_, vigra.VigraArray):
            if self._data_.channels > 1:
                for channel in range(self._data_.channels):
                    action = self.channelsMenu.addAction("%d" % channel)
                    action.setCheckable(True)
                    action.setChecked(False)
                    action.triggered.connect(self.slot_displayChannel)
                    self.displayIndividualChannelActions.append("Channel %d" % channel)
                    
            else:
                self.channelsMenu.clear()
                    
                self.displayIndividualChannelActions.clear()
                
        else:
            pass
                
    
    @pyqtSlot()
    def slot_displayChannel(self):
        sender = self.sender()
        
        if sender in self.displayIndividualChannelActions:
            text = sender.text()
            
            try:
                channel_index = int(eval(text))
                
                self.displayChannel(channel_index)
                
            except:
                return
            
    #@pyqtSlot()
    #def slot_refreshDisplayedWorkspaceImage(self):
        #"""Refreshes the data display.
        #Requires that self._scipyenWindow_ is of the appropriate type
        #and that self._data_var_name_ is a valid identifier for the data
        #in self._scipyenWindow_.workspace namespace
        #"""
        #from workspacefunctions import getvarsbytype
        
        #if self._scipyenWindow_ is None:
            #return
        
        #if isinstance(self._data_var_name_, str):
            #img_vars = dict(getvarsbytype(vigra.VigraArray, ws = self._scipyenWindow_.workspace))
            
            #if self._data_var_name_ not in img_vars.keys():
                #return
            
            #image = img_vars[self._data_var_name_]
            
            #if isinstance(self._displayedChannel_, int):
                #if self._displayedChannel_ >= image.channels:
                    #self._displayedChannel_ = "all"
            
            #self.view(image, title = self._data_var_name_, displayChannel = self._displayedChannel_)
            
        
    @pyqtSlot()
    def slot_loadImageFromWorkspace(self):
        from workspacefunctions import getvarsbytype
        
        if self._scipyenWindow_ is None:
            return
        
        img_vars = dict(getvarsbytype(vigra.VigraArray, ws = self._scipyenWindow_.workspace))
        
        if len(img_vars) == 0:
            return
        
        name_list = sorted([name for name in img_vars.keys()])
        
        choiceDialog = pgui.ItemsListDialog(parent=self, itemsList = name_list)
        
        ans = choiceDialog.exec()
        
        if ans == QtWidgets.QDialog.Accepted and choiceDialog.selectedItem is not None:
            image = img_vars[choiceDialog.selectedItem]
            image_title = choiceDialog.selectedItem
            self._data_var_name_ = choiceDialog.selectedItem
            
            if isinstance(self._displayedChannel_, int):
                if self._displayedChannel_ >= image.channels:
                    self._displayedChannel_ = "all"
            
            self.view(image, title = image_title, displayChannel = self._displayedChannel_)
        
    @pyqtSlot(bool)
    def slot_displayAllChannels(self, value):
        if value:
            self.displayAllChannels()
            
        
    # NOTE: 2017-07-25 22:07:49
    # TODO: generate calibrated coordinates here as well
    # as done for slot_displayMousePos;
    # TODO: factor out code for coordinate string generation 
    # (started in _displayValueAtCoordinates)
    # be aware that here the coordinates are a list
    # which may contain cursor window size as well
    @pyqtSlot(str, list)
    @safeWrapper
    def slot_displayCursorPos(self, value, coords):
        self._displayValueAtCoordinates(coords, value)

    @pyqtSlot(int,int)
    @safeWrapper
    def slot_displayMousePos(self, x, y):
        self._displayValueAtCoordinates((x,y))
        
    @pyqtSlot(object)
    @safeWrapper
    def slot_graphicsObjectAdded(self, obj):
        self.signal_graphicsObjectAdded.emit(obj)
        
    @pyqtSlot(object)
    @safeWrapper
    def slot_graphicsObjectChanged(self, obj):
        self.signal_graphicsObjectChanged.emit(obj)
        
    @pyqtSlot(object)
    @safeWrapper
    def slot_graphicsObjectRemoved(self, obj):
        self.signal_graphicsObjectRemoved.emit(obj)
        
    @pyqtSlot(object)
    @safeWrapper
    def slot_graphicsObjectSelected(self, obj):
        self.signal_graphicsObjectSelected.emit(obj)
        
    @pyqtSlot()
    @safeWrapper
    def slot_graphicsObjectDeselected(self):
        self.signal_graphicsObjectDeselected.emit()
        
    ####
    # private methods
    ####
    
    def _parseVigraArrayData_(self, img):
        """ Extract information about image axes to figure out how to display it.
        
        For now ImageViewer only accepts images with up to three dimensions.
        
        NOTE:
        1) a 3D image MAY be represented as a 4D vigra array with a channel axis
        
        2) a 2D image MAY be prepresented as a 3D vigra array with a channel axis
        
        img is a vigra.VigraArray object
        
        """
        import io
        
        if img is None:
            return False
        
        try:
            (nFrames, frameAxisInfo, widthAxisInfo, heightAxisInfo) = dt.getFrameLayout(img, userFrameAxis = self.userFrameAxisInfo)
            
        except Exception as e:
            s = io.StringIO()
            sei = sys.exc_info()
            traceback.print_exception(file=s, *sei)
            msgbox = QtWidgets.QMessageBox()
            msgbox.setSizeGripEnabled(True)
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            #msgbox.setWindowTitle(sei[0].__class__.__name__)
            msgbox.setWindowTitle(type(e).__name__)
            msgbox.setText(sei[0].__class__.__name__)
            msgbox.setDetailedText(s.getvalue())
            msgbox.exec()
            return False
            #QtWidgets.QMessageBox.critical(self, "Error", "Data must have at least two non-channel axes; instead it has %d" % (img.axistags.axisTypeCount(vigra.AxisType.NonChannel)))
            
        if np.any(np.iscomplex(img)):
            QtWidgets.QMessageBox.critical(self, "Error", "ImageViewer cannot display complex-valued data")
            return False
            #raise ValueError("Cannot display complex-valued data")
            
        try:
            # there may be a previous image stored here
            if self._data_ is not None and len(self.viewerWidget.cursors) > 0: # parse width/height of previos image if any, to check against existing cursors
                #if self._data_.width != img.width or self._data_.height != img.height:
                if self._data_.shape[self._data_.axistags.index(self.widthAxisInfo.key)] != img.shape[img.axistags.index(widthAxisInfo.key)] or \
                    self._data_.shape[self._data_.axistags.index(self.heightAxisInfo.key)] != img.shape[img.axistags.index(heightAxisInfo.key)]:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setText("New image frame geometry will invalidate existing cursors.")
                    msgBox.setInformativeText("Load image and bring all cursors to center?")
                    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                    msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
                    msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                    
                    ret = msgBox.exec()
                    
                    if ret == QtWidgets.QMessageBox.Cancel:
                        return False
                    
                    for c in self.viewerWidget.cursors.values():
                        widthAxisNdx = img.axistags.index(widthAxisInfo.key)
                        heightAxisNdx = img.axistags.index(heightAxisInfo.key)
                        c.rangeX = img.shape[widthAxisNdx]
                        c.rangeY = img.shape[heightAxisNdx]
                        c.setPos(img.shape[widthAxisNdx]/2, img.shape[heightAxisNdx]/2)
            
            self._number_of_frames_        = nFrames
            self.frameAxisInfo  = frameAxisInfo
            self.widthAxisInfo  = widthAxisInfo
            self.heightAxisInfo = heightAxisInfo
        
            self.framesQSlider.setMaximum(self._number_of_frames_-1)
            self.framesQSlider.setToolTip("Select frame.")
            
            self.framesQSpinBox.setMaximum(self._number_of_frames_-1)
            self.framesQSpinBox.setToolTip("Select frame .")
            self.nFramesLabel.setText("of %d" % self._number_of_frames_)
            
            return True
                
        except Exception as e:
            traceback.print_exc()
            return False
        
    def _applyColorTable_(self, image: vigra.VigraArray):
        """Applies the internal color table to the 2D array.
        
        Parameters:
        -----------
        image: vigra.VigraArray with ndim == 2: a 2D array, or a 2D slice view
            of a higher dimension array.
            
            NOTE: 2019-11-13 14:01:28
            This is called with self._currentFrameData_ passed as the "image"
            parameter.
            
            self._currentFrameData_ is either a 2D slice view, or a copy of it
            with np.nan values replaced by 0.0
            
        Returns:
        --------
        vigra.VigraArray: uint8 image with 4 channels. This is a copy of image, 
        with applied color table (see vigra.colors.applyColortable)
        """
        if isinstance(image, vigra.VigraArray):
            if np.isnan(image).any():
                return image
            
            if not isinstance(self.colorMap, colors.Colormap):
                #print("self.colorMap is a ", type(self.colorMap))
                return image
            
            if image.min() == image.max():
                return image
            
            lrMapImage = vigra.colors.linearRangeMapping(image)
            
            nMap = colors.Normalize(vmin=0, vmax=255)
            
            sMap = cm.ScalarMappable(norm = nMap, cmap = self.colorMap)
            
            #print(type(sMap))
            
            sMap.set_array(range(256))
            cTable = sMap.to_rgba(range(256), bytes=True)
            #cFrame = vigra.colors.applyColortable(image.astype('uint32'), cTable)
            if image.ndim > 2:
                if image.channelIndex < image.ndim and image.channels > 1: # TODO FIXME
                    # NOTE 2017-10-05 14:17:00
                    # do NOT apply colormap to multi-band image
                    #cFrame = lrMapImage.copy()
                    return image
                else:
                    cFrame = vigra.colors.applyColortable(lrMapImage.astype('uint32'), cTable)
                    
            else:
                cFrame = vigra.colors.applyColortable(lrMapImage.astype('uint32'), cTable)
                
            return cFrame
        
        elif isinstance(image, (QtGui.QImage, QtGui.QPixmap)):
            return image
            # FIXME/TODO 2019-11-13 13:58:31
            # figure out how to apply color table to a QImage/QPixmap!
            #if isinstance(image, QtGui.QPixmap):
                #qimg = image.toImage()
                
            #else:
                #qimg = image
                
            #if qimg.isGrayScale():
                #q
    
    def _generate_frame_view_(self, channel):
        """Returns a slice (frame) of self._data_ along the self.frameAxis
        
        If the slice contains np.nan returns a copy of the image slice.
        
        Otherwise, returns a REFERENCE to the image slice.
        
        """
        if not isinstance(self._data_, vigra.VigraArray):
            raise RuntimeError("Wrong function call for a non-vigra array image")
        
        if self.frameAxisInfo is not None:
            # NOTE: 2019-11-13 13:52:46
            # frameAxisInfo is None only for 2D data arrays
            if isinstance(self.frameAxisInfo, (tuple, list)):
                dimindices = list()
                
                frameAxisDims = [self._data_.shape[self._data_.axistags.index[ax.key]] for ax in self.frameAxisInfo]
                
                premultipliers = [1]
                
                premultipliers += list(np.cumprod([self._data_.shape[self._data_.axistags.index[ax.key]] for ax in self.frameAxisInfo])[:-1])
                
                frame = self._current_frame_index_
                
                for k in range(len(premultipliers)-1, -1, -1):
                    ndx = frame // premultipliers[k]
                    
                    frame = frame % premultipliers[k]
                    
                    dimindices.append(ndx)
                
                dimindices.reverse()
                
                # get a 2D slice view of the data
                img_view = self._data_.bindAxis(self.frameAxisInfo[0].key, dimindices[0])
                
                for k in range(1, len(dimindices)):
                    img_view = img_view.bindAxis(self.frameAxisInfo[k].key, dimindices[k])
                    
            else:
                img_view = self._data_.bindAxis(self.frameAxisInfo.key, self._current_frame_index_)
                dimindices = [self._current_frame_index_]
                
        else:
            img_view = self._data_
            dimindices = []
            
        # up to now, img_view is a 2D slice view of self._data_, will _ALL_ avaiable channels
            
        # get a channel view on the 2D slice view of self._data_
        if isinstance(channel, int) and "c" in self._currentFrameData_.axistags and channel_index in range(self._currentFrameData_.channels):
            img_view = img_view.bindAxis("c", channel)
            
        # check for NaNs
        if np.isnan(img_view).any():             # if there are nans
            img_view = img.view.copy()           # make a copy
            img_view[np.isnan(img_view)] = 0.0   # replace nans with 0
            
            
        return img_view, dimindices
        
    @safeWrapper
    def displayFrame(self, channel_index = None):
        #print("ImageViewer %s displayFrame()" % self.windowTitle())
        #print("viewing frame along the %s axis " % self.frameAxisInfo)
        #x = None
        #y = None
        
        if channel_index is None:
            channel_index = self._displayedChannel_
        
        if isinstance(channel_index, str):
            if channel_index.lower().strip() != "all":
                raise ValueError("When a string, channel_index must be 'all' -- case-insensitive; got %s instead" % channel_index)
            
        elif isinstance(channel_index, int):
            if channel_index < 0:
                raise ValueError("When an int, channel_index must be >= 0; got %d instead" % channel_index)
            
            if isinstance(self._data_, vigra.VigraArray):
                if channel_index >= self._data_.channels:
                    raise ValueError("Invalid channel_index %d for an image with %d channels" % (channel_index, self._data_.channels))
        
        if channel_index is not self._displayedChannel_:
            self._displayedChannel_ = channel_index
        
        if isinstance(self._data_, vigra.VigraArray):
            self._currentFrameData_, _ = self._generate_frame_view_(channel_index) # this is an array view !
            
            if self.colorMap is None:
                self.viewerWidget.view(self._currentFrameData_.qimage(normalize = self.imageNormalize))
                
            else:
                if self._currentFrameData_.channels == 1:
                    if self._currentFrameData_.channelIndex < self._currentFrameData_.ndim:
                        self._currentFrameData_ = self._currentFrameData_.squeeze()
                        
                    cFrame = self._applyColorTable_(self._currentFrameData_)
                    
                    self.viewerWidget.view(cFrame.qimage(normalize = self.imageNormalize))
                    
                else: # don't apply color map to a multi-band frame data
                    #warnings.warn("Cannot apply color map to a multi-band image")
                    self._currentFrameData_ = self._currentFrameData_.squeeze().copy()
                    self.viewerWidget.view(self._currentFrameData_.qimage(normalize = self.imageNormalize))
        
            # TODO FIXME: what if we view a transposed array ???? (e.g. viewing it on
            # Y or X axis instead of the Z or T axis?)
            w = self._data_.shape[self._data_.axistags.index(self.widthAxisInfo.key)] # this is not neccessarily space!
            h = self._data_.shape[self._data_.axistags.index(self.heightAxisInfo.key)] # this is not neccessarily space!
            # NOTE: 2017-07-24 09:03:38
            # w and h are a convention here
            
            # NOTE: 2017-07-26 22:18:14
            # get calibrates axes sizes
            cals = "(%s x %s)" % \
                (strutils.print_scalar_quantity(dt.getCalibratedAxisSize(self._data_, self.widthAxisInfo.key)), \
                    strutils.print_scalar_quantity(dt.getCalibratedAxisSize(self._data_, self.heightAxisInfo.key)))
    
            shapeTxt = "%s x %s: %d x %d %s" % \
                (dt.defaultAxisTypeName(self.widthAxisInfo), \
                    dt.defaultAxisTypeName(self.heightAxisInfo), \
                    w, h, cals)
            
            self.slot_displayColorBar(self.displayColorBarAction.isChecked())

        elif isinstance(self._data_, (QtGui.QImage, QtGui.QPixmap)):
            # NOTE 2018-09-14 11:45:13
            # TODO/FIXME adapt code to select channels from a Qimage is not allGray() or not isGrayscale()
            self.viewerWidget.view(self._data_)
            
            w = self._data_.width()
            h = self._data_.height()
            shapeTxt = "W x H: %d x %d " % (w, h)
            
        elif isinstance(self._data_, np.ndarray):
            if self._data_.ndim == 1:
                pass
            
        else:
            #print("nothing to do ?")
            return # shouldn't really get here
        
        self.viewerWidget.setTopLabelText(shapeTxt)
        
        #try:
            #if isinstance(self._data_, vigra.VigraArray):
                #self._currentFrameData_, _ = self._generate_frame_view_(channel_index) # this is an array view !
                
                #if self.colorMap is None:
                    #self.viewerWidget.view(self._currentFrameData_.qimage(normalize = self.imageNormalize))
                    
                #else:
                    #if self._currentFrameData_.channels == 1:
                        #if self._currentFrameData_.channelIndex < self._currentFrameData_.ndim:
                            #self._currentFrameData_ = self._currentFrameData_.squeeze()
                            
                        #cFrame = self._applyColorTable_(self._currentFrameData_)
                        
                        #self.viewerWidget.view(cFrame.qimage(normalize = self.imageNormalize))
                        
                    #else: # don't apply color map to a multi-band frame data
                        ##warnings.warn("Cannot apply color map to a multi-band image")
                        #self._currentFrameData_ = self._currentFrameData_.squeeze().copy()
                        #self.viewerWidget.view(self._currentFrameData_.qimage(normalize = self.imageNormalize))
            
                ## TODO FIXME: what if we view a transposed array ???? (e.g. viewing it on
                ## Y or X axis instead of the Z or T axis?)
                #w = self._data_.shape[self._data_.axistags.index(self.widthAxisInfo.key)] # this is not neccessarily space!
                #h = self._data_.shape[self._data_.axistags.index(self.heightAxisInfo.key)] # this is not neccessarily space!
                ## NOTE: 2017-07-24 09:03:38
                ## w and h are a convention here
                
                ## NOTE: 2017-07-26 22:18:14
                ## get calibrates axes sizes
                #cals = "(%s x %s)" % \
                    #(strutils.print_scalar_quantity(dt.getCalibratedAxisSize(self._data_, self.widthAxisInfo.key)), \
                        #strutils.print_scalar_quantity(dt.getCalibratedAxisSize(self._data_, self.heightAxisInfo.key)))
        
                #shapeTxt = "%s x %s: %d x %d %s" % \
                    #(dt.defaultAxisTypeName(self.widthAxisInfo), \
                        #dt.defaultAxisTypeName(self.heightAxisInfo), \
                        #w, h, cals)
                
                #self.slot_displayColorBar(self.displayColorBarAction.isChecked())

            #elif isinstance(self._data_, (QtGui.QImage, QtGui.QPixmap)):
                ## NOTE 2018-09-14 11:45:13
                ## TODO/FIXME adapt code to select channels from a Qimage is not allGray() or not isGrayscale()
                #self.viewerWidget.view(self._data_)
                
                #w = self._data_.width()
                #h = self._data_.height()
                #shapeTxt = "W x H: %d x %d " % (w, h)
                
            #else:
                ##print("nothing to do ?")
                #return # shouldn't really get here
            
            #self.viewerWidget.setTopLabelText(shapeTxt)
            
        #except Exception as e:
            #traceback.print_exc()
            #self._currentFrameData_ = None
            
    def _configureGUI_(self):
        self.setupUi(self)
        
        #self.setWindowTitle("Image Viewer")
        
        if self.viewerWidgetContainer.layout() is None:
            self.viewerWidgetContainer.setLayout(QtWidgets.QGridLayout(self.viewerWidgetContainer))
            
        self.viewerWidgetContainer.layout().setSpacing(0)
        self.viewerWidgetContainer.layout().setContentsMargins(0,0,0,0)
        
        self.intensityCalibrationWidget = None
            
        self.viewerWidget = GraphicsImageViewerWidget(parent = self.viewerWidgetContainer, imageViewer=self)
        self.viewerWidgetContainer.layout().setHorizontalSpacing(0)
        self.viewerWidgetContainer.layout().setVerticalSpacing(0)
        self.viewerWidgetContainer.layout().contentsMargins().setLeft(0)
        self.viewerWidgetContainer.layout().contentsMargins().setRight(0)
        self.viewerWidgetContainer.layout().contentsMargins().setTop(0)
        self.viewerWidgetContainer.layout().contentsMargins().setBottom(0)
        self.viewerWidgetContainer.layout().addWidget(self.viewerWidget, 0,0)
        
        # NOTE: 2017-12-18 09:37:07 this relates to mouse cursor position!!!
        self.viewerWidget.signalCursorAt[str, list].connect(self.slot_displayCursorPos)
        
        self.viewerWidget.scene.signalMouseAt[int, int].connect(self.slot_displayMousePos)
        #self.viewerWidget.scene.signalMouseLeave.connect(self._sceneMouseLeave)
        
        self.viewerWidget.signalCursorAdded[object].connect(self.slot_graphicsObjectAdded)
        self.viewerWidget.signalCursorChanged[object].connect(self.slot_graphicsObjectChanged)
        self.viewerWidget.signalCursorRemoved[object].connect(self.slot_graphicsObjectRemoved)
        self.viewerWidget.signalCursorSelected[object].connect(self.slot_graphicsObjectSelected)
        #self.viewerWidget.signalCursorDeselected[object].connect(self.slot_graphicsObjectDeselected)
        
        self.viewerWidget.signalRoiAdded[object].connect(self.slot_graphicsObjectAdded)
        self.viewerWidget.signalRoiChanged[object].connect(self.slot_graphicsObjectChanged)
        self.viewerWidget.signalRoiRemoved[object].connect(self.slot_graphicsObjectRemoved)
        self.viewerWidget.signalRoiSelected[object].connect(self.slot_graphicsObjectSelected)
        #self.viewerWidget.signalRoiDeselected[object].connect(self.slot_graphicsObjectDeselected)
        
        self.viewerWidget.signalGraphicsDeselected.connect(self.slot_graphicsObjectDeselected)
        
        self.actionView.triggered.connect(self.slot_loadImageFromWorkspace)
        #self.actionRefresh.triggered.connect(self.slot_refreshDisplayedWorkspaceImage)
        self.actionRefresh.triggered.connect(self.slot_refreshDataDisplay)
        
        self.actionExportAsPNG.triggered.connect(self.slot_exportSceneAsPNG)
        self.actionExportAsSVG.triggered.connect(self.slot_exportSceneAsSVG)
        self.actionExportAsTIFF.triggered.connect(self.slot_exportSceneAsTIFF)
        self.actionSaveTIFF.triggered.connect(self.slot_saveTIFF)
        
        self.displayMenu = QtWidgets.QMenu("Display", self)
        self.menubar.addMenu(self.displayMenu)
        
        self.channelsMenu = QtWidgets.QMenu("Channels", self)
        self.displayMenu.addMenu(self.channelsMenu)
        
        self.showAllChannelsAction = self.channelsMenu.addAction("All channels")
        self.showAllChannelsAction.setCheckable(True)
        self.showAllChannelsAction.setChecked(True)
        self.showAllChannelsAction.toggled[bool].connect(self.slot_displayAllChannels)
        
        self.displayIndividualChannelActions = list()
        
        self.colorMapMenu = QtWidgets.QMenu("Color Map", self)
        self.displayMenu.addMenu(self.colorMapMenu)
        
        self.cursorsRoisColorMenu = QtWidgets.QMenu("Colors for Cursor and Rois", self)
        self.displayMenu.addMenu(self.cursorsRoisColorMenu)
        
        self.colorMapAction = self.colorMapMenu.addAction("Choose Color Map")
        self.editColorMapAction = self.colorMapMenu.addAction("Edit Color Map")
        
        self.chooseCursorColorAction = self.cursorsRoisColorMenu.addAction("Set cursors color")
        self.chooseCursorColorAction.triggered.connect(self.slot_chooseCursorsColor)
        
        self.chooseCBCursorColorAction = self.cursorsRoisColorMenu.addAction("Set color for shared cursors")
        self.chooseCBCursorColorAction.triggered.connect(self.slot_chooseCBCursorsColor)
        
        self.chooseRoiColorAction = self.cursorsRoisColorMenu.addAction("Set rois color")
        self.chooseRoiColorAction.triggered.connect(self.slot_chooseRoisColor)
    
        self.chooseCBRoiColorAction = self.cursorsRoisColorMenu.addAction("Set color for shared rois")
        self.chooseCBRoiColorAction.triggered.connect(self.slot_chooseCBRoisColor)
    
        self.brightContrastGammaMenu = QtWidgets.QMenu("Brightness Contrast Gamma", self)
        self.displayMenu.addMenu(self.brightContrastGammaMenu)
        
        self.displayScaleBarAction = self.displayMenu.addAction("Scale bar")
        self.displayScaleBarAction.setCheckable(True)
        self.displayScaleBarAction.setChecked(False)
        self.displayScaleBarAction.toggled[bool].connect(self.slot_displayScaleBar)
        
        self.displayColorBarAction = self.displayMenu.addAction("Intensity Scale")
        self.displayColorBarAction.setCheckable(True)
        self.displayColorBarAction.setChecked(False)
        self.displayColorBarAction.toggled[bool].connect(self.slot_displayColorBar)
        
        self.imageBrightnessAction = self.brightContrastGammaMenu.addAction("Brightness")
        self.imageGammaAction = self.brightContrastGammaMenu.addAction("Gamma")
        
        self.framesQSlider.setMinimum(0)
        self.framesQSlider.setMaximum(0)
        self.framesQSlider.valueChanged.connect(self.slot_setFrameNumber)
        
        self._frames_slider_ = self.framesQSlider
        
        self.framesQSpinBox.setKeyboardTracking(False)
        self.framesQSpinBox.setMinimum(0)
        self.framesQSpinBox.setMaximum(0)
        self.framesQSpinBox.valueChanged.connect(self.slot_setFrameNumber)
        
        self._frames_spinner_ = self.framesQSpinBox

        #self.actionOpen.triggered.connect(self._openImageFile)
        self.editColorMapAction.triggered.connect(self._editColorMap)

        self.colorMapAction.triggered.connect(self.slot_chooseColorMap)
        self.imageBrightnessAction.triggered.connect(self._editImageBrightness)
        self.imageGammaAction.triggered.connect(self._editImageGamma)
        
        self.cursorsMenu = QtWidgets.QMenu("Cursors", self)
        
        self.menubar.addMenu(self.cursorsMenu)
        
        self.addCursorsMenu = QtWidgets.QMenu("Add Cursors", self)
        self.cursorsMenu.addMenu(self.addCursorsMenu)
        
        self.addVerticalCursorAction = self.addCursorsMenu.addAction("Vertical Cursor")
        self.addVerticalCursorAction.triggered.connect(self.viewerWidget.slot_newVerticalCursor)
        
        self.addHorizontalCursorAction = self.addCursorsMenu.addAction("Horizontal Cursor")
        self.addHorizontalCursorAction.triggered.connect(self.viewerWidget.slot_newHorizontalCursor)
        
        self.addCrosshairCursorAction = self.addCursorsMenu.addAction("Crosshair Cursor")
        self.addCrosshairCursorAction.triggered.connect(self.viewerWidget.slot_newCrosshairCursor)
        
        self.addPointCursorAction = self.addCursorsMenu.addAction("Point Cursor")
        self.addPointCursorAction.triggered.connect(self.viewerWidget.slot_newPointCursor)
        
        self.editCursorsMenu = QtWidgets.QMenu("Edit cursors", self)
        self.cursorsMenu.addMenu(self.editCursorsMenu)
        
        self.editCursorAction = self.editCursorsMenu.addAction("Edit Properties for Selected Cursor...")
        self.editCursorAction.triggered.connect(self.viewerWidget.slot_editSelectedCursor)
        
        self.editAnyCursorAction = self.editCursorsMenu.addAction("Edit Cursor Properties...")
        self.editAnyCursorAction.triggered.connect(self.viewerWidget.slot_editAnyCursor)
        
        self.removeCursorsMenu = QtWidgets.QMenu("Remove Cursors")
        
        self.removeCursorAction = self.removeCursorsMenu.addAction("Remove Selected Cursor")
        self.removeCursorAction.triggered.connect(self.viewerWidget.slot_removeSelectedCursor)
        
        self.removeAllCursorsAction = self.removeCursorsMenu.addAction("Remove All Cursors")
        self.removeAllCursorsAction.triggered.connect(self.viewerWidget.slot_removeCursors)
        
        self.cursorsMenu.addMenu(self.removeCursorsMenu)
        
        self.roisMenu = QtWidgets.QMenu("ROIs", self)
        
        # NOTE: 2017-08-10 10:23:52
        # TODO: add Point, Line, Rectangle, Ellipse, Polygon, Path, Text
        # for each of the above, give option to use the Mouse, or a dialogue for coordinates
        # to be able to generate several cursors and/or ROIs without clicking via too many
        # menus, TODO toolbar buttons (toggable) to create these
        #
        # TODO in addition, give the option to create pies and chords (secants), closed/open
        #
        # NOTE: all signals must be connected to appropriate viewerWidget slots!
        
        self.menubar.addMenu(self.roisMenu)
        
        self.addROIsMenu = QtWidgets.QMenu("Add ROIs", self)
        self.roisMenu.addMenu(self.addROIsMenu)
        
        self.newROIAction = self.addROIsMenu.addAction("New ROI")
        self.newROIAction.triggered.connect(self.viewerWidget.buildROI)
        
        self.editRoisMenu = QtWidgets.QMenu("Edit ROIs")
        self.roisMenu.addMenu(self.editRoisMenu)
        
        self.editSelectedRoiShapeAction = self.editRoisMenu.addAction("Selected ROI shape")
        self.editSelectedRoiShapeAction.triggered.connect(self.viewerWidget.slot_editRoiShape)
        
        self.editSelectedRoiPropertiesAction = self.editRoisMenu.addAction("Selected ROI Properties")
        self.editSelectedRoiPropertiesAction.triggered.connect(self.viewerWidget.slot_editRoiProperties)
        
        self.editRoiAction = self.editRoisMenu.addAction("Edit ROI...")
        self.editRoiAction.triggered.connect(self.viewerWidget.slot_editRoi)
        
        
        self.removeRoisMenu = QtWidgets.QMenu("Remove ROIs")
        self.roisMenu.addMenu(self.removeRoisMenu)
        
        self.removeSelectedRoiAction = self.removeRoisMenu.addAction("Remove Selected ROI")
        self.removeSelectedRoiAction.triggered.connect(self.viewerWidget.slot_removeSelectedRoi)
        
        self.removeAllRoisAction = self.removeRoisMenu.addAction("Remove All ROIS")
        self.removeAllRoisAction.triggered.connect(self.viewerWidget.slot_removeRois)
        
        self.toolBar = QtWidgets.QToolBar("Main", self)
        self.toolBar.setObjectName("DataViewer_Main_Toolbar")
        
        refreshAction = self.toolBar.addAction(QtGui.QIcon(":/images/view-refresh.svg"), "Refresh")
        refreshAction.triggered.connect(self.slot_refreshDataDisplay)
        
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        
        self.zoomToolBar = QtWidgets.QToolBar("Zoom Toolbar", self)
        self.zoomToolBar.setObjectName("ImageViewerZoomToolBar")
        
        self.zoomOutAction = self.zoomToolBar.addAction(QtGui.QIcon.fromTheme("zoom-out"), "Zoom Out")
        self.zoomOriginalAction = self.zoomToolBar.addAction(QtGui.QIcon.fromTheme("zoom-original"), "Original Zoom")
        self.zoomInAction = self.zoomToolBar.addAction(QtGui.QIcon.fromTheme("zoom-in"), "Zoom In")
        self.zoomAction = self.zoomToolBar.addAction(QtGui.QIcon.fromTheme("zoom"), "Zoom")
        
        #self.zoomToolBar.widgetForAction(self.zoomAction).setCheckable(True)
        
        self.zoomOutAction.triggered.connect(self.slot_zoomOut)
        self.zoomOriginalAction.triggered.connect(self.slot_zoomOriginal)
        self.zoomInAction.triggered.connect(self.slot_zoomIn)
        self.zoomAction.triggered.connect(self.slot_selectZoom)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.zoomToolBar)
    
    def _editColorMap(self):
        pass;
  
    @pyqtSlot(str)
    @safeWrapper
    def slot_testColorMap(self, item):
        self.colorMap = colormaps.get(item, None)
        self.displayFrame()
          
    @pyqtSlot()
    @safeWrapper
    def slot_chooseColorMap(self, *args):
        if self._data_ is None:
            return
        
        self.prevColorMap = self.colorMap # cache the current colorMap
        
        colormapnames = sorted([n for n in colormaps.keys()])
        
        if isinstance(self.colorMap, colors.Colormap):
            d = pgui.ItemsListDialog(self, itemsList=colormapnames, title="Select color map", preSelected=self.colorMap.name)
            
        else:
            d = pgui.ItemsListDialog(self, itemsList=colormapnames, title="Select color map", preSelected="None")
            
        d.itemSelected.connect(self.slot_testColorMap) # this will SET self.colorMap to the selected one
    
        a = d.exec_()

        if a == QtWidgets.QDialog.Accepted:
            self.displayFrame()
            
        else:
            self.colorMap = self.prevColorMap
            self.displayFrame()

    def _editImageBrightness(self):
        dlg = pgui.ImageBrightnessDialog(self)
        dlg.show()
        
    def _editImageGamma(self):
        pass;

    def _displayValueAtCoordinates(self, coords, crsId=None):
        """
        coords: a list or tuple with 2 -- 4 elements:
                (x,y), (x,y,wx), (x,y,wx,wy) where any can be None
                x,y = coordinates in the displayed frame
                wx, wy = range along the horizontal (wx) and vertical (wy) axis 
                         centered around x and y coordinate, respectively
                         
        crsId: string with cursor ID or None
        """
        if self._data_ is None:
            return
        
        #if self._currentFrameData_ is None:
            #return
        
        if coords[0] is not None:
            x = int(coords[0])
        else:
            x = None
            
        if coords[1] is not None:
            y = int(coords[1])
        else:
            y = None
        
        if len(coords) == 3:
            wx = coords[2]
        else:
            wx = None
        
        if len(coords) == 4:
            wy = coords[3]
        else:
            wy = None
            
        if isinstance(self._data_, vigra.VigraArray):
            # this can also be a PictArray!
            # NOTE: 2017-07-24 09:03:38
            # w and h are a convention here
            #w = self._data_.shape[0]
            #h = self._data_.shape[1]
            
            widthAxisIndex = self._data_.axistags.index(self.widthAxisInfo.key)
            heightAxisIndex = self._data_.axistags.index(self.heightAxisInfo.key)
            
            w = self._data_.shape[widthAxisIndex]
            h = self._data_.shape[heightAxisIndex]
            
            #
            # below, img is a view NOT a copy !
            #
            
            img, dimindices = self._generate_frame_view_(self._displayedChannel_)
            
            viewWidthAxisIndex = img.axistags.index(self.widthAxisInfo.key)
            viewHeightAxisIndex = img.axistags.index(self.heightAxisInfo.key)
            
            if wx is not None:
                cwx = dt.AxisCalibration(img.axistags[viewWidthAxisIndex]).getCalibratedAxialDistance(wx, img.axistags[viewWidthAxisIndex])
                    
                swx = " +/- %d (%.2f) " % (wx//2, cwx/2)
                
            else:
                swx = ""
                
            if wy is not None:
                cwy = dt.AxisCalibration(img.axistags[viewHeightAxisIndex]).getCalibratedAxialDistance(wy, img.axistags[viewHeightAxisIndex])
                    
                swy = " +/- %d (%.2f) " % (wy//2, cwy/2)
                
            else:
                swy = ""
            
            if crsId is not None:
                crstxt = "%s " % (crsId)
                
            else:
                crstxt = ""
                
            if x is not None and x >= w:
                x = w-1
                
            if x is not None and x < 0:
                x = 0
                
            if y is not None and y >= h:
                y = h-1
                
            if y is not None and y < 0:
                y = 0

            #print("w: %f, x: %f, h: %f, y: %f" % (w, x, h, y))
            
            if all([val is not None for val in (x,y)]):
                if img.ndim >= 2: # there may be a channel axis
                    cx = dt.AxisCalibration(img.axistags[viewWidthAxisIndex]).getCalibratedAxisCoordinate(x, img.axistags[viewWidthAxisIndex].key)
                    cy = dt.AxisCalibration(img.axistags[viewHeightAxisIndex]).getCalibratedAxisCoordinate(y, img.axistags[viewHeightAxisIndex].key)
                
                    scx = "%.2f %s" % (cx.magnitude, cx.units.dimensionality.string)
                    scy = "%.2f %s" % (cy.magnitude, cy.units.dimensionality.string)
                    
                    sx = img.axistags[viewWidthAxisIndex].key #dt.defaultAxisTypeSymbol(self._currentFrameData_.axistags[0])
                    sy = img.axistags[viewHeightAxisIndex].key #dt.defaultAxisTypeSymbol(self._currentFrameData_.axistags[1])
                    
                    if img.ndim > 2: # this is possible only when there is a channel axis!
                        if img.channels > 1:
                            val = [float(img.bindAxis("c", k)[x,y,...]) for k in range(img.channels)]
                        
                        else:
                            val = float(img[x,y])
                            
                        if self.frameAxisInfo is not None:
                            if isinstance(self.frameAxisInfo, vigra.AxisInfo):
                                if self.frameAxisInfo not in self._data_.axistags:
                                    raise RuntimeError("frame axis %s not found in the image" % self.frameAxisInfo.key)
                                
                                cz = dt.AxisCalibration(self.frameAxisInfo).getCalibratedAxisCoordinate(self._current_frame_index_, self.frameAxisInfo.key)

                                sz = self.frameAxisInfo.key

                                if isinstance(val, float):
                                    coordTxt = "%s<X: %d (%s: %s)%s, Y: %d (%s: %s)%s, Z: %d (%s: %.2f %s)> %.2f" % \
                                        (crstxt, \
                                        x, sx, scx, swx, \
                                        y, sy, scy, swy, \
                                        self._current_frame_index_, sz, cz.magnitude, cz.units.dimensionality.string, \
                                        val)
                                
                                elif isinstance(val, (tuple, list)):
                                    valstr = "(" + " ".join(["%.2f" % v for v in val]) + ")"
                                    
                                    coordTxt = "%s<X: %d (%s: %s)%s, Y: %d (%s: %s)%s, Z: %d (%s: %.2f %s)> %s" % \
                                        (crstxt, \
                                        x, sx, scx, swx, \
                                        y, sy, scy, swy, \
                                        self._current_frame_index_, sz, cz.magnitude, cz.units.dimensionality.string, \
                                        valstr)
                                    
                            else: # self.frameAxisInfo is a tuple
                                sz_cz = ", ".join(["%s: %s" % (ax.key, strutils.print_scalar_quantity(dt.AxisCalibration(ax).getCalibratedAxisCoordinate(self._current_frame_index_, ax.key))) for ax in self.frameAxisInfo])
                                
                                if isinstance(val, float):
                                    coordTxt = "%s<X: %d (%s: %s)%s, Y: %d (%s: %s)%s, Z: %d (%s)> %s" % \
                                        (crstxt, \
                                        x, sx, scx, swx, \
                                        y, sy, scy, swy, \
                                        self._current_frame_index_, sz_cz, \
                                        val)
                                
                                elif isinstance(val, (tuple, list)):
                                    valstr = "(" + " ".join(["%.2f" % v for v in val]) + ")"
                                    
                                    coordTxt = "%s<X: %d (%s: %s)%s, Y: %d (%s: %s)%s, Z: %d (%s)> %s" % \
                                        (crstxt, \
                                        x, sx, scx, swx, \
                                        y, sy, scy, swy, \
                                        self._current_frame_index_, sz_cz, \
                                        valstr)
                                    
                        else:
                            if isinstance(val, float):
                                coordTxt = "%s<X: %d (%s: %s)%s, Y: %d (%s: %s)%s> %s" % \
                                    (crstxt, \
                                    x, sx, scx, swx, \
                                    y, sy, scy, swy, \
                                    val)
                                
                            elif isinstance(val, (tuple, list)):
                                valstr = "(" + " ".join(["%.2f" % v for v in val]) + ")"
                                    
                                coordTxt = "%s<X: %d (%s: %s)%s, Y: %d (%s: %s)%s> %s" % \
                                    (crstxt, \
                                    x, sx, scx, swx, \
                                    y, sy, scy, swy, \
                                    valstr)
                                
                                
                    else:
                        val = float(np.squeeze(img[x,y]))
                        
                        coordTxt = "%s<X: %d (%s: %s)%s, Y: %d (%s: %s)%s> %.2f" % \
                            (crstxt, \
                            x, sx, scx, swx, \
                            y, sy, scy, swy, \
                            val)
                    
                else: # shouldn't realy get here, should we ?!?
                    val = float(img[x])

                    cx = dt.AxisCalibration(img.axistags[viewWidthAxisIndex]).getCalibratedAxisCoordinate(x, img.axistags[viewWidthAxisIndex].key)
                        
                    sx = img.axistags[viewWidthAxisIndex].key
                    
                    scx = "%.2f %s" % (cx.magnitude, cx.units.dimensionality.string)
                    
                    coordTxt = "%s<X: %d (%s: %s)%s> %.2f" % \
                        (crstxt, x, sx, scx, swx, val)
                    
            else:
                c_list = list()
                
                if y is None:
                    cx = dt.AxisCalibration(img.axistags[viewWidthAxisIndex]).getCalibratedAxisCoordinate(x, img.axistags[viewWidthAxisIndex])
                        
                    sx = img.axistags[viewWidthAxisIndex].key
                    
                    scx = "%.2f %s" % (cx.magnitude, cx.units.dimensionality.string)
                    
                    c_list.append("%s<X: %d (%s: %s)%s" % ((crstxt, x, sx, scx, swx)))
                    
                elif x is None:
                    cy = dt.AxisCalibration(img.axistags[viewHeightAxisIndex]).getCalibratedAxisCoordinate(y, img.axistags[viewHeightAxisIndex])
                        
                    sy = img.axistags[viewHeightAxisIndex].key
                    
                    scy = "%.2f %s" % (cy.magnitude, cy.units.dimensionality.string)
                    
                    c_list.append("%s<Y: %d (%s: %s)%s" % ((crstxt, y, sy, scy, swy)))
                
                if img.ndim > 2:
                    if self.frameAxisInfo is not None:
                        if isinstance(self.frameAxisInfo, vigra.AxisInfo):
                            if self.frameAxisInfo not in self._data_.axistags:
                                raise RuntimeError("frame axis intfo %s not found in the image" % self.frameAxisInfo.key)
                        
                            cz = dt.AxisCalibration(self.frameAxisInfo).getCalibratedAxisCoordinate(self._current_frame_index_, self.frameAxisInfo)
                        
                            sz = self.frameAxisInfo.key #dt.defaultAxisTypeSymbol(self.frameAxisInfo)
                        
                            c_list.append(", Z: %d (%s: %s)>" % (self._current_frame_index_, sz, cz))
                            
                        else:
                            sz_cz = ", ".join(["%s: %s" % (ax.key, dt.AxisCalibration(ax).getCalibratedAxisCoordinate(self._current_frame_index_, ax.key)) for ax in self.frameAxisInfo])
                                
                            c_list.append("(%s)" % sz_cz)
    
                    else:
                        c_list.append(">")
                    
                else:
                    c_list.append(">")
                
                coordTxt = "".join(c_list)
                
                    
            self.statusBar().showMessage(coordTxt)
            
        elif isinstance(self._data_, (QtGui.QImage, QtGui.QPixmap)):
            w = self._data_.width()
            h = self._data_.height()
        
            if wx is not None:
                swx = " +/- %d " % (wx//2)
            else:
                swx = ""
                
            if wy is not None:
                swy = " +/- %d " % (wy//2)
            else:
                swy = ""
            
            if crsId is not None:
                crstxt = "%s " % (crsId)
            else:
                crstxt = ""

            if isinstance(self._data_, QtGui.QImage):
                #val = self._data_.pixel(x,y)
                if self._data_.isGrayscale():
                    val = self._data_.pixel(x,y)
                    
                else:
                    pval = self._data_.pixelColor(x,y)
                    val = "R: %d, G: %d, B: %d, A: %d" % (pval.red(), pval.green(), pval.blue(), pval.alpha())
                    
                    
                msg = "%s<X %d%s, Y %d%s> : %s" % \
                    (crstxt, x, swx, y, swy, val)

            elif isinstance(self._data_, QtGui.QPixmap):
                pix = self._data_.toImage()
                if pix.isGrayscale():
                    val = pix.pixel(x,y)
                    
                else:
                    pval = pix.pixelColor(x,y)
                    val = "R: %d, G: %d, B: %d, A: %d" % (pval.red(), pval.green(), pval.blue(), pval.alpha())
                
                msg = "%s<X %d%s, Y %d%s> : %s" % \
                    (crstxt, x, swx, y, swy, val)

            else:
                val = None

            self.statusBar().showMessage(msg)
            
        else:
            return # shouldn't really get here
        
    ####
    # public methods
    ####
    
    def graphicsObjects(self, rois=None):
        """Delegation in order to keep code using ImageViewer small.
        
        rois: boolean or None (default)
        
            When None: returns a dict where keys are all registered graphics objects
                        and values are dicts
                        
            NOTE:  this is NOT a ChainMap
            
            When True: returns the dictionary of rois (a ChainMap)
            
            When False: returns the dictionary of cursors (a ChainMap)
            
        
        """
        if rois is None:
            return self.viewer.__graphicsObjects__
        
        elif rois is True:
            return self.viewer.rois
        
        else:
            return self.viewer.cursors
        
    def graphicsObject(self, name):
        """Delegation in order to keep code using ImageViewer small.
        
        Delegates to self.roi(value) if roi, or self.cursor(value) otherwise
        """
        if name in self.graphicsObjects(rois=True):
            return self.roi(name)
        
        if name in self.graphicsObjects(rois=False):
            return self.cursor(name)
        
    def hasGraphicsObject(self, name):
        """Delegation in order to keep code using ImageViewer small.
        
        Delegates to self.hasRoi(value) if roi, or self.hasCursor(value) otherwise
        """
        
        return name in self.rois or name in self.cursors
        
    @safeWrapper
    def slot_removeCursorByName(self, crsId):
        if crsId in self.graphicsObjects(rois=False):
            self.viewerWidget.slot_removeCursorByName(crsId)
        
    @safeWrapper
    def slot_removeRoiByName(self, crsId):
        if crsId in self.graphicsObjects(rois=True):
            self.viewerWidget.slot_removeRoiByName(crsId)
        
    @safeWrapper
    def removeGraphicsObject(self, name):
        #print("ImageViewer %s removeGraphicsObject %s" % (self.windowTitle(), name))
        if name in self.graphicsObjects(rois=True):
            self.viewerWidget.slot_removeRoiByName(name)
            
        elif name in self.graphicsObjects(rois=False):
            self.viewerWidget.slot_removeCursorByName(name)
        
    def _load_viewer_settings_(self):
        #colorMapName = self.settings.value("ImageViewer/ColorMap", None)
        colorMapName = self.settings.value("/".join([self.__class__.__name__, "ColorMap"]), None)
        
        if isinstance(colorMapName, str):
            self.colorMap = colormaps.get(colorMapName, None)
                
        elif isinstance(colorMapName, mpl.colors.Colormap):
            self.colorMap = colorMapName
            
        else:
            self.colorMap = None
        
        #color = self.settings.value("ImageViewer/CursorsColor", None)
        color = self.settings.value("/".join([self.__class__.__name__, "CursorColor"]), None)
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.cursorsColor = color
            
        #color = self.settings.value("ImageViewer/RoisColor", None)
        color = self.settings.value("/".join([self.__class__.__name__, "RoisColor"]), None)
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.roisColor = color
        
        #color = self.settings.value("ImageViewer/SharedCursorsColor", None)
        color = self.settings.value("/".join([self.__class__.__name__, "SharedCursorsColor"]), None)
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.sharedCursorsColor = color
            
        #color = self.settings.value("ImageViewer/SharedRoisColor", None)
        color = self.settings.value("/".join([self.__class__.__name__, "SharedRoisColor"]), None)
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.sharedRoisColor = roiscolor
            
    def _save_viewer_settings_(self):
        if isinstance(self.colorMap, mpl.colors.Colormap):
            self.settings.setValue("/".join([self.__class__.__name__, "ColorMap"]), self.colorMap.name)
            
        else:
            self.settings.setValue("/".join([self.__class__.__name__, "ColorMap"]), None)
        
        self.settings.setValue("/".join([self.__class__.__name__, "CursorColor"]), self.cursorsColor)
        
        self.settings.setValue("/".join([self.__class__.__name__, "RoisColor"]), self.roisColor)
        
        self.settings.setValue("/".join([self.__class__.__name__, "SharedCursorsColor"]), self.sharedCursorsColor)
        
        self.settings.setValue("/".join([self.__class__.__name__, "SharedRoisColor"]), self.sharedRoisColor)
            
    def setImage(self, image, doc_title=None, normalize=True, colormap=None, gamma=None,
                 frameAxis=None, displayChannel=None):
        self.setData(image, doc_title=doc_title, normalize=normalize, colortable=colortable, gamma=gamma,
                     frameAxis=frameAxis, displayChannel=displayChannel)
        
    def displayChannel(self, channel_index):
        if isinstance(self._data_, vigra.VigraArray):
            if channel_index < 0 or channel_index >= self._data_.channels:
                raise ValueError("channel_index must be in the semi-open interval [0, %d); got %s instead" % (self._data_.channels, channel_index))
            
        # see NOTE: 2018-09-25 23:06:55
        sigBlock = QtCore.QSignalBlocker(self.showAllChannelsAction)
        
        #self.showAllChannelsAction.toggled[bool].disconnect(self.slot_displayAllChannels)
        self.showAllChannelsAction.setChecked(False)
        #self.showAllChannelsAction.toggled[bool].connect(self.slot_displayAllChannels)#
        
        self.displayFrame(channel_index)
        self._displayedChannel_ = channel_index
        
    def displayAllChannels(self):
        # see NOTE: 2018-09-25 23:06:55
        signalBlockers = [QtCore.QSignalBlocker(widget) for widget in self.displayIndividualChannelActions]
        for action in self.displayIndividualChannelActions:
            #action.triggered.disconnect(self.slot_displayChannel)
            action.setChecked(False)
            #action.triggered.connect(self.slot_displayChannel)
            
        self.displayFrame("all")
        self._displayedChannel_ = "all"
        
    def view(self, image, doc_title=None, normalize=True, colortable=None, gamma=None,
             frameAxis=None, displayChannel=None, frameIndex=None):
        self.setData(image, doc_title=doc_title, normalize=normalize, colortable=colortable, gamma=gamma,
                     frameAxis=frameAxis, frameIndex=None, displayChannel=displayChannel)
        
    def _set_data_(self, data, normalize=True, colortable = None, gamma = None, 
            frameAxis=None, frameIndex=None, 
            arrayAxes:(type(None), vigra.AxisTags) = None, 
            displayChannel = None, 
            doc_title:(str, type(None)) = None,
            *args, **kwargs):
        '''
        SYNTAX: self.view(image, title = None, normalize = True, colortable = None, gamma = None, separateChannels = False, frameAxis = None)
    
        Parameters:
        ============
            image: a vigra.VigraArray object with up to 4 dimensions (for now) or a QImage or QPixmap
      
            title: a str, default None
            
            normalize: bool, default True
            
            colortable: default None
            
            gamma: float scalar or None (default)
            
            frameAxis: int, str, vigra.AxisInfo or None (default)
            
            displaychannel: int, "all", or None (default)
        '''
        
        self.colorTable         = colortable
        self.imageNormalize     = normalize
        self.imageGamma         = gamma

        if self.colorbar is not None:
            self.viewerWidget.scene.removeItem(self.colorbar)
            
        self.colorbar = None
                
        if displayChannel is None:
            self._displayedChannel_      = "all"
            
        else:
            if isinstance(displayChannel, str):
                if displayChannel.lower().strip()!="all":
                    raise ValueError("When a str, displayChannel must be 'all'; got %s instead" % displayChannel)
                
            elif isinstance(displayChannel, int):
                if displayChannel < 0:
                    raise ValueError("When an int, display channel must be >= 0")
                
            self._displayedChannel_ = displayChannel

        if isinstance(data, vigra.VigraArray):
            if isinstance(frameAxis, (int, str, vigra.AxisInfo)):
                self.userFrameAxisInfo  = frameAxis
                
            if self._parseVigraArrayData_(data):
                self._data_  = data
                self._setup_channels_display_actions_()
                self.displayFrame()
            
        elif isinstance(data, (QtGui.QImage, QtGui.QPixmap)):
            self._number_of_frames_ = 1
            self._data_  = data
            self.displayFrame()
            
        elif isinstance(data, np.ndarray):
            if arrayAxes is None:
                if data.ndim  == 1:
                    arrayAxes = vigra.VigraArray.defaultAxistags("x")
                    
                elif data.ndim == 2:
                    if utilities.isVector(data):
                        arrayAxes = vigra.VigraArray.defaultAxistags("y")
                    else:
                        arrayAxes = vigra.VigraArray.defaultAxistags("xy")
                    
                else:
                    arrayAxes = vigra.VigraArray.defaultAxistags(data.ndim, noChannels=True)
                    
            self._data_ = vigra.VigraArray(data, axistags=arrayAxes)
            
        else:
            raise TypeError("First argument must be a VigraArray or a numpy.ndarray")
        
        if kwargs.get("show", True):
            self.activateWindow()
        
    def clear(self):
        """Clears all image data cursors and rois from this window
        """
        self._number_of_frames_ = 0
        self._current_frame_index_ = 0
        self.framesQSlider.setMaximum(0)
        self.framesQSpinBox.setMaximum(0)
        self._data_ = None
        #self.imageNormalize             = None
        #self.imageGamma                 = None
        #self.colorMap                   = None
        #self.prevColorMap               = None
        #self.colorTable                 = None
        self._separateChannels           = False
        #self.setWindowTitle("Image Viewer")
        self.tStride                    = 0
        self.zStride                    = 0
        self.frameAxisInfo              = None
        self.userFrameAxisInfo          = None
        self.widthAxisInfo              = None # this is "visual" width which may not be on a spatial axis "x"
        self.heightAxisInfo             = None # this is "visual" height which may not be on a spatial axis "y"
        self._currentZoom_               = 0
        self._currentFrameData_          = None
        self._xScaleBar_                 = None
        self._xScaleBarTextItem_         = None
        self._yScaleBar_                 = None
        self._yScaleBarTextItem_         = None
        
        # see NOTE: 2018-09-25 23:06:55
        sigBlock = QtCore.QSignalBlocker(self.displayScaleBarAction)
        #self.displayScaleBarAction.toggled[bool].disconnect(self.slot_displayScaleBar)
        self.displayScaleBarAction.setChecked(False)
        #self.displayScaleBarAction.toggled[bool].connect(self.slot_displayScaleBar)
        
        if self.colorbar is not None:
            self.viewerWidget.scene.removeItem(self.colorbar)
            
            self.colorbar = None
        
        self.viewerWidget.clear()
        
    def setColorMap(self, value):
        if isinstance(value, str):
            self.colorMap = colormaps.get(value, None)
            
        elif isinstance(value, colors.Colormap):
                self.colorMap = value
                
        else:
            return
        
        self.displayFrame()
        
        
    def showScaleBars(self, origin=None, length=None, calibrated_length=None, pen=None, units=None):
        """Shows a scale bar for both axes in the display
        origin: tuple or list with (x,y) coordinates of scale bars origin
        length: tuple or list with the length of the respective scale bars (x and y)
        
        NOTE: both values are in pixels (i.e. ints)
        
        """
        
        if self._data_ is None:
            return
        
        if isinstance(self._data_, vigra.VigraArray):
            w = self._data_.shape[0]
            h = self._data_.shape[1]

        elif isinstance(self._data_, (QtGui.QImage, QtGui.QPixmap)):
            w = self._data_.width()
            h = self._data_.height()
            
        else:
            return # shouldn't really get here
    
        if origin is None:
            origin = self._scaleBarOrigin_
            
        if length is None:
            length = self._scaleBarLength_
            
        if calibrated_length is not None:
            cal_x = calibrated_length[0]
            cal_y = calibrated_length[1]
            
        else:
            cal_x = None
            cal_y = None
            
        if pen is None:
            pen = self._scaleBarPen_
            
        elif not isinstance(pen, QtGui.QPen):
            raise TypeError("Expecting a QtGui.QPen or None; got %s instead" % type(pen).__name__)
        
        if isinstance(pen, QtGui.QPen):
            self._scaleBarPen_ = pen
            
        if isinstance(units, tuple) and len(units) == 2 \
            and all([isinstance(u, (pq.Quantity, pq.UnitQuantity)) for u in units]):
                
            units_x = str(units[0].dimensionality)
            units_y = str(units[1].dimensionality)
                
        else:
            units_x = None
            units_y = None
        
        if self._display_horizontal_scalebar_:
            if self._xScaleBar_ is None:
                self._xScaleBar_ = QtWidgets.QGraphicsLineItem()
                #self._xScaleBar_.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                self._xScaleBar_.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
                self._xScaleBar_.setPen(self._scaleBarPen_)

                if self._xScaleBarTextItem_ is None:
                    self._xScaleBarTextItem_ = QtWidgets.QGraphicsTextItem(self._xScaleBar_)
                    self._xScaleBarTextItem_.setDefaultTextColor(self._scaleBarColor_)
                    self._xScaleBarTextItem_.setFont(QtGui.QFont("sans-serif"))
                    self._xScaleBarTextItem_.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                    self._xScaleBarTextItem_.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
                
                self.scene.addItem(self._xScaleBar_)
                
            self._xScaleBar_.setLine(origin[0], origin[1], 
                                    origin[0] + length[0], 
                                    origin[1])
        
            if cal_x is not None:
                self._xScaleBarTextItem_.setPlainText("%s" % cal_x)
                
            else:
                if units_x is not None:
                    self._xScaleBarTextItem_.setPlainText("%d %s" % (length[0], units_x))
                    
                else:
                    self._xScaleBarTextItem_.setPlainText("%d" % length[0])
                
            self._xScaleBarTextItem_.setPos(length[0]-self._xScaleBarTextItem_.textWidth(),
                                           3 * self._xScaleBar_.pen().width())
            
            self._xScaleBar_.setVisible(True)

        if self._display_vertical_scalebar_:
            if self._yScaleBar_ is None:
                self._yScaleBar_ = QtWidgets.QGraphicsLineItem()
                self._yScaleBar_.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
                #self._yScaleBar_.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                self._yScaleBar_.setPen(self._scaleBarPen_)

                if self._yScaleBarTextItem_ is None:
                    self._yScaleBarTextItem_ = QtWidgets.QGraphicsTextItem(self._yScaleBar_)
                    self._yScaleBarTextItem_.setDefaultTextColor(self._scaleBarColor_)
                    self._yScaleBarTextItem_.setFont(QtGui.QFont("sans-serif"))
                    self._yScaleBarTextItem_.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                    self._yScaleBarTextItem_.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
                
                self.scene.addItem(self._yScaleBar_)
                
            self._yScaleBar_.setLine(origin[0], origin[1],
                                    origin[0],
                                    origin[1] + length[1])
        
            if cal_y is not None:
                self._yScaleBarTextItem_.setPlainText("%s" % cal_y)
                
            else:
                if units_y is not None:
                    self._yScaleBarTextItem_.setPlainText("%d %s" % (length[1], units_y))
                    
                else:
                    self._yScaleBarTextItem_.setPlainText("%d" % length[1])
                
            self._yScaleBarTextItem_.setPos(3 * self._yScaleBar_.pen().width(),
                                           0)
            
            self._yScaleBarTextItem_.setRotation(-90)
                
            self._yScaleBar_.setVisible(True)
            
        self._scaleBarLength_ = length
        self._scaleBarOrigin_ = origin
        
        
        
        
        
    def addGraphicsObject(self, item, pos=None, movable=True, editable=True, 
                          label=None, window=None, radius=None, 
                          frame=None, framesVisible=None,
                          showLabel=True, labelShowsPosition=True):
        """Manually add a roi or a cursor to the underlying scene.
        
        Parameters:
        ===========
        
        item: either:
        
            a) pictgui.Cursor, a cursor GraphicsObjectType enum value (or int, 
                    resolving to a cursor GraphicsObjectType enum), 
                    
            or:
                    
            b) pictgui.Path, pctgui.Rect, pictgui.Ellipse, or a non-cursor 
               GraphicsObjectType enum (or int resolving to a non-cursor
               GraphicsObjectType enum) 
               
        Keyword parameters:
        ==================
        Passed to GraphicsObject constructor via GraphicsImageViewerWidget 
        createNewRoi() or createnewCursor() methods.
        
        """
        
        if isinstance(item, pgui.Cursor):
            #print("window %s adds cursor %s in frame %s\n" % (self.__repr__(), item.type, framesVisible))
            
            if framesVisible is None:
                framesVisible = item.frameIndices
                
            
            obj = self.viewerWidget.createNewCursor(item, 
                                                    pos                 = pos,
                                                    movable             = movable,
                                                    editable            = editable, 
                                                    frame               = frame,
                                                    label               = label,
                                                    frameVisibility     = framesVisible,
                                                    showLabel           = showLabel,
                                                    labelShowsPosition  = labelShowsPosition,
                                                    parentWidget        = self)
            
        elif isinstance(item, (int, pgui.GraphicsObjectType)) and \
            item & pgui.GraphicsObjectType.allCursorTypes:
            
            obj = self.viewerWidget.createNewCursor(item, 
                                                    window              = window, 
                                                    radius              = radius, 
                                                    pos                 = pos, 
                                                    movable             = movable, 
                                                    editable            = editable, 
                                                    frame               = frame, 
                                                    label               = label, 
                                                    frameVisibility     = framesVisible, 
                                                    showLabel           =  showLabel,
                                                    labelShowsPosition  = labelShowsPosition,
                                                    parentWidget        = self)
        
        elif isinstance(item, pgui.PlanarGraphics):
            roiType = item.type

            if framesVisible is None:
                framesVisible = item.frameIndices
                
            obj = self.viewerWidget.createNewRoi(params                 = item, 
                                                 roiType                =  roiType, 
                                                 label                  = label, 
                                                 frame                  = frame, 
                                                 pos                    = pos,
                                                 movable                =  movable, 
                                                 editable               = editable, 
                                                 frameVisibility        = framesVisible,
                                                 showLabel              = showLabel,
                                                 labelShowsPosition     = labelShowsPosition,
                                                 parentWidget           = self)
            
        else:
            raise TypeError("Unexpected item parameter: %s" % type(item).__name__)

        if isinstance(obj, pgui.PlanarGraphics) and obj.objectType & pgui.GraphicsObjectType.allCursorTypes:
            if isinstance(self.cursorsColor, QtGui.QColor) and self.cursorsColor.isValid():
                obj.color = self.cursorsColor
                
        else:
            if isinstance(self.roisColor, QtGui.QColor) and self.roisColor.isValid():
                obj.color = self.roisColor
                
        return obj
    
    @pyqtSlot()
    @safeWrapper
    def slot_chooseCursorsColor(self):
        if isinstance(self.cursorsColor, QtGui.QColor):
            initial = self.cursorsColor
            
        else:
            initial = QtCore.Qt.white

        color = QtWidgets.QColorDialog.getColor(initial=initial, 
                                                title="Choose cursors color",
                                                options=QtWidgets.QColorDialog.ShowAlphaChannel)
            
        self.setCursorsColor(color)
        
    @pyqtSlot()
    @safeWrapper
    def slot_chooseRoisColor(self):
        if isinstance(self.roisColor, QtGui.QColor):
            initial = self.roisColor
            
        else:
            initial = QtCore.Qt.white

        color = QtWidgets.QColorDialog.getColor(initial=initial, 
                                                title="Choose cursors color",
                                                options=QtWidgets.QColorDialog.ShowAlphaChannel)
        
        self.setRoisColor(color)
            
    @pyqtSlot()
    @safeWrapper
    def slot_chooseCBCursorsColor(self):
        if isinstance(self.cursorsColor, QtGui.QColor):
            initial = self.cursorsColor
            
        else:
            initial = QtCore.Qt.white

        color = QtWidgets.QColorDialog.getColor(initial=initial, 
                                                title="Choose cursors color",
                                                options=QtWidgets.QColorDialog.ShowAlphaChannel)
            
        self.setSharedCursorsColor(color)
        
    @pyqtSlot()
    @safeWrapper
    def slot_chooseCBRoisColor(self):
        if isinstance(self.sharedRoisColor, QtGui.QColor):
            initial = self.sharedRoisColor
            
        else:
            initial = QtCore.Qt.white

        color = QtWidgets.QColorDialog.getColor(initial=initial, 
                                                title="Choose cursors color",
                                                options=QtWidgets.QColorDialog.ShowAlphaChannel)
        
        self.setSharedRoisColor(color)
            
    def setCursorsColor(self, color):
        #print("ImageViewer.setCursorsColor", color)
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.cursorsColor = color
            for obj in self.graphicsObjects(rois=False).values():
                obj.color = self.cursorsColor
        
    def setRoisColor(self, color):
        #print("ImageViewer.setRoisColor", color)
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.roisColor = color
            for obj in self.graphicsObjects(rois=True).values():
                obj.color = self.roisColor
    
    def setSharedCursorsColor(self, color):
        #print("ImageViewer.setSharedCursorsColor", color.name())
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.sharedCursorsColor = color
            for obj in self.graphicsObjects(rois=False).values():
                obj.colorForSharedBackend = self.sharedCursorsColor
        
    def setSharedRoisColor(self, color):
        #print("ImageViewer.setRoisColor", color)
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.sharedRoisColor = color
            for obj in self.graphicsObjects(rois=True).values():
                obj.colorForSharedBackend = self.sharedRoisColor
        
    
