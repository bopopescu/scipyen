# -*- coding: utf-8 -*-
"""
Qt5-based viewer window for dict and subclasses
TODO
"""

#### BEGIN core python modules
from __future__ import print_function

import os, warnings
#### END core python modules

#### BEGIN 3rd party modules
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Q_ENUMS, Q_FLAGS, pyqtProperty
from PyQt5.uic import loadUiType as __loadUiType__

from pyqtgraph import DataTreeWidget
import neo
import numpy as np
#### END 3rd party modules

#### BEGIN pict.core modules
import core.datatypes as dt
import core.analysisunit
from core.analysisunit import AnalysisUnit

import core.axiscalibration
from core.axiscalibration import AxisCalibration

import core.scandata
from core.scandata import ScanData

import core.triggerprotocols
from core.triggerprotocols import TriggerEvent, TriggerProtocol

import core.datasignal
from core.datasignal import DataSignal, IrregularlySampledDataSignal

from core import xmlutils, strutils

from core.workspacefunctions import validateVarName

from core.utilities import (get_nested_value, set_nested_value, counterSuffix, )

from core.prog import (safeWrapper, safeGUIWrapper, )

#### END pict.core modules

#### BEGIN pict.gui modules
from .scipyenviewer import ScipyenViewer #, ScipyenFrameViewer
from . import quickdialog
from . import resources_rc
#### END pict.gui modules

class InteractiveTreeWidget(DataTreeWidget):
    """Adds support for custom context menu to pyqtgraph.DataTreeWidget.
    """
    def __init__(self, *args, **kwargs):
        super(InteractiveTreeWidget, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    

class DataViewer(ScipyenViewer): #, QtWidgets.QMainWindow):
    """Viewer for hierarchical collection types: (nested) dictionaries, lists, arrays
    Uses InteractiveTreeWidget which inherits from pyqtgraph DataTreeWidget 
    and in turn inherits from QTreeWidget.
    """
    sig_activated = pyqtSignal(int)
    closeMe  = pyqtSignal(int)
    signal_window_will_close = pyqtSignal()
    
    # TODO: 2019-11-01 22:44:34
    # implement viewing of other data structures (e.g., viewing their __dict__
    # for the generic case, )
    supported_types = (dict, list, tuple,
                        AnalysisUnit,
                        AxisCalibration,
                        neo.core.baseneo.BaseNeo,
                        ScanData, 
                        TriggerProtocol)
    
    view_action_name = "Object"
    
    def __init__(self, data: (object, type(None)) = None, parent: (QtWidgets.QMainWindow, type(None)) = None, 
                 pWin: (QtWidgets.QMainWindow, type(None))= None, ID:(int, type(None)) = None,
                 win_title: (str, type(None)) = None, doc_title: (str, type(None)) = None,
                 *args, **kwargs) -> None:
        super().__init__(data=data, parent=parent, pWin=pWin, win_title=win_title, doc_title = doc_title, ID=ID, *args, **kwargs)
        
    def _configureGUI_(self):
        #self.treeWidget = DataTreeWidget(parent = self)
        self.treeWidget = InteractiveTreeWidget(parent = self)
        
        self.treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        # TODO implement dragging from here to the workspace
        self.treeWidget.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.treeWidget.setDragEnabled(True)
        
        self.treeWidget.customContextMenuRequested[QtCore.QPoint].connect(self.slot_customContextMenuRequested)
        
        self.treeWidget.itemDoubleClicked[QtWidgets.QTreeWidgetItem, int].connect(self.slot_itemDoubleClicked)
        
        self.setCentralWidget(self.treeWidget)
        
        self.toolBar = QtWidgets.QToolBar("Main", self)
        self.toolBar.setObjectName("DataViewer_Main_Toolbar")
        
        refreshAction = self.toolBar.addAction(QtGui.QIcon(":/images/view-refresh.svg"), "Refresh")
        refreshAction.triggered.connect(self.slot_refreshDataDisplay)
        
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        
    #def setData(self, data:object, *args, **kwargs):
        #self._set_data_(data)
        
    def _set_data_(self, data:object, *args, **kwargs):
        """
        Display new data
        # TODO 2019-09-14 10:16:03:
        # expand this to other hierarchical containers including those in
        # the neo package (neo.Block, neo.Segment, neo.Unit, etc) and in the
        # datatypes module (ScanData)
        # FIXME you may want to override some of the pyqtgraph's DataTreeWidget
        # to treat other data types as well.
        # Solutions to be implemented in the InteractiveTreeWidget in this module
        """
        #print(data)
        
        if not isinstance(data, (dict, tuple, list)):
            # quick and dirty workaround for TODO 2019-09-14 10:16:03
            #data = {"Type":type(data).__name__, "__dict__":data.__dict__}
            data = {"Type":type(data), "__dict__":data.__dict__}
        
        if data is not self._data_:
            self._data_ = data
            
            self.treeWidget.setData(self._data_)
            
            top_title = self._docTitle_ if (isinstance(self._docTitle_, str) and len(self._docTitle_.strip())) else "/"
            
            if self.treeWidget.topLevelItemCount() == 1:
                self.treeWidget.topLevelItem(0).setText(0, top_title)
                
            for k in range(self.treeWidget.topLevelItemCount()):
                self._collapseRecursive_(self.treeWidget.topLevelItem(k), collapseCurrent=False)
                
        if kwargs.get("show", True):
            self.activateWindow()

    @pyqtSlot()
    @safeWrapper
    def slot_refreshDataDisplay(self):
        self.treeWidget.setData(self._data_)

        top_title = self._docTitle_ if (isinstance(self._docTitle_, str) and len(self._docTitle_.strip())) else "/"
        
        if self.treeWidget.topLevelItemCount() == 1:
            self.treeWidget.topLevelItem(0).setText(0, top_title)
            
        for k in range(self.treeWidget.topLevelItemCount()):
            self._collapseRecursive_(self.treeWidget.topLevelItem(k), collapseCurrent=False)

    @pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    @safeWrapper
    def slot_itemDoubleClicked(self, item, column):
        if self._scipyenWindow_ is None:
            return
        
        item_path = list()
        item_path.append(item.text(0))
        
        parent = item.parent()
        
        while parent is not None:
            item_path.append(parent.text(0))
            parent = parent.parent()
        
        item_path.reverse()
        
        obj = get_nested_value(self._data_, item_path[1:]) # because 1st item is the insivible root name
        
        #objname = strutils.string_to_valid_identifier(item_path[-1])
        objname = " > ".join(item_path)
        
        newWindow = bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier)
        
        #useSignalViewerForNdArrays = bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ControlModifier)
        
        self._scipyenWindow_.viewObject(obj, objname, 
                                       newWindow=newWindow)
        
        
    @pyqtSlot(QtCore.QPoint)
    @safeWrapper
    def slot_customContextMenuRequested(self, point):
        # FIXME/TODO copy to system clipboard? - what mime type? JSON data?
        if self._scipyenWindow_ is None: 
            return
        
        indexList = self.treeWidget.selectedIndexes()
        
        if len(indexList) == 0:
            return
        
        cm = QtWidgets.QMenu("Data operations", self)
        cm.setToolTipsVisible(True)
        
        copyItemData = cm.addAction("Copy to workspace")
        copyItemData.setToolTip("Copy item data to workspace (SHIFT to assign full path as name)")
        copyItemData.setStatusTip("Copy item data to workspace (SHIFT to assign full path as name)")
        copyItemData.setWhatsThis("Copy item data to workspace (SHIFT to assign full path as name)")
        copyItemData.triggered.connect(self.slot_exportItemDataToWorkspace)
        
        copyItemPath = cm.addAction("Copy path(s)")
        copyItemPath.triggered.connect(self.slot_copyPaths)
        
        sendToConsole = cm.addAction("Send data path to console")
        sendToConsole.triggered.connect(self.slot_exportItemPathToConsole)
        
        viewItemData = cm.addAction("View")
        viewItemData.setToolTip("View item in a separate window (SHIFT for a new window)")
        viewItemData.setStatusTip("View item in a separate window (SHIFT for a new window)")
        viewItemData.setWhatsThis("View item in a separate window (SHIFT for a new window)")
        viewItemData.triggered.connect(self.slot_viewItemDataInNewWindow)
        
        cm.popup(self.treeWidget.mapToGlobal(point), copyItemData)
        
    @safeWrapper
    def getSelectedPaths(self):
        items = self.treeWidget.selectedItems()
        
        if len(items) == 0:
            return
        
        if isinstance(self._data_, (dict, tuple, list)):
            item_paths = list()
            
            for item in items:
                item_path = self._get_path_for_item_(item)
                path_element_strings = [item_path[0]]
                
                for ipath in item_path[1:]:
                    path_element_strings.append("['"+ipath+"']")
                    
                item_paths.append("".join(path_element_strings))
                
        return item_paths
        
    @safeWrapper
    def exportPathsToClipboard(self, item_paths):
        if self._scipyenWindow_ is None:
            return
        
        if len(item_paths) > 1:
            if bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ControlModifier):
                self._scipyenWindow_.app.clipboard().setText(",\n".join(item_paths))
            else:
                self._scipyenWindow_.app.clipboard().setText(", ".join(item_paths))
                
        elif len(item_paths) == 1:
            self._scipyenWindow_.app.clipboard().setText(item_paths[0])
        
    @pyqtSlot()
    @safeWrapper
    def slot_copyPaths(self):
        if self._scipyenWindow_ is None:
            return
        
        item_paths = self.getSelectedPaths()
        self.exportPathsToClipboard(item_paths)

    @pyqtSlot()
    @safeWrapper
    def slot_exportItemPathToConsole(self):
        if self._scipyenWindow_ is None:
            return
        
        item_paths = self.getSelectedPaths()
        self.exportPathsToClipboard(item_paths)
        self._scipyenWindow_.console.paste()
                
    @pyqtSlot()
    @safeWrapper
    def slot_exportItemDataToWorkspace(self):
        fullPathAsName = bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier)
        
        if self._scipyenWindow_ is None:
            return
        
        items = self.treeWidget.selectedItems()
        
        if len(items) == 0:
            return
        
        self._export_data_items_(items, fullPathAsName=fullPathAsName)
        
    @pyqtSlot()
    @safeWrapper
    def slot_viewItemDataInNewWindow(self):
        if self._scipyenWindow_ is None:
            return
        
        items = self.treeWidget.selectedItems()
        
        if len(items) == 0:
            return
        
        values = list()
        
        item_paths = list()
        
        full_item_paths = list()
        
        useSignalViewerForNdArrays = bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ControlModifier)
        
        if isinstance(self._data_, (dict, tuple, list)):
            for item in items:
                item_path = list()
                item_path.append(item.text(0))
                
                parent = item.parent()
                
                while parent is not None:
                    item_path.append(parent.text(0))
                    parent = parent.parent()
                
                item_path.reverse()
                
                value = get_nested_value(self._data_, item_path[1:]) # because 1st item is the insivible root name
                
                values.append(value)
                
                item_paths.append(item_path[-1]) # object names
                
                full_item_paths.append(item_path)
                
            if len(values):
                if len(values) == 1:
                    obj = values[0]
                    #objname = strutils.string_to_valid_identifier(item_paths[-1])
                    newWindow = bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier)
        
                    objname = " \u3009".join(full_item_paths[0])
                    
                    # NOTE: 2019-09-09 22:15:45
                    # cannot use the ScipyenWindow logic to fallback to showing
                    # the variable in console using "execute()" because the
                    # variable (or object) is NOT visible in user's workspace
                    # FIXME how to do this?
                    # WORKAROUND: for now, copy the variable to workspace and 
                    # go from there
                    self._scipyenWindow_.viewObject(obj, objname, 
                                                   newWindow=newWindow)
                    
                else:
                    for name, path, obj in zip(item_paths, full_item_paths, values):
                        objname = " > ".join(path)
                        self._scipyenWindow_.viewObject(obj, objname, 
                                                       newWindow=True)
    
    @safeWrapper
    def _get_path_for_item_(self, item):
        item_path = list()
        item_path.append(item.text(0))
        
        parent = item.parent()
        
        while parent is not None:
            item_path.append(parent.text(0))
            parent = parent.parent()
        
        item_path.reverse()
        
        return item_path
    
    @safeWrapper
    def _export_data_items_(self, items, fullPathAsName=False):
        if self._scipyenWindow_ is None:
            return
        
        values = list()
        
        item_names = list()
        
        item_path_names = list()
        
        if isinstance(self._data_, (dict, tuple, list)):
            for item in items:
                item_path = self._get_path_for_item_(item)
                
                value = get_nested_value(self._data_, item_path[1:]) # because 1st item is the insivible root name
                
                values.append(value)
                
                item_names.append(item_path[-1])
                
                item_path_names.append("_".join(item_path))
                
            if len(values):
                if len(values) == 1:
                    dlg = quickdialog.QuickDialog(self, "Copy to workspace")
                    namePrompt = quickdialog.StringInput(dlg, "Data name:")
                    
                    if fullPathAsName:
                        newVarName = strutils.string_to_valid_identifier(item_path_names[0])
                    else:
                        newVarName = strutils.string_to_valid_identifier(item_names[0])
                    
                    namePrompt.variable.setClearButtonEnabled(True)
                    namePrompt.variable.redoAvailable=True
                    namePrompt.variable.undoAvailable=True
                    
                    namePrompt.setText(newVarName)
                    
                    if dlg.exec() == QtWidgets.QDialog.Accepted:
                        newVarName = validateVarName(namePrompt.text(), self._scipyenWindow_.workspace)
                        
                        self._scipyenWindow_._assignToWorkspace_(newVarName, values[0], from_console=False)
                        
                        
                else:
                    for name, full_path, value in zip(item_names, item_path_names, values):
                        if fullPathAsName:
                            newVarName = validateVarName(full_path, self._scipyenWindow_.workspace)
                        else:
                            newVarName = validateVarName(name, self._scipyenWindow_.workspace)
                            
                        self._scipyenWindow_._assignToWorkspace_(newVarName, value, from_console=False)
        
    def _collapseRecursive_(self, item, collapseCurrent=True):
        if item.childCount():
            for k in range(item.childCount()):
                self._collapseRecursive_(item.child(k))
                
        if collapseCurrent:
            self.treeWidget.collapseItem(item)
        
