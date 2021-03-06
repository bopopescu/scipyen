# -*- coding: utf-8 -*-
"""Superclass for Scipyen viewer windows
"""
from abc import ABC, ABCMeta, abstractmethod

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Q_ENUMS, Q_FLAGS, pyqtProperty

from core.utilities import safeWrapper

#print(__path__)

#from .. import mainwindow.ScipyenWindow as ScipyenWindow
#from  mainwindow import ScipyenWindow

class ScipyenViewer(QtWidgets.QMainWindow):
    """Base type for all Scipyen viewers.
    
    Includes common functionality for all viewer classes defined in Scypien.
    
    Derived classes:
    -----------------
    DataViewer, MatrixViewer, ScipyenFrameViewer, TableEditor, TextViewer, XMLViewer
    
    Developer information:
    -----------------------
    As a minimum, subclasses of ScipyenViewer must:
    
    1) define a :class: attribute named "supported_viewers", which is a tuple or
    list of python stypes supported by the viewer.
    
    2) define a :class: attribute called "view_action_name" which is a str that 
        gives the name for the menu item invoked to display a variable using this
        viewer. Scipyen will use this attribute to generate a menu item in the
        Workspace context menu. 
        
        NOTE: The Workspace context is invoked by single click of the right mouse
        button on a selected variable name in Scipyen "User variables" tab.
    
    2) implement the following abstract methods:
    
    _set_data_(data:object) -- sets up the actual display of data by the viewer's
        widgets (this may involve populating a custom data model specific
        to the viewer type and/or set).
        
        NOTE: ScipyenViewer holds a reference to the displayed data in the 
        attribute "_data_", but this mechanism can be superceded in the derived
        type.
    
    _configureGUI_() -- configures specific GUI widgets and menus
        
         ATTENTION: If the viewer inherits Qt widgets and actions defined in a
        QtDesigner *.ui file (loaded with PyQt5.uic.loadUiType()) then this function
        must call self.setupUi() very early.
    
    If there are viewer type-specific settigns that need to be made persistent
    across sessions then the following abstract mthods also need to be implemented:
    
        _save_viewer_settings_() -- saves viewer class-specific settings
    
        _load_viewer_settings_() -- loads viewer class-specific settings
        
    The other methods may be overridden in the derived classes.
    
    The python data types that the viewer subclass is specialized for, are
    specified in the class attribute "supported_types". This attribute is a 
    tuple or list of python types. 
    
    The same data type may be handled by more than one type of viewers, but one
    of these is the "preferred" one.
    
    When several viewer types can handle the same data type Scipyen assigns 
    priorities based on the order in which the data types are contained in the 
    "supported_types" attribute.
    
    The viewer type where the data type occurs at index 0 in the supported_types
    (i.e. is the first element) is the viewer with the highest priority, and so 
    on.
    
    Viewer types where a data type has the same index in their "supported_types"
    attribute are prioritized in increasing alphabetical order of the viewer types.
    
    For example, a (2D) numpy.ndarray may be displayed in MatrixViewer, as well 
    as in TableEditor. 
    
    If numpy.ndarray if the first element in TableEditor.supported_types
    but has a higher index in MatrixViewer.supported_types then Scipyen will 
    "prefer" the TableEditor to display the array when the user double clicks the
    left mouse buttom on the array name in the "User variables" tab.
    
    If, however, numpy.ndarray occurs at the same index in the "supported_types"
    attribute of both MatrixViewer and TableEditor, then Scipyen will use
    MatrixViewer.
    
    The other available viewer types can be invoked by menu items generated by
    Scipyen automatically according to the contents of the "supported_types"
    attribute of the viewer classes; the names of these menu items are set by
    the value of the "view_action_name" attribute.
    
    DataViewer has a special place. It has been designed to display tree-like
    data structures (e.g. dict and derived types) but can also display any python 
    object that has a "__dict__" attribute. Therefore, the dict and derived types
    shuld be the first elements in DataViewer.supported_types. In this way, other 
    data types for which there exists a specialized viewer will be displayed, 
    by default, in that specialized viewer, instead of DataViewer.
    """
    sig_activated           = pyqtSignal(int, name="sig_activated")
    sig_closeMe             = pyqtSignal(int)
    
    supported_types = (object, )
    view_action_name = None
    
    def __init__(self, data: (object, type(None))=None, parent: (QtWidgets.QMainWindow, type(None)) = None, 
                 pWin: (QtWidgets.QMainWindow, type(None))= None, ID:(int, type(None)) = None,
                 win_title: (str, type(None)) = None, doc_title: (str, type(None)) = None,
                 *args, **kwargs) -> None:
        """Constructor.
        
        Sets up attributes common to all Scipyen's viewers.
        
        Parameters:
        ----------
        
        data: object or None (default) - the data displayed in the viewer
        
        parent: QMainWindow or None (default) - the parent window 

        pWin: QMainWindow, or None (default) - the instance of the Scipyen main
            window.
            
            If present, the viewer will have access to the user's workspace, and
            will manage its own settings (save/load to/from the Scipyen 
            configuration file).
            
        win_title: str or None (default). The display name of the viewer, to be 
            used as part of the window title according to the pattern
            "document - window". 
            
            When None (default), the display name of the viewer will be set to
            the class name of the viewer and the window ID as a suffix.
            
        doc_title: str or None (default). The display name of the data, to be 
            used as part of the window title according to the pattern
            "document - window". 
            
            When None (the default) the window title will contain only the
            viewer name suffixed with the window ID.
        
        *args, **kwargs: variadic argument and keywords specific to the constructor of the
            derived subclass.
        """
        # should be set to True when the viewer is managed by another GUI inside Scipyen
        super().__init__(parent)
        
        self.settings = QtCore.QSettings()

        self._scipyenWindow_ = None
        
        self._docTitle_ = None
        self._winTitle_ = None # force auto-set in update_title()
        self._custom_viewer_name_ = None

        self._linkedViewers_ = list()
        
        self._data_ = None # holds a reference to data!
        
        # NOTE: 2019-11-09 09:30:38
        # _data_var_name_ is either None, or the symbol bound to the data in user's namespace
        #self._data_var_name_ = None

        if isinstance(ID, int):
            self._ID_ = ID
            
        else:
            self._ID_  = self.winId()

        if isinstance(pWin, QtWidgets.QMainWindow) and type(pWin).__name__ == "ScipyenWindow":
            self._scipyenWindow_  = pWin
        
        else:
            if type(parent).__name__ == "ScipyenWindow":
                self._scipyenWindow_   = parent
        
        #if isinstance(varname, str) and len(varname.strip()):
            #self._data_var_name_ = varname
            
        self._configureGUI_()
        
        self.loadSettings()
            
        if data is not None:
            self.setData(data = data, doc_title = doc_title) # , varname = varname)
            
        else:
            self.update_title(win_title = win_title, doc_title = doc_title)
            
    def update_title(self, doc_title: (str, type(None)) = None, 
                     win_title: (str, type(None)) = None,
                     enforce: bool = False):
        """Sets up the window title according to the pattern document - viewer.
        
        Parameters:
        -----------
        doc_title: str or None (default): display name of the data.
            When not None or non-empty, will replace the current display name
            of the data. Otherwise, the display name of the data is left unchanged
            (even if it is None or an empty string).
            
            When None, it will remove the data isplay name from the window title.
        
        win_title: str or None (default): display name of the viewer.
            When not None, or non-empty, will replace the current display name
            of the viewer, depending on the "enforce" parameter.
        
        enforce: bool (default: False) Used when win_title is None or an empty 
            string.
        
            When True, the display name of the viewer will be set to the canonical 
            name, even if the displayed viewer name had been previouly set to
            something else.
            
            When False (the default) the display name of the viewer will not be
            changed from its previous value (unless it is None, or an empty string)
            
        NOTE: a str is considered "empty" when it has a zero length after
        stripping all its leading and trailing whitespace.
            
        Developer information:
        ----------------------
            The canonical name is the viewer's class name suffixed with the 
            viewer's ID, or the name (symbol) that is bound to the viewer 
            variable in the user's namespace.
            
            str objects with zero length after stripping leading and trailing
            whitespace are treated as is they were None.
        
        """
        if isinstance(doc_title, str) and len(doc_title.strip()):
            self._docTitle_ = doc_title
            
        if isinstance(win_title, str) and len(win_title.strip()):
            # user-imposed viewer title
            self._winTitle_ = win_title
            self._custom_viewer_name_ = win_title
            
        else:
            if enforce or self._winTitle_ is None or (isinstance(self._winTitle_, str) and len(self._winTitle_.strip()) == 0): 
                # auto-set viewer title ONLY if not already set, or enforce is True
                if self._scipyenWindow_ is not None:
                    viewerVarName = [k for k in self._scipyenWindow_.workspace.keys() if \
                                    type(self._scipyenWindow_.workspace[k]).__name__ == type(self).__name__ and \
                                    self._scipyenWindow_.workspace[k].ID == self._scipyenWindow_.currentImageViewerWindowID]
                    
                    # NOTE: 2019-11-09 13:40:54
                    # when called from __init__, self is not bound to any
                    # symbol in the user's namespace, yet.
                    # this binding willl take place right after the constructor 
                    # is called e.g. by:
                    # some_window = Viewer()...
                    # some_window the is the name bound to the newly constructed
                    # viewer instance.
                    if len(viewerVarName):
                        self._winTitle_ = viewerVarName[-1]
                        self._custom_viewer_name_ = viewerVarName[-1]
                        
                    else:
                        self._winTitle_ = "%s%d" % (type(self).__name__, self._ID_)
                        self._custom_viewer_name_ = None
                else:
                    self._winTitle_ = "%s%d" % (type(self).__name__, self._ID_)
                    self._custom_viewer_name_ = None
                
        if isinstance(self._docTitle_, str) and len(self._docTitle_.strip()):
            self.setWindowTitle("%s - %s" % (self._docTitle_, self._winTitle_))
            
        else:
            self.setWindowTitle(self._winTitle_)

    @abstractmethod
    def _configureGUI_(self):
        """Custom GUI initialization.
        Abstract method, it must be implemented in the derived :class:.
        
        Required when specifc GUI elements are introduced to the viewer's
        instance.
        
        CAUTION: The function needs to call self.setupUi() early, if the viewer
        inherits from a QtDesigner :class: generated from an  *ui file and loaded
        by loadUiType().
        """
        pass
    
    @abstractmethod
    def _save_viewer_settings_(self):
        pass
    
    @abstractmethod
    def _load_viewer_settings_(self):
        """Restore viewer's settings from the Qt configuration file.
        NOTE: Must be defined (overridden) in the derived :class:.
        The configuration file is determined at application (Scipyen) level.
        See also QtCore.QSettings()
        """
        pass
    
    def saveSettings(self):
        """Save viewer's settings in Scipyen's configuration file.
        
        The function saves a set of settings common to all derived viewer 
        classes:
        
        window size, window position, and window state
        
        Subclass-specific settings are handled by _save_viewer_settings_ which
        MUST be implemented in the derived subclass.
        
        The configuration file is determined at application (Scipyen) level.
        See also QtCore.QSettings()
        """
        if type(self._scipyenWindow_).__name__ == "ScipyenWindow":
            self.settings.setValue("/".join([self.__class__.__name__, "WindowSize"]), self.size())
                
            self.settings.setValue("/".join([self.__class__.__name__, "WindowPos"]), self.pos())
                
            self.settings.setValue("/".join([self.__class__.__name__, "WindowState"]), self.saveState())
            
        self._save_viewer_settings_()
            
    def loadSettings(self):
        """Restores viewer's settings from Scipyen's configuration file.

        The function loads a set of settings common to all derived viewer 
        classes:
        
        window size, window position, and window state
        
        Subclass-specific settings are handled by _save_viewer_settings_ which
        MUST be implemented in the derived subclass.
        
        The configuration file is determined at application (Scipyen) level.
        See also QtCore.QSettings()
        """
        if type(self._scipyenWindow_).__name__ == "ScipyenWindow":
            windowSize = self.settings.value("/".join([self.__class__.__name__, "WindowSize"]), None)
            if windowSize is not None:
                self.resize(windowSize)
                
            windowPos = self.settings.value("/".join([self.__class__.__name__, "WindowPos"]), None)
            if windowPos is not None:
                self.move(windowPos)
                
            windowState = self.settings.value("/".join([self.__class__.__name__, "WindowState"]), None)
            if windowState is not None:
                self.restoreState(windowState)
                
            self._load_viewer_settings_()
                
    def view(self, data: (object, type(None)), 
                doc_title: (str, type(None)) = None, 
                *args, **kwargs):
        """Set the data to be displayed by this viewer.
        NOTE: Must be defined (overridden) in the derived :class:.
        In the derived class, the function binds the data to the actual data
        model used by the concrete viewer :class:.
        In addition, the implementation may choose to set the doc title and other
        properties of the viewer based on the data passed to this function.
        """
        self.setData(data, doc_title=doc_title, *args, **kwargs)
    
    def setData(self, *args, **kwargs):
        """Generic function to set the data to be displayed by this viewer.
        
        Checks that data is one of the supported types, or inherits from one of
        the supported types.
        
        Sets up the window title based on doc_title.
        
        May/should be overridden in the derived viewer type.
        
        Parameters:
        ----------
        data: a python object; its type depends of the types supported by
            the drived viewer class
            
        doc_title: data name to be shown as part of the window title
            
            
        Variadic named parameters (kwargs):
        ----------------------------------
        show: bool (default: True); when True, make the window visible
            
        """
        if len(args):
            data = args[0]
            
        else:
            data  = None
        
        show = kwargs.get("show", True)
        
        doc_title = kwargs.get("doc_title", None)
        
        data_mro = type(data).mro()
        
        if not isinstance(data, self.supported_types) or not any([t in type(data).mro() for t in self.supported_types]):
            raise TypeError("Expecting a %s; got %s instead" % (" ".join([s.__name__ for s in self.supported_types]), type(data).__name__))
        
        if isinstance(doc_title, str) and len(doc_title.strip()):
            self._docTitle_ = doc_title
            
        elif hasattr(data, "name") and isinstance(data.name, str) and len(data.name.strip()):
            self._docTitle_ = data.name
            
        else:
            self._docTitle_ = None
            
        #print("ScipyenViewer setData args", args)
        #print("ScipyenViewer setData kwargs", kwargs)
        
        if len(args)>1:
            self._set_data_(data, *args[1:], **kwargs)
            
        else:
            self._set_data_(data, **kwargs)
        
        self.update_title(doc_title = doc_title, win_title=self._winTitle_)
        
        if show:
            self.setVisible(True)
            #self.show()
        
    @abstractmethod
    def _set_data_(self, data: object, *args, **kwargs):
        pass
    
    @property
    def ID(self):
        """An unique ID for this viewer.
        The ID is typically the winId() of this viewer's QMainWindow instance
        and should NOT be confused with the python id 
        """
        return self._ID_
    
    @ID.setter
    def ID(self, val: int):
        """Sets the window ID.
        
        If the viewer does not have a custom display name this will also update
        the window title.
        
        Parameters:
        -----------
        val: int
        """
        self._ID_ = val
        
        if self._custom_viewer_name_ is None or (isinstance(self._custom_viewer_name_, str) and len(self._custom_viewer_name_.strip()) == 0):
            self.update_title()
            
    @property
    def appWindow(self):
        """The application main window.
        This is a reference to the  Scipyen main window, unless explicitly given
        as something else at the viewer's initiation.
        
        appWindow gives access to Scipyen main window API (e.g. the workspace)
        and is used regardless of the value of guiClient property.
        """
        return self._scipyenWindow_;
    
    @appWindow.setter
    def appWindow(self, val: QtWidgets.QMainWindow):
        if type(val).__name__ == "ScipyenWindow":
            self._scipyenWindow_ =val
        else:
            raise TypeError("Unexpected type for appWindow setter argument; a ScipyenWindow is required with attribute 'workspace'; instead we've got %s" % type(val).__name__)
    
    @property
    def guiClient(self):
        """Boolean (default False) indicating whether this window manages its own settings.
        
        When the viewer subclass instance is used as a standalone window, this 
        property should be set to False (its default value).
        
        When the viewer subclass instance is subordinated to another GUI main window
        which has control over, and manages the settings of this instance,
        then guiClient property should be set to True, to avoid race conditions
        and recurrences (infinite loops).
        
        guiClient is also useful for a managing Main Window instance to 
        control other aspects of the viewer's functionality, e.g. management of
        PlanarGraphics objects in an ImageViewer.
        
        This property also has a setter.
        
        ATTENTION: When guiClient is True, appWindow must be a reference to the
        Scipyen's MainWindow instance.
        """
        return type(self._scipyenWindow_).__name__ != "ScipyenViewer"
    
    #@guiClient.setter
    #def guiClient(self, value: bool):
        #"""Sets up this viewer as a GUI client.
        
        #When a GUI client, the viewer has a slightly restricted fucntionality.
        
        #"""
        #if not isinstance(value, bool):
            #raise TypeError("Expecting a bool; got %s instead" % type(value).__name__)
        
        #self._gui_client_ = value
        
    @property
    def winTitle(self):
        """The prefix of the window title.
        
        This is the initial string in the window title, used in common regardless
        of the document's own name (typically, this is the name of the viewer's 
        type).
        
        This property also has a setter.
        """
        return self._winTitle_
    
    @winTitle.setter
    def winTitle(self, value: (str, type(None)) = None):
        """Sets up a custom display name for the viewer.
        
        Calls self.update_title()
        
        Parameters:
        ----------
        value: str or None (default). When None, the display name of the viewer
            will revert to the canonical name (see update_title()).
        """
        if not isinstance(value, (str, type(None))):
            raise TypeError("Expecting a str, or None; got %s instead" % type(value.__name__))
        
        self.update_title(win_title = value, enforce=True)
            
    @property
    def docTitle(self):
        """The document-specific part of the window title (display name of data).
        
        This is typically, but not necessarily, the variable name of the data 
        displayed in the viewer i.e., the symbolic name that the data is bound
        to, in Scipyen's workspace (user's namespace).
        
        This property also has a setter.
        """
        return self._docTitle_
    
    @docTitle.setter
    def docTitle(self, value: (str, type(None)) = None):
        """Sets the display name of the data.
        
        This is part of the pattern "document - window" used in the window title.
        
        Parameters:
        ----------
        value: str or None (default)
        
            When None or an empty str, the data siaplay name will be removed from
            the window title.
            
            Calls self.update_title()
        """
        if not isinstance(value, (str, type(None))):
            raise TypeError("Expecting a str, or None; got %s instead" % type(value.__name__))
        
        self.update_title(doc_title=value)
        
    def resetTitle(self):
        """Resets the window title.
        
        Removes the data display name from the window title and reverts the 
        viewer display name to its canonical value.
        
        Calls self.update_title()
        """
        
        self.update_title(doc_title = None, win_title = None, enforce = True)
        
    def closeEvent(self, evt:QtCore.QEvent):
        """All viewers in Scipyen should behave consistently.
        May by overridden in derived classes.
        """
        self.saveSettings()
        evt.accept()
        self.close()
    
    def event(self, evt:QtCore.QEvent):
        """Generic event handler
        NOTE: This can be overriden in the derived :class:
        """
        evt.accept()
            
        if evt.type() in (QtCore.QEvent.FocusIn, QtCore.QEvent.WindowActivate):
            self.sig_activated.emit(self.ID)
            return True

        return super().event(evt)
    
    @pyqtSlot()
    @safeWrapper
    def slot_refreshDataDisplay(self):
        """Triggeres a refresh of the displayed information.
        Typical usage is to connect it to a signal emitted after data has been
        modified, and implies two things:
        
        1. appWindow is a reference to Scipyen MainWindow instance
        2. the data displayed in the viewer is defined in Scipyen's workspace
           (a.k.a. the user's workspace)
           
        e.g.:
        
        from core.workspacefunctions import getvarsbytype
        
        if isinstance(self._data_var_name_, str):
            data_vars = getvarsbytype(self.supported_types, ws = self._scipyenWindow_.workspace)
            
            if len(data_vars) == 0:
                return
            
            if self._data_var_name_ not in data_vars.keys():
                return
            
            data = data_vars[self._data_var_name_]
            
            self.setData(data)
        """
        pass
        #if type(self._scipyenWindow_).__name__ == "ScipyenWindow":
            #if self._data_ in self._scipyenWindow_.workspace.values():
                #pass
                
            #if isinstance(self._data_var_name_, str) and len(self._data_var_name_.strip()) and self._data_var_name_ in self._scipyenWindow_.workspace:
                #self.setData(self._scipyenWindow_.workspace[self._data_var_name_])
            
class ScipyenFrameViewer(ScipyenViewer):
    """Base type for Scipyen viewers that handle data "frames".
    
    This should be inherited by viewers for data that is organized, or can be 
    sliced, in "frames","sweeps" or "segments", and display one frame (sweep or 
    segment) at a time.
    
    ScipyenFrameViewer inherits from ScipyenViewer and supplements it with code
    (attributes and abstract methods) for managing data frames.
    
    The abstract methods defined in ScipyenViewer must still be implemented in
    the derived types
    
    ScipyenFrameViewer also defines the Qt signal frameChanged, which should be
    emitted by the implementation of currentFrame setter method.
    
    Examples:
    
    Use ImageViewer to display a 2D array view (slice) of a 3D array (e.g., vigra.VigraArray);
        the slice view is taken the array axis designated as "frame axis".
    
    Use SignalViewer to display:
        one neo.Segment out of a sequence of neo.Segments, possibly contained in a neo.Block
        
        one neo.BaseSignal (or its derivative) out of a stand-alone collection of signals
        
        one 1D array view (slice) of a 2D array (e.g. numpy ndarray or vigra.VigraArray)
        
    ATTENTION: Synchronizing frame navigation across instances of ScipyenFrameViewer.
    
    1) Subclasses of ScipyenFrameViewer should define at least one of two QWidgets 
    (a QSlider and a QSpinBox) used for frame navigation.
    
    In the implementation of _configureGUI_() these widgets should then be 
    aliased to self._frames_slider_ and self._frames_spinner_, respectively, to 
    allow for synchronization of frame navigation, e.g.:
    
        self._frame_slider_ = self.myQSliderQWidget
    
    2) To enable or disable synchronized frame navigation, use linkToViewers() or
    unlinkViewer() / unlinkFromViewers(), respectively.
    
    Synchronized viewers display the data frame with the same index (provided
    that the frame index is valid for their individually displayed data). 
    Navigating across frames in one viewer is propagated to all viewers that
    are synchronized with it.
    
    Derived classes:
    ----------------
    ImageViewer, SignalViewer, LSCaTWindow.
    """
    
    # signal emitted when the viewer displays 
    frameChanged            = pyqtSignal(int, name="frameChanged")
    
    def __init__(self, data: (object, type(None)) = None, 
                 parent: (QtWidgets.QMainWindow, type(None)) = None, 
                 pWin: (QtWidgets.QMainWindow, type(None))= None, 
                 ID:(int, type(None)) = None,
                 win_title: (str, type(None)) = None, 
                 doc_title: (str, type(None)) = None,
                 frameIndex:(int, tuple, list, range, slice, type(None)) = None,
                 currentFrame:(int, type(None)) = None,
                 *args, **kwargs):
        super().__init__(data=data, parent=parent, pWin=pWin, ID=ID,
                         win_title=win_title, doc_title=doc_title,
                         *args, **kwargs)
        """Constructor for ScipyenFrameViewer.
        
        Parameters:
        -----------
        data: object or None (default) - the data displayed in the viewer
        
        parent: QMainWindow or None (default) - the parent window 

        pWin: QMainWindow, or None (default) - the instance of the Scipyen main
            window.
            If present, the viewer will have access to the user's workspace.
            
        win_title: str or None (default). The display name of the viewer, to be 
            used as part of the window title according to the pattern
            "document - window". 
            When None (default), the display name of the viewer will be set to
            the class name of the viewer and the window ID as a suffix.
            
        doc_title: str or None (default). The display name of the data, to be 
            used as part of the window title according to the pattern
            "document - window". 
            
            When None (the default) the window title will contain only the
            viewer name suffixed with the window ID.
        
        frameIndex: int or None (default). The index of the data frameIndex to be displayed.
        
        *args, **kwargs: variadic argument and keywords specific to the constructor of the
            derived subclass.
        """
        
        self._current_frame_index_      = 0 
        self._number_of_frames_         = 1 # determined from the data
        self.rameIndex                  = range(self._number_of_frames_)
        #self._linkedViewers_            = list()
        
        # These two should hold a reference to the actual QSlider and QSpinBox
        # defined in the subclass, or in *.ui file used by the subclass
        self._frames_spinner_           = None
        self._frames_slider_            = None
        
    @abstractmethod
    def displayFrame(self, *args, **kwargs):
        """Display the data frame with _current_frame_index_.
        Must be implemented in the derived class.
        The implementation may rely on an internal "curent_frame":int, or
        expect the index of the frame to be passed as function parameter.
        """
        pass
    
    @property
    def dataFrames(self):
        """The number of "frames" (segments, sweeps) in which data is organized.
        """
        return self._data_frames_
    
    @property
    def nFrames(self):
        """The number of display "frames" this viewer knows of.
        The displayed frames may be a subset of the frames that the data is 
        logically organized in, consisting of the frames selected for viewing.
        
        In the general case,
            self.nFrames <= self.dataFrames
            
        An exception from this rule is case multi-channel signal plotted in
        SignalViewer, with one channel being plotted per frame - hence, there
        are several frames displayed one at a time, even if data is logically
        organized in just one frame.
        """
        return self._number_of_frames_
        
    @property
    def currentFrame(self):
        """The index of the current data "frame".
        Actually, the index into the current data frame index.
        
        For example, when only a subset of data frames are selected for display, 
        say, frames 1, 5, 7 out of a total of 10 frames, then nFrames = 3
        and currentFrame takes values in the half-open interval [0,3).
        
        Abstract method: it must be implemented in the derived class.
        This property also has a setter (also an abstract method that must be
        implemented in the derived class).
        """
        return self._current_frame_index_
    
    @currentFrame.setter
    def currentFrame(self, value:int):
        """Sets value of the current frame (to be displayed).
        
        The function actually sets the index into the current frame index; when
        the viewer displays only a subset of the available data frames, 
        currentFrame is an index into THAT subset, and not an index into all of
        the data frames.
        
        Does not emit frameChanged signal.
        
        Developer information:
        ---------------------
        Deliberately NOT an abstract method therefore it does not need to be 
        implemented in subclasses.
        
        However derived subclasses may override this function to implement more
        specific functionality.
        """
        if not isinstance(value, int) or value >= self._number_of_frames_ or value < 0:
            return
        
        self._current_frame_index_ = value
        
        # widgets which we want to prevent from emitting signals, temporarily
        # signals from wudgets in this list will be blocked for the lifetime of
        # this list (i.e. until and just before the function returns)
        blocked_signal_emitters = list()
        
        if isinstance(self._frames_slider_, QtWidgets.QSlider):
            blocked_signal_emitters.append(self._frames_slider_)
            
        if isinstance(self._frames_spinner_, QtWidgets.QSpinBox):
            blocked_signal_emitters.append(self._frames_spinner_)
            
        if len(blocked_signal_emitters):
            signalBlockers = [QtCore.QSignalBlocker(w) for w in blocked_signal_emitters]
            
            if isinstance(self._frames_slider_, QtWidgets.QSlider):
                self._frames_slider_.setValue(value)
                
            if isinstance(self._frames_spinner_, QtWidgets.QSpinBox):
                self._frames_spinner_.setValue(value)
                
        self.displayFrame()
            
    @property
    def linkedViewers(self):
        """A list with linked viewers.
        All viewers must be ScipyenFrameViewer objects, and the "link" refers to
        the synchronization of frame navigation across several viewers.
        
        Data in each viewer should be structured with the same number of frames.
        
        """
        return self._linkedViewers_
    
    @property
    def framesSlider(self):
        """Read-only access to the frames QSlider.
        
        This is either None, or the actual QSlider used by the derived class
        for frame navigation (if defined). 
        """
        return self._frames_slider_
    
    @property
    def framesSpinner(self):
        """Read-only access to the frames QSpinBox.
        """
        return self._frames_spinner_
    
    @safeWrapper
    def linkToViewers(self, broadcast: bool = True, *viewers):
        """Synchronizes frame navigation with the specified viewer(s).
        
        Named parameters:
        ----------------
        broadcast: bool (default True). If True, also synchronizes frame
            navigation among the viewers.
        
        Var-positional parameters:
        -------------------------
        viewers: Instances of ScipyenFrameViewer
        
        """
        if len(viewers) == 0:
            return
        
        for viewer in viewers:
            if isinstance(viewer, ScipyenFrameViewer):
                self._linkedViewers_.append(viewer)
                
                if self not in viewer.linkedViewers:
                    viewer.linkedViewers.append(self)
                    
            if broadcast:
                for v in viewers:
                    if v is not viewer and viewer not in v.linkedViewers: # avoid synchronizing to itself
                        v.linkedViewers.append(viewer)
    
    @safeWrapper
    def unlinkViewer(self, other):
        """Removes the bidirectional link with the other viewer.
        """
        if isinstance(other, ScipyenFrameViewer) and other in self._linkedViewers_:
            if self in other.linkedViewers:
                other.linkedViewers.remove(self)
                
            if other in self._linkedViewers_:
                self._linkedViewers_.remove(other)
            
    @safeWrapper
    def unlinkFromViewers(self, *others):
        """Removes frame navigation synchronization with other viewers.
        
        Var-positional parmeters:
        =========================
        "others" : sequence of viewers that support multiple data frames
            and are present in self.linkedViewers property.
            and have a slot named "slot_setFrameNumber", i.e. SignalViewer and 
            ImageViewer.
            
        When "others" is empty, removes synchronization with all viewers in
        self.linkedViewers.
            
        
        Any navigation links between the others are left intact. This asymmetry 
        with linkToViewers() is deliberate.
        """
        
        if len(others):
            for viewer in others:
                if isinstance(viewer, ScipyenFrameViewer) and viewer in self._linkedViewers_:
                    self.unlinkViewer(others)
            
        else: # break all currently defined "links"
            for viewer in self._linkedViewers_:
                if self in viewer.linkedViewers:
                    viewer.unlinkViewer(self)
                    
            self._linkedViewers_.clear()
        
    @pyqtSlot(int)
    @safeWrapper
    def slot_setFrameNumber(self, value:int):
        """Drives frame navigation from the GUI.
        
        The valueChanged signal of the widget used to select the index of the 
        displayed data frame should be connected to this slot in _configureGUI_()
        
        NOTE: the subclass can override this function.
        """
        #print("ScipyenFrameViewer %s slot_setFrameNumber %d" % (type(self).__name__, value))
        if value >= self._number_of_frames_ or value < 0:
            return
        
        self.currentFrame = value
        
        for viewer in self.linkedViewers:
            viewer.currentFrame = value
        
