# -*- coding: utf-8 -*-
""" Various utilities for dealing with neo data structures for electrophysiology.

NOTATIONS USED BELOW:

"cursor": signalviewer.SignalCursor object

"cursor time point", "cursor time coordinate", "cursor domain coordinate": 
the value of a cursor's 'x' attribute (floating point scalar). This is the 
undimensioned value of the signal's domain at the cursor position.

The module provides a set of utility functions to operate primarily on objects
in NeuralEnsemble's neo package (http://neuralensemble.org/), 
documented here: https://neo.readthedocs.io/en/stable/

Some of these function also apply to datatypes.DataSignal in Scipyen package.


I. Cursor- and epoch-based functions
=====================================

These functions measure a signal parameter on closed intervals that are defined
using, respectively, signalviewer.SignalCursor objects or a neo.Epoch.

The type of SignalCursor objects must be:

SignalCursor.SignalCursorTypes.vertical, 
or 
SignalCursor.SignalCursorTypes.horizontal.

The difference between cursor- and epoch-based functions consist in the way the 
functions calculate the signal values at the interval boundaries, and in the
number of intervals that a single function can process.

1 Cursor-based functions: named with the prefix "cursor_" or "cursors_".

The function uses the 'x' and 'xwindow' attributes of a vertical or crosshar 
SignalCursor. These are floating point scalars and are converted internally to
python Quantity scalars with the units of the signal domain.

'x' is the horizontal coordinate of the cursor.
'xwindow' is a duration of a horizontal window (or interval) centered on 'x'

1.a "cursor_*" functions use a single cursor:
    * the signal interval is defined by the cursor's horizontal window 
        (the 'xwindow' attribute).
     
    * the signal values at the interval boundaries, if used, are the actual 
        signal sample values at the interval's boundary time points 
        (the interval is closed, i.e. it contains its boundaries)
        
    List of functions based on a single cursor:
    
    cursor_value: the signal sample value at the time point of the cursor 
        (i.e., at the cursor's 'x' attribute) regardless of the size of the
        cursor's 'xwindow'
        
    cursor_min, cursor_max: returns the signal minimum (maximum) across the 
                cursor's horizontal window (or cursor_value if xwindow is zero)
                
    cursor_maxmin: return a tuple of signal max and min in the cursor's window
    
    cursor_average: average of signal samples across the cursor's window.
        NOTE: When cursor's xwindow is zero, this calls cursor_value()
    
    cursor_argmin, cursor_argmax: the index of the signal minimum (maximum) 
                in the cursor window
        
    cursor_argmaxmin: tuple of indices for signal max and min in the cursor's 
            window
            
    
    If the cursor's horizontal window is zero, the above functions return
    the signal sample value at the cursor's coordinate or index 0
    
    
1.b "cursors_*" functions use two cursors to define a signal interval:
    * the signal interval is bounded by the cursor's 'x' coordinates, and is
        closed (i.e. the boundaries are part of the interval):
        
        left boundary: left_cursor.x
        
        right_boundary: right_cursor.x
        
    * the signal values at the interval boundaries, if used, are the averages
        of signal samples across the cursor's horizontal window, if not zero, at
        the respective boundary.
        
        
    List of functions based on two cursors:
    
    cursors_difference: the signed difference between the signal values at two cursors.
        NOTE: for each cursor, the signal value "at the cursor" is determined by 
        calling cursor_average(). This means that, if the cursor's xwindow is 
        zero, the value "at cursor" is the actual sample value at the cursor's
        time coordinate.
        
    cursors_chord_slope
    
All cursor-based functions return a python Quantity array of shape(m,1) with
    m = number of channels.
        
2. Epoch-based functions: named with the prefix "epoch_".

These functions use a single neo.Epoch object to define signal intervals. 

An interval is described by time and duration, contained in the 'times' and 
'durations' attributes of the neo.Epoch object. Since both these attributes
are numeric arrays with the same length, it follows that a neo.Epoch can define 
more than one interval. All intervals are considered closed (i.e. they contain
their boundaries).

    For interval 'k' where 0 <= k < len(epoch) the boundaries are:
        left boundary: times[k]
        right boundary: times[k] + durations[k]
        
The 'times' and 'durations' are python Quantities in time units ("s" by default)
as are the units of the signal domain.

Signal values at the interval boundaries, if used, are the sample values at the
the boundary time points (unlike "cursors_*" functions).

The "epoch_*" functions return a python Quantity array with the shape (m,n) with

    m = number of intervals in the epoch
    n = number of channels in the signal
    
List of neo.Epoch-based functions:
    epoch_average
    

As a rule of thumb:

* when several scalar measures, each derived from a signal interval, are needed,
use neo.Epoch to define the signal intervals where the measures are calculated.

* when a single measure derived from two signal locations is needed, use 
signalviewer.SignalCursors to define the locations.

II. Statistics across multiple signals
=======================================
aggregate_signals: calculates several statistical moments across several
    single-channel signals with identical shapes; each moment is returned as a
    new signal with the same shape as the arguments, contained in a dictionary
    
average_blocks

average_blocks_by_segments

average_segments

average_segments_in_block

average_signals

III. Signal manipulations: assigning values to signal, signal intervals, or 
isolated signal samples; signal channels
=============================================================================
assign_to_signal
assign_to_signal_in_epoch
batch_normalise_signals
batch_remove_offset
concatenate_blocks
concatenate_signals
neo_copy
merge_signal_channels
set_relative_time_start

IV. Management of events, trigger events, trigger protocols
===========================================================
auto_define_trigger_events
auto_detect_trigger_protocols
clear_events
detect_trigger_events
detect_trigger_times
embed_trigger_event
embed_trigger_protocol
modify_trigger_protocol
parse_trigger_protocols
remove_events
remove_trigger_protocol

V. Signal processing
======================
convolve
correlate
diff
ediff1d
forward_difference
gradient
peak_normalise_signal
remove_signal_offset
parse_step_waveform_signal
resample_pchip
resample_poly
root_mean_square
sampling_rate_or_period
signal_to_noise

VI. Synthetic signal and waveforms
==================================
generate_ripple_trace
generate_spike_trace

VII. Lookup functions
=====================
get_index_of_named_signal
get_non_empty_epochs
get_non_empty_events
get_non_empty_spike_trains
get_segments_in_channel_index
get_signal_names_indices
get_time_slice
inverse_lookup
is_same_as
lookup
normalized_signal_index
normalized_segment_index

VIII I/O-related
=================
parse_acquisition_metadata

IX Generic indexing for the neo framework (provisional)
========================================================
    Structured indices:
    
    child_collection_name is obtained by calling neo_child_container_name(...)
    
        it can be a 
        
        data_child_collection_name (sequence of data objects), 
        
        or a
        
        container_child_collection_name (sequence of container objects)
        
        In both cases these are prescribed attribute names of 
        neo.container.Container objects.
    
    indices = an iterable of int (i.e., tuple, list or range), NOT a slice
    
    root container: a top level neo container object (neo.container.Container)
    
    subcontainer: a neo container object that is contained in another neo container.
    
    containment of neo objects can be:
    
    a) direct containment: the neo object is an element of a sequence of neo 
        objects of the same type, and this sequence is a member (attribute) of 
        a neo.container.Container object. 
        
        For example, a neo.AnalogSignal object is an element of "analogsignals", 
        which is a member of a neo.Segment object: the Segment object contains 
        the AnalogSignal object "directly"; the AnalogSignal object is contained
        "directly" by the Segment object.
        
        The Segment object is the "root" container; the search for the neo 
        object starts with the root.
        
    b) indirect containment: a neo object is contained in a neo container which
        itself is directly contained by a root neo container.
        
        For example:
        
        A neo.AnalogSignal object is directly contained by a neo.Segment object,
        and the Segment object is directly contained by a neo.Block object.
        
        Therefore the AnalogSignal object is contained indirectly by the Block.
        
        The Block object is the "root" (top level) container, and the Segment 
        object is a sub container. 
        
        There can be more than one level of indirect containment (see the 
        composition hierarchy schematics below).
    
    Below, child_collection_name is specific for the type of neo object that
    if looked up _for_
    
    
    NOTATION:
    ========
    container: a neo.Container
    
    contained type: a type that is an element of a member collection
    
    member: an attribute of a type instance (gettable by calling getattr)
    
    member collection  = sequence (list or tuple) of objects, that is
    a member of a neo.Container
    
    COMPOSITION HIERARCHIES for neo 0.8.0
    =====================================
    Data object containers are specialized on the types of data object they
    may contain. The neo library allows for a data object type to be
    simultaneously contained in different types of container objects.
    
    The top-level container in neo library is a Block. However, data
    objects are never direcly contained in a block. Instead, a Block
    instance is composed of iterable collections of container objects. In 
    turn, each container object in the collection is composed of collections
    of data objects.
    
    In short, objects in the neo library are never directly contained. Instead,
    tey are stored in appropriate collection of objects with the same type.
    
    For example, neo.AnalogSignal objects are contained in a list which can
    be a member of a neo.Container instance, either a Segment, or a
    ChannelIndex (or both).
    
    Therefore, analog signals have two types of parents: Segment and 
    ChannelIndex, and both of these are in turn contained in collection members
    of a Block instance. The composition hierarchy looks like a diamond:
    
                         AnalogSignal                                    
                    IrregularlySampledSignal                                    
                         DataSignal                                    
                  IrregularlySampledDataSignal                                    
                        /               \                                     
                       /                 \                                     
                      /                   \                                     
                     /                     \                                    
                    /                       \                                    
    Segment.analogsignals             ChannelIndex.analogsignals                                    
    Segment.irregularlysampledsignals ChannelIndex.irregularlysampledsignals                                    
                    \                        /                                    
                     \                      /                                    
                      \                    /                                    
                       \                  /                                    
                        \                /                                    
                Block.segments        Block.channel_indexes                                    
                           \           /                                    
                            \         /                                    
                               Block                                    
        
    
    Likewise, neo.SpikeTrain objects can only be found in th member list of
    of a Segment (Segment.spiketrains) or a Unit. Unit is a Container which 
    is only contained in a ChannelIndex (although it can be also accessed in
    read-only mode from a Block). The composition hierarchy looks like this:
        
                      SpikeTrain    
                    /            \ 
                   /              \ 
                  /                \ 
                 /                  \
                /                    \
        Segment.spiketrains         Unit.spiketrains
                \                     |            \
                 \                    |             \   
                  \            ChannelIndex.units    \
                   \                 /                \
                    \               /                 |
              Block.segments  Block.channel_indexes   |
                      \           /                   |
                       \         /                    |
                          Block  - - - - - Block.list_units
                          
        
    For all other BaseSignal types there a direct (linear) composition 
    hierarchy:
        
              ImageSequence, Epoch, Event
                            |
                            |
                            |
             Segment member colection name: 
             imagesequences, epochs, events
                            |
                            |
                            |
                          Block
        
    And also for other neo object types:
        
                     RegionOfInterest
                            |
                            |
                            |
                  Block.regionsofinterest
                            |
                            |
                            |
                          Block
        
        
    As a design decision, when the container is a Block and we lookup a
    neo.AnalogSignal, we traverse the container's Segments.
    When the container if another container (which for a signal can 
    only be a ChannelIndex) when then get directly to its analogsignals
    member collection.
    
    For information, these are the INHERITANCE HIERARCHIES in neo:
    ==============================================================
         object
           |
           V
        BaseNeo
           |                    pq.Quantity
           |\                       |
           | \                      V
           |  ----------------> DataObject -------> BaseSignal
           |                        |                   |        
           V                        V                   V    
        Container               Epoch               AnalogSignal    
           |                    Event               IrregularlySampledSignal
           V                    SpikeTrain          ImageSequence
        Block                                       
        Segment                                     
        Unit                                        outside neo, in scipyen:
        ChannelIndex                                dataypes.DataSignal
                                                    datatypes.IrregularlySampledDataSignal

        object --> RegionOfInterest ------> RectangularRegionOfInterest,
                                            CircularRegionOfInterest,
                                            PolygonRegionOfInterest

    Case 1: index of neo objects in a generic python sequence of object of the
    same type:
    ============================================================================
    returns:
        indices
    
    code:
    
        utilities.normalized_index(seq, index_obj) => tuple or range
    
    checks: 
    
    1) when index_obj is a str, or a sequence where at least one element is a
        str, check if the neo objects have a "name" attribute,  that "name" is
        not empty, and equals the value(s) in index_obj.
        
        if silent, return None for each str index_obj value that does not find
        a neo object with that name, and issue a warning
        
        otherwise, raise IndexError
    
    2) when index_obj is an int or a sequence where at least one element is an
        int, check the int values in index_obj are <= len(seq)
        
        if silent, return None for each of the invalid int values and issue a
        warning
        
        otherwise raise IndexError
        
    3) when index_obj is a range, check that 0 < len(index_obj) <= len(seq)
    
        if silent, return (None,) otherwise raise IndexError
    
    4) when index_obj is a slice, check that len(index_obj.indices(len(seq))) > 0
        is silent return (None,) otherwise raise IndexError.
    
    
    Case 2: index of neo objects contained directly in a neo.Container 
    ("root container" can be a Block, a Segment, a ChannelIndex, or a Unit):
    ============================================================================
    
    returns:
        {child_collection_name0: indices, 
         child_collection_name1: indices,
         etc...}
    
    child_collection_name can refer to a data child, or a container child.
    
    There is one child_collection_name for each type of object that is being
    looked up
    
    Root container type:    data child collection:     container child collection:
    -----------------------------------------------------------------------------
    Segment                 "analogsignals", 
                            "irregularlysampledsignals", 
                            "imagesequences", 
                            "spiketrains", 
                            "epochs", 
                            "events"
                                    
    ChannelIndex            "analogsignals"             "units"
    
    Unit                    "spiketrains"
    
    Block                                               "segments"
                                                        "channel_indexes"
                                                        "list_units" - read-only!
    
    code :
        for each object type call silently
            setup child_collection_name
            execute Case 1 for getattr(container, child_collection_name)
                                       
            if child_collection_name is appropriate and call was successful then
                map child_collection_name (key) to the return from the call (value)
                               
    checks:
    
        in addition to case 1: data_child_collection_name is an attribute of container.
    
    
    Case 3: index of neo objects in a generic python sequence of containers 
    (each container contains the objects directly)
    ============================================================================
    
    returns:
        {index0: {child_collection_name0: indices, 
                  child_collection_name1:indices,
                  etc...}, 
         index1: {...},
         etc...}
     
    index0, index1, etc: indices of the container in the sequence where the 
            lookup was successful
     
    These indices are not necessarily the same as Segment.index or ChannelIndex
    value! Instead they are the indices of said objects in the collection where
    the lookup takes place.
    
    code:
        for each container in seq enumeration:
            execute Case 2 => "inner" dict
                    
            if result not empty:
                map container index in enumeration (key) to result (value)
                
    checks:
        all checks of Case 2, for each member of seq
    
    
    Case 4: search objects contained indirectly in root container (nested search)
    ============================================================================
    
    returns:
    
    {container_collection_name0: {index0 : {child_collection_name0: indices,
                                            child_collection_name1: indices,
                                            etc...},
                                  index1 : {...},
                                  etc...},
     container_collection_name0: {...},
     etc...}
     
    NOTE: there can be more than one container child collection in case of 
    "diamond" composition hierarchy.
     
     
    code:
        for each obj_type:
            if hasattr(container, neo_child_container_name(obj_type)):
                # find out if object type is contained directly in this container
                # we use our own function which covers more possibilities than
                # neo.container.Container._data_child_containers and
                # neo.container.Container._container_child_containers
                #
                # first, these two functions would have to be called separately
                # (or distinctly) for neo data objects and neo container objects
                #
                # second, neo_child_container_name also takes into account
                # RegionOfInterest objects (currently only neo.Block can have these)
                
                execute Case 2 on getattr(container, neo_child_container_name(obj_type)
                
                map key = neo_child_container_name(obj_type) to
                    value = result
                
            else: 
                if hasattr(container, neo_child_property_name(obj_type)):
                    # find out if object type is contained child_properties
                    # (currently only Block has "Units" among its child_properties,
                    # referenced as "list_units"; for all other container types 
                    # _child_properties is an empty tuple, but this may change)
                    # also we use neo_child_property_name for a more generic coverage
                    # (see comments above)
                    
                    execute Case 2 on getattr(container, neo_child_property_name(obj_type))
                    
                    map key = neo_child_property_name(obj_type) to
                        value = result
                    
                else:
                    # obj_type not found in either child containers or in child
                    # properties - we need to descend one level into the current 
                    # chid containers & properties of container
                    
                    for each container_type in obj_type._single_parent_objects:
                    
                        if hasattr(container, neo_child_container_name(container_type)):
                            execute Case 2 on getattr(container, neo_child_container_name(container_type))
                            map key = neo_child_container_name(container_type) to
                                value = result
                            
                        elif hasattr(container, neo_child_property_name(container_type)):
                            execute Case 2
                            map key = neo_child_property_name(container_type) to
                                value = result
                                
                        else:
                            continue
                
                for each discovered container collection name:
                    execute Case 3 on getattr(container, container_collection_name)
                    
                    map contained_collection_name (key) to result (value)
        
            
    checks:
        
    
    
    Case 5: Case 3 with indirect containment
    ========================================
    
    For spike trains in a sequence of ChannelIndex, one may also select the units:
    
    {index0: {container_child_collection_name: {nested_index0:{data_child_collection_name: indices}}},
     index1: {...},
     etc...}
     
     Here index0/1/etc: indices of the channel index in the sequence
          nested_index0/1/etc: indices of the Units

        
    Example 5: nested index of signal in a Block
    =============================================
    {container_child_collection_name: {index0: {data_child_collection_name: indices},
                                      index1: {...},
                                      etc... },
                                        
    for analog signals, should indicate preference between "segments" and "channel_indexes"
        default is "segments"
    
    for spike trains, should indicate preference between "segments" and "units"
        default is "segments"
        if "units", this implies traversing "channel_indexes" if looking up in
        a Block
    

    Example 6: nested index of signal in a sequence of blocks
    =========================================================
    {index1:    {"segments": {index1: {child_collection_name: indices},
                              index2: {...},
                              etc... },
                 "channel_indexes": {index: {child_collection_name: indices}, 
                                     etc... }},
     index2:    {"segments": {index1: {child_collection_name: indices},
                              index2: {...},
                              etc... },
                 "channel_indexes": {index: {child_collection_name: indices}, 
                                     etc... }},
     etc...}
    



"""
#### BEGIN core python modules
import traceback
import datetime
import collections
import numbers
import inspect
import itertools
import functools
import warnings
import typing
from enum import Enum, IntEnum
#### END core python modules

#### BEGIN 3rd party modules
import numpy as np
import quantities as pq
import neo
import matplotlib as mpl
import pyqtgraph as pg
#### END 3rd party modules

#### BEGIN pict.core modules
#from . import plots
from .prog import safeWrapper
from .datatypes import  normalized_index
from .datasignal import DataSignal, IrregularlySampledDataSignal
from .triggerprotocols import TriggerEvent, TriggerProtocol
from .scandata import ScanData

from . import datatypes as dt
from . import workspacefunctions
from . import signalprocessing as sigp
from . import utilities


#from .patchneo import neo

from gui.signalviewer import SignalCursor as SignalCursor

#### END pict.core modules

if __debug__:
    global __debug_count__

    __debug_count__ = 0

def get_neo_version() -> tuple:
    major, minor, dot = neo.version.version.split(".")
    return eval(major), eval(minor), eval(dot)

#"def" silentindex(a, b):
    #""" Call this instead of list.index, such that a missing value returns None instead
    #of raising an Exception
    #"""
    #if b in a:
        #return a.index(b)
    #else:
        #return None
    
def correlate(in1, in2, **kwargs):
    """Calls scipy.signal.correlate(in1, in2, **kwargs).
    
    Correlation mode is by default set to "same", but can be overridden.
    
    Parameters
    
    ----------
    
    in1 : neo.AnalogSignal, neo.IrregularlySampledSignal, datatypes.DataSignal, or np.ndarray.
    
        Must be a 1D signal i.e. with shape (N,) or (N,1) where N is the number 
        of samples in "in1"
    
        The signal for which the correlation with "in2" is to be calculated. 
        
        Typically this is the longer of the signals to correlate.
        
    in2 : neo.AnalogSignal, neo.IrregularlySampledSignal, datatypes.DataSignal, or np.ndarray
    
        Must be a 1D signal, i.e. with shape (M,) or (M,1) where M is the number 
        of samples in "in2"
        
        The signal that "in1" is correlated with (typically, shorter than "in1")
        
    Var-keyword parameters
    
    -----------------------
    
    method : str {"auto", "direct", "fft"}, optional; default is "auto"
        Passed to scipy.signal.correlate
        
    name : str
        The name attribute of the result
        
    units : None or a Python Quantity or UnitQuantity. Default is None.
    
        These is mandatory when "a" is a numpy array
    
        The units of the returned signal; when None, the units of the returned 
        signal are pq.dimensionless (where "pq" is an alias for Python quantities
        module)
    
    Returns
    
    -------
    
    ret : object of the same type as "in1"
        Contains the result of correlating "in1" with "in2".
        
        When "in1" is a neo.AnalogSignal, neo.IrregularlySampledSignal, or datatypes.DataSignal,
        ret will have "times" attribute copied from "in1" and with "units" attribute
        set to dimensionless, unless specified explicitly by "units" var-keyword parameter.
        
        
    NOTE
    
    ----
    
    The function correlates the magnitudes of the signals and does not take into
    account their units, or their definition domains (i.e. "times" attribute).
    
    See also:
    --------
    scipy.signal.correlate
    
    """
    
    from scipy.signal import correlate
    
    from . import datatypes as dt
    
    name = kwargs.pop("name", "")
    
    units = kwargs.pop("units", pq.dimensionless)
    
    mode = kwargs.pop("mode", "same") # let mdoe be "same" by default but allow it to be overridden
    
    if in1.ndim > 1 and in1.shape[1] > 1:
        raise TypeError("in1 expected to be a 1D signal")
    
    if in2.ndim > 1 and in2.shape[1] > 1:
        raise TypeError("in2 expected to be a 1D signal")
    
    if isinstance(in1, (neo.AnalogSignal, neo.IrregularlySampledSignal, DataSignal)):
        in1_ = in1.magnitude.flatten()
        
    else:
        in1_ = in1.flatten()

    if isinstance(in2, (neo.AnalogSignal, neo.IrregularlySampledSignal, DataSignal)):
        in2_ = in2.magnitude.flatten()
        
    else:
        in2_ = in2.flatten()
        
    in2_ = np.flipud(in2_)
        
    corr = correlate(in1_, in2_, mode=mode, **kwargs)
    
    if isinstance(in1, (neo.AnalogSignal, DataSignal)):
        ret = neo.AnalogSignal(corr, t_start = in1.t_start,
                                units = units, 
                                sampling_period = in1.sampling_period,
                                name = name)
    
        if isinstance(in2, (neo.AnalogSignal, neo.IrregularlySampledSignal, DataSignal)):
            ret.description = "Correlation of %s with %s" % (in1.name, in2.name)
            
        else:
            ret.description = "Correlation of %s with an array" % in1.name
            
        return ret
    
    elif isinstance(in1, neo.IrregularlySampledSignal):
        ret = neo.IrregularlySampledSignal(corr, 
                                            units=units,
                                            times = in1.times,
                                            name = name)
    
        if isinstance(in2, (neo.AnalogSignal, neo.IrregularlySampledSignal, DataSignal)):
            ret.description = "Correlation of %s with %s" % (in1.name, in2.name)
            
        else:
            ret.description = "Correlation of %s with an array" % in1.name
            
        return ret

    else:
        return corr
    

@safeWrapper
def assign_to_signal(dest:neo.AnalogSignal, src:[neo.AnalogSignal, pq.Quantity], 
                     channel:[int, type(None)]=None):
    """Assigns values in src to values in dest, for the specified channel, or all channels
    
    Parameters:
    ==========
    dest: destination AnalogSignal
    
    src: source AnalogSignal or a scalar python quantity with same units as dest
    
        when source is an AnalogSignal, its time domain must be WITHIN or 
        equal to the destination time domain
            
    channel int or None; when int it must point to a valid channel index into both signals
    
    """
    if not isinstance(dest, neo.AnalogSignal):
        raise TypeError("dest expected to be an AnalogSignal; got %s instead" % (type(dest).__name__))

    if isinstance(src, neo.AnalogSignal):
        if src.t_start < dest.t_start:
            raise ValueError("Source signal starts (%s) before destination signal (%s)" % (src.t_start, dest.t_start))
        
        if src.t_stop > dest.t_stop:
            raise ValueError("Source signal stops (%s) after destination signal (%s)" % (src.t_stop, dest.t_stop))
        
        if src.units != dest.units:
            raise TypeError("Mismatch between destination unts (%s) and source units (%s)" % (dest.units, src.units))
    
        ndx = np.where((dest.times >= src.t_start) & (dest.times < src.t_stop))
        
        if channel is None:
            dest[ndx[0],:] = src[:,:]
            
        else:
            dest[ndx[0],channel] = src[:,channel]

    elif isinstance(src, pq.Quantity) and src.units == dest.units:# and src.size == 1:
        if channel is None:
            dest[:,:] = src
            
        else:
            dest[:,channel] = src
            
    elif isinstance(src, np.ndarray) and utilities.isVector(src):
        # TODO
        if channel is None:
            pass
        else:
            pass
        
            
    else:
        raise TypeError("source expected to be an AnalogSignal or a scalar python quantity of same units as destination")
    
        
@safeWrapper
def assign_to_signal_in_epoch(dest:neo.AnalogSignal, 
                              src:[neo.AnalogSignal, pq.Quantity], 
                              epoch:neo.Epoch, 
                              channel:[int, type(None)] = None):
    """Assigns values in src to values in dest, within an epoch, for the specified channel, or all channels
    """
    
    if not isinstance(dest, neo.AnalogSignal):
        raise TypeError("dest expectyed to be an AnalogSignal; got %s instead" % (type(dest).__name__))

    if not isinstance(epoch, neo.Epoch):
        raise TypeError("epoch expected to be a neo.EPoch; got %s instead" % (type(epoch).__name__))
    
    if isinstance(src, neo.AnalogSignal):
        if src.t_start < dest.t_start:
            raise ValueError("Source signal starts (%s) before destination signal (%s)" % (src.t_start, dest.t_start))
        
        if src.t_stop > dest.t_stop:
            raise ValueError("Source signal stops (%s) after destination signal (%s)" % (src.t_stop, dest.t_stop))
    
        if src.units != dest.units:
            raise TypeError("Mismatch between destination unts (%s) and source units (%s)" % (dest.units, src.units))
    
        if any([t < dest.t_start for t in epoch.times]):
            raise ValueError("Epoch cannot start before destination")
        
        if any([(epoch.times[k] + epoch.durations[k]) > dest.t_stop for k in range(len(epoch))]):
            raise ValueError("Epoch cannot extend past destination end")
        
        if any([t < src.t_start for t in epoch.times]):
            raise ValueError("Epoch cannot start before source")
    
        if any([(epoch.times[k] + epoch.durations[k]) > src.t_stop for k in range(len(epoch))]):
            raise ValueError("Epoch cannot extend past source end")
        
        for k in range(len(epoch)):
            src_ndx = np.where((dest.times >= epoch.times[k]) & (dest.times < (epoch.times[k] + epoch.durations[k])))
            
            dest_ndx = np.where((src.times >= epoch.times[k]) & (src.times < (epoch.times[k] + epoch.durations[k])))
    
            if len(src_ndx[0]) != len(dest_ndx[0]):
                raise RuntimeError("Mismatch array lenghts")
            
            if channel is None:
                dest[dest_ndx[0],:] = src[src_ndx[0],:]
                
            else:
                dest[dest_ndx[0], channel] = srdc[src_ndx[0], channel]
                
    elif isinstance(src, pq.Quantity) and src.units == dest.units and src.size == 1:
        if any([t < dest.t_start for t in epoch.times]):
            raise ValueError("Epoch cannot start before destination")
        
        if any([(epoch.times[k] + epoch.durations[k]) > dest.t_stop for k in range(len(epoch))]):
            raise ValueError("Epoch cannot extend past destination end")
        
        for k in range(len(epoch)):
            dest_ndx = np.where((dest.times >= epoch.times[k]) & (dest.times < (epoch.times[k] + epoch.durations[k])))
            
            if channel is None:
                dest[dest_ndx[0],:] = src
                
            else:
                dest[dest_ndx[0], channel] = src
                
    else:
        raise TypeError("source expected to be an AnalogSignal or a scalar python quantity of same units as destination")
    
    
@safeWrapper
def cursors2epoch(*args, **kwargs) -> typing.Union[neo.Epoch, typing.Sequence]:
    """Constructs a neo.Epoch from a sequence of SignalCursor objects.
    
    Each cursor contributes to an interval in the Epoch.
    
    SignalCursor objects are defined in the signalviewer module; this function
    expects vertical and crosshair cursors (i.e., with cursorType one of
    SignalCursor.SignalCursorTypes.vertical, 
    SignalCursor.SignalCursorTypes.horizontal). 
    
    SignalCursors can be represented by tuples of cursor 
    "parameters" (see below), although tuples and cursor objects cannot be mixed.
    
    Variadic parameters:
    --------------------
    *args: One or more SignalCursor object(s) (comma-separated list) or a  
        sequence (tuple, list) of SignalCursor objects.
        
        SignalCursor objects must all be of type vertical or crosshair.
        
        Alternatively, the function accepts tuples (2, 3 or 5 elements) of
        cursor parameters, instead of actual SignalCursor objects, as follows:
        
        a) 2-tuples are interpreted as (time, window) pairs of coordinates
            for a notional vertical cursor
            
        b) 3-tuples are interpreted as (time, window, label) triples of 
            parameters of a notional vertical cursor
            
        c) 5-tuples are interpreted as (x, xwindow, y, ywindow, label) tuples of
            a notional crosshair cursor. In this case only the x, xwindow and
            label elements are used.
            
        NOTE 1: the cases (a) and (b) are the value of the 'parameters' property
        of a vertical and crosshair cursor, respectively. This means that such
        a tuple can be obtained by referencing cursor.parameters property.
        
        NOTE 2: Mixing SignalCursor objects with parameter tuples is NOT allowed.
        
    Var-keyword parameters:
    ----------------------
    
    units: python Quantity or None (default)
        By default, the epoch's units are seconds (pq.s) but in a neo.Epoch can
        support any units
    
    name: str, default is" Epoch"; not used when intervals is True (see below)
    
    sort: bool, default if True
        When True, the cursors are sorted by their x coordinate
        
    intervals: bool, default is False.
    
        When True, the function returns triplets of (start, stop, label)
        
        Otherwise returns a neo.Epoch
        
    Returns:
    -------
    
    When intervals is False (default), returns a neo.Epoch with intervals 
        generated from the cursor x coordinates and horizontal windows:
        
            times = cursor.x - cursor.xwindow/2
            durations = cursor.xwindow
            
            By design, the epoch's units are time units (pq.s by default)
            
    When intervals is True, returns a list of triplets:
            (start, stop, label)
            
            If units are provided, start and stop are python Quantity scalars,
            otherwise they are floating point scalars.
            
    Examples:
    ========
    
    Given "cursors" a list of vertical SignalCursors, and "params" the 
    corresponding list of cursor parameters:
    
    >>> params = [c.params for c in cursors]
    
    >>> params
        [(0.20573370205046024, 0.001, 'v2'),
         (0.1773754848365214,  0.001, 'v1'),
         (0.16775228528220001, 0.001, 'v0')]
         
    The following examples are valid call syntax:

    >>> epoch = cursors2epoch(cursors)
    >>> epoch1 = cursors2epoch(*cursors)
    >>> epoch2 = neoutils.cursors2epoch(params)
    >>> epoch3 = neoutils.cursors2epoch(*params)
    
    >>> epoch == epoch1
    array([ True,  True,  True])

    >>> epoch == epoch2
    array([ True,  True,  True])
    
    >>> epoch2 == epoch3
    array([ True,  True,  True])
    
    >>> epoch4 = neoutils.cursors2epoch(*params, units=pq.um)
    >>> epoch4 == epoch3
    array([False, False, False]) #  because units are different
    
    >>> interval = cursors2epoch(cursors, intervals=True)
    >>> interval1 = cursors2epoch(*cursors, intervals=True)
    
    >>> interval == interval1
    True
    
    >>> interval2 = neoutils.cursors2epoch(params, intervals=True)
    >>> interval3 = neoutils.cursors2epoch(*params, intervals=True)
    
    >>> interval2 == interval3
    True
    
    >> interval == interval2
    True
    """
    intervals = kwargs.get("intervals", False)
    
    units = kwargs.get("units", pq.s)
    
    if not isinstance(units, pq.UnitQuantity):
        units = units.units
        
    elif not isinstance(units, pq.Quantity) or units.size > 1:
        raise TypeError("Units expected to be a python Quantity; got %s instead" % type(units).__name__)
        
    name = kwargs.get("name", "Epoch")
    if not isinstance(name, str):
        raise TypeError("name expected to be a string")
    
    if len(name.strip())==0:
        raise ValueError("name must not be empty")
    
    sort = kwargs.get("sort", True)
    if not isinstance(sort, bool):
        raise TypeError("sort must be a boolean")
    
    def __parse_cursors_tuples__(*values):
        # check for dimensionality consistency
        #print(type(values))
        #print(len(values))
        if len(values) == 1:#  allow for a sequence to be given as first argument
            values = values[0]
            
        #print("given values", values)
        values_ = list(values)
        
        for k,c in enumerate(values_):
            if all([isinstance(v, pq.Quantity) for v in c[0:2]]):
                if c[0].units != c[1].units:
                    if not dt.units_convertible(c[0], c[1]):
                        raise TypeError("Quantities must have compatible dimensionalities")
                    
                values = values_ # convert back
                
            elif all([isinstance(v, numbers.Number) for v in c[0:2]]):
                if units is not None:
                    c_ = [v*units for v in c[0:2]]
                    
                    if len(c) > 2:
                        c_ += list(c[2:])
                        
                    values_[k] = tuple(c_)
                    
                values = tuple(values_)
        
        #print("values:", values)
        
        if intervals:
            return [(v[0]-v[1]/2., v[0]+v[1]/2., "%d"%k) if len(v) == 2 else (v[0]-v[1]/2., v[0]+v[1]/2., v[2]) if len(v) == 3 else (v[0]-v[1]/2., v[0]+v[1]/2., v[4]) for k,v in enumerate(values)]
            
        else:
            return [(v[0]-v[1]/2., v[1],         "%d"%k) if len(v) == 2 else (v[0]-v[1]/2., v[1],         v[2]) if len(v) == 3 else (v[0]-v[1]/2., v[1],         v[4]) for k,v in enumerate(values)]
        
    #cursors = None
    
    if len(args) == 0:
        raise ValueError("Expecting at least one argument")
    
    if len(args) == 1:
        if isinstance(args[0], (tuple, list)):
            if all ([isinstance(c, SignalCursor) for c in args[0]]):
                if all([c.cursorTypeName in ("vertical", "crosshair")  for c in args[0]]):
                    t_d_i = __parse_cursors_tuples__(*[c.parameters for c in args[0]])                    
                else:
                    raise TypeError("Expecting only vertical or crosshair cursors")
                #t_d_i = [(c.x - c.xwindow/2., c.xwindow, c.ID) for c in args[0]]
                
            elif all([isinstance(c, (tuple, list)) for c in args[0]]):
                if all([len(c) in (2,3,5) for c in args[0]]):
                    t_d_i = __parse_cursors_tuples__(args[0])
                    
                else:
                    raise TypeError("All cursor parameter tuples must have two or three elements")
                         
        elif isinstance(args[0], SignalCursor):
            if args[0].cursorType is SignalCursor.SignalCursorTypes.horizontal:
                raise TypeError("Expecting a vertical or crosshair cursor")
            
            t_d_i = __parse_cursors_tuples__([args[0].parameters])
            
        elif len(args[0] == 3):
            t_d_i = __parse_cursors_tuples__([args[0]])
            
        else:
            raise TypeError("Unexpected argument type %s" % type(args[0]).__name__)
        
    else:
        if all([isinstance(c, SignalCursor) for c in args]):
            if all ([c.cursorTypeName in ("vertical", "crosshair") for c in args]):
                t_d_i = __parse_cursors_tuples__([c.parameters for c in args])
                
            else:
                raise TypeError("Expecting only vertical or crosshair cursors")
            
        elif all([isinstance(c, (tuple, list)) and len(c) in (2,3,5) for c in args]):
            t_d_i = __parse_cursors_tuples__(args)
            
        else:
            raise TypeError("Unexpected argument types")
        
    if sort:
        t_d_i = sorted(t_d_i, key=lambda x: x[0])

    
    if intervals:
        return t_d_i
    
    else:
        # transpose t_d_i and unpack:
        t, d, i = [v for v in zip(*t_d_i)]
        
        if isinstance(t[0], pq.Quantity):
            units = t[0].units
        
        return neo.Epoch(times=t, durations=d, labels=i, units=units, name=name)
    
def cursors2intervals(*args, **kwargs) -> typing.Union[typing.Sequence, np.ndarray]:
    """Calls cursors2epochs with intervals set to True
    
    Additional var-keyword parameters:
    --------------------------------
    unwrap: bool default True
        When False, calling the function with a single cursor (or cursor parameter
            tuple) will return a single interval tuple (t0, t1, label) wrapped in
            a list.
            
        When True, the function returns the single interval tuple directly
    """
    kwargs.pop("intervals", True) # avoid double parameter specification
    
    unwrap = kwargs.pop("unwrap", True)
    
    ret = cursors2epoch(*args, **kwargs, intervals=True)
    
    if unwrap and len(ret) == 1:
        return ret[0]
    
    

@safeWrapper
def signal2epoch(sig, name=None, labels=None):
    """Constructs a neo.Epochs from the times and durations in a neo.IrregularlySampledSignal
    
    Parameters:
    ----------
    
    sig: neo.IrregularlySampledSignal where the signal's units are time units
        (typically, this signal contains an array of durations, and its elements
        will be used to supply the durations values for the Epoch)
        
    name: str or None (default)
        The name of the Epoch
        
    labels: numpy array with dtype "S" (str), a str, or None (default)
        Array with labels for each interval in the epoch.
        
        When an array it must have the same length as sig.
    
    """
    from . import datatypes as dt
    
    if not isinstance(sig, neo.IrregularlySampledSignal):
        raise TypeError("Expecting a neo.IrregularlySampledSignal; got %s instead" % type(sig).__name__)
    
    if not dt.units_convertible(sig.units, sig.times.units):
        raise TypeError("Signal was expected to have time units; it has %s instead" % sig.units)
    
    if isinstance(labels, str) and len(labels.strip()):
        labels = np.array([label] * sig.times.size)
        
    elif isinstance(labels, np.ndarray):
        if not dt.is_string(labels):
            raise TypeError("'labels' array has wrong dtype: %s" % labels.dtype)
        
        if labels.shape != sig.times.shape:
            raise TypeError("'labels' array has wrong shape (%s); shloud have %s" % (labels.shape, sig.times.shape))
        
    elif labels is not None:
        raise TypeError("'labels' expected to be a str, numpy array of string dtype, or None; got %s instead" % type(labels).__name__)
    
    if not isinstance(name, (str, type(None))):
        raise TypeError("'name' expected to be None or a string; got %s instead" % type(name).__name__)
    
    if isinstance(name, str) and len(name) == 0:
        name = sig.name # this may be None

    ret = neo.Epoch(times = sig.times,
                    durations = sig.magnitude * sig.units,
                    name = name,
                    labels = labels)
    
    return ret

@safeWrapper
def cursor_max(signal: typing.Union[neo.AnalogSignal, DataSignal],
               cursor: typing.Union[SignalCursor, tuple],
               channel: typing.Optional[int] = None) -> pq.Quantity:
    """The maximum value of the signal across the cursor's window.
    
    Parameters:
    ----------
    signal: neo.AnalogSignal, DataSignal
    cursor: tuple (x, window) or SignalCursor of type vertical or crosshair
    channel: int or None (default)
        For multi-channel signal, specified which channel is used:
        0 <= channel < signal.shape[1]
    
    Returns:
    --------
    Python Quantity array of shape (signal.shape[1], ) with the signal maximum
    in the interval defined by the cursor's window, or the signal's sample value
    at the cursor's x coordinate if cursor window is zero.
    
    NOTE: to get the signal extremes (and their sample indices) between two 
    cursors, just call max(), min(), argmax() argmin() on a signal time slice 
    obtained using the two cursor's x values.
    """
    
    t0,t1, _ = cursors2intervals(cursor, signal.times.units)
    
    if t0 == t1:
        ret = signal[signal.time_index(t0),:]
        
    else:
        ret = signal.time_slice(t0,t1).max(axis=0).flatten()
    
    if isinstance(channel, int):
        return ret[channel].flatten()
    
    return ret

@safeWrapper
def cursor_argmax(signal: typing.Union[neo.AnalogSignal, DataSignal],
                  cursor: typing.Union[SignalCursor, tuple],
                  channel: typing.Optional[int] = None) -> np.ndarray:
    """The index of maximum value of the signal across the cursor's window.

    Parameters:
    ----------
    signal: neo.AnalogSignal, DataSignal
    cursor: tuple (x, window) or SignalCursor of type vertical or crosshair
    channel: int or None (default)
        For multi-channel signal, specified which channel is used:
        0 <= channel < signal.shape[1]
    
    Returns:
    --------
    Array with the index of the signal maximum, relative to the start of the 
    interval, with shape (signal.shape[1], ).
    
    When cursor's xwindow is zero, returns an array of shape (1,) containing 
    the sample index of the cursor's x coordinate relative to the beginning of
    the signal.
    """
    
    t0,t1,_ = cursors2intervals(cursor, units=signal.times.units)
    
    t0_ndx = np.array(signal.time_index(t0)).flatten()
    
    if t0 == t1:
        return t0_ndx
        
    else:
        ret = signal.time_slice(t0,t1).argmax(axis=0).flatten() + t0_ndx
    
        if isinstance(channel, int):
            return ret[channel].flatten()
        
        return ret

@safeWrapper
def cursor_min(signal: typing.Union[neo.AnalogSignal, DataSignal],
               cursor: typing.Union[tuple, SignalCursor],
               channel: typing.Optional[int] = None) -> pq.Quantity:
    """The minimum value of the signal across the cursor's window.
    
    Parameters:
    ----------
    signal: neo.AnalogSignal, DataSignal
    cursor: tuple (x, window) or SignalCursor of type vertical or crosshair
    channel: int or None (default)
        For multi-channel signal, specified which channel is used:
        0 <= channel < signal.shape[1]
    
    Returns:
    --------
    Python Quantity array of shape (1, signal.shape[1]) with the signal minimum
    in the interval defined by the cursor's window, or the signal's sample value
    at the cursor's x coordinate if cursor window is zero.
    
    """
    
    t0,t1,_ = cursors2intervals(cursor, units=signal.times.units)
    
    if t0 == t1:
        ret = signal[signal.time_index(t0),:]
        
    else:
        ret = signal.time_slice(t0,t1).min(axis=0).flatten()
    
    if isinstance(channel, int):
        return ret[channel].flatten()
    
    return ret

@safeWrapper
def cursor_argmin(signal: typing.Union[neo.AnalogSignal, DataSignal],
                  cursor: typing.Union[tuple, SignalCursor],
                  channel: typing.Optional[int] = None) -> np.ndarray:
    """The index of minimum value of the signal across the cursor's window.

    Parameters:
    ----------
    signal: neo.AnalogSignal, DataSignal
    cursor: tuple (x, window) or SignalCursor of type vertical or crosshair
    channel: int or None (default)
        For multi-channel signal, specified which channel is used:
        0 <= channel < signal.shape[1]
    
    Returns:
    --------
    Array with the index of the signal minimum, relative to the start of the 
    interval, with shape (signal.shape[1], ).
    
    When cursor's xwindow is zero, returns an array of shape (1,) containing 
    the sample index of the cursor's x coordinate relative to the beginning of
    the signal.
    """
    
    t0,t1, _ = cursors2intervals(cursor, units=signal.times.units)
    
    t0_ndx = np.array(signal.time_index(t0)).flatten()
    
    if t0 == t1:
        return t0_ndx
        
    else:
        ret = signal.time_slice(t0,t1).argmin(axis=0).flatten() + t0_ndx
        
        if isinstance(channel, int):
            return ret[channel].flatten()
        
        return ret

@safeWrapper
def cursor_maxmin(signal: typing.Union[neo.AnalogSignal, DataSignal],
                  cursor: typing.Union[tuple, SignalCursor],
                  channel: typing.Optional[int] = None) -> tuple:
    """The maximum and minimum value of the signal across the cursor's window.

    Parameters:
    ----------
    signal: neo.AnalogSignal, DataSignal
    cursor: tuple (x, window) or SignalCursor of type vertical or crosshair
    channel: int or None (default)
        For multi-channel signal, specified which channel is used:
        0 <= channel < signal.shape[1]
    
    Returns:
    --------
    Tuple of two Python Quantity arrays each of shape (signal.shape[1], )
    respectively, with the signal maximum and minimum (respectively) in the 
    interval defined by the cursor's window.
    
    If cursor window is zero, returns a tuple with the signal's sample values 
    at the cursor's x coordinate (same value is replicated, so that the return
    object is still a two-element tuple).
    
    """
    t0,t1, _ = cursors2intervals(cursor, units = signal.times.units)
    
    if t0==t1:
        ret = signal[signal.time_index(t0),:]
        
        if isinstance(channel, int):
            ret = ret[channel].flatten()
            
        return (ret, ret)
        
    else:
    
        mx = signal.time_slice(t0,t1).max(axis=0).flatten()
        
        if isinstance(channel, int):
            mx = mx[channel].flatten()
        
        mn = signal.time_slice(t0,t1).min(axis=0).flatten()
        
        if isinstance(channel, int):
            mn = mn[channel].flatten()
        
        return (mx, mn)

@safeWrapper
def cursor_argmaxmin(signal: typing.Union[neo.AnalogSignal, DataSignal],
                     cursor: typing.Union[tuple, SignalCursor],
                     channel: typing.Optional[int] = None) -> tuple:
    """The indices of signal maximum and minimum across the cursor's window.
    """
    t0,t1,_ = cursors2intervals(cursor, units=signal.times.units)
    
    t0_ndx = np.array(signal.time_index(t0)).flatten()
    
    if t0==t1:
        return (t0_ndx, t0_ndx)
        
    else:
    
        mx = signal.time_slice(t0,t1).argmax(axis=0).flatten() + t0_ndx
        
        if isinstance(channel, int):
            mx = mx[channel].flatten()
        
        mn = signal.time_slice(t0,t1).argmin(axis=0).flatten() + t0_ndx
        
        if isinstance(channel, int):
            mn = mn[channel].flatten()
        
        return (mx, mn)

@safeWrapper
def cursor_average(signal: typing.Union[neo.AnalogSignal, DataSignal],
                   cursor: typing.Union[tuple, SignalCursor],
                   channel: typing.Optional[int]=None) -> pq.Quantity:
    """Average of signal samples across the window of a vertical cursor.
    
    Parameters:
    -----------
    
    signal: neo.AnalogSignal or datatypes.DataSignal
    
    cursor: tuple, or signalviewer.SignalCursor (vertical).
        When a tuple (t,w), it represents a notional vertical cursor with window
        "w" centered at time "t". "t" and "w" must be floats or python 
        Quantity objects with the same units as the signal's domain.
        
    channel: int or None (default). For multi-channel signals, it specifies the 
        signal channel to get the average value from.
        
        When channel is None, the function returns a python Quantity array
        (one value for each channel).
        
        When channel is an int, the function returns the average at the specifed
        channel (if it is valid)
        
    Returns:
    -------
    A python Quantity with the same units as the signal.
    
    """
    
    t0, t1, _ = cursors2intervals(cursor, units=signal.times.units)
    if t0 == t1:
        ret = cursor_value(signal, cursor, channel=channel)
        
    else:
        ret = signal.time_slice(t0,t1).mean(axis=0)
        
    
    if isinstance(channel, int):
        return ret[channel].flatten() # so that it can accept array indexing
    
    return ret

@safeWrapper
def cursor_value(signal:typing.Union[neo.AnalogSignal, DataSignal],
                 cursor: typing.Union[float, SignalCursor, pq.Quantity, tuple],
                 channel: typing.Optional[int] = None) -> pq.Quantity:
    """Value of signal at the vertical cursor's time coordinate.
    
    Signal sample values are NOT averaged across the cursor's window.
    
    Parameters:
    -----------
    signal: neo.AnalogSignal or datatypes.DataSignal
    
    cursor: float, python Quantity or vertical SignalCursor
    
            When float, it must be a valid value in the signal's domain 
                (signal domain ubnits are assumed)
                
            When a Quantity, its units must be convertible to the units of the
                signal's domain.
                
            When a SignalCursor, it must be a vertical or crosshair cursor.
            
    channel: int or None (default). Specifies which signal channel is the value
        retrieved from.
        
            When None (default), the function returns all channel values at 
                cursor. Otherwise, returns the value in the specified channel
                (channel must be a valid index >= 0 and < number of channels)
                
    Returns:
    --------
    
    python Quantity array with signal's, and shape (signal.shape[1], ) or (1,)
    when channel is specified.
    
    """
    
    data_index = cursor_index(signal, cursor)
    
    ret = signal[data_index,:]
    
    if channel is None:
        return ret
    
    return ret[channel].flatten() # so that it can be indexed

@safeWrapper
def cursor_index(signal:typing.Union[neo.AnalogSignal, DataSignal],
                 cursor: typing.Union[float, SignalCursor, pq.Quantity, tuple]) -> int:
    """Index of signal sample at the vertical cursor's time coordinate.
    
    Parameters:
    -----------
    signal: neo.AnalogSignal or datatypes.DataSignal
    
    cursor: float, python Quantity, vertical SignalCursor or cursor parameters
            tuple
    
            When float, it must be a valid value in the signal's domain 
                (signal domain ubnits are assumed)
                
            When a Quantity, its units must be convertible to the units of the
                signal's domain.
                
            When a SignalCursor, it must be a vertical or crosshair cursor.
            
                
    Returns:
    --------
    An int: index of the sample
    
    """
    # NOTE: specifying a channel doesn't make sense here because all
    # channels in the signal sharethe domain and have the same number of
    # samples
    if isinstance(cursor, float):
        t = cursor * signal.time.units
        
    elif isinstance(cursor, SignalCursor):
        if cursor.cursorType not in (SignalCursor.SignalCursorTypes.vertical, SignalCursor.SignalCursorTypes.crosshair):
            raise TypeError("Expecting a vertical or crosshair cursor; got %s instead" % cursor.cursorType)
        
        t = cursor.x * signal.times.units
        
    elif isinstance(cursor, pq.Quantity):
        if not dt.units_convertible(cursor, signal.times.units):
            raise TypeError("Expecting %s for cursor units; got %s instead" % (signal.times.units, cursor.units))
        
        t = cursor
        
    elif isinstance(cursor, (tuple, list)) and len(cursor) in (2,3) and all([isinstance(c, (numbers.Number, pq.Quantity)) for v in cursor[0:2] ]):
        # cursor parameter sequence
        t = cursor[0]
        
        if isinstance(t, numbers.Number):
            t *= signal.times.units
            
        else:
            if t.units != signal.times.units:
                if not dt.units_convertible(t, signal.times):
                    raise TypeError("Incompatible units for cursor time")
            
            t = t.rescale(signal.times.units)
        
    else:
        raise TypeError("Cursor expected to be a float, python Quantity or SignalCursor; got %s instead" % type(cursor).__name__)
    
    data_index = signal.time_index(t)
    
    return data_index

@safeWrapper
def cursors_measure(func, data, *cursors, 
                    segment_index: int = None, 
                    analog: typing.Optional[typing.Union[int, str]] = None, 
                    irregular: typing.Optional[typing.Union[int, str]] = None,
                    **kwargs) -> pq.Quantity:
    """
    data: a neo.AnalogSignal or datatypes.DataSignal
    """
    
    def __signal_measure__(f, x, *cursors, **kwargs):
        return f(x, *cursors, **kwargs)
    
    def __parse_signal_index__(x, ndx, stype):
        if isinstance(ndx, int):
            if ndx < 0 or ndx >= len(x):
                raise ValueError("Invalid signal index %d for %d signals" % (ndx, len(x)))
            
            return ndx
        
        elif isinstance(ndx, str):
            ndx = get_index_of_named_signal(x, ndx, stype=stype)
            
        else:
            raise TypeError("invalid indexing type")
            
    
    if not isinstance(func, types.FunctionType):
        raise TypeError("first parameter expected to be a function; got %s instead")
    
    if isinstance(data, (neo.AnalogSignal, DataSignal)):
        return __signal_measure__(func, data, *cursors, **kwargs)
    
    elif isinstance(data, neo.Segment):
        if analog is not None:
            analog = __parse_signal_index__(data, analog, stype=neo.AnalogSignal)
            return __signal_measure__(func, data.analogsignals[analog], *cursors, **kwargs)
            
        elif irregular is not None:
            irregular = __parse_signal_index__(data, irregular, stype=neo.IrregularlySampledDataSignal)
            return __signal_measure__(func, data.irregularlysampledsignals[irregular], *cursors, **kwargs)
        
        else:
            raise TypeError("Analog signal index must be specified")
        
    elif isinstance(data, neo.Block):
        # iterate through segments
        pass
    
    elif isinstance(data, (tuple, list)):
        if all([isinstance(s, (neo.AnalogSignal, DataSignal)) for s in data]):
            # treat as a segment's signal collection
            pass
        
        elif all([isinstance(d, neo.Segment) for d in data]):
            # iterate through segments as for block
            pass
            
        
    return func(data, *cursors, **kwargs)

    
@safeWrapper
def cursors_difference(signal: typing.Union[neo.AnalogSignal, DataSignal],
                       cursor0: typing.Union[SignalCursor, tuple], 
                       cursor1: typing.Union[SignalCursor, tuple],
                       channel: typing.Optional[int] = None) -> pq.Quantity:
    """Calculates the signal amplitude between two notional vertical cursors.
    
    amplitude = y1 - y0
    
    where y0, y1 are the average signal values across the windows of cursor0 and
    cursor1
    
    Parameters:
    -----------
    signal:neo.AnalogSignal, datatypes.DataSignal
    
    cursor0, cursor1: (x, window) tuples representing, respectively, the 
        cursor's x coordinate (time) and window (horizontal extent).
        
    Returns:
    -------
    
    Python Quantity array with signal's units and shape (signal.shape[1], ) or
    (1, ) when channel is specified.
        
    """
    
    y0 = cursor_average(signal, cursor0, channel=channel)
    y1 = cursor_average(signal, cursor1, channel=channel)
    
    return y1-y0

@safeWrapper
def cursors_distance(signal: typing.Union[neo.AnalogSignal, DataSignal],
                     cursor0: typing.Union[SignalCursor, tuple], 
                     cursor1: typing.Union[SignalCursor, tuple],
                     channel: typing.Optional[int] = None) -> pq.Quantity:
    """Distance between two cursors, in signal samples.
    
    NOTE: The distance between two cursors in the signal domain can be
    calculated directly as the difference between the cursors' x coordinates
    
    """
    ret = [cursor_index(signal, c) for c in (cursor0, cursor1)]
    
    return abs(ret[1]-ret[0])

@safeWrapper
def chord_slope(signal: typing.Union[neo.AnalogSignal, DataSignal], 
                t0: typing.Union[float, pq.Quantity], 
                t1: typing.Union[float, pq.Quantity],
                w0: typing.Optional[typing.Union[float,  pq.Quantity]]=0.001*pq.s,
                w1: typing.Optional[typing.Union[float, pq.Quantity]] = None,
                channel: typing.Optional[int] = None) -> pq.Quantity:
    """Calculates the chord slope of a signal between two time points t0 and t1.
    
                    slope = (y1 - y0) / (t1 - t0)
    
    The signal values (y0, y1) at time points (t0, t1) are taken as the average 
    of the sample values in a window (w) around t0 and t1:
    
    y0 = signal.time_slice(t0-w0/2, t0+w0/2).mean(axis=0)
    y1 = signal.time_slice(t1-w1/2, t1+w1/2).mean(axis=0)
    
    Parameters:
    ==========
    signal: neo.AnalogSignal, DataSignal
    
    t0: scalar float or python Quantity =  the limits of the interval where
            the chord slope is calculated, including the half-windows before t0
            and after t1;
            
            Their units must be convertible to the signal's time units
    
    w:  a scalar float or python Quantity = a window around the time points, 
        across which the mean signal value is calculated (useful for noisy 
        signals).
        
        Default is 0.001 * pq.s (i.e. 1 ms)
        
    w1: like w (optional default is None). When present, the windows w and w1
    are used respectively, with the time points t0 and t1.
        
    channel: int or None (default). For multi-channel signals, it specifies the 
        signal channel to get the average value from.
        
        When channel is None, the function returns a python Quantity array
        (one value for each channel).
        
        When channel is an int, the function returns the average at the specifed
        channel (if it is valid)
        
    Returns:
    ========
    
    A python quantity array with as many values as there are column vectors
    (channels) in the signal. The units are derived from the signal units and 
    signal's time units.
    
    """
    if isinstance(t0, numbers.Real):
        t0 *= signal.times.units
        
    if isinstance(t1, numbers.Real):
        t1 *= signal.times.units
        
    if isinstance(w, numbers.Real):
        w0 *= signal.times.units
        
    if isinstance(w1, numbers.Real):
        w1 *= signal.times.units
        
    y0 = signal.time_slice(t0-w0/2, t0+w0/2).mean(axis=0)
    
    if w1 is not None:
        y1 = signal.time_slice(t1-w1/2, t1+w1/2).mean(axis=0)
        
    else:
        y1 = signal.time_slice(t1-w0/2, t1+w0/2).mean(axis=0)
        
    #print(y0, y1, t0, t1)
    
    ret = (y1-y0) / (t1-t0)
    
    if channel is None:
        return ret
    
    else:
        return ret[channel].flatten() # so that it can accept array indexing
    
#@safeWrapper
#"def" epoch_chord_slope(signal,
                      #epoch: neo.Epoch,
                      #channel: typing.Optional[int] = None) -> pq.Quantity:
    #pass
    
@safeWrapper
def cursors_chord_slope(signal: typing.Union[neo.AnalogSignal, DataSignal],
                        cursor0: typing.Union[SignalCursor, tuple],
                        cursor1: typing.Union[SignalCursor, tuple],
                        channel: typing.Optional[int] = None) -> pq.Quantity:
    """Signal chord slope between two vertical cursors.
    
    The function calculates the slope of a straight line connecting the 
    intersection of the signal with two vertical cursors (of with the vertical
    lines os two crosshair cursors).
    
    The signal value at each cursor is taken as the average of signal samples
    across the cursor's horizontal window if non-zero, or the sample values at 
    the cursor's coordinate.
    
    Parameters:
    ----------
    signal
    
    cursor0, cursor1: tuple (x, window) representing, respectively, the cursor's
        x coordinate (time) and (horizontal) window, or a
        gui.signalviewer.SignalCursor of type "vertical"
    
    """
    t0 = cursor0[0] if isinstance(cursor0, tuple) else cursor0.x
    
    y0 = cursor_average(signal, cursor0, channel=channel)
    
    if isinstance(t0, float):
        t0 *= signal.times.units
        
    t1 = cursor1[0] if isinstance(cursor1, tuple) else cursor1.x

    if isinstance(t1, float):
        t1 *= signal.times.units
        
    y1 = cursor_average(signal, cursor1, channel=channel)
    
    return (y1-y0)/(t1-t0)
    
@safeWrapper
def epoch2cursors(epoch: neo.Epoch, 
                  axis: typing.Optional[typing.Union[pg.PlotItem, pg.GraphicsScene]] = None,
                  **kwargs) -> typing.Sequence:
    """Creates vertical signal cursors from a neo.Epoch.
    
    Parameters:
    ----------
    epoch: neo.Epoch
    
    axis: (optional) pyqtgraph.PlotItem, pyqtgraph.GraphicsScene, or None.
    
        Default is None, in which case the function returns cursor parameters.
    
        When not None, the function populates 'axis' with a sequence of 
        vertical SignalCursor objects and returns their references in a list.
        
    Var-keyword parameters:
    ----------------------
    keep_units: bool, optional default is False
        When True, the numeric cursor parameters are python Quantities with the
        units borrowed from 'epoch'
        
    Other keyword parameters are passed to the cursor constructors:
    parent, follower, xBounds, yBounds, pen, linkedPen, hoverPen
    
    See the documentation of signalviewer.SignalCursor.__init__ for details.
    
    Returns:
    --------
    When axis is None, returns a list of tuples of vertical cursor parameters
        (time, window, labels) where:
        
        time = epoch.times + epoch.durations/2.
        window = epoch.durations
        labels = epoch.labels -- the labels of the epoch's intervals
        
    When axis is a pyqtgraph.PlotItem or a pyqtgraph.GraphicsScene, the function
    adds vertical SignalCursors to the axis and returns a list with references
    to them.
    
    Side effects:
    -------------
    When axis is not None, the cursors are added to the PlotItem or GraphicsScene
    specified by the 'axis' parameter.
    """
    keep_units = kwargs.pop("keep_units", False)
    if not isinstance(keep_units, bool):
        keep_units = False
        
    if keep_units:
        ret = [(t + d/2., d, l) for (t, d, l) in zip(epoch.times, epoch.durations, epoch.labels)]
        
    else:
        ret = [(t + d/2., d, l) for (t, d, l) in zip(epoch.times.magnitude, epoch.durations.magnitude, epoch.labels)]
    
    if isinstance(axis, (pg.PlotItem, pg.GraphicsScene)):
        # NOTE: 2020-03-10 18:23:03
        # cursor constructor accepts python Quantity objects for its numeric
        # parameters x, y, xwindow, ywindow, xBounds and yBounds
        cursors = [SignalCursor(axis, x=t, xwindow=d,
                                cursor_type=SignalCursor.SignalCursorTypes.vertical,
                                cursorID=l) for (t,d,l) in ret]
        return cursors
    
    return ret

@safeWrapper
def epoch2intervals(epoch: neo.Epoch, keep_units:bool = False) -> typing.Sequence:
    """Generates a sequence of intervals as triplets (t_start, t_stop, label).
    
    Each interval coresponds to the epoch's interval.
    
    Parameters:
    ----------
    epoch: neo.Epoch
    
    keep_units: bool (default False)
        When True, the t_start and t_stop in each interval are scalar python 
        Quantity objects (units borrowed from the epoch)
    
    """
    if keep_units:
        return [(t, t+d, l) for (t,d,l) in zip(epoch.times, epoch.durations, epoch.labels)]
        
    else:
        return [(t, t+d, l) for (t,d,l) in zip(epoch.times.magnitude, epoch.durations.magnitude, epoch.labels)]
    
@safeWrapper
def intervals2epoch(*args, **kwargs) -> neo.Epoch:
    """Construct a neo.Epoch from a sequence of interval tuples or triplets.
    
    Variadic parameters:
    --------------------
    tuples (t0,t1) or triplets (t0,t1,label), or a sequence of tuples or triplets
    each specifying an interval
    
    """
    units = kwargs.pop("units", pq.s)
    if not isinstance(units, pq.Quantity) or units.size > 1:
        raise TypeError("units expected to be a scalar python Quantity")

    name = kwargs.pop("name", "Epoch")
    if not isinstance(name, str):
        raise TypeError("name expected to be a string")
    
    if len(name.strip())==0:
        raise ValueError("name must not be empty")
    
    sort = kwargs.pop("sort", True)
    if not isinstance(sort, bool):
        raise TypeError("sort must be a boolean")
    
    def __generate_epoch_interval__(value):
        if not isinstance(value, (tuple, list)) or len(value) not in (2,3):
            raise TypeError("expecting a tuple of 2 or 3 elements")
        
        if len(value) == 3:
            if not isinstance(value[2], str) or len(value[2].strip()) == 0:
                raise ValueError("expecting a non-empty string as thirs element in the tuple")
            
            l = value[2]
                
        else:
            l = None
            
        u = units # by default if boundaries are scalars
        
        if not all([isinstance(v, (pq.Quantity, numbers.Number)) for v in value[0:2]]):
            raise TypeError("interval boundaries must be scalar numbers or quantities")
        
        if all([isinstance(v, pq.Quantity) for v in value[0:2]]):
            if any([v.size != 1 for v in value[0:2]]):
                raise TypeError("interval boundaries must be scalar quantities")
            
            u = value[0].units #store the units
            
            if value[0].units != value[1].units:
                if not dt.units_convertible(value[0], value[1]):
                    raise TypeError("interval boundaries must have compatible units")
                
                else:
                    value = [float(value[0]), float(value[1].rescale(value[0].units))]
                    
            else:
                value = [float(v) for v in value[0:2]]
            
        t, d = (value[0], value[1] - value[0])
        
        if d < 0:
            raise ValueError("interval cannot have negative duration")

        return (t, d, u) if l is None else (t, d, u, l)
     
    tdl = None
    
    if len(args) == 1:
        if isinstance(args[0], (tuple, list)):
            if len(args[0]) in (2,3): # a sequence with one tuple of 2-3 elements
                if all([isinstance(v, (numbers.Number, pq.Quantity)) for v in args[0][0:2]]):
                    # this can be an interval tuple
                    tdl = [__generate_epoch_interval__(args[0])]
                    
                elif all([isinstance(v, (tuple, list)) and len(v) in (2,3) and all([isinstance(_x, (numbers.Number, pq.Quantity)) for _x in v[0:2]]) for v in args[0]]):
                    # or a sequence of tuples -- feed this into __generate_epoch_interval__
                    # and hope for the best
                    if sort:
                        tdl = [__generate_epoch_interval__(v) for v in sorted(args[0], key=lambda x: x[0])]
                        
                    else:
                        tdl = [__generate_epoch_interval__(v) for v in args[0]]
                    
                else:
                    raise TypeError("incorrect syntax")
                
            else:
                if all([isinstance(v, (tuple, list)) and len(v) in (2,3) and all([isinstance(_x, (numbers.Number, pq.Quantity)) for _x in v[0:2]]) for v in args[0]]):
                    if sort:
                        tdl = [__generate_epoch_interval__(v) for v in sorted(args[0], key=lambda x: x[0])]
                    else:
                        tdl = [__generate_epoch_interval__(v) for v in args[0]]

        else:
            raise TypeError("expecting a sequence of tuples, or a 2- or 3- tuple")
        
    else:
        # sequence of 2- or 3- tuples
        if all([isinstance(v, (tuple, list)) and len(v) in (2,3) and all([isinstance(_x, (numbers.Number, pq.Quantity)) for _x in v[0:2]]) for v in args]):
            if sort:
                tdl = [__generate_epoch_interval__(v) for v in sorted(args, key=lambda x: x[0])]
                
            else:
                tdl = [__generate_epoch_interval__(v) for v in args]
        
        else:
            raise TypeError("expecting 2- or 3- tuples")
        
    if tdl is not None:
        # all numeric elements in tdl are python quantities
        if all([len(v) == 4 for v in tdl]):
            times, durations, units, labels = [x_ for x_ in zip(*tdl)]
            ret = neo.Epoch(times = times, durations = durations, units = units[0], labels=labels)
        else:
            times, durations, units = [x_ for x_ in zip(*tdl)]
            ret = neo.Epoch(times = times, durations = durations, units=units[0])
                
        return ret

@safeWrapper
def intervals2cursors(*args, **kwargs) -> typing.Sequence:
    """Construct a neo.Epoch from a sequence of interval tuples or triplets.
    
    Variadic parameters:
    --------------------
    triplets (t0,t1,label), or a sequence of tuples or triplets
    each specifying an interval
    
    """
    axis = kwargs.pop("axis", None)
    if not isinstance(axis, (int, pg.PlotItem, type(None))):
        raise TypeError("axis expected to be an int, a PlotItem or None; got %s instead" % type(axis).__name__)

    sort = kwargs.pop("sort", True)
    
    if not isinstance(sort, bool):
        raise TypeError("sort must be a boolean")
    
    def __generate_cursor_params__(value):
        # start, stop, label
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise TypeError("expecting a tuple of 3 elements")
        
        if not isinstance(value[2], str) or len(value[2].strip()) == 0:
            raise ValueError("expecting a non-empty string as thirs element in the tuple")
        
        l = value[2]
        
        if not all([isinstance(v, (pq.Quantity, numbers.Number)) for v in value[0:2]]):
            raise TypeError("interval boundaries must be scalar numbers or quantities")
        
        if all([isinstance(v, pq.Quantity) for v in value[0:2]]):
            if any([v.size != 1 for v in value[0:2]]):
                raise TypeError("interval boundaries must be scalar quantities")
            
            if value[0].units != value[1].units:
                if not dt.units_convertible(value[0], value[1]):
                    raise TypeError("interval boundaries must have compatible units")
                
                else:
                    value = [float(value[0]), float(value[1].rescale(value[0].units)), value[2]]
                    
            else:
                value = [float(v) for v in value[0:2]] + [value[2]]
            
        x, xwindow = (value[0], value[1]-value[0])
        
        if xwindow < 0:
            raise ValueError("interval cannot have negative duration")
        
        x += xwindow/2. 
        
        return (x, xwindow, l)
     
    xwl = None
    
    if len(args) == 1:
        if isinstance(args[0], (tuple, list)):
            if len(args[0]) in (2,3): # a sequence with one tuple of 2-3 elements
                if all([isinstance(v, (numbers.Number, pq.Quantity)) for v in args[0][0:2]]):
                    # this can be an interval tuple
                    xwl = [__generate_cursor_params__(args[0])]
                    
                elif all([isinstance(v, (tuple, list)) and len(v) in (2,3) and all([isinstance(_x, (numbers.Number, pq.Quantity)) for _x in v[0:2]]) for v in args[0]]):
                    # or a sequence of tuples -- feed this into __generate_cursor_params__
                    # and hope for the best
                    if sort:
                        xwl = [__generate_cursor_params__(v) for v in sorted(args[0], key=lambda x: x[0])]
                    
                    else:
                        xwl = [__generate_cursor_params__(v) for v in args[0]]
                    
                else:
                    raise TypeError("incorrect syntax")
                
            else:
                if all([isinstance(v, (tuple, list)) and len(v) in (2,3) and all([isinstance(_x, (numbers.Number, pq.Quantity)) for _x in v[0:2]]) for v in args[0]]):
                    if sort:
                        xwl = [__generate_cursor_params__(v) for v in sorted(args[0], key=lambda x: x[0])]

        else:
            raise TypeError("expecting a sequence of tuples, or a 2- or 3- tuple")
        
    else:
        # sequence of 2- or 3- tuples
        if all([isinstance(v, (tuple, list)) and len(v) in (2,3) and all([isinstance(_x, (numbers.Number, pq.Quantity)) for _x in v[0:2]]) for v in args]):
            if sort:
                xwl = [__generate_cursor_params__(v) for v in sorted(args, key=lambda x: x[0])]
            
            else:
                xwl = [__generate_cursor_params__(v) for v in args]
        
        else:
            raise TypeError("expecting 2- or 3- tuples")
        
    if xwl is not None:
        if axis is not None:
            cursors = [SignalCursor(axis, x=p[0], xwindow=p[1], cursorID=p[2], 
                                    cursor_type=SignalCursor.SignalCursorTypes.vertical) for p in xwl]
                
            return cursors
        
        return xwl

@safeWrapper
def epoch_average(signal: typing.Union[neo.AnalogSignal, DataSignal],
                  epoch: neo.Epoch,
                  channel: typing.Optional[int] = None) -> list:
    """Signal average across an epoch's intervals.
    
    Parameters:
    -----------
    signal: neo.AnalogSignal or datatypes.DataSignal
    
    epoch: neo.Epoch
    
    channel: int or None (default)
    
    Returns:
    --------
    
    A list of python Quantity objects with as many elements as there
    are times,durations pairs in the epoch.
    
    For multi-channel signals, the Quantity are arrays of size that equals the
    number of channels.
    
    """
    
    t0 = epoch.times
    t1 = epoch.times + epoch.durations
    
    ret = [signal.time_slice(t0_, t1_).mean(axis=0) for (t0_, t1_) in zip(t0,t1)]
    
    if isinstance(channel, int):
        ret = [r[channel].flatten() for r in ret]
        
    return ret

@safeWrapper
def plot_signal_vs_signal(x: typing.Union[neo.AnalogSignal, neo.Segment, neo.Block],
                          *args, **kwargs):
    from . import plots
    
    if isinstance(x, neo.Block):
        segment = kwargs.pop("segment", 0)
        
        return plot_signal_vs_signal(x.segments[segment], **kwargs)
        
    elif isinstance(x, neo.Segment):
        sig0 = kwargs.pop("sig0", 0)
        sig1 = kwargs.pop("sig1", 1)
        
        if isinstance(sig0, str):
            sig0 = get_index_of_named_signal(x, sig0, stype=neo.AnalogSignal)
            
        if isinstance(sig1, str):
            sig1 = get_index_of_named_signal(x, sig1, stype=neo.AnalogSignal)
        
        return plot_signal_vs_signal(x.analogsignals[sig0], x.analogsignals[sig1], **kwargs)
        
    elif isinstance(x, neo.AnalogSignal):
        return plots.plotZeroCrossedAxes(x,args[0], **kwargs)


@safeWrapper
def plot_spike_waveforms(x: neo.SpikeTrain, 
                         figure: typing.Union[mpl.figure.Figure, type(None)] = None, 
                         new: bool = True, 
                         legend: bool = False):
    import matplotlib.pyplot as plt
    
    if not isinstance(x, neo.SpikeTrain):
        raise TypeError("Expected a neo.SpikeTrain object; got %s instead" % (type(x).__name__))

    if (x.waveforms is None) or (not x.waveforms.size):
        return
    
    if figure is None:
        figure = plt.gcf()
        
    elif type(figure).__name__ == "Figure":
        plt.figure(figure.number)
        
    else:
        raise TypeError("'figure' argument must be None or a matplotlib figure; got %s instead" % type(figure).__name__)
    
    if new:
        plt.clf()
        
    lines = plt.plot(np.squeeze(x.waveforms.T))
    
    if legend:
        for k,l in enumerate(lines):
            l.set_label("spike %d" % (k))
            
        plt.legend()
        
        figure.canvas.draw_idle()
    
    return lines
    
def get_signal_names_indices(data: typing.Union[neo.Segment, typing.Sequence],
                             analog: bool = True) -> typing.List[str]:
    """Returns a list of analog signal names in data.
    
    Produces a list of signal names in the data; for signals that do not have a
    name ('name' attribute is either None or the empty string after stripping 
    blank characters) the list contains a string representation of the signal
    indices in the data in the form of "signal_k" where "k" stands for the signal
    iteration index; signals with "name" attribute that is not a string will
    be treated similarly.
    
    NOTE: here, signal "indices" represent their position in the signal collection
    in the data, in iteration order and should not be confused with the signal's 
    "index" attribute (whch has a totally different mreaning in neo library).
    
    The function is useful especially for GUI programming when a list of signal 
    names may be used for populating a combo box, for instance.
    
    Parameters:
    ==========
    
    data: a neo.Segment, or a sequence of neo.AnalogSignal, datatypes.DataSignal, 
            and/or neo.IrregularlySampledSignal objects
    
    analog: boolean, default True: returns the names/indices of analosignals and
            datasignals otherwise returns the names/indices of irregularly 
            sampled signals
            
            used only when data is a neo.Segment (as it may contain either of the above)
    
    """
    from . import datatypes as dt
    
    if isinstance(data, neo.Segment):
        if analog:
            if not hasattr(data, "analogsignals"):
                return list()
            
            signals = data.analogsignals
            
        else:
            if not hasattr(data, "irregularlysampledsignals"):
                return list()
            
            signals = data.irregularlysampledsignals
        
    elif isinstance(data, (tuple, list)):
        if all([isinstance(s, (neo.AnalogSignal, DataSignal, neo.IrregularlySampledSignal)) for s in data]):
            signals = data
            
        else:
            raise TypeError("The sequence should contain only neo.AnalogSignal, datatypes.DataSignal and neo.IrregularlySampledSignal objects")

    else:
        raise TypeError("Expecting a neo.Segment or a sequence of neo.AnalogSignal, datatypes.DataSignal and neo.IrregularlySampledSignal objects; got %s instead" % type(data).__name__)
    
    sig_indices_names = [[k, sig.name] for k, sig in enumerate(signals)]
    
    #print("sig_indices_names", sig_indices_names)
    
    for k in range(len(signals)):
        if sig_indices_names[k][1] is None or not isinstance(sig_indices_names[k][1], str) or len(sig_indices_names[k][1].strip()) == 0:
            sig_indices_names[k][1] = "signal_%d" % sig_indices_names[k][0]
            
    return [item[1] for item in sig_indices_names]
    
def normalized_segment_index(src: neo.Block,
                             index: typing.Union[int, str, range, slice, typing.Sequence]):
    """Returns integral indices of a Segment in a neo.Block or list of Segments.
    """
    
    if isinstance(src, neo.Block):
        src = src.segments
        
    elif isinstance(src, neo.Segment):
        src = [src]
        
    elif not isinstance(src, (tuple, list)) or not all([isinstance(s, neo.Segment) for s in src]):
        raise TypeError("src expected to be a neo.Block, a sequence of neo.Segments, or a neo.Segment; got %s instead" % type(src).__name__)
    
    data_len = len(src)
    
    if isinstance(index, (int, range, slice, np.ndarray, type(None))):
        return normalized_index(data_len, index)
    
    elif isinstance(index, str):
        if slient:
            return utilities.silentindex([i.name for i in src], index)

        return [i.name for i in src].index(index)
    
    elif isinstance(index, (tuple, list)):
        indices = list()
        
        for ndx in index:
            if isinstance(ndx, int):
                indices.append(normalized_index(data_len, ndx))
                
            elif isinstance(ndx, str):
                if silent:
                    indices.append(utilities.silentindex([i.name for i in src], ndx))
                    
                else:
                    indics.append([i.name for i in src].index(ndx))
                    
            else:
                raise TypeError("Invalid index element type %s" % type(ndx).__name__)
        return indices
    
    else:
        raise TypeError("Invalid indexing: %s" % index)
    
def neo_child_property_name(type_or_obj):
    """Provisional.
    As of neo 0.8.0 this only works for neo.Unit, in neo.Block
    """    
    return "list_%s" % neo_child_container_name(type_or_obj)
        
def neo_child_container_name(type_or_obj):
    """Provisional: name of member collection.
    Returns a valid child container name; doesn't tell is a container actually
    HAS these children
    """
    if inspect.isclass(type_or_obj):
        if neo.regionofinterest.RegionOfInterest in inspect.getmro(type_or_obj):
            return "regionsofinterest"
        
        else:
            return neo.baseneo._container_name(type_or_obj.__name__)
        
    elif isinstance(type_or_obj, str):
        if type_or_obj in dir(neo.regionofinterest):
            return "regionsofinterest"
        
        else:
            return neo.baseneo._container_name(type_or_obj)
        
    else:
        if isinstance(type_or_obj, neo.regionofinterest.RegionOfInterest):
            return "regionsofinterest"
        
        else:
            return neo.baseneo._container_name(type(type_or_obj).__name__)
            
        
def neo_child_reference_name(type_or_obj):
    """Provisional: name of attribute name ot reference instance of type_or_obj
    """
    
    if inspect.isclass(type_or_obj):
        if neo.regionofinterest.RegionOfInterest in inspect.getmro(type_or_obj):
            return "regionofinterest"
        
        else:
            return neo.baseneo._reference_name(type_or_obj.__name__)
        
    elif isinstance(type_or_obj, str):
        if s in dir(neo.regionofinterest):
            return "regionofinterest"
        
        else:
            return neo.baseneo._reference_name(type_or_obj)
        
    else:
        if isinstance(type_or_obj, neo.regionofinterest.RegionOfInterest):
            return "regionofinterest"
        
        else:
            return neo.baseneo._reference_name(type(type_or_obj).__name__)
        
def __get_container_collection_attribute__(container, attrname,
                                           container_index=None,
                                           multiple=True):
    
    ret = getattr(container, attrname, None)
    
    if container_index is None:
        return [(k, c) for k, c in enumerate(ret)]
    
    else:
        return [(k, ret[k]) for k in normalized_index(len(ret), container_index, multiple=multiple)]
            
def __container_lookup__(container: neo.container.Container, 
                         index_obj: typing.Union[str, int, tuple, list, np.ndarray, range, slice],
                         contained_type: neo.baseneo.BaseNeo,
                         multiple:bool = True, 
                         return_objects:bool = False,
                         **kwargs) -> dict:
    """ Cases 2 & 4       
    """
    # 1) check if the container's type is among the contained_type._parent_objects
    
    if isinstance(container, neo.container.Container):
        pfun0 = functools.partial(normalized_index, index=index_obj, multiple=multiple)
        
        member_collection_names = [neo_child_container_name(contained_type), neo_child_property_name(contained_type)]
        
        member_collections = [getattr(container, cname, None) for cname in member_collection_names]
            
        ret = dict((cname, t) for cname, t in zip(member_collection_names, map(pfun0, member_collections)) if len(t) > 0)
        
        if len(ret) == 0:
            # might by indirectly contained
            # this is where additional index objects for collection of data that may be in kwargs should be applied
            
            direct_containers = contained_type._single_parent_objects
            
            child_container_names = [neo_child_container_name(c) for c in direct_containers]
            
            child_container_collections = [getattr(container, cname, None) for cname in child_container_names]
            
            child_container_collections2 = [__get_container_collection_attribute__(container, cname, kwargs.get(cname, None)) for cname in child_container_names]
            
            pfun = functools.partial(__collection_lookup__, 
                                    index_obj = index_obj,
                                    contained_type = contained_type,
                                    multiple = multiple,
                                    return_objects = return_objects)
            
            ret = dict((cname, d) for cname, d in zip(child_container_names, map(pfun, child_container_collections)) if len(d) > 0)

    else:
        ret = dict()
        
    return ret

def __collection_lookup__(seq: typing.Sequence, 
                          index_obj: typing.Union[str, int, tuple, list, np.ndarray, range, slice],
                          contained_type: neo.baseneo.BaseNeo,
                          seq_index: typing.Optional[typing.Union[int, tuple, list, range, slice]] = None,
                          multiple:bool = True, 
                          return_objects:bool = False,
                          **kwargs) -> dict:
    """ Case 3
    """
    if seq is None:
        return dict()
    
    pfun = functools.partial(__container_lookup__, 
                             index_obj = index_obj,
                             contained_type = contained_type, 
                             multiple = multiple,
                             return_objects = return_objects)
    
    if seq_index is None:
        return dict((k, d) for k, d in enumerate(map(pfun, seq)) if len(d) > 0 and any([len(val) > 0 for key, val in d.items()]))
    
    elif isinstance(seq_index, (tuple, list, range)) and all([isinstance(v, int) for v in seq]):
        k_ = [k for k in seq_index]
        seq_ = [seq[k] for k in k_]
        
        return dict((k, d) for k, d in zip(map(pfun, seq), k_) if len(d) > 0 and any([len(val) > 0 for key, val in d.items()]))
    
    elif isinstance(seq_index, slice):
        k_ = [k for k in seq_index.indices(len(seq))]
        seq_ = seq[seq_index]
        
        return dict((k, d) for k, d in zip(map(pfun, seq), k_) if len(d) > 0 and any([len(val) > 0 for key, val in d.items()]))
    
    else:
        return dict()
    
        
def neo_lookup(src: typing.Union[neo.core.container.Container, typing.Sequence[neo.core.container.Container]],
               index: typing.Union[int, str, range, slice, typing.Sequence],
               ctype: type = neo.AnalogSignal,
               multiple: bool = True,
               return_objects:bool = False) -> typing.Union[dict, tuple]:
    """Provisional - work in progress
    
    Positional parameters:
    ----------------------
    src: neo.core.container.Container or a sequence of Container objects
        (neo.core.container.Container is the ancestor of all container objects 
        in the neo package)
        
    index: int, str, range, slice, or sequence of int or str.
        CAUTION: The sequence can contain a mixture of int and str.
        
        When index is a string, the function looks up objects by the value of 
        their "name" attribute - all data objects in the neo package except for 
        neo.regionofinterest.RegionOfInterest. 
        
        WARNING This name lookup assumes that all data object children have 
            unique values for their "name" attribute.
            
        If this is not the case, the behaviour of the function depends on the
            value of the "multiple" parameter (see below).
        
    ctype: type, default is neo.AnalogSignal; the type of the contained object
    
    multiple: bool, default is True; controls the behaviour when looking up
        objects by their "name" attribute.
        
        When True, the function will return  the index of all objects for which
        the "name" attribute equals the value in index.
        
        When False, the function returns the index of the first object for which
        the "name" attribute equals the value in index (python's default)
        
        This parameters is passed to, and control the bbehaviour of, the 
        utilities.normalized_index(...) function.
        
    See also:
        utilities.normalized_index
        
    """
    if isinstance(src, (tuple, list)):
        return tuple([__container_lookup__(s, index, ctype, multiple=True, return_objects=return_objects) for s in src])
    
    else:
        return __container_lookup__(src, index, ctype, multiple=True, return_objects=return_objects)
    
def neo_index(src: typing.Union[neo.container.Container, typing.Sequence],
                    ndx: typing.Union[typing.Mapping, typing.Sequence]) -> tuple:
    """Provisional. Applies dictionary ndx created by neo_lookup.
    """
    if __debug__:
        global __debug_count__
        __debug_count__ += 1
        
        __debug_indent__ = "   " * (__debug_count__ -1)
        
    ret = list()
    
    if isinstance(src, (tuple, list)): # NOTE: 2020-03-23 23:41:16 sequence of containers or data objects
        if isinstance(ndx, (tuple, list)) and all([isinstance(k, int) for k in ndx]): # sequence of ints
            ret += [src[k] for k in ndx] # simply return the kth element, k in ndx
            
        elif isinstance(ndx, int):# and all([isinstance(s, neo.container.Container) for s in src]):
            ret += [src[ndx]] # return the ndxth element
            
        elif isinstance(ndx, dict):
            for key, index in ndx.items():
                if isinstance(key, int):
                    ret_ = neo_index(src[key], index)
                    ret += [v for v in ret_ if all([not is_same_as(v, v_) for v_ in ret])]
                              
                else:
                    raise IndexError("Unexpected index:%s at key:%s = %s, for src:%s" % (type(index).__name__, type(key).__name__, key, type(src).__name__))
            
        else:
            raise TypeError("Unexpected indexing type %s for %s object" % (type(ndx).__name__, type(src).__name__))
        
    elif isinstance(src, neo.container.Container): # typical entry point
        if isinstance(ndx, dict):
            for key, index in ndx.items(): # iterate through the ndx dict's key/value pairs
                if isinstance(key, str): # works on Container's attribute in 'key'
                    collection = getattr(src, key, None) # sequence of containers or data objects
                    
                    if collection is None:
                        raise AttributeError("%s is an invalid attribute of %s" % (key, type(src).__name__))
                    
                    if isinstance(index, (dict, tuple, list)):
                        ret += [v for v in neo_index(collection, index) if v not in ret] # enters at NOTE: 2020-03-23 23:41:16 
                        
                    else:
                        raise KeyError("Unexpected indexing structure type %s for %s object" % (type(index).__name__, type(collection).__name__))
                    
                #elif isinstance(key, int): # an int key in a dict ndx - cannot work
                    
                    #if isinstance(src, (tuple, list)):
                        #ret += [v for v in neo_index(src[key], index) if v not in ret]
                        
                    #else:
                        #raise TypeError("Invalid object of indexing: %s" % type(src).__name__)
    else:
        raise IndexError("Invalid indexing structure type: %s" % type(ndx).__name__)
    

    
    #if isinstance(ndx, dict):
        #for key, index in ndx.items():
            #if isinstance(key, str):
                #if isinstance(src, neo.container.Container):
                    #collection = getattr(src, key, None)
                    
                    #if collection is None:
                        #raise AttributeError("%s is an invalid attribute of %s" % (key, type(src).__name__))
                    
                    #if isinstance(index, (dict, tuple, list)):
                        #try:
                            #ret += [v for v in neo_index(collection, index) if v not in ret]
                                #if __debug__:
                                #print("%sCall %d" % (__debug_indent__, __debug_count__))
                                #print("%ssrc: %s" % (__debug_indent__, type(src).__name__))
                                #print("%sndx: %s" % (__debug_indent__, type(ndx).__name__))
                                #print("%sndx key: %s = %s " % (__debug_indent__, type(key).__name__, key))
                                #print("%sndx index: %s " % (__debug_indent__, type(index).__name__))
                                #print("%scollection: %s" % (__debug_indent__, type(collection).__name__))
                            
                        #except Exception as e:
                            #if __debug__:
                                #print("%sException in call %d" % (__debug_indent__, __debug_count__))
                                #print("%ssrc: %s" % (__debug_indent__, type(src).__name__))
                                #print("%sndx: %s" % (__debug_indent__, type(ndx).__name__))
                                #print("%sndx key: %s = %s " % (__debug_indent__, type(key).__name__, key))
                                #print("%sndx index: %s " % (__debug_indent__, type(index).__name__))
                                #print("%scollection: %s" % (__debug_indent__, type(collection).__name__))
                                
                                #__debug_count__ -= 1
                            
                            #raise e
                        
                    #else:
                        #raise KeyError("Unexpected indexing structure type: %s" % type(index).__name__)
                    
                #else:
                    #raise TypeError("Invalid object of indexing: %s" % type(src).__name__)
                
            #elif isinstance(key, int):
                #if isinstance(src, (tuple, list)):
                    #try:
                        ##ret += [v for v in neo_index(src[key], index) if v not in ret]
                        #ret += [v for v in neo_index(src[key], index)]
                        #if __debug__:
                            #print("%sCall %d: " % (__debug_indent__, __debug_count__))
                            #print("%ssrc: %s" % (__debug_indent__, type(src).__name__))
                            #print("%sndx: %s" % (__debug_indent__, type(ndx).__name__))
                            #print("%sndx key: %s = %s " % (__debug_indent__, type(key).__name__, key))
                            #print("%sndx index: %s " % (__debug_indent__, type(index).__name__))
                            #print("%ssrc[key]: %s" % (__debug_indent__, type(src[key]).__name__))
                            
                    #except Exception as e:
                        #if __debug__:
                            #print("%sException in call %d: " % (__debug_indent__, __debug_count__))
                            #print("%ssrc: %s" % (__debug_indent__, type(src).__name__))
                            #print("%sndx: %s" % (__debug_indent__, type(ndx).__name__))
                            #print("%sndx key: %s = %s " % (__debug_indent__, type(key).__name__, key))
                            #print("%sndx index: %s " % (__debug_indent__, type(index).__name__))
                            #print("%ssrc[key]: %s" % (__debug_indent__, type(src[key]).__name__))
                            
                            #__debug_count__ -= 1
                        
                        #raise e
                        
                    
                #else:
                    #raise TypeError("Invalid object of indexing: %s" % type(src).__name__)
                
    #elif isinstance(ndx, tuple):
        #if isinstance(src, (tuple, list)):
            #try:
                #ret += [src[k] for k in ndx if src[k] not in ret]
                #if __debug__:
                    #print("%sCall %d: " % (__debug_indent__, __debug_count__))
                    #print("%ssrc: %s" % (__debug_indent__, type(src).__name__))
                    #print("%sndx: %s" % (__debug_indent__, type(ndx).__name__))
            #except Exception as e:
                #if __debug__:
                    #print("%sException in call %d: " % (__debug_indent__, __debug_count__))
                    #print("%ssrc: %s" % (__debug_indent__, type(src).__name__))
                    #print("%sndx: %s" % (__debug_indent__, type(ndx).__name__))
                    
                    #__debug_count__ -= 1
                
                #raise e
                
    
        #else:
            #raise TypeError("Invalid object of indexing: %s" % type(src).__name__)
        
    #else:
        #raise TypeError("Invalid indexing structure type: %s" % type(ndx).__name__)
    
    if __debug__:
        __debug_count__ -= 1
        
    return tuple(ret)
            
def normalized_signal_index(src: neo.core.container.Container,
                            index: typing.Union[int, str, range, slice, typing.Sequence],
                            ctype: type = neo.AnalogSignal, 
                            silent: bool = False) -> typing.Union[range, list]:
    """Returns the integral index of a signal in its container.
    
    Useful to get the index of data by its name. 
    CAUTION Indexing by name assumes that all data in the container have unique names.
    
    Parameters:
    ----------
    
    src: neo.Segment, neo.ChannelIndex, or neo.Unit.
    
    index: int, str, tuple, list, range, or slice; any valid form of indexing
        including by the value of the signal's "name " attribute.
    
    ctype: type object; the type of signal to index; valid signal types are 
        neo.AnalogSignal, neo.IrregularlySampledSignal, 
        neo.Event, neo.Epoch, neo.SpikeTrain, neo.ImageSequence, neo.Unit,
        datatypes.DataSignal and datatypes.IrregularlySampledDataSignal
        
        Defaults is neo.AnalogSignal.
        
        NOTE: 
        ChannelIndex objects contains analog & irregularly sampled signals and units.
        
        Segment objects contain analog & irregularly sampled signals, events,
            epochs, spike trains, channel indexes, and image sequences.
            
        Unit objects contain only spike trains.
        
    Returns:
    --------
    a range or list of integer indices
    
    """
    major, minor, dot = get_neo_version()
    
    data_len = None
    
    if not isinstance(src, (neo.Segment, neo.ChannelIndex, neo.Unit)):
        raise TypeError("Expecting a neo.Segment or neo.ChannelIndex; got %s instead" % type(src).__name__)
    
    #### BEGIN figure out what signal collection we're after'
    if ctype in (neo.AnalogSignal, DataSignal):
        if not isinstance(src, (neo.Segment, neo.ChannelIndex)):
            raise TypeError("%s does not contain %s" % (type(src).__name__, ctype.__name__))
        
        signal_collection = src.analogsignals
        
    elif ctype in (neo.IrregularlySampledSignal, IrregularlySampledDataSignal):
        if not isinstance(src, (neo.Segment, neo.ChannelIndex)):
            raise TypeError("%s does not contain %s" % (type(src).__name__, ctype.__name__))
        
        signal_collection = src.irregularlysampledsignals
        
    elif ctype is neo.SpikeTrain:
        if not isinstance(src, (neo.Segment, neo.Unit)):
            raise TypeError("%s does not contain %s" % (type(src).__name__, ctype.__name__))
        
        signal_collection = src.spiketrains
        
    elif ctype is neo.Event:
        if not isinstance(src, neo.Segment):
            raise TypeError("%s does not contain %s" % (type(src).__name__, ctype.__name__))
            
        signal_collection = src.events
        
    elif ctype is neo.Epoch:
        if not isinstance(src, neo.Segment):
            raise TypeError("%s does not contain %s" % (type(src).__name__, ctype.__name__))
            
        signal_collection = src.epochs
        
    elif any([major >= 0, minor >= 8]) and ctype is neo.core.ImageSequence:
        if not isinstance(src, neo.Segment):
            raise TypeError("%s does not contain %s" % (type(src).__name__, ctype.__name__))
            
        # ImageSequence: either a 3D numpy array [frame][row][column] OR
        # a sequence (list) of 2D numpy arrays [row][column]
        signal_collection = src.imagesequences
        
        if not all([(hasattr(i, "image_data") and hasattr(i, "name")) for i in signal_collection]):
            raise TypeError("Inconsistent collection of image sequences")
        
        if len(signal_collection) == 1:
            img = signal_collection[0].image_data
            
            if img.ndim == 3:
                data_len = img.shape[0]
                
            else:
                raise TypeError("Ambiguous image sequence data type")
            
        elif len(signal_collection) > 1:
            if any([i.image_data.ndim != 2 for i in signal_collection]):
                raise TypeError("Ambiguous image sequence data type")
            
            data_len = len(signal_collection)
            
    elif ctype is neo.Unit:
        if not isinstance(src, neo.ChannelIndex):
            raise TypeError("%s does not contain %s" % (type(src).__name__, ctype.__name__))
        
        signal_collection = src.units
        
    else:
        raise TypeError("Cannot handle %s" % ctype.__name__)
    
    #### END figure out what signal collection we're after'

    if signal_collection is None or len(signal_collection) == 0:
        return range(0)
    
    if data_len is None:
        data_len = len(signal_collection)
        
    #print("data_len", data_len)
    
    if isinstance(index, (int, range, slice, np.ndarray, type(None))):
        return normalized_index(data_len, index)    
        
    elif isinstance(index, str):
        if silent:
            return utilities.silentindex([i.name for i in signal_collection], index)
        
        return [i.name for i in signal_collection].index(index)
    
    elif isinstance(index, (tuple, list)):
        indices = list()
        
        for ndx in index:
            if isinstance(ndx, int):
                indices.append(normalized_index(data_len, ndx))
                
            elif isinstance(ndx, str):
                if silent:
                    indices.append(utilities.silentindex([i.name for i in signal_collection], ndx))
                    
                else:
                    indices.append([i.name for i in signal_collection].index(ndx) )
                    
            else:
                raise TypeError("Invalid index element type %s" % type(ndx).__name__)
                
        return indices
                
    else:
        raise TypeError("Invalid indexing: %s" % index)
    
def get_segments_in_channel_index(channelIndex:neo.ChannelIndex) -> tuple:
    """Query the segments linked to the channel index.
    
    Parameters:
    ----------
    channelIndex: neo.ChannelIndex
    
    Returns:
    -------
    a tuple of segments that contain the signals linkes to this channel index

    NOTE: the segments may or may not belong to the same Block; this can be 
    queried by testing the identity of segment.block attribute
    
    """
    if not isinstance(channelIndex, neo.ChannelIndex):
        raise TypeError("Expecting a neo.ChannelIndex; got %s instead" % type(channelIndex).__name__)
    
    # use generator expression
    genex = (x.segment for x in channelIndex.analogsignals + channelIndex.irregularlysampledsignals if isinstance(x.segment, neo.Segment))
    
    return tuple(set(genex))
    
#@safeWrapper
def get_index_of_named_signal(src, names, stype=neo.AnalogSignal, silent=False):
    """Returns a list of indices of signals named as specified by 'names', 
    and contained in src.
    
    Positional parameters:
    ----------------------
    
    Src: a neo.Block or a neo.Segment, or a list of signal-like objects
    
    
    names: a string, or a list or tuple of strings
    
    Keyword parameters:
    -------------------
    
    stype:  a type (python class ) of signal; optional, default is neo.AnalogSignal
                other valid types are:
                DataSignal
                neo.IrregularlySampledSignal
                neo.SpikeTrain
                neo.Event
                neo.Epoch
            
            or the tuple (neo.AnalogSignal, datatypes.DataSignal)
            
            TODO: or a tuple of types as above # TODO FIXME
            
    silent: boolean (optional, default is False): when True, the function returns
        'None' for each signal name not found; otherwise it will raise an exception
    
    Returns
    ======= 
    
    Depending on what 'src' and 'names' are, returns a list of indices, or a list of
    nested lists of indices:
    
    If 'src' is a neo.Block:
    
        if 'names' is a str, the function returns a list of indices of the signal
            named as specified by 'names', with as many elements as there are segments
            in the block.
            
        if 'names' is a sequence of str, the function returns a list of nested lists
            where each inner list is as above (one inner list for each element of
            'names'); 
            
    If 'src' is a neo.Segment:
    
        if 'names' is str the function simply returns the index of the signal named 
            by 'names'
            
        if 'names' is a sequence of str, then the function returns a list of indices
            as above (one integer index for each element of 'names')
    
    NOTE:
    When a signal with the specified name is not found:
        If 'silent' is True, then the function places a None in the list of indices.
        If 'silent' is False, then the function raises an exception.
    
    ATTENTION:
    1) The function presumes that, when 'src' is a Block, it has at least one segment
    where the 'analogsignals' attribute a list) is not empty. Likewise, when 
    'src' is a Segment, its attribute 'analogsignals' (a list) is not empty.
    
    2) iT IS ASSUMED THAT ALL SIGNALS HAVE A NAME ATTRIBUTE THAT IS NOT None
    (None is technically acceptable value for the name attribute)
    
    Such signals will be skipped / missed!
    """
    from . import datatypes as dt
    
    signal_collection = "%ss" % stype.__name__.lower()
    
    if signal_collection == "datasignals":
        signal_collection = "analogsignals"
    
    if isinstance(src, neo.core.Block) or (isinstance(src, (tuple, list)) and all([isinstance(s, neo.Segment) for s in src])):
        # construct a list of indices (or list of lists of indices) of the named
        # signal(s) in each of the Block's segments
        
        if isinstance(src, neo.Block):
            data = src.segments
            
        else:
            data = src
        
        if isinstance(names, str):
            # NOTE: 2017-12-14 00:54:06
            # I don't think this is really necessary because DataSignal objects
            # can be very well contained in the analogsignals list of a segment
            # alongside neo.AnalogSignal objects ( guess ... TODO check this)
            
            if silent:
                return [utilities.silentindex([i.name for i in getattr(j, signal_collection)], names) for j in data]
            
            return [[i.name for i in getattr(j, signal_collection)].index(names) for j in data]
             
        elif isinstance(names, (list, tuple)):
            if np.all([isinstance(i,str) for i in names]):
                # proceed only if all elements in names are strings and return a 
                # list of lists, where each list element has the indices for a given
                # signal name
                if silent:
                    return [[utilities.silentindex([i.name for i in getattr(j, signal_collection)], k) for k in names] for j in data]
                
                return [[[i.name for i in getattr(j, signal_collection)].index(k) for k in names ] for j in data]
                
    elif isinstance(src, neo.core.Segment):
        objectList = getattr(src, signal_collection)
        #if stype in (neo.AnalogSignal, DataSignal) or \
            #(isinstance(stype, (tuple, list)) and all([s.__name__ in ("AnalogSignal", "DataSignal") for s in stype])):
            #objectList = src.analogsignals
            
        #elif stype is neo.IrregularlySampledSignal:
            #objectList = src.irregularlysampledsignals
            
        #elif stype is neo.SpikeTrain:
            #objectList = src.spiketrains
            
        #elif stype is neo.Event:
            #objectList = src.events
            
        #elif stype is neo.Epoch:
            #objectList = src.epochs
            
        #else:
            #raise TypeError("Invalid stype")
        
        if isinstance(names, str):
            if silent:
                return utilities.silentindex([i.name for i in objectList], names)
            
            return [i.name for i in objectList].index(names)
            
        elif isinstance(names, (list, tuple)):
            if np.all([isinstance(i,str) for i in names]):
                if silent:
                    return [utilities.silentindex([i.name for i in objectList], j) for j in names]
                
                return [[i.name for i in objectList].index(j) for j in names]
            
        else:
            raise TypeError("Invalid indexing")
        
    else:
        raise TypeError("First argument must be a neo.Block object, a list of neo.Segment objects, or a neo.Segment object; got %s instead" % type(src).__name__)

@safeWrapper
def resample_poly(sig, new_rate, p=1000, window=("kaiser", 5.0)):
    """Resamples signal using a polyphase filtering.
    
    Resampling uses polyphase filtering (scipy.signal.resample_poly) along the
    0th axis.
    
    Parameters:
    ===========
    
    sig: neo.AnalogSignal or datatypes.DataSignal
    
    new_rate: either a float scalar, or a Python Quantity 
            When a Python Quantity, it must have the same units as signal's 
            sampling RATE units.
            
            Alternatively, if it has the same units as the signal's sampling 
            PERIOD, its inverse will be taken as the new sampling RATE.
             
            NOTE: It must be strictly positive i.e. new_rate > 0
             
            When new_rate == sig.sampling_rate, the function returns a copy of sig.
             
            Otherwise, the function returns a copy of sig where all columns are resampled via
            scipy.signal.resample_poly
    
    p: int
        factor of precision (default 1000): power of 10 used to calculate up/down sampling:
        up = new_rate * p / signal_sampling_rate
        down = p
        
    window: string, tuple, or array_like, optional
        Desired window to use to design the low-pass filter, or the FIR filter 
        coefficients to employ. see scipy.signal.resample_poly() for details
    
    """
    from scipy.signal import resample_poly as resample
    
    using_rate=True
    
    if not isinstance(sig, neo.AnalogSignal):
        raise TypeError("First parameter expected to be a neo.AnalogSignal; got %s instead" % type(sig).__name__)
    
    if isinstance(new_rate, numbers.Real):
        new_rate = new_rate * sig.sampling_rate.units
        
    elif isinstance(new_rate, pq.Quantity):
        if new_rate.size > 1:
            raise TypeError("Expecting new_rate a scalar quantity; got a shaped array %d" % new_res)
        
        if new_rate.units != sig.sampling_rate.units:
            if new_rate.units == sig.sampling_period.units:
                using_rate = False
                
            else:
                raise TypeError("Second parameter should have the same units as signal's sampling rate (%s); it has %s instead" % (sig.sampling_rate.units, new_rate.units))
                
    
    if new_rate <= 0:
        raise ValueError("New sampling rate (%s) must be strictly positive !" % new_rate)
    
    p = int(p)
    
    if using_rate:
        if new_rate == sig.sampling_rate:
            return sig.copy()
        
        up = int(new_rate / sig.sampling_rate * p)
        
    else:
        if new_rate == sig.sampling_period:
            return sig.copy()
            
        up = int(sig.sampling_period / new_rate * p)
    
    if using_rate:
        ret = neo.AnalogSignal(resample(sig, up, p, window=window), 
                               units = sig.units, 
                               t_start = sig.t_start,
                               sampling_rate = new_rate)
        
    else:
        ret = neo.AnalogSignal(resample(sig, up, p, window=window), 
                               t_start = sig.t_start,
                               units = sig.units, 
                               sampling_period = new_rate) 
        
    ret.name = sig.name
    ret.description = "%s resampled %f fold on axis 0" % (sig.name, up)
    ret.annotations = sig.annotations.copy()
    
    return ret

@safeWrapper
def get_time_slice(data, t0, t1=None, window=0, \
                    segment_index=None, \
                    analogsignal_index=None, \
                    irregularsignal_index=None,\
                    spiketrain_index=None, \
                    epoch_index=None,\
                    event_index=None):
    """Returns a time slice from a neo.Block or neo.Segment object.
    
    The time slice is a Block or a Segment (depending on the type of "data"
    object) with the time slice of all signals or from selected signals.
    
    NOTE: neo.AnalogSignals.time_slice() member function fulfills the same role.
    
    Positional parameters:
    ---------------------
    
        data: a neo.Block or a neo.Segment
        
        t0: a neo.Epoch, a scalar or a python quantity in time units
        
            When 't0' is an EPoch, it already specifies both the start time and 
            the duration of the time slice.
            
            When 't0' is a scalar real or a python quantity, it only specifies 
            the start time; then, either 't1' (end time) or 'window' must be 
            also given (see below).
        
        
    Keyword parameters:
    -------------------
        t1: (optional, default = None) scalar, a python quantity in time units, 
            or None;
            
            NOTE that when 't0' is an epoch, 't1' is calculated from 't0' and 
            the value given for 't1' here is discarded:
            
                t1 = t0.times + t0.durations
                
                t0 = t0.times
            
        window (optional, default = 0): scalar, or python quantity in time units.
        
            NOTE: window is MANDATORY when 't1' is None and 't0' is NOT an epoch
            (see NOTE below)
            
        segment_index (optional, default = None): scalar index or sequence of indices
            for the segments in the data, from which the time slice is to be extracted.
            
            Only used when data is a neo.Block.
            
            When None, the result will contain the time slices taken from all segments.
            
        analogsignal_index (optional, default = None): index or sequence of indices
            for the AnalogSignals (regularly sampled) in each segment. 
            When None, the function will return time slices from all signals found.
            
            The index can be specified as an integer, or as a string containing
            the signal name.
            
        irregularsignal_index (optional, default = None): 
            as for analogsignal_index, this is an index or sequence of indices
            for the IrregularlySampledSignals in each segment. When None, the 
            function will return time slices from all signals found.
            
            The index can be specified as an integer, or as a string containing
            the signal name.
            
        spiketrain_index (optional, default is None): index of sequence of indices
            of spiketrains; same semantics as for analogsignal_index
            
        epoch_index (optional, default is None): index of sequence of indices
            of epochs; same semantics as for analogsignal_index
            
        event_index (optional, default is None): index of sequence of indices
            of event ARRAYS; same semantics as for analogsignal_index
            
            NOTE: each segment may contain several neo.Event arrays; this index
            specifies the Event ARRAY, not the index of individual events WITHIN
            an Event array! Similar to the other cases above, neo.Event arrays
            can also be selected by their "name" attribute (which is the name of 
            the entire Event array, and NOT the name of individual events in the
            array).
        
    NOTE: 
        When 't0' is a scalar, the time slice is specified as 't0', 't1', or as
        't0', 'window'.
        
        In the latter case, the window gives the duration CENTERED AROUND t0 and 
            the time slice is calculated as:
            
            t1 = t0 + window/2
            
            t0 = t0 - window/2.
    
    NOTE: 2019-11-25 20:38:44
    
    From neo version 0.8.0 segments also support time_slicing
    
    """
    from . import datatypes as dt
    
    # get_time_slice (1) check for t1 first
    
    if isinstance(t1, pq.Quantity):
        _d_ = [k for k in t0.dimensionality.keys()][0]
        if not isinstance(_d_, pq.time.UnitTime):
            raise ValueError("The t1 quantity must be in time unit; got %s instead" % type(_d_).__name__)
        
    elif isinstance(t1, numbers.Real):
        t1 =t1 * pq.s
        
    elif t1 is not None:
        raise TypeError("When given, t1 must be a real scalar, time python quantity, or None; got %s instead" % type(t1).__name__)
        
        
    # get_time_slice (2) check for t0, override t1 if t0 is an epoch
    
    if isinstance(t0, neo.Epoch):
        if t0.size != 1:
            raise ValueError("When given as a neo Epoch, t0 must have size 1; instead it has %d" % (t0.size))
        
        t1 = t0.times + t0.durations
        t0 = t0.times
    
    elif isinstance(t0, pq.Quantity):
        _d_ = [k for k in t0.dimensionality.keys()][0]
        
        if not isinstance(_d_, pq.time.UnitTime):
            raise ValueError("The t0 quantity must be in time unit; got %s instead" % type(_d_).__name__)
        
    elif isinstance(t0, numbers.Real):
        t0 = t0 * pq.s
        
    else:
        raise TypeError("t0 must be a neo.Epoch, real scalar or python quantity in time units; got %s instead" % type(t0).__name__)


    # get_time_slice (3) if t1 is None, check for window and calculate t1
    
    if t1 is None:
        if isinstance(window, pq.Quantity):
            _d_ = [k for k in window.dimensionality.keys()][0]
            
            if not isinstance(_d_, pq.time.UnitTime):
                raise ValueError("The window quantity must be in time units; got %d instead" % type(_d__).__name__)
            
        elif isinstance(window, numbers.Real):
            window = window * pq.s
            
        elif window is None:
            raise TypeError("When t1 is missing, window must be given")
            
        else:
            raise TypeError("When given, window must be a time python quantity or a real scalar; got %s instead" % type(window).__name__)
    
        t1 = t0 + window/2
        t0 = t0 - window/2
        
    # get_time_slice (4) now picks up the time slice and construct the return value: 
    # a neo.Block, if data is a neo.Block, or a neo.Segment, if data is a neo.Segment, 
    # or raise exception if data is neither
    
    if isinstance(data, neo.Block): # yes, this function calls itself = recursion
        ret = neo.core.Block()
        if segment_index is None: # get time slice from ALL segments
            ret.segments = [get_time_slice(seg, t0, t1, 0, analogsignal_index, irregularsignal_index, spiketrain_index, event_index, epoch_index) for seg in data.segments]
            
        elif isinstance(segment_index, int): # or from just the selected segments
            ret.segments = [get_time_slice(data.segments[segment_index], t0, t1, analogsignal_index, irregularsignal_index, spiketrain_index, event_index, epoch_index)]
            
        else:
            raise TypeError("Unexpected segment indexing type")
        
    elif isinstance(data, neo.Segment): 
        ret = neo.Segment()
        
        # get the time slice from a single segment;
        # 'time_slice' method will check that t0 and t1 fall within each signal 
        # time base
        
        # 1) AnalogSignals
        
        if len(data.analogsignals) > 0:
            if analogsignal_index is None: # from ALl signals
                ret.analogsignals = [a.time_slice(t0,t1) for a in data.analogsignals]
                
            elif isinstance(analogsignal_index, (str, int)):
                if isinstance(analogsignal_index,str):
                    analogsignal_index= get_index_of_named_signal(data, analogsignal_index)
                
                ret.analogsignals = [data.analogsignals[analogsignal_index].time_slice(t0,t1)]
                
            elif isinstance(analogsignal_index, (list, tuple)):
                if all([isinstance(s, str) for s in analogsignal_index]):
                    analogsignal_index = [get_index_of_named_signal(data, s) for s in analogsignal_index]
                
                ret.analogsignals = [data.analogsignals[k].time_slice(t0,t1) for k in analogsignal_index]
                
            else:
                raise TypeError("Unexpected analogsignal_index type")
        
        # 2) IrregularlySampledSignals
        
        if len(data.irregularlysampledsignals) > 0:
            if irregularsignal_index is None: # from ALl signals
                ret.irregularlysampledsignals = [a.time_slice(t0,t1) for a in data.irregularlysampledsignals]
                
            elif isinstance(irregularsignal_index, (str, int)):
                if isinstance(irregularsignal_index,str):
                    irregularsignal_index = get_index_of_named_signal(data, irregularsignal_index, stype=neo.IrregularlySampledSignal)
                
                ret.irregularlysampledsignals = [data.irregularlysampledsignals[irregularsignal_index].time_slice(t0,t1)]
                
            elif isinstance(irregularsignal_index, (list, tuple)):
                if all([isinstance(s, str) for s in irregularsignal_index]):
                    irregularsignal_index = [get_index_of_named_signal(data, s, stype = neo.IrregularlySampledSignal) for s in irregularsignal_index]
                
                ret.irregularlysampledsignals = [data.irregularlysampledsignals[k].time_slice(t0,t1) for k in irregularsignal_index]
                
            else:
                raise TypeError("Unexpected irregularsignal_index index type")
            
            
        # 3) Spike trains
        
        if len(data.spiketrains) > 0:
            if spiketrain_index is None: # ALL spike trains
                ret.spiketrains = [a.time_slice(t0, t1) for a in data.spiketrains]
                
            elif isinstance(spiketrain_index, (str, int)):
                if isinstance(spiketrain_index, str):
                    spiketrain_index = get_index_of_named_signal(data, spiketrain_index, stype=neo.SpikeTrain)
                    
                ret.spiketrains = [data.spiketrains[spiketrain_index].time_slice(t0,t1)]
                
            elif isinstance(spiketrain_index, (list, tuple)):
                if all([isinstance(s, str) for s in spiketrain_index]):
                    spiketrain_index = [get_index_of_named_signal(data, s, stype=neo.SpikeTrain) for s in spiketrain_index]
                    
                ret.spiketrains = [data.spiketrains[k].time_slice(t0,t1) for k in spiketrain_index]
                
            else:
                raise TypeError("Unexpected spiketrain index type")
            
                
        # 4) Event
        
        if len(data.events) > 0:
            if event_index is None:
                ret.events = [e.time_slice(t0, t1) for e in data.events]
                
            elif isinstance(event_index, (str, int)):
                if isinstance(event_index, str):
                    event_index = get_index_of_named_signal(data, event_index, stype=neo.Event)
                    
                ret.event = [data.events[event_index].time_slice(t0,t1)]
                
            elif isinstance(event_index, (tuple, list)):
                if all([isinstance(s, str) for s in event_index]):
                    event_index = [get_index_of_named_signal(data, s, stype=neo.Event) for s in event_index]
                    
                ret.events = [data.events[k].time_slice(t0, t1) for k in event_index]
                
            else:
                raise TypeError("Unexpected event index type")
            
                
        # 5) Epoch
        
        if len(data.epochs) > 0:
            if epoch_index is None:
                ret.epochs = [e.time_slice(t0, t1) for e in data.epochs]
                
            elif isinstance(epoch_index, (str, int)):
                if isinstance(epoch_index, str):
                    event_index = get_index_of_named_signal(data, epoch_index, stype=neo.Event)
                    
                ret.event = [data.epochs[epoch_index].time_slice(t0,t1)]
                
            elif isinstance(epoch_index, (tuple, list)):
                if all([isinstance(s, str) for s in epoch_index]):
                    epoch_index = [get_index_of_named_signal(data, s, stype=neo.Event) for s in epoch_index]
                    
                ret.epochs = [data.epochs[k].time_slice(t0, t1) for k in epoch_index]
                
            else:
                raise TypeError("Unexpected epoch index type")
        
    elif isinstance(data, (neo.AnalogSignal, DataSignal)):
        return data.time_slice(t0,t1)
    
    else:
            
        raise TypeError("Expecting data to be a neo.Block or neo.Segment; got %s instead" % (type(data).__name__))
        
    
    # set up attributes below, that are common to neo.Block and neo.Segment
    
    if data.name is not None:
        ret.name = data.name + " Time slice %g - %g" % (t0,t1)
        
    else:
        ret.name = "Time slice %g - %g" % (t0,t1)
        
    ret.rec_datetime = datetime.datetime.now()
        
    return ret

@safeWrapper
def concatenate_signals(*args, axis=1, ignore_domain = False, ignore_units=False):
    """Concatenates regularly sampled signals.
    
    Var-positional parameters:
    -------------------------
    
    a sequence of signals, or a comma-separated list of signals.
    
    All signals must have the same shape except for the dimension of the 
    concatenating axis.
    
    Named parameters:
    ----------------
    axis: int; default is 1
        The concatenation axis
        
    ignore_domain: bool, default is False
        When False (default) all signals must have identical time domains 
        (t_start, units and sampling_rate)
        
        When True, the data will be concatenated and a new time domain will be
        generated with the units of the first signal, t_start = 0 (domain units) 
        with sampling rate set to that of the first signal in the sequence.
        
    ignore_units = bool, default False
        When True, will skip checks for units compatibilty among signals.
    
    """
    from . import datatypes as dt
    
    if len(args) == 1:
        if isinstance(args[0], (tuple, list)):
            signals = args[0]
            
        else:
            raise TypeError("Expecting a sequence; got %s instead" % type(args[0]).__name__)
    else:
        signals = args
        
    # NOTE 2019-09-11 12:31:00:
    # a sequence of signals
    # break-up the conditions so that we enforce al element to be of the SAME type
    # instead of either one of the two types -- i.e. do NOT accept sequences of
    # mixed types !!!
    if all([isinstance(sig, neo.AnalogSignal) for sig in signals]) or \
        all([isinstance(sig, DataSignal) for sig in signals]):
        sig_shapes = [[s for s in sig.shape] for sig in signals]
        
        for s in sig_shapes:
            s[axis] = None
            
        if not all(sig_shapes[0] == s for s in sig_shapes):
            raise TypeError("signals do not have identical shapes on non-concatenating axes")
        
        # NOTE: axis 0 is the domain axis!
        if axis > 0 or axis == -1:
            if not ignore_domain:
                if not all([sig.t_start == signals[0].t_start for sig in signals[1:]]):
                    raise ValueError("To concatenate signals on 2nd dimension they must have identical domains ")
                
        # this is needed for any concatenation axis!
        if not ignore_domain:
            if not all([np.isclose(sig.sampling_rate.magnitude, signals[0].sampling_rate.magnitude) for sig in signals[1:]]):
                raise ValueError("To concatenate signals on the 2nd dimension they must all have the same sampling rate")
            
            if not all([sig.times.units] == signals[0].times.units for sig in signals[1:]):
                raise ValueError("To concatenate signals on 2nd dimension they must have identical domain units ")
            
        if not ignore_units:
            if not all([dt.units_convertible(sig.units, signals[0].units) for sig in signals[1:]]):
                warnings.warn("There are signals with non-convertible units; this may become an error in the future")
            
        if ignore_domain:
            t_start = 0 * signals[0].times.units
        
        else:
            t_start = signals[0].t_start
            
        sig_names = ["signal_%d" % k if sig.name is None else sig.name for (k, sig) in enumerate(signals)]
            
        concat_sig_names = ", ".join(sig_names)
        
        sampling_rate = signals[0].sampling_rate
        
        units_0 = signals[0].units
        
        if ignore_units:
            signal_data = [sig.magnitude for sig in signals]
            
        else:
            signal_data = [sig.rescale(units_0).magnitude for sig in signals]
        
        result = neo.AnalogSignal(np.concatenate(signal_data, axis=axis),
                                    units = units_0,
                                    t_start = t_start,
                                    sampling_rate = sampling_rate,
                                    name = "Concatenated signal",
                                    description = "Concatenated %s" % concat_sig_names)
                                    
        return result
           
    else:
        raise TypeError("Expecting a sequence of neo.AnalogSignal or datatypes.DataSignal objects")
                

@safeWrapper
def concatenate_blocks(*args, **kwargs):
    """Concatenates the segments in *args into a new Block.
    
    Copies of neo.Segment objects in the source data (*args) are appended in the
    order they are encountered.
    
    Optionally a subset of the signals contained in the source data are retained
    in the concatenated Block.
    
    Events, spike trains and epochs contained in the selected segments will be
    copied to the concatenated Block.
    
    Var-positional parameters:
    --------------------------
    args : a comma-separated list of neo.core.Block or neo.core.Segment objects
    
    Var-keyword parameters:
    -----------------------
    
    name            see neo.Block docstring
    description     see neo.Block docstring
    rec_datetime    see neo.Block docstring
    file_origin     see neo.Block docstring
    file_datetime   see neo.Block docstring
    annotation      see neo.Block docstring
    
    segment:    int or None; 
                when None, all segments in each block will be used
                when int then only segments with given index will be used
                (i.e. only one segment from each block will be retained in 
                the concatenated data)
                    
    analog:     int, str, range, slice, typing.Sequence
                Indexing of analog signal(s) into each of the segments, that
                will be retained in the concatenated data. These include
                neo.AnalogSignal and datatypes.DataSignal
                
                This index can be (see neo_index_lookup):
                int, str (signal name), sequence of int or str, a range, a
                slice, or a numpy array of int or booleans.
                    
    irregular:  as analog, for irregularly sampled signals. These 
                include neo.IrregularlySampledSignal and 
                datatypes.IrregularlySampledDataSignal
    
    image:      as analog, for neo.ImageSequence objects (for neo version
                from 0.8.0 onwards)
                
                
    channel:    int, index  of the neo.ChannelIndex
                    
                    
    Returns:
    -------
    a new neo.Block object
    
    NOTE: this is different from Block.merge() and Segment.merge() which basically
    append analog signals to same segments (thus requiring identical time bases)
    
    Example:
    
    block = concatenate_blocks(getvars("data_name_prefix*"), segment_index=0)
    
    will concatenate the first segment (segment_index = 0) from all neo.Block 
    variables having names beginning with 'data_name_prefix' in the user 
    workspace.

    
    """
    major, minor, dot = get_neo_version()
    
    neo_ge_8 = any([major >=0, minor >= 8])
    
    #if not isinstance(arg0, (neo.core.Block, neo.core.Segment)):
        #raise TypeError("First argument must be a Block or a Segment")
        
    if len(args) == 0:
        return None
    
    if len(args) == 1:
        if isinstance(args[0], str):
            try:
                args =  workspacefunctions.getvars(args[0], sort=True, sortkey=lambda x: x.rec_datetime)
                
            except Exception as e:
                print("String argument did not resolve to a list of neo.Block objects")
                traceback.print_exc()
                return
        else:
            args = args[0] # unpack the tuple
    
    name = kwargs.get("name", "Concatenated block")
    description = kwargs.get("description", "Concatenated block")
    file_origin = kwargs.get("file_origin", "")
    file_datetime = kwargs.get("file_datetime", None)
    rec_datetime = kwargs.get("datetime", datetime.datetime.now())
    annotations = kwargs.get("annotations", dict())
    
    segment_index = kwargs.get("segment", None)
    analog_index = kwargs.get("analog", None)
    irregular_index = kwargs.get("irregular", None)
    image_index = kwargs.get("image", None)
    channel_index = kwargs.get("channel", None)
    
     # the returned data:
    ret = neo.core.Block(name=name, description=description, file_origin=file_origin,
                         file_datetime=file_datetime, rec_datetime=rec_datetime, 
                         **annotations)
    
    if isinstance(args, neo.core.Block):
        if segment_index is None:
            for (l,seg) in enumerate(args.segments):
                if analog_index is None:
                    #seg_ = copy(seg)
                    seg_ = neo_copy(seg)
                    seg_.name = "%s_%s" % (args.name, seg.name)
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    ret.segments.append(seg_)
                    
                else:
                    # NOTE: 2020-03-13 08:48:10 
                    # we do NOT copy; instead we create a new segment, that we
                    # then populate with selected signals
                    seg_ = neo.Segment(rec_datetime = seg.rec_datetime, name="%s_%s" % (args.name, seg.name))
                    seg_.merge_annotations(seg)
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    
                    if isinstance(analog_index, str):
                        seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                        
                    elif isinstance(analog_index, int):
                        seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                        
                    elif isinstance(analog_index, (tuple, list)):
                        for sigNdx in analog_index:
                            if isinstance(sigNdx, str):
                                sigNdx = get_index_of_named_signal(seg, sigNdx)
                                
                            elif not isinstance(sigNdx, int):
                                raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                
                            seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                            
                    else:
                        raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                        
                    ret.segments.append(seg_)
        else:
            if segment_index < len(args.segments):
                # NOTE: 2020-03-13 08:51:32
                # get a reference to the segment with index "index"
                # then either:
                # a) copy it, if all signals are to be retained
                # b) create a new segment populated only with the selected signals
                seg = args.segments[segment_index] # a reference
                
                if analog_index is None:
                    seg_ = copy(seg)
                    seg_.name = "%s_%s" % (args.name, seg.name)
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    ret.segments.append(seg_) # copy of original seg
                    
                else:
                    seg_ = neo.Segment(rec_datetime = seg.rec_datetime, name="%s_%s" % (args.name, seg.name)) # new seg
                    seg_.merge_annotations(seg)
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    
                    analog_index = neo_index_lookup(seg, analog_index, )
                    
                    if isinstance(analog_index, str):
                        seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                        
                    elif isinstance(analog_index, int):
                        seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                        
                    elif isinstance(analog_index, (tuple, list)):
                        for sigNdx in analog_index:
                            if isinstance(sigNdx, str):
                                sigNdx = get_index_of_named_signal(seg, sigNdx)
                                
                            elif not isinstance(sigNdx, int):
                                raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                
                            seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                            
                    else:
                        raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                        
                    ret.segments.append(seg_)
        
    elif isinstance(args,(tuple, list)):
        for (k,arg) in enumerate(args):
            if isinstance(arg, neo.core.Block):
                if segment_index is None:
                    for (l,seg) in enumerate(arg.segments):
                        if analog_index is None:
                            ret.segments.append(seg)
                            ret.segments[-1].annotate(origin=arg.file_origin, original_segment=segment_index)
                            
                        else:
                            seg_ = neo.Segment(rec_datetime = seg.rec_datetime)
                            seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                            
                            if isinstance(analog_index, str):
                                seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                                
                            elif isinstance(analog_index, int):
                                seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                                
                            elif isinstance(analog_index, (tuple, list)):
                                for sigNdx in analog_index:
                                    if isinstance(sigNdx, str):
                                        sigNdx = get_index_of_named_signal(seg, sigNdx)
                                        
                                    elif not isinstance(sigNdx, int):
                                        raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                        
                                    seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                                    
                            else:
                                raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                                
                            ret.segments.append(seg_)
        
                            
                else:
                    if segment_index < len(arg.segments):
                        if analog_index is None:
                            ret.segments.append(arg.segments[segment_index])
                            ret.segments[-1].annotate(origin=arg.file_origin, original_segment=segment_index)
                            
                        else:
                            seg = arg.segments[segment_index]
                            
                            seg_ = neo.Segment(rec_datetime = seg.rec_datetime)
                            seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                            
                            if isinstance(analog_index, str):
                                seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                                
                            elif isinstance(analog_index, int):
                                seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                                
                            elif isinstance(analog_index, (tuple, list)):
                                for sigNdx in analog_index:
                                    if isinstance(sigNdx, str):
                                        sigNdx = get_index_of_named_signal(seg, sigNdx)
                                        
                                    elif not isinstance(sigNdx, int):
                                        raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                        
                                    seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                                    
                            else:
                                raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                                
                            ret.segments.append(seg_)
        
            elif isinstance(arg, neo.core.Segment):
                if analog_index is None:
                    ret.segments.append(arg)
                    
                else:
                    seg_ = neo.Segment(rec_datetime = arg.rec_datetime)
                    seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                    
                    if isinstance(analog_index, str):
                        seg_.analogsignals.append(arg.analogsignals[get_index_of_named_signal(arg, analog_index)].copy())
                        
                    elif isinstance(analog_index, int):
                        seg_.analogsignals.append(arg.analogsignals[analog_index].copy())
                        
                    elif isinstance(analog_index, (tuple, list)):
                        for sigNdx in analog_index:
                            if isinstance(sigNdx, str):
                                sigNdx = get_index_of_named_signal(arg, sigNdx)
                                
                            elif not isinstance(sigNdx, int):
                                raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                
                            seg_.analogsignals.append(arg.analogsignals[sigNdx].copy())
                            
                    else:
                        raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                        
                    ret.segments.append(seg_)
        
                    
    else:
        raise TypeError("Expecting a neo.Block or a sequence of neo.Block objects, got %s instead" % type(args).__name__)
            
    return ret

@safeWrapper
def concatenate_blocks2(*args, **kwargs):
    """Concatenates the segments in *args into a new Block.
    
    Copies of neo.Segment objects in the source data (*args) are appended in the
    order they are encountered.
    
    Optionally a subset of the signals contained in the source data are retained
    in the concatenated Block.
    
    Events, spike trains and epochs contained in the selected segments will be
    copied to the concatenated Block.
    
    Var-positional parameters:
    --------------------------
    args : a comma-separated list of neo.core.Block or neo.core.Segment objects
    
    Var-keyword parameters:
    -----------------------
    
    name            see neo.Block docstring
    description     see neo.Block docstring
    rec_datetime    see neo.Block docstring
    file_origin     see neo.Block docstring
    file_datetime   see neo.Block docstring
    annotation      see neo.Block docstring
    
    segment:    int or None; 
                when None, all segments in each block will be used
                when int then only segments with given index will be used
                (i.e. only one segment from each block will be retained in 
                the concatenated data)
                    
    analog:     int, str, range, slice, typing.Sequence
                Indexing of analog signal(s) into each of the segments, that
                will be retained in the concatenated data. These include
                neo.AnalogSignal and datatypes.DataSignal
                
                This index can be (see neo_index_lookup):
                int, str (signal name), sequence of int or str, a range, a
                slice, or a numpy array of int or booleans.
                    
    irregular:  as analog, for irregularly sampled signals. These 
                include neo.IrregularlySampledSignal and 
                datatypes.IrregularlySampledDataSignal
    
    image:      as analog, for neo.ImageSequence objects (for neo version
                from 0.8.0 onwards)
                
                
    channel:    int, index  of the neo.ChannelIndex
                    
                    
    Returns:
    -------
    a new neo.Block object
    
    NOTE: this is different from Block.merge() and Segment.merge() which basically
    append analog signals to same segments (thus requiring identical time bases)
    
    Example:
    
    block = concatenate_blocks(getvars("data_name_prefix*"), segment_index=0)
    
    will concatenate the first segment (segment_index = 0) from all neo.Block 
    variables having names beginning with 'data_name_prefix' in the user 
    workspace.

    
    """
    major, minor, dot = get_neo_version()
    
    neo_ge_8 = any([major >=0, minor >= 8])
    
    #if not isinstance(arg0, (neo.core.Block, neo.core.Segment)):
        #raise TypeError("First argument must be a Block or a Segment")
        
    if len(args) == 0:
        return None
    
    if len(args) == 1:
        if isinstance(args[0], str):
            try:
                args =  workspacefunctions.getvars(args[0], sort=True, sortkey=lambda x: x.rec_datetime)
                
            except Exception as e:
                print("String argument did not resolve to a list of neo.Block objects")
                traceback.print_exc()
                return
        else:
            args = args[0] # unpack the tuple
    
    name = kwargs.get("name", "Concatenated block")
    description = kwargs.get("description", "Concatenated block")
    file_origin = kwargs.get("file_origin", "")
    file_datetime = kwargs.get("file_datetime", None)
    rec_datetime = kwargs.get("datetime", datetime.datetime.now())
    annotations = kwargs.get("annotations", dict())
    
    segment_index = kwargs.get("segment", None)
    analog_index = kwargs.get("analog", None)
    irregular_index = kwargs.get("irregular", None)
    image_index = kwargs.get("image", None)
    channel_index = kwargs.get("channel", None)
    
     # the returned data:
    ret = neo.core.Block(name=name, description=description, file_origin=file_origin,
                         file_datetime=file_datetime, rec_datetime=rec_datetime, 
                         **annotations)
    
    #print(len(args))
    
    if isinstance(args, neo.core.Block):
        if segment_index is None:
            for (l,seg) in enumerate(args.segments):
                if analog_index is None:
                    #seg_ = copy(seg)
                    seg_ = neo_copy(seg)
                    seg_.name = "%s_%s" % (args.name, seg.name)
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    ret.segments.append(seg_)
                    
                else:
                    # NOTE: 2020-03-13 08:48:10 
                    # we do NOT copy; instead we create a new segment, that we
                    # then populate with selected signals
                    seg_ = neo.Segment(rec_datetime = seg.rec_datetime, name="%s_%s" % (args.name, seg.name))
                    
                    seg_.merge_annotations(seg)
                    
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    
                    signal_index = neo_index_lookup(seg, analog_index)
                    
                    sig_ = seg.analogsignals[signal_index]
                    
                    #if isinstance(analog_index, str):
                        #seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                        
                    #elif isinstance(analog_index, int):
                        #seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                        
                    #elif isinstance(analog_index, (tuple, list)):
                        #for sigNdx in analog_index:
                            #if isinstance(sigNdx, str):
                                #sigNdx = get_index_of_named_signal(seg, sigNdx)
                                
                            #elif not isinstance(sigNdx, int):
                                #raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                
                            #seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                            
                    #else:
                        #raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                        
                    ret.segments.append(seg_)
        else:
            if segment_index < len(args.segments):
                # NOTE: 2020-03-13 08:51:32
                # get a reference to the segment with index "index"
                # then either:
                # a) copy it, if all signals are to be retained
                # b) create a new segment populated only with the selected signals
                seg = args.segments[segment_index] # a reference
                
                if analog_index is None:
                    seg_ = copy(seg)
                    seg_.name = "%s_%s" % (args.name, seg.name)
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    ret.segments.append(seg_) # copy of original seg
                    
                else:
                    seg_ = neo.Segment(rec_datetime = seg.rec_datetime, name="%s_%s" % (args.name, seg.name)) # new seg
                    seg_.merge_annotations(seg)
                    seg_.annotate(origin=args.file_origin, original_segment=segment_index)
                    
                    analog_index = neo_index_lookup(seg, analog_index, )
                    
                    if isinstance(analog_index, str):
                        seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                        
                    elif isinstance(analog_index, int):
                        seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                        
                    elif isinstance(analog_index, (tuple, list)):
                        for sigNdx in analog_index:
                            if isinstance(sigNdx, str):
                                sigNdx = get_index_of_named_signal(seg, sigNdx)
                                
                            elif not isinstance(sigNdx, int):
                                raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                
                            seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                            
                    else:
                        raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                        
                    ret.segments.append(seg_)
        
    elif isinstance(args,(tuple, list)):
        for (k,arg) in enumerate(args):
            if isinstance(arg, neo.core.Block):
                if segment_index is None:
                    for (l,seg) in enumerate(arg.segments):
                        seg_ = neo_copy(seg)
                        if analog_index is None:
                            seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                            ret.segments.append(seg_)
                            
                        else:
                            seg_ = neo.Segment(rec_datetime = seg.rec_datetime)
                            seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                            
                            if isinstance(analog_index, str):
                                seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                                
                            elif isinstance(analog_index, int):
                                seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                                
                            elif isinstance(analog_index, (tuple, list)):
                                for sigNdx in analog_index:
                                    if isinstance(sigNdx, str):
                                        sigNdx = get_index_of_named_signal(seg, sigNdx)
                                        
                                    elif not isinstance(sigNdx, int):
                                        raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                        
                                    seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                                    
                            else:
                                raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                                
                            ret.segments.append(seg_)
        
                            
                else:
                    if segment_index < len(arg.segments):
                        if analog_index is None:
                            seg_ = neo_copy(arg.segments[segment_index])
                            seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                            ret.segments.append(seg_)
                            #ret.segments.append(arg.segments[segment_index])
                            #ret.segments[-1].annotate(origin=arg.file_origin, original_segment=segment_index)
                            
                        else:
                            seg = arg.segments[segment_index]
                            
                            seg_ = neo.Segment(rec_datetime = seg.rec_datetime)
                            seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                            
                            if isinstance(analog_index, str):
                                seg_.analogsignals.append(seg.analogsignals[get_index_of_named_signal(seg, analog_index)].copy())
                                
                            elif isinstance(analog_index, int):
                                seg_.analogsignals.append(seg.analogsignals[analog_index].copy())
                                
                            elif isinstance(analog_index, (tuple, list)):
                                for sigNdx in analog_index:
                                    if isinstance(sigNdx, str):
                                        sigNdx = get_index_of_named_signal(seg, sigNdx)
                                        
                                    elif not isinstance(sigNdx, int):
                                        raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                        
                                    seg_.analogsignals.append(seg.analogsignals[sigNdx].copy())
                                    
                            else:
                                raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                                
                            ret.segments.append(seg_)
        
            elif isinstance(arg, neo.core.Segment):
                if analog_index is None:
                    ret.segments.append(arg)
                    
                else:
                    seg_ = neo.Segment(rec_datetime = arg.rec_datetime)
                    seg_.annotate(origin=arg.file_origin, original_segment=segment_index)
                    
                    if isinstance(analog_index, str):
                        seg_.analogsignals.append(arg.analogsignals[get_index_of_named_signal(arg, analog_index)].copy())
                        
                    elif isinstance(analog_index, int):
                        seg_.analogsignals.append(arg.analogsignals[analog_index].copy())
                        
                    elif isinstance(analog_index, (tuple, list)):
                        for sigNdx in analog_index:
                            if isinstance(sigNdx, str):
                                sigNdx = get_index_of_named_signal(arg, sigNdx)
                                
                            elif not isinstance(sigNdx, int):
                                raise TypeError("Signal index expected to be a str or an int; got %s instead" % type(sigNdx).__name__)
                                
                            seg_.analogsignals.append(arg.analogsignals[sigNdx].copy())
                            
                    else:
                        raise TypeError("analog_index parameter expected to be None, a str, int or a sequence of these types; got %s instead" % type(analog_index).__name__)
                        
                    ret.segments.append(seg_)
        
                    
    else:
        raise TypeError("Expecting a neo.Block or a sequence of neo.Block objects, got %s instead" % type(args).__name__)
            
    return ret

#@safeWrapper
def average_blocks(*args, **kwargs):
    """Generates a block containing a list of averaged AnalogSignal data from the *args.
    
    Parameters:
    -----------
    
    args: a comma-separated list of neo.Block objects
    
    kwargs: keyword/value pairs:
    
        count               how many analogsignals into one average
        
        every               how many signals to skip between averages
        
        segment_index       which segment index into the block argument(s) to consider
        
        analog_index        index of signal into each of the segments to be used;
                            can also be a signal name
        
        name                see neo.Block docstring
        
        annotation          see neo.Block docstring
        
        rec_datetime        see neo.Block docstring
        
        file_origin         see neo.Block docstring
        
        file_datetime       see neo.Block docstring
        
    
    Returns:
    --------
    
    A new Block containing AnalogSignal data that are averages of the AnalogSignal 
    object in the *args across the segments, taken n segments at a time, every m segments.
    
    Depending on the values of 'n' and 'm', the result may contain several segments,
    each containing AnalogSignals averaged from the data.
    
    NOTE:
    
    By contrast to average_blocks_by_segments, this function can result in the 
    average of ALL segments in a block (or sequence of blocks) in  particular
    when "count" and "every" are not set (see below).
    
    The function only takes AnalogSignal data, and discards IrregularlySampledSignal
    SpikeTrain, Event and Epoch data that may be present in the blocks specified
    by *args.
    
    This is because, by definition, only AnalogSignal data may be enforced to be 
    shape-compatible for averaging, and this is what usually one is after, when 
    averaging multiple electrophysiology record sweeps acquired with the same
    protocol (sampling, duration, etc).
    
    For this reason only analog_index can be specified, to select from the
    analogsignals list in the segments.
    
    Examples of usage:
    ------------------
    
    >>> blocklist = getvars(sel=neo.Block, sort=True, by_name=False, sortkey="rec_datetime")
    >>> # or:
    >>> blocklist = getvars(locals(), sel="[\W]*common_data_name*", sort=True, by_name=True)
    >>> # then:
    >>> ret = average_blocks(blocklist, segment_index=k, count=n, every=m)
    
    ret is a neo.Block with segments where each segment contains the average signals from kth segment
    for groups of "n" blocks taken every "m" from the list of blocks given as starred argument(s) 

    """
    if len(args) == 0:
        return None
    
    if len(args) == 1:
        args = args[0] # unpack the tuple
        
    #print(args)
    
    n = None
    m = None
    segment_index = None
    analog_index = None
    
# we do something like this:
    #BaseDataPath0MinuteAverage = neo.Block()
    #BaseDataPath0MinuteAverage.segments = neoutils.average_segments(BaseDataPath0.segments, n=6, every=6)
    #sgw.plot(BaseDataPath0MinuteAverage, signals=["Im_prim_1", "Vm_sec_1"])

    
    ret = neo.core.block.Block()
    
    if len(kwargs) > 0 :
        for key in kwargs.keys():
            if key not in ["count", "every", "name", "segment_index", 
                           "analog_index", "annotation", "rec_datetime", 
                           "file_origin", "file_datetime"]:
                raise RuntimeError("Unexpected named parameter %s" % key)
            
        if "count" in kwargs.keys():
            n = kwargs["count"]
            
        if "every" in kwargs.keys():
            m = kwargs["every"]
            
        if "name" in kwargs.keys():
            ret.name = kwargs["name"]
            
        if "segment_index" in kwargs.keys():
            segment_index = kwargs["segment_index"]
            
        if "analog_index" in kwargs.keys():
            analog_index = kwargs["analog_index"]
            
        if "annotation" in kwargs.keys():
            ret.annotation = kwargs["annotation"]

        if "rec_datetime" in kwargs.keys():
            ret.rec_datetime = kwargs["datetime"]
            
        if "file_origin" in kwargs.keys():
            ret.file_origin = kwargs["file_origin"]
            
        if "file_datetime" in kwargs.keys():
            ret.file_datetime = kwargs["file_datetime"]
            
    def __applyRecDateTime(sgm, blk):
        if sgm.rec_datetime is None:
            sgm.rec_datetime = blk.rec_datetime
            
        return sgm
        
    if segment_index is None:
        #segments = [block.segments for block in args]
        segments = [[__applyRecDateTime(sgm, b) for sgm in b.segments] for b in args]
        
    elif isinstance(segment_index, int):
        #segments = [block.segments[segment_index] for block in args if segment_index < len(block.segments)]
        segments = [__applyRecDateTime(b.segments[segment_index], b) for b in args if segment_index < len(b.segments)]
        
    else:
        raise TypeError("Unexpected segment index type (%s) -- expected an int" % segment_index)
    
    #print(len(segments))
    
    if segment_index is not None:
        segment_str = str(segment_index)
        
    else:
        segment_str = "all"
        
    if analog_index is not None:
        signal_str = str(analog_index)
    else:
        signal_str = "all"
        
    block_names= list()
    
    #print(args)
    
    try:
        cframe = inspect.getouterframes(inspect.currentframe())[1][0]
        bname = ""
        for b in args:
            if b.name is None or len(b.name) == 0:
                if b.file_origin is None or len(b.file_origin) == 0:
                    for (k,v) in cframe.f_globals.items():
                        if isinstance(v, neo.Block) and v == b:
                            bname = k
                else:
                    bname = b.file_origin
            else:
                bname = b.name
                
            block_names.append(bname)
                    
        
    finally:
        del(cframe)
        
    ret.segments = average_segments(segments, count=n, every=m, analog_index=analog_index)
    
    ret.annotations["Averaged"] = dict()
    ret.annotations["Averaged"]["Count"] = n
    ret.annotations["Averaged"]["Every"] = m
    ret.annotations["Averaged"]["Origin"] = dict()
    ret.annotations["Averaged"]["Origin"]["Blocks"]   = "; ".join(block_names)
    ret.annotations["Averaged"]["Origin"]["Segments"] = segment_str
    ret.annotations["Averaged"]["Origin"]["Signals"]  = signal_str
    
    return ret

@safeWrapper
def average_blocks_by_segments(*args, **kwargs):
    """Generates a neo.Block whose segments contains averages of the corresponding
    signals in the corresponding segments across a sequence of blocks.
    
    All blocks in the sequence must contain the same number of segments.
    
    By contrast to average_blocks, the result will contain the same number of 
    segments as each block in *args, and each segment will contain an average
    of the corresponding analogsignals from the segment at the corresponding index 
    across all blocks.
    
    
    Arguments:
    =========
    
    args: a sequence of comma-separated list of neo.Blocks
    
    **kwargs:
    ========
    analog_index: which signal into each of the segments to consider
                  can also be a signal name; optional default is None 
                  (thus taking all signals)
                  
    name: str or None (optional default is None)
                  
    NOTE: the signals will keep their individuality in the averaged segment
    
    NOTE: do not use for I-clamp experiments where the amount of injected current
    is different in each segment!!!
    
    
    """
    if len(args) == 0:
        return None
    
    if len(args) == 1:
        args = args[0] # unpack the tuple
    
    analog_index = None
    
    name = None
    
    if len(kwargs) > 0:
        if "analog_index" in kwargs.keys():
            analog_index = kwargs["analog_index"]
            
        if "name" in kwargs.keys():
            name = kwargs["name"]
            
            
    # first check all blocks in the list have the same number of segments
    
    nSegs = [len(block.segments) for block in args]
    
    if min(nSegs) != max(nSegs):
        raise ValueError("The blocks must contain equal number of segments")
    
    nSegs = nSegs[0]
    
    # the check all segments have the same number of signals
    #nSigs = [[len(segment.analogsignals) for segment in block.segments] for block in args]
    
    ret = neo.Block()
    
    for k in range(nSegs):
        nSigs = [len(block.segments[k].analogsignals) for block in args]
        if min(nSigs) != max(nSigs):
            raise ValueError("Corresponding segments must have the same number of signals")
        
        segment = average_segments([block.segments[k] for block in args], analog_index = analog_index)
        ret.segments.append(segment[0])
    
    ret.name="Segment by segment average %s" % name
    
    return ret

@safeWrapper
def remove_signal_offset(sig):
    if not isinstance(sig, neo.AnalogSignal):
        raise TypeError("Expecting an AnalogSignal; got %s instead" % type(sig).__name__)
    
    return sig - sig.min()

@safeWrapper
def batch_normalise_signals(*arg):
    ret = list()
    for sig in arg:
        ret.append(peak_normalise_signal(sig))
        
    return ret

@safeWrapper
def batch_remove_offset(*arg):
    ret = list()
    for sig in arg:
        ret.append(remove_signal_offset(sig))

    return ret
    
@safeWrapper
def peak_normalise_signal(sig, minVal=None, maxVal=None):
    """Returns a peak-normalized copy of the I(V) curve
    
    Positional parameters:
    ----------------------
    
    sig = AnalogSignal with Im data (typically, a time slice corresponding to the
            Vm ramp)
            
    minVal, maxVal = the min and max values to normalize against;
    
    Returns:
    -------
    
    AnalogSignal normalized according to:
    
            ret = (sig - minVal) / (maxVal - minVal)
    
    """
    
    #return neo.AnalogSignal((sig - minVal)/(maxVal - minVal), \
                            #units = pq.dimensionless, \
                            #sampling_rate = sig.sampling_rate, \
                            #t_start = sig.t_start)
                        
    if any([v is None for v in (minVal, maxVal)]):
        if isinstance(sig, neo.AnalogSignal):
            maxVal = sig.max()
            minVal = sig.min()
            
        else:
            raise TypeError("When signal is not an analog signal both minVal and maxVal must be specified")

    return (sig - minVal)/(maxVal - minVal)

@safeWrapper
def average_segments_in_block(data, **kwargs):
    """Returns a new neo.Block containing one segment which is the average of 
    the segments in the block.
    
    Parameters:
    ==========
    "data" a neo.Block.
        
    Var-keyword parameters:
    ======================
    "segment_index" = integer, sequence of integers, range or slice that chooses
            which segment(s) are taken into the average
            
            optional: by default, all segments will be included in the average
        
        e.g. from a block with 5 segments, one may choose to calculate the
        average between segments 1, 3 and 5: segment_index = [1,3,5]
        
    "analog_index" = integer or string, or sequence of integers or strings
        that indicate which channels need to be included in the averaged
        segment. This argument is pased directly to neoutils.average_segments
        function.
        
        NOTE: All segments in "Data" must contain the same number of channels,
        and these channels must have the same names.
        
    
    
    This will average individual signals in all the segments in data.
    The time base will be that of the first segment in data.
    
    
    Arguments:
    =========
    
    To operate on a list of segments, use "neoutils.average_blocks" function.
    
    Keyword Arguments **kwargs: key/value pairs:
    ================================================
            
    Returns:
    =======
    
    A neo.Block with one segment which represents the average of the segments in
    "data" (either all segments, or of those selected by "segment_index").
    
    The new (average) segment contains averages of all signals, or of the signals
    selected by "analog_index".
    
    """

    if not isinstance(data, neo.Block):
        raise TypeError("Data must be a neo.Block instance; got %s instead" % (type(data).__name__))
    
            
    segment_index = None
    analog_index = None
    
    if len(kwargs) > 0:
        for key in kwargs.keys():
            if key not in ["segment_index", "analog_index", 
                           "annotation", "rec_datetime", 
                           "file_origin", "file_datetime"]:
                raise RuntimeError("Unexpected named parameter %s" % key)
            
        if "segment_index" in kwargs.keys():
            segment_index = kwargs["segment_index"]
            
        if "analog_index" in kwargs.keys():
            analog_index = kwargs["analog_index"]
            
    
    if segment_index is not None:
        if isinstance(segment_index, (tuple, list)) and all(isinstance(k, numbers.Integral) and k >=0 and k <len(data.segments) for k in segment_index):
            sgm = [data.segments[k] for k in segment_index]
            
        elif isinstance(segment_index, (slice, numbers.Integral)):
            sgm = data.segments[segment_index]
            
        elif isinstance(segment_index, range):
            sgm = [data.segments[k] for k in segment_index]
            
        else:
            raise ValueError("Invalid segment index; got: %s" % (str(segment_index)))
        
    else:
        sgm = data.segments

    ret = neo.Block()
    ret.segments = average_segments(sgm, analog_index = analog_index)
    
    ret.annotations = data.annotations
    ret.file_origin = data.file_origin
    ret.rec_datetime = data.rec_datetime
    
    if data.name is None or (isinstance(data.name, str) and len(data.name) == 0):
        #data_name = kwargs["data"]
        if data.file_origin is not None and isinstance(data.file_origin, str) and len(data.file_origin) > 0:
            data_name = data.file_origin
            
        else:
            # find the variable name of data in the caller stack frame
            cframe = inspect.getouterframes(inspect.currentframe())[1][0]
            try:
                for (k,v) in cframe.f_globals.items():
                    if isinstance(v, neo.Block) and v == data:
                        data_name = k
            finally:
                del(cframe)
                data_name = "Block"
            
    else:
        data_name = data.name
        
    ret.name = "Average of %s" % (data_name)
        
    if segment_index is None:
        ret.annotations["averaged_segments"] = "all segments"
    else:
        ret.annotations["averaged_segments"] = segment_index
        
    if analog_index is None:
        ret.annotations["averaged_signals"] = "all signals"
    else:
        ret.annotations["averaged_signals"] = analog_index
        
    return ret
        
def neo_copy(src: typing.Union[neo.Block, neo.Segment, neo.ChannelIndex, neo.Unit]) -> typing.Union[neo.Block, neo.Segment, neo.ChannelIndex, neo.Unit]:
    """Copies a neo.Block or a neo.Segment
    
    CAUTION: neo data objects' copy() function creates shallow copies
    
    WARNING: units are not copied across blocks
    
    """
    if isinstance(src, neo.Block):
        ret = neo.Block(name=src.name, 
                        description=src.description,
                        file_origin=src.file_origin, 
                        file_datetime=src.file_datetime,
                        rec_datetime=src.rec_datetime,
                        index=src.index)
        ret.annotations.update(src.annotations)
        
        for r in src.regionsofinterest:
            r_ = None
            
            if isinstance(r, neo.PolygonRegionOfInterest):
                r_ = neo.PolygonRegionOfInterest(*r.vertices)
                
            elif isinstance(r, neo.RectangularRegionOfInterest):
                r_ = neo.RectangularRegionOfInterest(r.x, r.y, r.width, r.height)
                
            elif isinstance(r, neo.CircularRegionOfInterest):
                r_ = neo.CircularRegionOfInterest(r.x, r.y, r.radius)
            
            if r_ is not None:
                ret.regionsofinterest.append(r_)
            
        
        # NOTE: 2020-03-13 18:33:19
        # original channel: {"copy": copied channel, "units": {original unit: copied unit}}
        channels = dict() 
        
        for c in src.channel_indexes:
            c_ = neo.ChannelIndex(index=c.index, name=c.name, 
                                  channel_ids=c.channel_ids,
                                  channel_names=c.channel_names,
                                  description=c.description,
                                  file_origin=c.file_origin,
                                  coordinates=c.coordinates,
                                  **c.annotations)
            
            c_.block = ret
            
            channels[c] = {"copy": c_, "units": dict()}
            
            for u_ in c.units:
                u_ = neo.Unit(name=u.name, description=u.description,
                              fle_origin=u.file_origin,
                              **u.annotations)
                u_.channel_index = u.c_
                c_.units.append(u_)
                
                channels[c]["units"][u] = u_
                
        for s in src.segments:
            s_ = neo.Segment(name=s.name, description=s.description,
                             file_origin=s.file_origin,
                             file_datetime=s.file_datetime,
                             rec_datetime=s.rec_datetime,
                             index = s.index,
                             **s.annotations)
            
            for asig in s.analogsignals:
                asig_ = asig.copy()
                
                for c in channels:
                    #if asig in c.analogsignals:
                    if any([np.all(asig==sig) for sig in c.analogsignals]):
                        asig_.channel_index = channels[c]
                        channels[c]["copy"].analogsignals.append(asig_)
                
                s_.analogsignals.append(asig_)
                
            for st in s.spiketrains:
                st_ = st.copy()
                
                for c in channels:
                    if len(c["units"]):
                        if st.unit in c["units"]:
                            st_.unit = c["units"][u]
                
                s_.spiketrains.append(st_)
                    
            s_.irregularlysampledsignals += [sig.copy() for sig in s.irregularlysampledsignals]
                
            s_.epochs += [e.copy() for e in s.epochs]
            
            s_.events += [e.copy() for e in s.events]
            
            s_.imagesequences == [i.copy() for i in s.imagesequences]
            
            ret.segments.append(s_)
            
        ret.create_many_to_one_relationship()
        
    elif isinstance(src, neo.Segment):
        # NOTE: 2020-03-14 00:56:12
        # bare-bones copy; the channel_index and units are NOT copied
        # the respective links are references to the data in the source 
        # 
        #print("neo_copy(segment)")
        ret = neo.Segment(name = src.name, 
                          description = src.description,
                          file_origin = src.file_origin,
                          file_datetime = src.file_datetime,
                          rec_datetime = src.rec_datetime,
                          index = src.index,
                          **src.annotations)
        
        ret.analogsignals += [s.copy() for s in src.analogsignals]
        
        ret.irregularlysampledsignals += [s.copy() for s in src.irregularlysampledsignals]

        ret.spiketrains += [s.copy() for s in src.spiketrains]
        
        ret.create_many_to_one_relationship()
        
    elif isinstance(src, neo.ChannelIndex):
        # NOTE: 2020-03-14 00:42:29
        # bare-bones copy; the analogsignals and units are NOT copied
        # the respective links must be restored manually
        ret = neo.ChannelIndex(index=src.index, name=src.name, 
                               channel_ids=src.channel_ids,
                               channel_names=src.channel_names,
                               description=src.description,
                               file_origin=src.file_origin,
                               coordinates=src.coordinates,
                               **src.annotations)
        
    elif isinstance(src, neo.Unit):
        # NOTE: 2020-03-14 00:55:16
        # bare-bones copy; the spiketrains and channel_index are NOT copied
        # the respective links must be restored manually
        ret = neo.Unit(name=src.name, description=src.description,
                       file_origin=src.file_origin,
                       **src.annotations)
        
    else:
        raise TypeError("Expecting a neo.Block or a neo.Segment; got %s instead" % type(src).__name__)

    return ret

#@safeWrapper
def average_segments(*args, **kwargs):
    """Returns a LIST of Segment objects with the average of signals in the list of segments
    
    args    comma-separated list of neo.Segment objects, or a sequence (list, tuple) of segments
    kwargs  keyword/value pairs
        count
        every
        analog_index
        
    
    """
    from . import datatypes as dt
    
    def __resample_add__(signal, new_signal):
        from . import datatypes as dt
        if new_signal.sampling_rate != signal.sampling_rate:
            ss = resample_poly(new_signal, signal.sampling_rate)
            
        else:
            ss = new_signal
            
        # neo.AnalogSignal and DataSignal always have ndim == 2
        
        if ss.shape != signal.shape:
            ss_ = neo.AnalogSignal(np.full_like(signal, np.nan),
                                                units = signal.units,
                                                t_start = signal.t_start,
                                                sampling_rate = signal.sampling_rate,
                                                name = ss.name,
                                                **signal.annotations)
            
            src_slicing = [slice(k) for k in ss.shape]
            
            dest_slicing = [slice(k) for k in ss_.shape]
            
            if ss.shape[0] < ss_.shape[0]:
                dest_slicing[0] = src_slicing[0]
                
            else:
                src_slicing[0]  = dest_slicing[0]
                
            if ss.shape[1] < ss_.shape[1]:
                dest_slicing[1] = src_slicing[1]
                
            else:
                src_slicing[1] = dest_slicing[1]
                
            ss_[tuple(dest_slicing)] = ss[tuple(src_slicing)]
            
            ss = ss_
                
        return ss
    
    #print(args)
    
    if len(args) == 0:
        return
    
    if len(args) == 1:
        args = args[0]
    
    if all([isinstance(s, (tuple, list)) for s in args]):
        slist = list()
        
        for it in args:
            for s in it:
                slist.append(s)
                
        args = slist
        
    if not all([isinstance(a, neo.Segment) for a in args]):
        raise TypeError("This function only works with neo.Segment objects")
        
    n = None
    m = None
    analog_index = None
    
    
    if len(kwargs) > 0:
        if "count" in kwargs.keys():
            n = kwargs["count"]
            
        if "every" in kwargs.keys():
            m = kwargs["every"]
            
        if "analog_index" in kwargs.keys():
            analog_index = kwargs["analog_index"]
            
    if n is None:
        n = len(args)
        m = None
        
    if m is None:
        ranges_avg = [range(0, len(args))] # take the average of the whole segments list
        
    else:
        ranges_avg = [range(k, k + n) for k in range(0,len(args),m)] # this will result in as many segments in the data block
        
        
    #print("ranges_avg ", ranges_avg)
    
    if ranges_avg[-1].stop > len(args):
        ranges_avg[-1] = range(ranges_avg[-1].start, len(args))
        
    #print("ranges_avg ", ranges_avg)
    
    ret_seg = list() #  a LIST of segments, each containing averaged analogsignals!
    
    if analog_index is None: #we want an average across the Block list for all signals in the segments
        if not all([len(arg.analogsignals) == len(args[0].analogsignals) for arg in args[1:]]):
            raise ValueError("All segments must have the same number of analogsignals")
        
        for range_avg in ranges_avg:
            #print("range_avg: ", range_avg.start, range_avg.stop)
            #continue
        
            seg = neo.core.segment.Segment()
            
            for k in range_avg:
                if k == range_avg.start:
                    if args[k].rec_datetime is not None:
                        seg.rec_datetime = args[k].rec_datetime

                    for sig in args[k].analogsignals:
                        seg.analogsignals.append(sig.copy())

                elif k < len(args):
                    for (l,s) in enumerate(args[k].analogsignals):
                        seg.analogsignals[l] += __resample_add__(seg.analogsignals[l], s)

            for sig in seg.analogsignals:
                sig /= len(range_avg)

            ret_seg.append(seg)
            
    elif isinstance(analog_index, str): # only one signal indexed by name
        for range_avg in ranges_avg:
            seg = neo.core.segment.Segment()
            for k in range_avg:
                if k == range_avg.start:
                    if args[k].rec_datetime is not None:
                        seg.rec_datetime = args[k].rec_datetime
                        
                    seg.analogsignals.append(args[k].analogsignals[get_index_of_named_signal(args[k], analog_index)].copy())
                    
                else:
                    s = args[k].analogsignals[get_index_of_named_signal(args[k], analog_index)].copy()

                    seg.analogsignals[0] += __resample_add__(seg.analogsignals[0], s)
                    
            seg.analogsignals[0] /= len(range_avg) # there is only ONE signal in this segment!
            
            ret_seg.append(seg)
            
    elif isinstance(analog_index, int):
        #print("analog_index ", analog_index)
        for range_avg in ranges_avg:
            seg = neo.core.segment.Segment()
            for k in range_avg:
                if args[k].rec_datetime is not None:
                    seg.rec_datetime = args[k].rec_datetime
                    
                if k == range_avg.start:
                    seg.analogsignals.append(args[k].analogsignals[analog_index].copy())
                    
                else:
                    s = args[k].analogsignals[analog_index].copy()
                    
                    seg.analogsignals[0] += __resample_add__(seg.analogsignals[0], s)
                    
            seg.analogsignals[0] /= len(range_avg)# there is only ONE signal in this segment!
            
            ret_seg.append(seg)
            
    elif isinstance(analog_index, (list, tuple)):
        for range_avg in ranges_avg:
            seg = neo.core.segment.Segment()
            for k in range_avg:
                if k == range_avg.start:
                    if args[k].rec_datetime is not None:
                        seg.rec_datetime = args[k].rec_datetime

                    for sigNdx in analog_index:
                        if isinstance(sigNdx, str):
                            sigNdx = get_index_of_named_signal(args[k], sigNdx)
                            
                        seg.analogsignals.append(args[k].analogsignals[sigNdx].copy()) # will raise an error if sigNdx is of unexpected type
                        
                else:
                    for ds in range(len(analog_index)):
                        sigNdx = analog_index[ds]
                        
                        if isinstance(sigNdx, str):
                            sigNdx = get_index_of_named_signal(args[k], sigNdx)
                            
                        s = args[k].analogsignals[sigNdx].copy()
                        
                        seg.analogsignals[ds] += __resample_add__(seg.analogsignals[ds], s)
                        
            for sig in seg.analogsignals:
                sig /= len(range_avg)
            
            ret_seg.append(seg)
            
    else:
        raise TypeError("Unexpected type for signal index")
    
    return ret_seg
    
@safeWrapper
def average_signals(*args, fun=np.mean):
    """ Returns an AnalogSignal containing the element-by-element average of several neo.AnalogSignals.
    All signals must be single-channel and have compatible shapes and sampling rates.
    """
    
    if len(args) == 0:
        return
    
    if len(args) == 1 and isinstance(args[0], (list, tuple)) and all([isinstance(a, neo.core.analogsignal.AnalogSignal) for a in args[0]]):
        args = args[0]

    #ret = args[0].copy() # it will inherit t_start, t_stop, name, annotations, sampling_rate
    
    if any([s.shape != args[0].shape for s in args]):
        raise ValueError("Signals must have identical shape")
    
    if any([s.shape[1]>1 for s in args]):
        raise ValueError("Expecting single-channel signals only")
    
    ret_signal = fun(np.concatenate(args, axis=1), axis=1)
    
    return ret_signal
    #if all([sig.shape == args[0].shape for sig in args[1:]]):
        #ret_signal = fun(np.concatenate(args, axis=1), axis=1)
        #return ret_signal
        
        ##for sig in args[1:]:
            ##ret += sig
            
        ##ret /= len(args)
        
    #else:
        #raise ValueError("Cannot average AnalogSignal objects of different shapes")
        
    
    return ret

@safeWrapper
def merge_signal_channels(*args, name=""):
    """Returns an analog signal containing merged channels of the analog signals in args
    """
    from . import datatypes as dt
    
    def __internal_merge__(*signals):
        from . import datatypes as dt
        sigs = [s.magnitude for s in signals]
        ret_sig = signals[0].__class__(np.concatenate(sigs, axis=1), 
                                       units = signals[0].units,
                                       sampling_period = signals[0].sampling_period,
                                       t_start = signals[0].t_start,
                                       name=name)
        
        return ret_sig
        
    
    if not all([isinstance(s, neo.AnalogSignal) for s in args]) and \
        not all([isinstance(s, DataSignal) for s in args]):
        raise TypeError("All data in the parameter sequence must be either AnalogSignal objects or DataSignal objects")
        
    if not all([s.shape[0] == args[0].shape[0] for s in args]):
        raise ValueError("Signals must have same axis length")
    
    if not all([s.sampling_period == args[0].sampling_period for s in args]):
        raise ValueError("All signals must have the same sampling period")
    
    return __internal_merge__(*args)
    
@safeWrapper
def aggregate_signals(*args, name_prefix:str, 
                      collectSD:bool=True, collectSEM:bool=True) -> dict:
    """Returns signal mean, SD, SEM, and number of signals in args.
    All signals must be single-channel.
    
    Keyword parameters:
    
    name_prefix : a str; must be specified (default is None)
    
    Returns a dict
    
    """
    from . import datatypes as dt
    
    if len(args) == 0:
        return
    
    if len(args) == 1 and isinstance(args[0], (list, tuple)) and all([isinstance(a, (neo.AnalogSignal, Datasignal)) for a in args[0]]):
        args = args[0]

    if any([s.shape != args[0].shape for s in args]):
        raise ValueError("Signals must have identical shape")
    
    if any([s.shape[1] > 1 for s in args]):
        raise ValueError("Expecting single-channel signals only")
    
    count = len(args)
    
    allsigs = np.concatenate(args, axis=1)
    
    ret_mean = np.mean(allsigs, axis=1).magnitude
    
    ret_SD = np.std(allsigs, axis = 1, ddof=1).magnitude
    
    ret_SEM = ret_SD/(np.sqrt(count-1))
    
    if collectSD:
        ret_mean_SD = np.concatenate((ret_mean[:,np.newaxis], 
                                      (ret_mean-ret_SD)[:,np.newaxis], 
                                      (ret_mean + ret_SD)[:,np.newaxis]),
                                     axis=1)
        suffix = "mean_SD"
        
        ret_mean_SD = neo.AnalogSignal(ret_mean_SD, units = args[0].units,
                                       sampling_period = args[0].sampling_period,
                                       name = "%s_%s" % (name_prefix, suffix))
        
    else:
        ret_mean_SD = None
        
    if collectSEM:
        ret_mean_SEM = np.concatenate((ret_mean[:,np.newaxis], 
                                       (ret_mean - ret_SEM)[:,np.newaxis],
                                       (ret_mean + ret_SEM)[:,np.newaxis]), 
                                     axis=1)
        
        suffix = "mean_SEM"
        
        ret_mean_SEM = neo.AnalogSignal(ret_mean_SEM, units = args[0].units,
                                        sampling_period = args[0].sampling_period,
                                        name = "%s_%s" % (name_prefix, suffix))
    
    else:
        ret_mean_SEM = None
    
    suffix = "mean"
        
    ret_mean = neo.AnalogSignal(ret_mean, units = args[0].units, 
                                sampling_period = args[0].sampling_period, 
                                name = "%s_%s" % (name_prefix, suffix))
    
        
    ret_SD = neo.AnalogSignal(ret_SD, units = args[0].units,
                              sampling_period = args[0].sampling_period,
                              name = "%s_SD" % name_prefix)
    
    ret_SEM = neo.AnalogSignal(ret_SEM, units = args[0].units,
                              sampling_period = args[0].sampling_period,
                              name = "%s_SEM" % name_prefix)
    
    
    ret = dict()
    
    ret["mean"] = ret_mean
    ret["sd"] = ret_SD
    ret["SEM"] = ret_SEM
    ret["mean-SEM"] = None
    ret["mean-SD"] = None
    ret["name"] = name_prefix
    ret["count"] = count
    
    if ret_mean_SEM is not None:
        ret["mean-SEM"] = ret_mean_SEM
        
    if ret_mean_SD is not None:
        ret["mean-SD"]  = ret_mean_SD

    return ret
    
    
    
@safeWrapper
def convolve(sig, w, **kwargs):
    """1D convolution of neo.AnalogSignal sig with kernel "w".
    
    Parameters:
    -----------
    
    sig : neo.AnalogSignal; if it has multiple channels, the convolution is
        applied for each channel
        
    w : 1D array-like
    
    Var-keyword parameters are passed on to the scipy.signal.convolve function,
    except for the "mode" which is always set to "same"
    """
    
    from scipy.signal import convolve
    
    name = kwargs.pop("name", "")
    
    units = kwargs.pop("units", pq.dimensionless)
    
    kwargs["mode"] = "same" # force "same" mode for convolution
    
    if sig.shape[1] == 1:
        ret = neo.AnalogSignal(convolve(sig.magnitude.flatten(), w, **kwargs),\
                            units = sig.units, \
                            t_start = sig.t_start, \
                            sampling_period = sig.sampling_period,\
                            name = "%s convolved" % sig.name)
        
    else:
        csig = [convolve(sig[:,k].magnitude.flatten(), w, **kwargs)[:,np.newaxis] for k in range(sig.shape[1])]
        
        ret = neo.AnalogSignal(np.concatenate(csig, axis=1),
                               units = sig.units,
                               t_start = sig.t_start,
                               sampling_period = sig.sampling_period,
                               name = "%s convolved" % sig.name)
        
    ret.annotations.update(sig.annotations)
    
    return ret

@safeWrapper
def parse_acquisition_metadata(data:neo.Block, configuration:[type(None), dict] = None):
    """Parses metadata from electrophysiology acquisition data.
    
    Tries to bring acquisition parameters and protocols from different
    software vendors under a common structure.
    
    NOTE: 2020-02-18 13:53:56
        Currently supports only data loaded from axon binary files (*.abf) 
    TODO: 2020-02-18 13:54:00 Support for:
    * axon text files (*.atf)
    * axon protocol files (*.pro)
    * CED Signal files (CFS)
    * CED Spike2 files (SON) -- see neo.io
    
    
    Parameters:
    ----------
    
    data: neo.Block loaded from an electrophysiology acquisition software
    
    configuration: dict or None (default): additional configuration data loaded
        from a configuration file alongside with the data acquisition file 
        
    
    
    Returns:
    --------
    A dictionary with fields detailing, to the extent possible, acquisition 
    protocols and parameters. 
    """
    
    if not isinstance(data, neo.Block):
        raise TypeError("Expecting a neo.Block; got %s instead" % type(data).__name__)
    
    if "software" in data.annotations:
        pass

@safeWrapper
def parse_step_waveform_signal(sig, method="state_levels", **kwargs):
    """Parse a step waveform -- containing two states ("high" and "low").
    
    Typical example is a depolarizing curent injection step (or rectangular pulse)
    
    Parameters:
    ----------
    sig = neo.AnalogSignal with one channel (i.e. sig.shape[1]==1)
    
    Named parameters:
    -----------------
    box_size = length of smoothing boxcar window (default, 0)
    
    method: str, one of "state_levels" (default) or "kmeans"
    
    The following are used only when methos is "state_levels" and are passed 
    directly to signalprocessing.state_levels():
    
    adcres,
    adcrange,
    adcscale
    
    Returns:
    
    down: quantity array of high to low transitions times (in units of signal.times)
    up:  the same, for low to high transition times (in units of signal.times)
    inj: scalar quantity: the amplitude of the transition (in units of the signal)
    centroids: numpy array with shape (2,1): the centroid values i.e., the mean values
        of the two state levels
        
        
    """
    from scipy import cluster
    from scipy.signal import boxcar
    
    if not isinstance(sig, neo.AnalogSignal):
        raise TypeError("Expecting an analogsignal; got %s instead" % type(sig).__name__)
    
    if sig.ndim == 2 and sig.shape[1] > 1:
        raise ValueError("Expecting a signal with one channel, instead got %d" % sig.shape[1])
    
    box_size = kwargs.pop("box_size", 0)
    
    if box_size > 0:
        window = boxcar(box_size)/box_size
        sig_flt = convolve(sig, window)
        #sig_flt = convolve(np.squeeze(sig), window, mode="same")
        #sig_flt = neo.AnalogSignal(sig_flt[:,np.newaxis], units = sig.units, t_start = sig.t_start, sampling_rate = 1/sig.sampling_period)
    else:
        sig_flt = sig
        
    # 1) get transition times from injected current
    # use filtered signal, if available
    
    if method is "state_levels":
        levels = kwargs.pop("levels", 0.5)
        adcres = kwargs.pop("adcres", 15)
        adcrange = kwargs.pop("adcrange", 10)
        adcscale = kwargs.pop("adcrange", 1e3)
    
        centroids = sigp.state_levels(sig_flt.magnitude, levels = levels, 
                                    adcres = adcres, 
                                    adcrange = adcrange, 
                                    adcscale = adcscale)
        
        #centroids = sigp.state_levels(sig_flt.magnitude, levels = 0.5, 
                                    #adcres = adcres, 
                                    #adcrange = adcrange, 
                                    #adcscale = adcscale)
        
        
        centroids = np.array(centroids).T[:,np.newaxis]
        
    else:
        centroids, distortion = cluster.vq.kmeans(sig_flt, 2)
        centroids = np.sort(centroids, axis=0)
    
    #print(centroids)
    
    label, dst = cluster.vq.vq(sig, centroids) # use un-filtered signal here
    edlabel = np.ediff1d(label, to_begin=0)
    
    down = sig.times[np.where(edlabel == -1)]
    
    up  = sig.times[np.where(edlabel == 1)]

    # NOTE: 2017-08-31 23:04:26 FYI: depolarizing = down > up 
    # in current-clamp, a depolarizing current injection is an outward current 
    # which therefore goes up BEFORE it goes back down, hence down is later than
    # up 
    
    # the step amplitude
    #amplitude = np.diff(centroids.ravel()) * sig.units
    amplitude = np.diff(centroids.flatten()) * sig.units
    
    return down, up, amplitude, centroids, label

@safeWrapper
def resample_pchip(sig, new_sampling_period, old_sampling_period = 1):
    """Resample a signal using a piecewise cubic Hermite interpolating polynomial.
    
    Resampling is calculated using scipy.interpolate.PchipInterpolator, along the
    0th axis.
    
    Parameters:
    -----------
    
    sig: numpy ndarray, python Quantity array or numpy array subclass which has 
        the attribute "sampling_period"
    
    new_sampling_period: float scalar
        The desired sampling period after resampling
        
    old_sampling_period: float scalar or None (default)
        Must be specified when sig is a generic numpy ndarray or Quantity array.
        
    Returns:
    --------
    
    ret: same type as sig
        A version of the signal resampled along 0th axis:
        
        * upsampled if new_sampling_period < old_sampling_period
        
        * downsampled if new_sampling_period > old_sampling_period
        
    When new_sampling_period == old_sampling_period, returns a reference to the
        signal (no resampling is performed and no data is copied).
        
        CAUTION: In this case the result is a REFERENCE to the signal, and 
                 therefore, any methods that modify the result in place will 
                 also modify the original signal!
    
    """
    # for upsampling this will introduce np.nan at the end
    # we replace these values wihtt he last signal sample value
    from scipy.interpolate import PchipInterpolator as pchip
    
    from . import datatypes as dt
    
    if isinstance(sig, (neo.AnalogSignal, DataSignal)):
        if isinstance(new_sampling_period, pq.Quantity):
            if not dt.units_convertible(new_sampling_period, sig.sampling_period):
                raise TypeError("new sampling period units (%s) are incompatible with those of the signal's sampling period (%s)" % (new_sampling_period.units, sig.sampling_period.units))
            
            new_sampling_period.rescale(sig.sampling_period.units)
            
        else:
            new_sampling_period *= sig.sampling_period.units
    
        if sig.sampling_period > new_sampling_period:
            scale = sig.sampling_period / new_sampling_period
            new_axis_len = int(np.floor(len(sig) * scale))
            descr = "Upsampled"
            
        elif sig.sampling_period < new_sampling_period:
            scale = new_sampling_period / sig.sampling_period
            new_axis_len = int(np.floor(len(sig) // scale))
            descr = "Downsampled"
            
        else: # no resampling required; return reference to signal
            return sig
        
        new_times, new_step = np.linspace(sig.t_start.magnitude, sig.t_stop.magnitude, 
                                          num=new_axis_len, retstep=True, endpoint=False)
        
        #print("neoutils.resample_pchip new_step", new_step, "new_sampling_period", new_sampling_period)
        
        assert(np.isclose(new_step, float(new_sampling_period.magnitude)))
        
        interpolator = pchip(sig.times.magnitude.flatten(), sig.magnitude.flatten(), 
                             axis=0, extrapolate=False)
        
        new_sig = interpolator(new_times)
        
        new_sig[np.isnan(new_sig)] = sig[-1,...]
        
        ret = sig.__class__(new_sig, units=sig.units,
                            t_start = new_times[0]*sig.times.units,
                            sampling_period=new_sampling_period,
                            name = sig.name,
                            description="%s %s %d-fold" % (sig.name, descr, scale))
        
        ret.annotations.update(sig.annotations)
    
        return ret
    
    else:
        if old_sampling_period is None:
            raise ValueError("When signal is a generic array the old sampling period must be specified")
        
        if isinstance(old_sampling_period, pq.Quantity):
            old_sampling_period = old_sampling_period.magnitude
            
        if isinstance(new_sampling_period, pq.Quantity):
            new_sampling_period = new_sampling_period.magnitude
            
        if old_sampling_period > new_sampling_period:
            scale = int(old_sampling_period / new_sampling_period)
            new_axis_len = sig.shape[0] * scale
            
        elif old_sampling_period < new_sampling_period:
            scale = int(new_sampling_period / old_sampling_period)
            new_axis_len = sig.shape[0] // scale
            
        else: # no resampling required; return reference to signal
            return sig
        
        t_start = 0
        
        t_stop = sig.shape[0] * old_sampling_period
        
        new_times, new_step = np.linspace(sig.t_start.magnitude, sig.t_stop.magnitude, 
                                          num=new_axis_len, retstep=True, endpoint=False)
        
        assert(np.isclose(new_step,float(new_sampling_period.magnitude)))
        
        interpolator = pchip(sig.times.magnitude.flatten(), sig.magnitude.flatten(), 
                             axis=0, extrapolate=False)
        
        ret = interpolator(new_times)
        
        ret[np.isnan(ret)] = sig[-1, ...]
        
        return ret

@safeWrapper
def diff(sig, n=1, axis=-1, prepend=False, append=True):
    """Calculates the n-th discrete difference along the given axis.
    
    Calls numpy.diff() under the hood.
    
    Parameters:
    ----------
    sig: numpy.array or subclass
        NOTE: singleton dimensions will be squeezed out
    
    Named parameters:
    -----------------
    These are passed directly to numpy.diff(). 
    The numpy.diff() documentation is replicated below highlighting any differences.
    
    n: int, optional
        The number of times values are differenced. 
        If zero the input is returned as is.
        
        Default is 1 (one)
    
    prepend, append: None or array-like, or bool
        Values to prepend/append to sig along the axis PRIOR to performing the 
        difference!
        
        NOTE:   When booleans, a value of True means that prepend or append will
        take, respectively, the first or last signal values along difference axis.
        
                A value of False is equivalent to None.
                
        NOTE:   "prepend" has default False; "append" has default True
        
    
    """
    if not isinstance(axis, int):
        raise TypeError("Axis expected to be an int; got %s instead" % type(axis).__name__)
    
    # first, squeeze out the signal's sigleton dimensions
    sig_data = np.array(sig).squeeze() # also copies the data; also we can use plain arrays
    #sig_data = sig.magnitude.squeeze() # also copies the data
    
    if isinstance(append, bool):
        if append:
            append_ndx = [slice(k) for k in sig_data.shape]
            append_ndx[axis] = -1
            
            append_shape = [slice(k) for k in sig_data.shape]
            append_shape[axis] = np.newaxis
            
            append = sig_data[tuple(append_ndx)][tuple(append_shape)]
            
        else:
            append = None
            
    if isinstance(prepend, bool):
        if prepend:
            prepend_ndx = [slice(k) for k in sig_data.shape]
            prepend_ndx[axis] = 0
            
            prepend_shape = [slice(k) for k in sig_data.shape]
            prepend_shape[axis] = np.newaxis
            
            prepend = sig_data[tuple(prepend_ndx)][tuple(prepend_shape)]
            
        else:
            prepend = None
            
    diffsig = np.diff(sig_data, n = n, axis = axis, prepend=prepend, append=append)
    
    ret = neo.AnalogSignal(diffsig, 
                           units = sig.units/(sig.times.units ** n),
                           t_start = 0 * sig.times.units,
                           sampling_rate = sig.sampling_rate,
                           name = sig.name,
                           description = "%dth order difference of %s" % (n, sig.name))
    
    ret.annotations.update(sig.annotations)
    
    return ret

@safeWrapper
def gradient(sig:[neo.AnalogSignal, DataSignal, np.ndarray], 
             n:int=1, 
             axis:int=0) -> neo.AnalogSignal:
    """ First order gradient through central differences.
    
    Parameters:
    ----------
    
    sig: numpy.array or subclass
        The signal; can have at most 2 dimensions.
        When sig.shape[1] > 1, the gradient is calculated across the specified axis
    
    n: int; default is 1 (one)
        The spacing of the gradient (see numpy.gradient() for details)
    
    axis: int; default is 0 (zero)
        The axis along which the gradient is calculated;
        Can be -1 (all axes), 0, or 1.
        
        TODO/FIXME 2019-04-27 10:07:26: 
        At this time the function only supports axis = 0
        
    Returns:
    -------
    
    ret: neo.AnalogSignal or DataSignal, according to the type of "sig".
    
    
    """
    diffsig = np.array(sig) # for a neo.AnalogSignal this also copies the signal's magnitude
    
    if diffsig.ndim == 2:
        for k in range(diffsig.shape[1]):
            diffsig[:,k] = np.gradient(diffsig[:,k], n, axis=0)
            
        diffsig /= (n * sig.sampling_period.magnitude)
            
    elif diffsig.ndim == 1:
        diffsig = np.gradient(diffsig, n, axis=0)
        diffsig /= (n * sig.sampling_period.magnitude)
            
    else:
        raise TypeError("'sig' has too many dimensions (%d); expecting 1 or 2" % diffsig.ndim)
        
    if isinstance(sig, DataSignal):
        ret = DataSignal(diffsig, 
                            units = sig.units / sig.times.units, 
                            t_start = sig.t_start, 
                            sampling_period = sig.sampling_period, 
                            name = sig.name,
                            description = "Gradient of %s over %d samples along axis %d" % (sig.name, n, axis))
 
    else:
        ret = neo.AnalogSignal(diffsig, 
                            units = sig.units / sig.times.units, 
                            t_start = sig.t_start, 
                            sampling_period = sig.sampling_period, 
                            name = sig.name,
                            description = "Gradient of %s over %d samples along axis %d" % (sig.name, n, axis))
 
    ret.annotations.update(sig.annotations)
    
    return ret

    
    
@safeWrapper
def ediff1d(sig:[neo.AnalogSignal, DataSignal, np.ndarray],
            to_end:numbers.Number=0, 
            to_begin:[numbers.Number, type(None)]=None) -> neo.AnalogSignal:
    """Differentiates each channel of an analogsignal with respect to its time basis.
    
    Parameters:
    -----------
    
    sig: neo.AnalogSignal, numpy.array, or Quantity array
    
    
    Named parameters (see numpy.ediff1d):
    -------------------------------------
    Passed directly to numpy.ediff1d:
    
    to_end: scalar float, or 0 (default) NOTE: for numpy.ediff1d, the default is None
    
    to_begin: scalar float, or None (default)
    
    Returns:
    --------
    DataSignal or neo.AnalogSignal, according to the type of "sig"
    
    """
    
    diffsig = np.array(sig) # for a neo.AnalogSignal this also copies the signal's magnitude
    
    if diffsig.ndim == 2:
        for k in range(diffsig.shape[1]):
            diffsig[:,k] = np.ediff1d(diffsig[:,k], to_end=to_end, to_begin=to_begin)# to_end = to_end, to_begin=to_begin)
            
    elif diffsig.ndim == 1:
        diffsig = np.ediff1d(diffsig, to_end=to_end, to_begin=to_begin)
            
    else:
        raise TypeError("'sig' has too many dimensions (%d); expecting 1 or 2" % diffsig.ndim)
        
    diffsig /= sig.sampling_period.magnitude
    
    if isinstance(sig, DataSignal):
        ret = DataSignal(diffsig, units = sig.units / sig.times.units, 
                            t_start = sig.t_start, 
                            sampling_period = sig.sampling_period, 
                            name = sig.name,
                            description = "First order forward difference of %s" % sig.name)
    
        
    else:
        ret = neo.AnalogSignal(diffsig, units = sig.units / sig.times.units, 
                            t_start = sig.t_start, 
                            sampling_period = sig.sampling_period, 
                            name = sig.name,
                            description = "First order forward difference of %s" % sig.name)
    
    ret.annotations.update(sig.annotations)
    
    return ret

@safeWrapper
def forward_difference(sig:[neo.AnalogSignal, DataSignal, np.ndarray], 
                       n:int=1, 
                       to_end:numbers.Number=0,
                       to_begin:[numbers.Number, type(None)]=None) -> neo.AnalogSignal:
    """Calculates the forward difference along the time axis.
    
    Parameters:
    -----------
    
    sig: neo.AnalogSignal, numpy.array, or Quantity array
    
    
    Named parameters (see numpy.ediff1d):
    -------------------------------------
    
    n: int;
        number of samples in the difference.
        
        Must satisfy 0 <= n < len(sig) -2
        
        When n=0 the function returns a reference to the signal.
        
        When n=1 (the default), the function calls np.ediff1d() on the signal's 
            magnitude and the result is divided by signals sampling period
        
        When n > 1 the function calculates the forward difference 
            
            (sig[n:] - sig[:-n]) / (n * sampling_rate)
            
        Values of n > 2 not really meaningful.
            
    to_end: scalar float, or 0 (default) NOTE: for numpy.ediff1d, the default is None
    
    to_begin: scalar float, or None (default)
    
    Returns:
    --------
    DataSignal or neo.AnalogSignal, according to the type of "sig"
    
    """
    
    def __n_diff__(ary, n, to_b, to_e):
        dsig = ary[n:] - ary[:-n]
        
        shp = [s for s in ary.shape]
        
        if to_end is not None:
            if to_begin is None:
                shp[0] = n
                dsig = np.append(dsig, np.full(tuple(shp), to_e), axis=0)
                
            else:
                to_start = n//2
                to_stop = n - to_start
                
                shp[0] = to_start
                dsig = np.insert(dsig, np.full(tuple(shp), to_b), axis=0)
                
                shp[0] = to_stop
                dsig = np.append(dsig, np.full(tuple(shp), to_e), axis=0)
                
        else:
            if to_end is None:
                shp[0] = n
                dsig = np.insert(dsig, np.full(tuple(shp), to_b), axis=0)
                
            else:
                to_start = n//2
                to_stop = n - to_start
                
                shp[0] = to_start
                dsig = np.insert(dsig, np.full(tuple(shp), to_b), axis=0)
                
                shp[0] = to_stop
                dsig = np.append(dsig, np.full(tuple(shp), to_e), axis=0)
                
        return dsig
        
    
    if not isinstance(n, int):
        raise TypeError("'n' expected to be an int; got %s instead" % type(n).__name__)
    
    if n < 0: 
        raise ValueError("'n' must be >= 0; got %d instead" % n)
    
    diffsig = np.array(sig) # for a neo.AnalogSignal this also copies the signal's magnitude
    
    if diffsig.ndim == 2:
        if n >= diffsig.shape[0]:
            raise ValueError("'n' is too large (%d); should be n < %d" % (n, diffsig.shape[0]))
        
        if n == 0:
            return sig
        
        elif n == 1:
            for k in range(diffsig.shape[1]):
                diffsig[:,k] = np.ediff1d(diffsig[:,k], to_end=to_end, to_begin=to_begin)# to_end = to_end, to_begin=to_begin)
                
            diffsig /= sig.sampling_period.magnitude
            
        else:
            for k in range(diffsig.shape[1]):
                diffsig[:,k] = __n_diff__(diffsig[:,k], n=n, to_e=to_end, to_b=to_begin)# to_end = to_end, to_begin=to_begin)
            
            diffsig /= (n * sig.sampling_period.magnitude)
            
    elif diffsig.ndim == 1:
        if n >= len(diffsig):
            raise ValueError("'n' is too large (%d); should be < %d" % (n, len(diffsig)))
        
        if n == 0:
            return sig
        
        elif n == 1:
            diffsig = __n_diff__(diffsig, n=n, to_e = to_end, to_b = to_begin)
            #diffsig = np.ediff1d(diffsig, to_end=to_end, to_begin=to_begin)
            diffsig /= sig.sampling_period.magnitude
            
        else:
                    
            diffsig /= (n * sig.sampling_period.magnitude)
            
    else:
        raise TypeError("'sig' has too many dimensions (%d); expecting 1 or 2" % diffsig.ndim)
        
        
    if isinstance(sig, DataSignal):
        ret = DataSignal(diffsig, units = sig.units / sig.times.units, 
                            t_start = sig.t_start, 
                            sampling_period = sig.sampling_period, 
                            name = "%s_diff(1)" % sig.name,
                            description = "Forward difference (%dth order) of %s" % (n, sig.name))
 
    else:
        ret = neo.AnalogSignal(diffsig, units = sig.units / sig.times.units, 
                            t_start = sig.t_start, 
                            sampling_period = sig.sampling_period, 
                            name = "%s_diff(1)" % sig.name,
                            description = "Forward difference (%dth order) of %s" % (n, sig.name))
 
    ret.annotations.update(sig.annotations)
    
    return ret

def auto_detect_trigger_protocols(data:[ScanData, neo.Block], 
                               presynaptic:tuple=(), 
                               postsynaptic:tuple=(),
                               photostimulation:tuple=(),
                               imaging:tuple=(),
                               clear:bool=False):
    
    """Determines the set of trigger protocols in scandata by searching for 
    trigger waveforms in the analogsignals contained in data.
    
    Time stamps of the detected trigger protocols will then be used to construct
    TriggerEvent objects according to which of the keyword parameters below
    have been specified.
    
    Positional parameters:
    =====================
    
    data:   either a ScanData object, or a neo.Block object
            
            If a ScanData object, it must contain a non-empty electrophysiology
            block.
            
    Named parameters:
    =================
    
    presynaptic, postsynaptic, photostimulation, imaging:
    
        each is a tuple with 0 (default), two or three elements that specify 
        parameters for the detection of pre-, post-synaptic, photo-stimulation
        or imaging (trigger) event types, respectively.
        
        First element (int): the index of the analog signal in the electrophysiology 
            block segments, containing the trigger signal (usually a square pulse, 
            or a train of square pulses)
        
        Second element (str): a label to be assigned to the detected event
        
        Third (optional) element:  a tuple of two python Quantity objects defining
            a time slice within the signal, used for the detection of the events.
            
            This is recommended in case the trigger signal contains other 
            waveforms in addition to the trigger waveform.
            In this case, the trigger waveform will be searched/analysed within
            the signal regions between these two time points (right-open interval).
            
        When empty, no events of the corresponding type will be constructed.
        
    clear: bool (default False)
        When False (default), detected event arrays will be appended.
        
        When True, old events will be cleared from data.electrophysiology
        
    Returns:
    =======
    A list of trigger protocols
        
    """
    from . import datatypes as dt

    if isinstance(data, ScanData):
        target = data.electrophysiology
        
    elif isinstance(data, neo.Block):
        target = data
        
    else:
        raise TypeError("Expecting a datatypes.ScanData or a neo.Block; got %s instead" % type(data).__name__)
    
    if not isinstance(clear, bool):
        raise TypeError("clear parameter expected to be a boolean; got %s instead" % type(clear).__name__)
        
    #print("auto_detect_trigger_protocols: presynaptic", presynaptic)
    #print("auto_detect_trigger_protocols: postsynaptic", postsynaptic)
    #print("auto_detect_trigger_protocols: photostimulation", photostimulation)
    #print("auto_detect_trigger_protocols: imaging", imaging)
        
    if clear:
        clear_events(target)
    
    # NOTE: 2019-03-14 21:43:21
    # each auto-detection below embeds detected events in the "target" 
    # (for ScanData, the "target" is the electrophysiology block, as it is the 
    # only container of signals with trigger waveforms
    # 
    # depending on the length of the kwyrod parameters (see the docstring)
    # we detect events in the whole signal or we limit detetion to a defined 
    # time-slice of the signal
    
    if len(presynaptic) == 2:
        auto_define_trigger_events(target, presynaptic[0], "presynaptic", label=presynaptic[1])
        
    elif len(presynaptic) == 3:
        auto_define_trigger_events(target, presynaptic[0], "presynaptic", label=presynaptic[1], time_slice = presynaptic[2])
        
    if len(postsynaptic) == 2:
        auto_define_trigger_events(target, postsynaptic[0], "postsynaptic", label = postsynaptic[1])
        
    elif len(postsynaptic) == 3:
        auto_define_trigger_events(target, postsynaptic[0], "postsynaptic", label = postsynaptic[1], time_slice = postsynaptic[2])
        
    if len(photostimulation) == 2:
        auto_define_trigger_events(target, photostimulation[0], "photostimulation", label=photostimulation[1])
        
    elif len(photostimulation) == 3:
        auto_define_trigger_events(target, photostimulation[0], "photostimulation", label=photostimulation[1], time_slice = photostimulation[2])
        
    if len(imaging) == 2:
        auto_define_trigger_events(target, imaging[0], "frame", label = imaging[1])
        
    elif len(imaging) == 3:
        auto_define_trigger_events(target, imaging[0], "frame", label = imaging[1], time_slice = imaging[2])
        
    #for s in target.segments:
        #s.annotations["trigger_protocol"] = "protocol"
        
    # create the collection of TriggerProtocol objects by parsing TriggerEvents in "target"
    tp, _ = parse_trigger_protocols(target)
    
    return tp

@safeWrapper
def auto_define_trigger_events(src, analog_index, event_type, 
                               times=None, label=None, name=None, 
                               use_lo_hi=True, time_slice=None, 
                               clearSimilarEvents=True, clearTriggerEvents=True, 
                               clearAllEvents=False):
    """Populates the events lists for the segments in src with TriggerEvent objects.
    
    Searches for trigger waveforms in signals specified by analog_index, to define
    TriggerEvent objects.
    
    A TriggerEvent is an array of time values and will be added to the events list
    of the neo.Segment objects in src.
    
    Calls detect_trigger_events()
    
    Parameters:
    ===========
    
    src: a neo.Block, a neo.Segment, or a list of neo.Segment objects
    
    analog_index:   specified which signal to use for event detection; can be one of:
    
                    int (index of the signal array in the data analogsignals)
                        assumes that _ALL_ segments in "src" have the desired analogsignal
                        at the same position in the analogsignals array
    
                    str (name of the analogsignal to use for detection) -- must
                        resolve to a valid nalogsignal index in _ALL_ segments in 
                        "src"
                    
                    a sequence of int (index of the signal), one per segment in src 

    event_type: a str that specifies the type of trigger event e.g.:
                'acquisition',
                'frame'
                'imaging',
                'imaging_frame',
                'imaging_line',
                'line'
                'photostimulation',
                'postsynaptic',
                'presynaptic',
                'sweep',
                'user'
                
            or a valid datatypes.TriggerEventType enum type, e.g. TriggerEventType.presynaptic
    
    (see detect_trigger_events(), datatypes.TriggerEventType)
    
    Named parameters:
    =================
    times: either None, or a python quantity array with time units
    
        When "times" is None (the default) the function calls detect_trigger_events() 
        on the analogsignal specified by analog_index in src, to detect trigger 
        events. The specified analogsignal must therefore contain trigger waveforms 
        (typically, rectangular pulses).
        
        Otherwise, the values in the "times" array will be used to define the 
        trigger events.
        
    label: common prefix for the individual trigger event label in the event array
            (see also detect_trigger_events())
    
    name: name for the trigger event array 
            (see also detect_trigger_events())
    
    use_lo_hi: boolean, (default is True);  
        when True, use the rising transition to detect the event time 
            (see also detect_trigger_events())
        
    time_slice: pq.Quantity tuple (t_start, t_stop) or None.
        When detecting events (see below) the time_slice can specify which part of  
        a signal can be used for automatic event detection.
        
        When time_slice is None this indicates that the events are to be detected 
        from the entire signal.
        
        The elements need to be Python Quantity objects compatible with the domain
        of the signal. For AnalogSignal, this is time (usually, pq.s)
        
    NOTE: The following parameters are passed directly to embed_trigger_event
    
    clearSimilarEvents: boolean, default is True: 
        When True, existing neo.Event objects with saame time stamps, labels,
            units and name as those of the parameter "event" will be removed. 
            In case of TriggerEvent objects the comparison also considers the 
            event type.
            
        NOTE: 2019-03-16 12:06:14
        When "event" is a TriggerEvent, this will clear ONLY the pre-exising
        TriggerEvent objects of the same type as "event" 
        (see datatypes.TriggerEventType for details)
        
    clearTriggerEvents: boolean, default is True
        when True, clear ALL existing TriggerEvent objects
        
        NOTE: 2019-03-16 12:06:07
        to clear ONLY existing TriggerEvent objects with the same type
            as the "event" (when "event" is also a TriggerEvent) 
            set clearSimilarEvents to True; see NOTE: 2019-03-16 12:06:14
    
    clearAllEvents: boolean, default is False:
        When True, clear ANY existing event in the segment.
        
    Returns:
    ========
    The src parameter (a reference)
    
    Side effects:
        Creates and appends TriggerEvent objects to the segments in src
    """
    from . import datatypes as dt
    
    if isinstance(src, neo.Block):
        data = src.segments
        
    elif isinstance(src, (tuple, list)) and all([isinstance(s, neo.Segment) for s in src]):
        data = src
        
    elif isinstance(src, neo.Segment):
        data = [src]
        
    else:
        raise TypeError("src expected to be a neo.Block, neo.Segment or a sequence of neo.Segment objects; got %s instead" % type(src).__name__)
    
    #print("auto_define_trigger_events in %s" % type(src))
    
    if isinstance(times, pq.Quantity):
        if not dt.check_time_units(times):  # event times passed at function call -- no detection is performed
            raise TypeError("times expected to have time units; it has %s instead" % times.units)

        for segment in data: # construct eventss, store them in segments
            event = TriggerEvent(times=times, units=times.units,
                                    event_type=event_type, labels=label, 
                                    name=name)
            
            embed_trigger_event(event, segment,
                                clearTriggerEvents = clearTriggerEvents,
                                clearSimilarEvents = clearSimilarEvents,
                                clearAllEvents = clearAllEvents)
            
    elif times is None: #  no event times specified =>
        # auto-detect trigger events from signal given by analog_index
        if isinstance(analog_index, str):
            # signal specified by name
            analog_index = get_index_of_named_signal(data, analog_index)
            
        if isinstance(analog_index, (tuple, list)):
            if all(isinstance(s, (int, str)) for s in analog_index):
                if len(analog_index) != len(data):
                    raise TypeError("When a list of int, analog_index must have as many elements as segments in src (%d); instead it has %d" % (len(data), len(analog_index)))
                
                for (s, ndx) in zip(data, analog_index):
                    if isinstance(ndx, str):
                        sndx = get_index_of_named_signal(s, ndx, silent=True)
                        
                    else:
                        sndx = ndx
                        
                    if sndx in range(len(s.analogsignals)):
                        if isinstance(time_slice, (tuple, list)) \
                            and all([isinstance(t, pq.Quantity) and dt.check_time_units(t) for t in time_slice]) \
                                and len(time_slice) == 2:
                            event = detect_trigger_events(s.analogsignals[sndx].time_slice(time_slice[0], time_slice[1]), 
                                                        event_type=event_type, 
                                                        use_lo_hi=use_lo_hi, 
                                                        label=label, name=name)
                            
                        else:
                            event = detect_trigger_events(s.analogsignals[sndx], 
                                                        event_type=event_type, 
                                                        use_lo_hi=use_lo_hi, 
                                                        label=label, name=name)
                            
                        embed_trigger_event(event, s, 
                                            clearTriggerEvents = clearTriggerEvents,
                                            clearSimilarEvents = clearSimilarEvents,
                                            clearAllEvents = clearAllEvents)
                        
                    else:
                        raise ValueError("Invalid signal index %d for a segment with %d analogsignals" % (ndx, len(s.analogsignals)))

        elif isinstance(analog_index, int):
            for s in data:
                if analog_index in range(len(s.analogsignals)):
                    if isinstance(time_slice, (tuple, list)) \
                        and all([isinstance(t, pq.Quantity) and dt.check_time_units(t) for t in time_slice]) \
                            and len(time_slice) == 2:
                        event = detect_trigger_events(s.analogsignals[analog_index].time_slice(time_slice[0], time_slice[1]), 
                                                      event_type=event_type, 
                                                      use_lo_hi=use_lo_hi, 
                                                      label=label, name=name)
                        
                    else:
                        event = detect_trigger_events(s.analogsignals[analog_index], 
                                                      event_type=event_type, 
                                                      use_lo_hi=use_lo_hi, 
                                                      label=label, name=name)
                        
                    embed_trigger_event(event, s, 
                                        clearTriggerEvents = clearTriggerEvents,
                                        clearSimilarEvents = clearSimilarEvents,
                                        clearAllEvents = clearAllEvents)
                    
                else:
                    raise ValueError("Invalid signal index %d for a segment with %d analogsignals" % (analog_index, len(s.analogsignals)))
                
        else:
            raise RuntimeError("Invalid signal index %s" % str(analog_index))

    else:
        raise TypeError("times expected to be a python Quantity array with time units, or None")
                
                
    return src
        
def clear_events(src, triggersOnly=False, triggerType=None):
    """Shorthand for clearing neo.Event objects embedded in src.
    
    This includes TriggerEvent objects!
    
    e.g. [s.events.clear() for s in src.segments] where src is a neo.Block
    
    Parameters:
    ===========
    
    src: a neo.Block, or a neo.Segment, or a list of neo.Segment objects
    
    Keyword parameters:
    ==================
    
    triggersOnly: boolean, default is False
        When True, only removes datatypes.TriggerEvent objects (these inherit neo.Event)
    
    triggerType: None (default) or a valid datatypes.TriggerEventType
    
        When a TriggerEventType, only TriggerEvent objects of the specified type will be
        removed (triggersOnly will be implied to be True)
    
    
    """
    from . import datatypes as dt

    if isinstance(src, neo.Block):
        target = src.segments
        #[s.events.clear() for s in src.segments];
        
    elif isinstance(src, (tuple, list)) and all([isinstance(s, neo.Segment) for s in src]):
        target = src
        #[s.events.clear() for s in src]
        
    elif isinstance(src, neo.Segment):
        target = [src]
        #src.events.clear()
        
    else:
        raise TypeError("Expecting a neo.Block, a neo.Segment or a sequence of neo.Segment objects; got %s instead" % type(src).__name__)
    
    for s in target:
        all_events_ndx = range(len(s.events))
        
        trigs = []
        
        if isinstance(triggerType, TriggerEventType):
            trigs = [(endx, e) for (endx, e) in enumerate(s.events) if isinstance(e, TriggerEvent) and e.type & triggerType]
            
        elif triggersOnly:
            trigs = [(endx, e) for (endx, e) in enumerate(s.events) if isinstance(e, TriggerEvent)]

        if len(trigs):
            (endx, evs) = zip(*trigs)
            
            keep_events = [s.events[k] for k in all_events_ndx if k not in endx]
            
            s.events[:] = keep_events
            
        else:
            s.events.clear()
                
@safeWrapper
def get_non_empty_events(sequence:(tuple, list)):
    from . import datatypes as dt

    if len(sequence) == 0:
        return list()
    
    if not all([isinstance(e, (neo.Event, TriggerEvent)) for e in sequence]):
        raise TypeError("Expecting a sequence containing only neo.Event or datatypes.TriggerEvent objects")
    
    return [e for e in sequence if len(e)]

@safeWrapper
def get_non_empty_spike_trains(sequence:(tuple, list)):
    if len(sequence) == 0:
        return list()
    
    if not all([isinstance(e, neo.SpikeTrain) for e in sequence]):
        raise TypeError("Expecting a sequence containing only neo.SpikeTrain objects")
    
    return [s for s in sequence if len(s)]
    
@safeWrapper
def get_non_empty_epochs(sequence:(tuple, list)):
    if len(sequence) == 0:
        return list()
    
    if not all([isinstance(e, neo.Epoch) for e in sequence]):
        raise TypeError("Expecting a sequence containing only neo.Epoch objects")
    
    return [e for e in sequence if len(e)]
    
    
@safeWrapper
def detect_trigger_events(x, event_type, use_lo_hi=True, label=None, name=None):
    """Creates a datatypes.TriggerEvent object (array) of specified type.
    
    Calls detect_trigger_times(x) to detect the time stamps.
    
    Parameters:
    ===========
    
    x: neo.AnalogSsignal
    
    event_type: a datatypes.TriggerEventType enum value or datatypes.TriggerEventType name (str)
    
    Named parameters:
    ================
    use_lo_hi: boolean, optional (default is True): 
    
        The datatypes.TriggerEvent objects will be created from low -> high 
        state transition times when "use_lo_hi" is True, otherwise from the 
        high -> low state transition times.
            
    label: str, optional (default None): the labels for the events in the 
        datatypes.TriggerEvent array
    
    name: str, optional (default  None): the name of the generated 
        datatypes.TriggerEvent array
    
    Returns:
    ========
    
    A datatypes.TriggerEvent object (essentially an array of time stamps)
    
    """
    from . import datatypes as dt
    
    if not isinstance(x, (neo.AnalogSignal, DataSignal, np.ndarray)):
        raise TypeError("Expecting a neo.AnalogSignal, or a datatypes.DataSignal, or a np.ndarray as first parameter; got %s instead" % type(x).__name__)
    
    if isinstance(event_type, str):
        if event_type in list(TriggerEventType.__members__.keys()):
            event_type = TriggerEventType[event_type]
            
        else:
            raise (ValueError("unknown trigger event type: %s; expecting one of %s" % event_type, " ".join(list([TriggerEventType.__members__.keys()]))))
        
    elif not isinstance(event_type, TriggerEventType):
        raise TypeError("'event_type' expected to be a datatypes.TriggerEventType enum value, or a str in datatypes.TriggerEventType enum; got %s instead" % type(event_type).__name__)

    if label is not None and not isinstance(label, str):
        raise TypeError("'label' parameter expected to be a str or None; got %s instead" % type(label).__name__)
    
    if name is not None and not isinstance(name, str):
        raise TypeError("'name' parameter expected to be a str or None; got %s instead" % type(name).__name__)
    
    if not isinstance(use_lo_hi, bool):
        raise TypeError("'use_lo_hi' parameter expected to be a boolean; got %s instead" % type(use_lo_hi).__name__)
    
    [lo_hi, hi_lo] = detect_trigger_times(x)
    
    if use_lo_hi:
        times = lo_hi
        
    else:
        times = hi_lo
        
    trig = TriggerEvent(times=times, units=x.times.units, event_type=event_type, labels=label, name=name)
    
    if name is None:
        if label is not None:
            trig.name = "%d%s" % (trig.times.size, label)
            
        else:
            if np.all(trig.labels == trig.labels[0]):
                trig.name = "%d%s" % (trig.times.size, label)
                
            else:
                trig.name = "%dtriggers" % trig.times.size
                
    
    return trig
    
    
def root_mean_square(x, axis = None):
    """ Computes the RMS of a signal.
    
    Positional parameters
    =====================
    x = neo.AnalogSignal, neo.IrregularlySampledSignal, or datatypes.DataSignal
    
    Named parameters
    ================
    
    axis: None (defult), or a scalar int, or a sequence of int: index of the axis,
            in the interval [0, x.ndim), or None (default)
            
            When a sequence of int, the RMS will be calculated across all the
            specified axes
    
        When None (default) the RMS is calculated for the flattened signal array.
        
        This argument is passed on to numpy.mean
        
    Returns: a scalar float
    RMS = sqrt(mean(x^2))
    
    """
    from . import datatypes as dt
    
    if not isinstance(x, (neo.AnalogSignal, neo.IrregularlySampledSignal, DataSignal)):
        raise TypeError("Expecting a neo.AnalogSignal, neo.IrregularlySampledSignal, or a datatypes.DataSignal; got %s instead" % type(x).__name__)
    
    if not isinstance(axis, (int, tuple, list, type(None))):
        raise TypeError("axis expected to be an int or None; got %s instead" % type(axis).__name__)
    
    if isinstance(axis, (tuple, list)):
        if not all([isinstance(a, int) for a in axis]):
            raise TypeError("Axis nindices must all be integers")
        
        if any([a < 0 or a > x.ndim for a in axis]):
            raise ValueError("Axis indices must be inthe interval [0, %d)" % x.ndim)
    
    if isinstance(axis, int):
        if axis < 0 or axis >= x.ndim:
            raise ValueError("Invalid axis index; expecting value between 0 and %d ; got %d instead" % (x.ndim, axis))
        
    return np.sqrt(np.mean(np.abs(x), axis=axis))
    
def signal_to_noise(x, axis=None, ddof=None, db=True):
    """Calculates SNR for the given signal.
    
    Positional parameters:
    =====================
    x = neo.AnalogSignal, neo.IrregularlySampledSignal, or datatypes.DataSignal
    
    Named parameters
    ================
    
    axis: None (defult), or a scalar int, or a sequence of int: index of the axis,
            in the interval [0, x.ndim), or None (default)
            
            When a sequence of int, the RMS will be calculated across all the
            specified axes
    
        When None (default) the RMS is calculated for the flattened signal array.
        
        This argument is passed on to numpy.mean and numpy.std
        
    ddof: None (default) or a scalar int: delta degrees of freedom
    
        When None, it sill be calculated from the size of x along the specified axes
        
        ddof is passed onto numpy.std (see numpy.std for details)
        
    db: boolean, default is True
        When True, the result is expressed in decibel (10*log10(...))
        
    """
    from . import datatypes as dt

    if not isinstance(x, (neo.AnalogSignal, neo.IrregularlySampledSignal, DataSignal)):
        raise TypeError("Expecting a neo.AnalogSignal, neo.IrregularlySampledSignal, or a datatypes.DataSignal; got %s instead" % type(x).__name__)
    
    if not isinstance(axis, (int, tuple, list, type(None))):
        raise TypeError("axis expected to be an int or None; got %s instead" % type(axis).__name__)
    
    if isinstance(axis, (tuple, list)):
        if not all([isinstance(a, int) for a in axis]):
            raise TypeError("Axis nindices must all be integers")
        
        if any([a < 0 or a > x.ndim for a in axis]):
            raise ValueError("Axis indices must be inthe interval [0, %d)" % x.ndim)
    
    if isinstance(axis, int):
        if axis < 0 or axis >= x.ndim:
            raise ValueError("Invalid axis index; expecting value between 0 and %d ; got %d instead" % (x.ndim, axis))
        
    if not isinstance(ddof, (int, type(None))):
        raise TypeError("ddof expected to be an int or None; got %sinstead" % ype(ddof).__name__)
    
    if ddof is None:
        if axis is None:
            ddof = 1
            
        elif isinstance(axis, int):
            ddof = 1
            
        else:
            ddof = len(axis)
            
    else:
        if ddof < 0:
            raise ValueError("ddof must be >= 0; got %s instead" % ddof)
        
        
    rms = root_mean_square(x, axis=axis)
    
    std = np.std(x, axis=axis, ddof=ddof)
    
    ret = rms/std
    
    if db:
        return np.log10(ret.magnitude.flatten()) * 20 
    
    return ret
    
            



#@safeWrapper
def detect_trigger_times(x):
    """Detect and returns the time stamps of rectangular pulse waveforms in a neo.AnalogSignal
    
    The signal must undergo at least one transition between two distinct states 
    ("low" and "high").
    
    The function is useful in detecting the ACTUAL time of a trigger (be it 
    "emulated" in the ADC command current/voltage or in the digital output "DIG") 
    when this differs from what was intended in the protocol (e.g. in Clampex)
    """
    from scipy import cluster
    from scipy import signal
    
    #flt = signal.firwin()
    
    if not isinstance(x, neo.AnalogSignal):
        raise TypeError("Expecting a neo.AnalogSignal object; got %s instead" % type(x).__name__)
    
    # WARNING: algorithm fails for noisy signls with no TTL waveform!
    cbook, dist = cluster.vq.kmeans(x, 2)
    
    #print("code_book: ", cbook)
    
    #print("sorted code book: ", sorted(cbook))
    
    code, cdist = cluster.vq.vq(x, sorted(cbook))
    
    diffcode = np.diff(code)
    
    ndx_lo_hi = np.where(diffcode ==  1)[0].flatten() # transitions from low to high
    ndx_hi_lo = np.where(diffcode == -1)[0].flatten() # hi -> lo transitions
    
    if ndx_lo_hi.size:
        times_lo_hi = [x.times[k] for k in ndx_lo_hi]
        
    else:
        times_lo_hi = None
        
    if ndx_hi_lo.size:
        times_hi_lo = [x.times[k] for k in ndx_hi_lo]
        
    else:
        times_hi_lo = None
        
    return times_lo_hi, times_hi_lo

def remove_trigger_protocol(protocol, block):
    from . import datatypes as dt

    if not isinstance(protocol, TriggerProtocol):
        raise TypeError("'protocol' expected to be a TriggerProtocol; got %s instead" % type(protocol).__name__)
    
    if not isinstance(block, neo.Block):
        raise TypeError("'block' was expected to be a neo.Block; got % instead" % type(block).__name__)
    
    if len(protocol.segmentIndices()) > 0:
        protocol_segments = protocol.segmentIndices()
        
    else:
        protocol_segments = range(len(block.segments))
        
    for k in protocol_segments:
        if k >= len(block.segments):
            warnings.warn("skipping segment index %d of protocol %s because it points outside the list of segments with %d elements" % (k, protocol.name, len(block.segments)), 
                          RuntimeWarning)
            continue
        
        if k < 0:
            warnings.warn("skipping negative segment index %d in protocol %s" % (k, protocol.name), RuntimeWarning)
            continue
        
        for event in protocol.events:
            remove_events(event, block.segments[k])
        
        block.segments[k].annotations.pop("trigger_protocol", None)
                
def modify_trigger_protocol(protocol, block):
    """
    Uses the events in the protocol to add TriggerEvents or modify exiting ones,
    in the segment indices specified by this protocol's segment indices.
    """
    from . import datatypes as dt

    if not isinstance(protocol, TriggerProtocol):
        raise TypeError("'value' expected to be a TriggerProtocol; got %s instead" % type(value).__name__)
    
    if not isinstance(block, neo.Block):
        raise TypeError("'block' was expected to be a neo.Block; got % instead" % type(block).__name__)
    
    if len(protocol.segmentIndices()) > 0:
        protocol_segments = protocol.segmentIndices()
        
    else:
        protocol_segments = range(len(block.segments))
        
    for k in protocol_segments:
        if k >= len(block.segments):
            warnings.warn("skipping segment index %d of protocol %s because it points outside the list of segments with %d elements" % (k, protocol.name, len(block.segments)), 
                          RuntimeWarning)
            continue
        
        if k < 0:
            warnings.warn("skipping negative segment index %d in protocol %s" % (k, protocol.name), RuntimeWarning)
            continue
        
        # check if the segment has any events of the type found in the protocol
        # remove them and add the protocol's events instead
        # NOTE: ONE segment -- ONE protocol at all times.
        if isinstance(protocol.presynaptic, TriggerEvent) and protocol.presynaptic.event_type == TriggerEventType.presynaptic:
            presynaptic_events = [e for e in block.segments[k].events if isinstance(e, TriggerEvent) and e.event_type == TriggerEventType.presynaptic]
            
            for event in presynaptic_events:
                # should contain AT MOST ONE event object
                block.segments[k].events.remove(event)
                
            block.segments[k].events.append(protocol.presynaptic)
                
        if isinstance(protocol.postsynaptic, TriggerEvent) and protocol.postsynaptic.event_type == TriggerEventType.postsynaptic:
            postsynaptic_events = [e for e in block.segments[k].events if isinstance(e, TriggerEvent) and e.event_type == TriggerEventType.postsynaptic]
            
            for event in postsynaptic_events:
                block.segments[k].events.remove(event)
                
            block.segments[k].events.append(protocol.postsynaptic)
            
            
        if isinstance(protocol.photostimulation, TriggerEvent) and protocol.photostimulation.event_type == TriggerEventType.photostimulation:
            photostimulation_events = [e for e in block.segments[k].events if isinstance(e, TriggerEvent) and e.event_type == TriggerEventType.photostimulation]
            
            for event in photostimulation_events:
                block.segments[k].events.remove(event)
                
            block.segments[k].event.append(protocol.photostimulation)
            
        if len(protocol.acquisition):
            for event in protocol.acquisition:
                existing_events = [e for e in block.segments[k].events if isinstance(e, TriggerEvent) and e.event_type == event.event_type]
                
                for e in existing_events:
                    block.segments[k].events.remove(e)
                    
                block.segments[k].events.append(event)
                
        if isinstance(protocol.name, str) and len(protocol.name.strip()) > 0:
            pr_name = protocol.name
            
        else:
            pr_name = "unnamed_protocol"
            
        block.segments[k].annotations["trigger_protocol"] = pr_name
        
def remove_events(event, segment, byLabel=True):
    """Rremoves an event from the neo.Segment "segment"
    
    Parameters:
    ==========
    event: a neo.Event, an int, a str or a datatypes.TriggerEventType.
    
        When a neo.Event (or TriggerEvent), the functions remove the reference 
        to that event, if found, or any event that is identical to the specified 
        one, if found.
        NOTE: two event objects can have identical time stamps, labels,
        names, units, and in the case of TriggerEvent, event type, even if they
        are distinct Python objects (e.g., one is a deep copy of the other).
        
        When an int, the function removes the event at index "event" in the
            segment's events list (if the index is valid)
            
        When a str, the function removes _ALL_ the events for having either the
            label (if byLabel is True) or name (is byLabel is False) equal to 
            the "event" parameter, if such events are found in the segment.
            
        When a TriggerEventType, _ALL_ TriggerEvent objects of this type will be
        removed, if found.
            
    Keyword parameters:
    ==================
    byLabel: boolean default True. Used when event is a str (see above)
        
        When True, _ALL_ events with label given by "event" parameter will be removed,
            if found.
            
        Otherwise, _ALL_ events with name given by "event" parameter will be removed,
            if found.
    """
    from . import datatypes as dt

    if not isinstance(segment, neo.Segment):
        raise TypeError("segment expected to be a neo.Segment; got %s instead" % type(segment).__name__)
    
    if len(segment.events) == 0:
        return
    
    if isinstance(event, neo.Event):
        if event in segment.events: # find event reference stored in events list
            evindex = segment.events.index(event)
            del segment.events[evindex]
            
        else: # find events stored in event list that have same attributes as event
            evs = [(k,e) for (k,e) in enumerate(segment.events) if e.is_same_as(event)]
            
            if len(evs):
                (evndx, events) = zip(*evs)
                all_events_ndx = range(len(segment.events))
                
                keep_events = [segment.events[k] for k in all_events_ndx if k not in evndx]
                
                segment.events[:] = keep_events
                
    elif isinstance(event, int):
        if event in range(len(segment.events)):
            del segment.events[event]
            
    elif isinstance(event, str):
        evs = []
        
        if byLabel:
            evs = [(k,e) for (k,e) in segment.events if np.any(e.labels == event)]
            
        else:
            evs = [(k,e) for (k,e) in segment.events if e.name == event]
            
        if len(evs):
            (evndx, events) = zip(*evs)
            all_events_ndx = range(len(segment.events))
            
            keep_events = [segment.events[k] for k in all_events_ndx if k not in evndx]
            
            segment.events[:] = keep_events
            
    elif isinstance(event, TriggerEventType):
        evs = [(k,e) for (k,e) in segment.events if isinstance(e, TriggerEvent) and e.type & event]

        if len(evs):
            (evndx, events) = zip(*evs)
            all_events_ndx = range(len(segment.events))
            
            keep_events = [segment.events[k] for k in all_events_ndx if k not in evndx]
            
            segment.events[:] = keep_events
            
    else:
        raise TypeError("event expected to be a neo.Event, an int, a str or a datatypes.TriggerEventType; got %s instead" % type(event).__name__)
    
        
def embed_trigger_event(event, segment, clearSimilarEvents=True, clearTriggerEvents=True, clearAllEvents=False):
    """
    Embeds the neo.Event object event in the neo.Segment object segment.
    
    In the segment's events list, the event is stored by reference.
    
    WARNING: one could easily append events with identical time stamps!
        While this is NOT recommended, it cannot be easily prevented.
        
        To add time stamps to a TriggerEvent, create a new TriggerEvent object
        by calling use TriggerEvent.append_times() or TriggerEvent.merge() then 
        embed it here.
        
        To add time stamps to a generic neo.Event, create a new Event by calling
        Event.merge() then embed it here.
        
        To remove time stamps ise numpy array indecing on the event.
        
        See datatypes.TriggerEvent for details.
    
    Parameters:
    ===========
    
    event: a neo.Event, or a datatypes.TriggerEvent
    
    segment: a neo.Segment
    
    Named parameters:
    ===================
    
    clearSimilarEvents: boolean, default is True: 
        When True, existing neo.Event objects with saame time stamps, labels,
            units and name as those of the parameter "event" will be removed. 
            In case of TriggerEvent objects the comparison also considers the 
            event type.
            
        NOTE: 2019-03-16 12:06:14
        When "event" is a TriggerEvent, this will clear ONLY the pre-exising
        TriggerEvent objects of the same type as "event" 
        (see datatypes.TriggerEventType for details)
        
    clearTriggerEvents: boolean, default is True
        when True, clear ALL existing TriggerEvent objects
        
        NOTE: 2019-03-16 12:06:07
        to clear ONLY existing TriggerEvent objects with the same type
            as the "event" (when "event" is also a TriggerEvent) 
            set clearSimilarEvents to True; see NOTE: 2019-03-16 12:06:14
    
    clearAllEvents: boolean, default is False:
        When True, clear ANY existing event in the segment.
        
    Returns:
    =======
    A reference to the segment.
    
    """
    from . import datatypes as dt
    
    if not isinstance(event, (neo.Event, TriggerEvent)):
        raise TypeError("event expected to be a neo.Event; got %s instead" % type(event).__name__)
    
    if not isinstance(segment, neo.Segment):
        raise TypeError("segment expected to be a neo.Segment; got %s instead" % type(segment).__name__)
    
    if clearAllEvents:
        segment.events.clear()
        
    else:
        all_events_ndx = range(len(segment.events))
        evs = []
    
        if clearSimilarEvents:
            evs = [(k,e) for (k,e) in enumerate(segment.events) if is_same_as(event, e)]
            
        elif clearTriggerEvents:
            evs = [(k,e) for (k,e) in enumerate(segment.events) if isinstance(e, TriggerEvent)]
            
        if len(evs):
            (evndx, events) = zip(*evs)
            
            keep_events = [segment.events[k] for k in all_events_ndx if k not in evndx]
            
            segment.events[:] = keep_events
            
    segment.events.append(event)
    
    return segment
            
            
#@safeWrapper
def embed_trigger_protocol(protocol, target, useProtocolSegments=True, clearTriggers=True, clearEvents=False):
    """ Embeds TriggerEvent objects found in the TriggerProtocol 'protocol', 
    in the segments of 'target'.
    
    Inside the target, trigger event objects are stored by reference!
    
    Parameters:
    ==========
    protocol: a dataypes.TriggerProtocol object
    
    target: a neo.Block, neo.Segment or a sequence of neo.Segment objects
    
    Keyword parameters:
    ==================
    
    useProtocolSegments: boolean, default True: use the segments indices given by the protocol
        to embed only in those segments in the "target"
        
        when False, "target" is expected to be a sequence of neo.Segments as long as
        the protocol's segmentIndices
        
        this is ignored when "target" is a neo.Block or a neo.Segment
    
    clearTriggers: boolean, default True; when True, existing TriggerEvent obects will be removed
    
    clearEvents: boolean, default False; when True, clear _ALL_ existing neo.Event objects
        (including TriggerEvents!)
    
    CAUTION: This will wipe out existing trigger events in those segments
    indicated by the 'segmentIndices' attribute of 'protocol'.
    """
    from . import datatypes as dt

    # check if there are synaptic events already in the scans data target:
    # each segment can hold at most one TriggerEvent object of each 
    # type (pre-, post-, photo-);
    # NOTE: a TriggerEvent actually holds an ARRAY of time points
    
    if not isinstance(protocol, TriggerProtocol):
        raise TypeError("'protocol' expected to be a TriggerProtocol; got %s instead" % type(protocol).__name__)
    
    if not isinstance(target, (neo.Block, neo.Segment)):
        raise TypeError("'target' was expected to be a neo.Block or neo.Segment; got %s instead" % type(target).__name__)
    
    if isinstance(target, neo.Block):
        segments = target.segments
        
        if len(protocol.segmentIndices()) > 0:
            value_segments = [i for i in protocol.segmentIndices() if i in range(len(segments))]
            value_segments = protocol.segmentIndices()
            
        else:
            value_segments = range(len(segments))
            
        if len(value_segments) == 0:
            warnings.warn("No suitable segment index found in protocol %s with %s, given %d segments in for %s %s" % (protocol.name, protocol.segmentIndices(), len(segments), type(target).__name__, target.name))
            return
        
        
    elif isinstance(target, (tuple, list)) and all([isinstance(s, neo.Segment) for s in target]):
        segments = target
        if not useProtocolSegments:
            if len(segments) != len(protocol.segmentIndices):
                raise ValueError("useProtocolSegments is False, but target has %d segments whereas protocol indicates %d segments" % (len(segments), len(protocol.segmentIndices())))
            
            value_segments = range(len(segments))
            
        else:
            # the list of segments 
            if len(protocol.segmentIndices()) > 0:
                value_segments = [i for i in protocol.segmentIndices() if i in range(len(segments))]
                value_segments = protocol.segmentIndices()
                
            else:
                value_segments = range(len(segments))
            
        if len(value_segments) == 0:
            warnings.warn("No suitable segment index found in protocol %s with %s, given %d segments in for %s %s" % (protocol.name, protocol.segmentIndices(), len(segments), type(target).__name__, target.name))
            return
        
    elif isinstance(target, neo.Segment):
        segments = [target]
        value_segments = [0]
    
    if len(value_segments) == 0:
        warnings.warn("No suitable segment index found in protocol %s with %s, given %d segments in for %s %s" % (protocol.name, protocol.segmentIndices(), len(segments), type(target).__name__, target.name))
        return
        
    #print("embed_trigger_protocol: value_segments ", value_segments, " target segments: %d" % len(target.segments))
        
    for k in value_segments: 
        if clearTriggers:
            trigs = [(evndx, ev) for (evndx, ev) in enumerate(segments[k].events) if isinstance(ev, TriggerEvent)]

            if len(trigs): # TriggerEvent objects found in segment
                (trigndx, trigevs) = zip(*trigs)
                
                all_events_ndx = range(len(segments[k].events))
                
                keep_events = [segments[k].events[i] for i in all_events_ndx if i not in trigndx]
                
                segments[k].events[:] = keep_events
                
        elif clearEvents:
            segments[k].events.clear()
            
        # now go and append events contained in protocol
        
        #print("embed_trigger_protocol: in %s (segment %d): protocol.name %s; acquisition: %s" % (target.name, k, protocol.name, protocol.acquisition))
        
        if isinstance(protocol.acquisition, (tuple, list)) and len(protocol.acquisition):
            # for old API
            segments[k].events.append(protocol.acquisition[0]) # only ONE acquisition event per protocol!
                
        elif isinstance(protocol.acquisition, TriggerEvent):
            segments[k].events.append(protocol.acquisition)
                
        if protocol.presynaptic is not None:
                segments[k].events.append(protocol.presynaptic)
            
        if protocol.postsynaptic is not None:
                segments[k].events.append(protocol.postsynaptic)
            
        if protocol.photostimulation is not None:
                segments[k].events.append(protocol.photostimulation)
                                
        if isinstance(protocol.name, str) and len(protocol.name.strip()) > 0:
            pr_name = protocol.name
            segments[k].name = protocol.name
            
        else:
            pr_name = "unnamed_protocol"
            
        segments[k].annotations["trigger_protocol"] = pr_name

def is_same_as(e1, e2, rtol = 1e-4, atol =  1e-4, equal_nan = True):
    """Returns True if the neo.Events e1 ans e2 have identical time stamps, units, labels and names.
    
    In addition, if e1 and e2 are datatype.TriggerEvents, checks if they have the 
    same type.
    
    Time stamps are compared within a relative and absolute tolerances by
    calling numpy.isclose()
    
    Parameters:
    ==========
    
    e1, e2: neo.Event objects (including datatypes.TriggerEvent)
    
    Keyword parameters:
    ==================
    
    rtol, atol: float values, default for both is 1e-4 (see numpy.isclose())
    
    equal_nan: boolean default is True (see numpy.isclose())
    
    """
    from . import datatypes as dt

    if any([not isinstance(e, neo.Event) for e in (e1,e2)]):
        return False
    
    if all([isinstance(e, TriggerEvent) for e in (e1,e2)]):
        return e1.is_same_as(e2)
    
    compatible_units = e1.units == e2.units
    
    if not compatible_units:
        e1_dim    = pq.quantity.validate_dimensionality(e1.units)
        
        e2_dim   = pq.quantity.validate_dimensionality(e2.units)
        
        if e1_dim != e2_dim:
            try:
                cf = pq.quantity.get_conversion_factor(e2_dim, e1_dim)
                compatible_units = True
                
            except AssertionError:
                compatible_units = False
            
    result = compatible_units
    
    if result:
        result &= e2.times.flatten().size == e1.times.flatten().size
    
    if result:
        result &= np.all(np.isclose(e2.times.magnitude, e1.times.magnitude,
                                    rtol=rtol, atol=atol,equal_nan=equal_nan))
    
    if result: 
        result &= np.all(np.isclose(e2.magnitude, e1.magnitude, 
                                    rtol=rtol, atol=atol, equal_nan=equal_nan))
        
    if result:
        result &= e2.labels.flatten().size == e1.labels.flatten().size
        
    if result:
        result &= np.all(e2.labels.flatten() == e2.labels.flatten)
        
    if result:
        result &= e1.name == e2.name
        
    return result
    
        
def generate_text_stimulus_file(spike_times, start, duration, sampling_frequency, 
                         spike_duration, spike_value, filename,
                         atol=1e-12, rtol=1e-12, skipInvalidTimes=True,
                         maxSweepDuration=None):
    
    spike_trace = generate_spike_trace(spike_times, start, duration, sampling_frequency, 
                         spike_duration, spike_value, asNeoSignal=False)
    
    np.savetxt(filename, spike_trace)
    
    
def generate_ripple_trace(ripple_times, start, duration, sampling_frequency,
                          spike_duration=0.001, spike_value=5000, 
                          spike_count=5, spike_isi=0.01,
                          filename=None, atol=1e-12, rtol=1e-12, 
                          skipInvalidTimes=True):
    """Similar as generate_spike_trace and generate_text_stimulus_file combined.
    
    However, ripple times are the t_start values for ripple events. In turn,
    a ripple event if generated as a short burst of spikes containing 
    spike_count spikes, with spike_isi interval, spike_duration and spike_value.
    
    Positional parameters:
    =====================
    ripple_times: np.array (column vector) of ripple event timings (dimensionless,
                            but values are expected to time in s)
                            
    start: sweep start (dimensonless scalar representing the sweep start time in s)
    
    duration: sweep duration (dimensionless scalar, representing the duration of the sweep in s)
    
    sampling_frequency: dimensionless scalar representing the sampling frequency of the sweep in Hz
    
    Named parameters:
    =================
    spike_duration: float scalar: duration of ONE spike in the ripple-generating burst
        default: 0.001 s
        
    spike_value: float scalar (mV) default 5000
    
    spike_count: int scalar: number of spikes in a ripple event, default 5
    
    spike_isi: float scalar: the inter-spike interval in a ripple event
                (default if 0.01 s)
        
    filename = None (default) or a str (name of file where the trace will be written as ASCII)
    
    atol, rtol, skipInvalidTimes: see generate_spike_trace
    
    """
    
    def __inner_generate_ripples__(t_array, sp_times, t0, t_duration, 
                                 s_freq, skip_invalid, atol_, rtol_):
        
        #print(sp_times)
        #print("t_duration", t_duration)
        
        ripple_trace = np.full_like(t_array, 0.0)
        
        order = int(np.log10(s_freq))
        
        pwr = eval("1e%d" % order)
        
        for k, ripple_time in enumerate(list(sp_times)):
            # generate spike train for one ripple
            #print("k, ripple_time", k, ripple_time)
            if skip_invalid:
                if ripple_time < start or ripple_time > (t0+t_duration):
                    continue
                
            clipped = int(ripple_time * pwr)/pwr
            
            ndx = np.where(np.isclose(t_array, clipped, atol=atol, rtol=rtol))[0]
            
            #print("ndx", ndx)
            
            if ndx.size == 1:
                for k_spike in range(spike_count):
                    
                    stride = int(spike_isi * s_freq) * k_spike
                        
                    spike_index = int(ndx + stride)
                    
                    ripple_trace[spike_index] = spike_value 
            
                    for k in range(int(spike_duration * s_freq)):
                        index = int(spike_index + k)
                        if index < ripple_trace.size:
                            ripple_trace[index] = spike_value
                        
                        
            elif ndx.size == 0:
                raise RuntimeError("spike time %g not found in the times array given start: %g, duration: %g, sampling frequency: %g and tolerances (atol: %g, rtol: %g). \nConsider increasing the tolerances or changing start and /or duration." \
                    % (spike_time, t0, t_duration, s_freq, atol_, rtol_))
            
            else:
                raise RuntimeError("ambiguous spike time found for %g, given start: %g, duration: %g, sampling frequency: %g and tolerances (atol: %g, rtol: %g). \nConsider decreasing the tolerances" \
                    % (spike_time, t0, t_duration, s_freq, atol_, rtol_))
            
        return ripple_trace
            
        
    
    if np.any(np.isnan(ripple_times)):
        raise ValueError("ripple times array cannot contain NaN values")
    
    if duration < np.max(ripple_times):
        warnings.warn("Duration (%s) is less than the maximum spike times (%s)" \
            % (float(duration), float(np.max(ripple_times))), RuntimeWarning)
        
    if start > np.min(ripple_times):
        warnings.warn("Start time (%s) is greater than the minimum spike time (%s)" \
            % (start, float(np.min(ripple_times))), RuntimeWarning)
        
    if spike_isi * sampling_frequency <= 1:
        raise ValueError("Either sampling frequency %g is too small or spike isi %g is too large")
    
    times_array = np.arange(start, start+duration, step=1/sampling_frequency)
    
    print("Generating trace ...")

       
    try:
        ret = __inner_generate_ripples__(times_array, ripple_times, 
                                        start, duration, 
                                        sampling_frequency,
                                        skipInvalidTimes, atol, rtol)
        
        if isinstance(filename, str):
            np.savetxt(filename, ret)
        
    except Exception as e:
        traceback.print_exc()
        return
        
    print("\n ... done")
    
    return ret
    
            
@safeWrapper
def generate_spike_trace(spike_times, start, duration, sampling_frequency, 
                         spike_duration=0.001, spike_value=5000,
                         atol=1e-12, rtol=1e-12, skipInvalidTimes=True,
                         maxSweepDuration=None,
                         asNeoSignal=True, 
                         time_units = pq.s, spike_units=pq.mV,
                         name="Spike trace", description="Synthetic spike trace",
                         **annotations):
    """
    Converts a spike times array file to an AnalogSignal.
    
    A spike times array is a 1D array (column vector) that contains time "stamps"
    (in s)
    
    This kind of data can be loaded from a spike file (ASCII file) that lists the
    values in a single column (which in turn can be created in a spreadsheet program).
    
    To loadsuch a file use np.loadtxt(filename).
    
    Positional parameters:
    =====================
    spike_times: 1D array (float values) of spike times (in s) -- column vector
    start: scalar float = value of start time (in s);
    duration: scalar float = duration of the trace (in s);
    sampling_frequency: scalar float (in Hz)
    
    Named parameters:
    =================
    spike_duration: scalar float (in s), default is 0.001
    spike_value: scalar, default is 5000 (mV)

    atol, rtol: scalar floats: absolute  and relative tolerance, respectively, 
        for locating spike times in a linear time array (default for both: 1e-12)
        
        See np.isclose() for details
        
    skipInvalidTimes: bool (default True)
    
        If True, then invalid times (that fall outside the half-open interval 
        [start..start+duration) ) are skipped.
        
        When False, the function raises an error whenever an invalid time is found
        (see above).
        
    maxSweepDuration: scalar float (in s) or None (default is None)
        if given as a scalar float and the duration exceeds the sweep length
        then a list of analogsignals (one per sweep) will be produced having 
        a duration specified here
        
        
    asNeoSignal: bool (default, False) 
        When False, (the default) the function returns the spike trace as a 1D array
        (column vector).
        
        When True, the function returns the spike trace as a neo.AnalogSignal 
        object, in combination with the next named parameters
        
    NOTE: the following parameters are passed to the neo.AnalogSignal constructor
    and are used only when asNeoSignal is True:
        
    time_units: python Quantity (time, default is pq.s)
    
    spike_units: python Quantity (default is pq.mV)
    
    name: None, or str (default is "Spike trace")
    
    description: None or str (default is "Synthetic spike trace")
    
    Var-keyword parameters:
    ======================
    **annotations -- passed directly to the neo.AnalogSignal constructor
        
    """
    
    def __inner_trace_generate__(t_array, sp_times, t0, t_duration, 
                                 s_freq, skip_invalid, atol_, rtol_):
        
        spike_trace = np.full_like(t_array, 0.0)
        
        order = int(np.log10(s_freq))
        
        pwr = eval("1e%d" % order)
        
        # take a slow for loop version otherwise we'd run out of memory pretty quickly
        # if we were to use numpy broadcasting here
        for k, spike_time in enumerate(sp_times):
            if skip_invalid:
                if spike_time < start or spike_time > (t0 + t_duration):
                    continue
                
            clipped = int(spike_time * pwr) / pwr
            
            ndx = np.where(np.isclose(t_array, clipped, atol=atol_, rtol=rtol_))[0]
            
            if ndx.size == 1:
                spike_trace[int(ndx)] = spike_value # this is just ONE sample
                
                # but the "spike" is a pulse waveform, so go ahead and generate the
                # rest of the waveform, too (for the spike_duration)
                for k in range(int(spike_duration * s_freq)):
                    index = int(ndx) + k
                    if index < spike_trace.size:
                        spike_trace[index] = spike_value
        
            elif ndx.size == 0:
                raise RuntimeError("spike time %g not found in the times array given start: %g, duration: %g, sampling frequency: %g and tolerances (atol: %g, rtol: %g). \nConsider increasing the tolerances or changing start and /or duration." \
                    % (spike_time, t0, t_duration, s_freq, atol_, rtol_))
            
            else:
                raise RuntimeError("ambiguous spike time found for %g, given start: %g, duration: %g, sampling frequency: %g and tolerances (atol: %g, rtol: %g). \nConsider decreasing the tolerances" \
                    % (spike_time, t0, t_duration, s_freq, atol_, rtol_))
            
        return spike_trace
    
    
    #resolution = 1/sampling_frequency
    
    #atol = 1e-12
    
    #rtol = 1e-12
    
    if np.any(np.isnan(spike_times)):
        raise ValueError("spike times array cannot contain NaN values")
    
    if duration < np.max(spike_times):
        warnings.warn("Duration (%s) is less than the maximum spike times (%s)" \
            % (float(duration), float(np.max(spike_times))), RuntimeWarning)
        
    if start > np.min(spike_times):
        warnings.warn("Start time (%s) is greater than the minimum spike time (%s)" \
            % (start, float(np.min(spike_times))), RuntimeWarning)
    
    times_array = np.arange(start, start+duration, step=1/sampling_frequency)
    
    if maxSweepDuration is not None:
        nSweeps = duration//maxSweepDuration
        if duration % maxSweepDuration > 0:
            nSweeps += 1
            
    else:
        nSweeps = 1
    
    result = list()
    
    if nSweeps > 1:
        print("Generating %d traces ..." % nSweeps)

        for k in range(nSweeps):
            start_time = float(k * maxSweepDuration)
            stop_time = float((k+1) * maxSweepDuration)
            
            times_sub_array = times_array[(times_array >= start_time) & (times_array < stop_time)]
            spike_sub_array = spike_times[(spike_times >= start_time) & (spike_times < stop_time)]
            
            try:
                ret = __inner_trace_generate__(times_sub_array, spike_sub_array, 
                                               start_time, maxSweepDuration, 
                                               sampling_frequency,
                                               skipInvalidTimes, atol, rtol)
                
                if asNeoSignal:
                    result.append(neo.AnalogSignal(ret, units=spike_units, 
                                                   t_start = start * time_units,
                                                   sampling_rate=sampling_frequency*pq.Hz,
                                                   name="%s_%d" % (name, k), 
                                                   description=description,
                                                   **annotations))
                    
                else:
                    result.append(ret)
                
            except Exception as e:
                traceback.print_exc()
                print( "In sub  array %d k")
                return
        
        
    
    else:
        print("Generating trace ...")
        
        try:
            ret = __inner_trace_generate__(times_array, spike_times, 
                                            start, duration, 
                                            sampling_frequency,
                                            skipInvalidTimes, atol, rtol)
            
            #print(ret.size)
            
            if asNeoSignal:
                result.append(neo.AnalogSignal(ret, units=spike_units, 
                                                t_start = start * time_units,
                                                sampling_rate=sampling_frequency*pq.Hz,
                                                name=name, 
                                                description=description,
                                                **annotations))
                
            else:
                result.append(ret)
            
        except Exception as e:
            traceback.print_exc()
            return
        
    print("\n ... done")
    
    if len(result) == 1:
        return result[0]
    
    else:
        return result
    
    
@safeWrapper
def parse_trigger_protocols(src):
    """Constructs a list of TriggerProtocol objects by parsing TriggerEvent objects in "src".
    
    Parameters:
    ==========
    "src" can be a neo.Block with a non-empty segments list, or 
        a list of neo.Segments, or just a neo.Segment
        
    Returns:
    =======
    A list of protocols
    src
        
    ATTENTION: this constructs TriggerProtocol objects with default names.
    Usually this is NOT what you want !!!
    
    Individual TriggerEvent objects can be manually appended to the events 
        list of each neo.Segment.
    
    Alternatively, the function detect_trigger_times() in "neoutils" module can 
    help generate TriggerEvent objects from particular neo.AnalogSignal arrays
    containing recorded trigger-like data (with transitions between a low and 
    a high state, e.g. rectangular pulses, or step functions).
    
    Returns an empty list if no trigger events were found.
    
    NOTE: each segment in "src" can have at most ONE protocol
    
    NOTE: each protocol can have at most one event for each event type in 
        presynaptic, postsynaptic, and photostimulation
    
    NOTE: each event object CAN contain more than one time stamp  (i.e. a 
        pq.Quantity array -- which in fact derives from np.ndarray)
    
    NOTE: several segments CAN have the same protocol!
    
    Once generated, the TriggerProtocol objects should be stored somewhere, for 
    example in the "annotations" dictoinary of the block or segment so that they
    won't have to be recreated (especially when their names/event time stamps
    will have been customized at later stages)
    
    CAUTION: The TriggerEvent objects in the protocols are COPIES of those found
        in "src". This means that any permissible modification brought to the 
        events in the TriggerProtocol is NOT reflected in the events of the source
        "src".
        
        To enable this, call embed_trigger_protocol() by using:
            each protocol in the result list
            "src" as target
            clearTriggers parameter set to True
    
        NOTE: Permissible modifications to TriggerEvents are changes to their 
            labels, names, and units. These will be reflected in the embedded
            events whenn they are stored by reference.
        
            Event time stamps can only be changed by creating an new TriggerEvent.
            To reflect time stamp changes in the "src" events, call remove_events()
            then embed_trigger_event() for the particular event and neo.Segment 
            in "src".
            
        
    """
    from . import datatypes as dt
    
    def __compose_protocol__(events, protocol_list, index = None):
        """
        events: a list of TriggerEvent objects
        
        protocol: TriggerProtocol or None (default); 
            when a trigger protocol, just update it (especially the segment indices)
            else: create a new TriggerProtocol
            
        segment_index: int or None (default): index of segment in the collection; will
            be appended to the protocol's segment indices
            
            When None the protocol's segment indices will not be changed
        
        """
        from . import datatypes as dt

        pr_names = []
        pr_first = []
            
        imaq_names = []
        imaq_first = []
        
        protocol = TriggerProtocol() # name = protocol_name)
        
        for e in events:
            if e.event_type == TriggerEventType.presynaptic:
                if protocol.presynaptic is None:
                    protocol.presynaptic = e
                    
                    pr_names.append(e.name)
                    pr_first.append(e.times.flatten()[0])
                    
                else:
                    warnings.warn("skipping presynaptic event array %s as protocol %s has already got one (%s)" % (e, protocol.name, protocol.presynaptic))
                    
            elif e.event_type == TriggerEventType.postsynaptic:
                if protocol.postsynaptic is None:
                    protocol.postsynaptic = e

                    pr_names.append(e.name)
                    pr_first.append(e.times.flatten()[0])
                        
                    
                else:
                    warnings.warn("skipping postsynaptic event array %s as protocol %s has already got one (%s)" % (e, protocol.name, protocol.postsynaptic))
                    
            elif e.event_type == TriggerEventType.photostimulation:
                if protocol.photostimulation is None:
                    protocol.photostimulation = e

                    pr_names.append(e.name)
                    pr_first.append(e.times.flatten()[0])
                    
                else:
                    warnings.warn("skipping photostimulation event array %s as protocol %s has already got one (%s)" % (e, protocol.name, protocol.photostimulation))
                    
            elif e.event_type & TriggerEventType.acquisition:
                # NOTE: only ONE acquisition trigger event per segment!
                if isinstance(protocol.acquisition, (tuple, list)) and len(protocol.acquisition) == 0: # or e not in protocol.acquisition:
                    protocol.acquisition[:] = [e]
                    
                else:
                    protocol.acquisition = e

                imaq_names.append(e.name)
                imaq_first.append(e.times.flatten()[0])
                
                if e.event_type == TriggerEventType.imaging_frame:
                    protocol.imagingDelay = e.times.flatten()[0]
                
        # NOTE 2017-12-16 10:08:20 DISCARD empty protocols
        if len(protocol) > 0: 
            # assign names differently if only imaging events are present
            if len(pr_first) > 0 and len(pr_first) == len(pr_names):
                plist = [(k, t,name) for k, (t, name) in enumerate(zip(pr_first, pr_names))]
                
                plist.sort()
                
                pr_names = [name_ for k, p, name_ in plist]
                
            elif len(imaq_names) > 0 and len(imaq_first) == len(imaq_names):
                plist = [(k,t,name) for k, (t,name) in enumerate(zip(imaq_first, imaq_names))]
                plist.sort()
                
                pr_names = [name_ for k, p, name_ in plist]
                    
            protocol.name = " ".join(pr_names)
            
            if isinstance(index, int):
                protocol.__segment_index__ = [index]
            
            if len(protocol_list) == 0:
                protocol_list.append(protocol)
                
            else:
                pp = [p_ for p_ in protocol_list if p_.hasSameEvents(protocol) and p_.imagingDelay == protocol.imagingDelay]
                
                if len(pp):
                    for p_ in pp:
                        p_.updateSegmentIndex(protocol.segmentIndices())
                        
                else:
                    protocol_list.append(protocol)
        
    protocols = list()
    
    if isinstance(src, neo.Block):
        # NOTE: 2019-03-14 22:01:20
        # trigs is a sequence of tuples: (index, sequence of TriggerEvent objects)
        # segments without events are skipped
        # segment events that are NOT TriggerEvent objects are skipped
        trigs = [ (k, [e for e in s.events if isinstance(e, TriggerEvent)]) \
                        for k,s in enumerate(src.segments) if len(s.events)]
        
        if len(trigs) == 0:
            return protocols, src
        
        for (index, events) in trigs:
            __compose_protocol__(events, protocols, index=index)
            
        if len(protocols):
            for p in protocols:
                for s in p.segmentIndices():
                    src.segments[s].annotations["trigger_protocol"] = p.name
        
    elif isinstance(src, neo.Segment):
        trigs = [e for e in src.events if isinstance(e, TriggerEvent)]
        
        if len(trigs) == 0:
            return protocols, src
        
        __compose_protocol__(trigs, protocols, index=0)
        
        if len(protocols):
            src.annotations["trigger_protocol"] = protocols[0].name
                
    elif isinstance(src, (tuple, list) and all([isinstance(v, neo.Segment) for v in src])):
        trigs = [ (k, [e for e in s.events if isinstance(e, TriggerEvent)]) \
                        for k,s in enumerate(src) if len(s.events)]
        
        if len(trigs) == 0:
            return protocols, src
        
        for (index, events) in trigs:
            __compose_protocol__(events, protocols, index)
            
        if len(protocols):
            for p in protocols:
                for f in p.segmentIndices():
                    src[f].annotations["trigger_protocol"] = p.name
                
    else:
        raise TypeError("src expected to be a neo.Block, neo.Segment, or a sequence of neo.Segment objects; got %s instead" % type(src).__name__)
            
    return protocols, src

def sampling_rate_or_period(rate, period):
    """
    Get sampling rate period, or period from rate, or checks that they are
    the inverse of each other.
    
    Parameters:
    ----------
    rate, period: None or Quantity. They cannot both be None.
    
    Returns:
    -------
    
    rate as 1/period when rate is None
    
    period as 1/rate when period is None
    
    a bool when both rate and period are supplied (simply verifies they are the inverse of each other)
    
    see also neo.core.analogsignal._get_sampling_rate
    """
    if period is None:
        if rate is None:
            raise TypeError("Expecting either rate or period, at least")
        
        period = 1.0 /rate
        
        return period
        
    elif rate is None:
        if period is None:
            raise TypeError("Expecting either rate or period, at least")
            
        rate = 1.0 / period
        
        return rate
        
    else:
        return np.isclose(period, 1.0 / rate)
    
    if not hasattr(rate, "units"):
        raise TypeError("Sampling rate or period must have units")
    
    return rate
        

def set_relative_time_start(data, t = 0 * pq.s):
    """
    TODO: propagate to other members of a segment as well 
    (IrregularlySampledSignal, epochs, spike trains, etc)
    """
    from . import datatypes as dt

    if isinstance(data, neo.Block):
        for segment in data.segments:
            #for epoch in segment.epochs:
                #epoch.times = epoch.times-segment.analogsignals[0].t_start + t
                
            #for sptrain in segment.spiketrains:
                #sptrain.times = sptrain.times-segment.analogsignals[0].t_start + t
                
            #for evt in segment.events:
                #evt.times  = evt.times - segment.analogsignals[0].t_start + t
                
            for isig in segment.irregularlysampledsignals:
                isig.times = isig.times-segment.analogsignals[0].t_start + t
                
            for signal in segment.analogsignals:
                signal.t_start = t
                
            try:
                new_epochs = list()
                
                for epoch in segment.epochs:
                    if epoch.times.size > 0:
                        new_times = epoch.times - epoch.times[0] + t
                        
                    else:
                        new_times = epoch.times
                        
                    new_epoch = neo.Epoch(new_times,
                                          durations = epoch.durations,
                                          labels = epoch.labels,
                                          units = epoch.units,
                                          name=epoch.name)
                    
                    new_epoch.annotations.update(epoch.annotations)
                    
                    new_epochs.append(new_epoch)
                    
                segment.epochs[:] = new_epochs
                    
                new_trains = list()
                
                for spiketrain in segment.spiketrains:
                    if spiketrain.times.size > 0:
                        new_times = spiketrain.times - spiketrain.times[0] + t
                        
                    else:
                        new_times = spiektrain.times
                        
                    new_spiketrain = neo.SpikeTrain(new_times, 
                                                    t_start = spiketrain.t_start - spiketrain.times[0] + t,
                                                    t_stop = spiketrain.t_stop - spiketrain.times[0] + t,
                                                    units = spiketrain.units,
                                                    waveforms = spiketrain.waveforms,
                                                    sampling_rate = spiketrain.sampling_rate,
                                                    name=spiketrain.name,
                                                    description=spiketrain.description)
                    
                    new_spiketrain.annotations.update(spiketrain.annotations)
                        
                    new_trains.append(spiketrain)
                        
                segment.spiketrains[:] = new_trains
                    
                new_events = list()
                
                for event in segment.events:
                    new_times = event.times - event.times[0] + t if event.times.size > 0 else event.times
                    
                    if isinstance(event, TriggerEvent):
                        new_event = TriggerEvent(times = new_times,
                                                    labels = event.labels,
                                                    units = event.units,
                                                    name = event.name,
                                                    description = event.description,
                                                    event_type = event.event_type)
                    else:
                        new_event = neo.Event(times = new_times,
                                              labels = event.labels,
                                              units = event.units,
                                              name=event.name,
                                              description=event.description)
                        
                        new_event.annotations.update(event.annotations)
                        
                    new_events.append(new_event)

                    #if event.times.size > 0:
                        #event.times = event.times - event.times[0] + t
                        
                segment.events[:] = new_events
            
            except Exception as e:
                traceback.print_exc()
                
    elif isinstance(data, (tuple, list)):
        if all([isinstance(x, neo.Segment) for x in data]):
            for s in data:
                for isig in s.irregularlysampledsignals:
                    isig.times = isig.times-segment.analogsignals[0].t_start + t
                    
                for signal in s.analogsignals:
                    signal.t_start = t
                    
                for epoch in s.epochs:
                    epoch.times = epoch.times - epoch.times[0] + t
                    
                for strain in s.spiketrains:
                    strain.times = strain.times - strain.times[0] + t
                    
                for event in s.events:
                    event.times = event.times - event.times[0] + t
                
        elif all([isinstance(x, (neo.AnalogSignal, DataSignal)) for x in data]):
            for s in data:
                s.t_start = t
                
        elif all([isinstance(x, (neo.IrregularlySampledSignal, IrregularlySampledDataSignal))]):
            for s in data:
                s.times = s.times - s.times[0] + t
                
        elif all([isinstance(x, (neo.SpikeTrain, neo.Event, neo.Epoch))]):
            for s in data:
                s.times = s.times - s.times[0] + t
                    
                
    elif isinstance(data, neo.Segment):
        #for epoch in data.epochs:
            #epoch.times = epoch.times-data.analogsignals[0].t_start + t
            
        #for sptrain in data.spiketrains:
            #sptrain.times = sptrain.times-data.analogsignals[0].t_start + t
            
        #for evt in data.events:
            #evt.times  = evt.times - data.analogsignals[0].t_start + t
            
        for isig in data.irregularlysampledsignals:
            isig.times = isig.times-data.analogsignals[0].t_start + t
            
        for signal in data.analogsignals:
            signal.t_start = t
            
        for epoch in data.epochs:
            epoch.times = epoch.times - epoch.times[0] + t
            
        for strain in data.spiketrains:
            strain.times = strain.times - strain.times[0] + t
            
        for event in data.events:
            event.times = event.times - event.times[0] + t
                
    elif isinstance(data, (neo.AnalogSignal, DataSignal)):
        data.t_start = t
        
    elif isinstance(data, (neo.IrregularlySampledSignal, IrregularlySampledDataSignal)):
        data.times = data.times - data.times[0] + t
        
    elif isinstance(data, (neo.SpikeTrain, neo.Event, neo.Epoch)):
        data.times = data.times = data.times[0] + t
        #pass # TODO
        
    else:
        raise TypeError("Expecting a neo.Block, neo.Segment, neo.AnalogSignal or datatypes.DataSignal; got %s instead" % type(data).__name__)
        
        
    return data

def lookup(signal, value, channel=0, rtol=1e-05, atol=1e-08, equal_nan = False, right=False):
    """Lookup signal values for given domain value(s).
    
    Parameters:
    ----------
    signal: one of neo.AnalogSignal, neo.IrregularlySampledSignal, 
            datatypes.DataSignal, or datatypes.IrregularlySampledDataSignal.
        
    value: float scalar, the nominal value of the domain, or a monotonic 
            sequence (tuple, list) of scalars.
            
            When a scalar, the function looks up the signal samples that correspond 
            to domain values close to value within the atol and rtol, 
            using numpy.isclose().
            
            NOTE 1:
            
            `a` and `b` are "close to" each other when
            
            absolute(`a` - `b`) <= (`atol` + `rtol` * absolute(`b`))
            
            When a sequence, its elements are boundaries of bins to which domain
            values belong (half-open intervals, direction specified by the 
            value of `right`); the function looks up signal samples for the 
            domain values with indices that fall these bins, as determined using 
            numpy.digitize().
            
            NOTE 2: From numpy.digitize docstring:
            
            numpy.digitize(x, bins, right=False)[source]
                
                Return the indices of the bins to which each value in input array belongs.
                right     order of bins   returned index i satisfies  meaning
                False     increasing      bins[i-1] <= x <  bins[i]   x in [bins[i-1], bins[i])
                True      increasing      bins[i-1] <  x <= bins[i]   x in (bins[i-1], bins[i]]
                False     decreasing      bins[i-1] >  x >= bins[i]   x in [bins[i], bins[i-1])
                True      decreasing      bins[i-1] >= x >  bins[i]   x in (bins[i], bins[i-1]]

            If values in x are beyond the bounds of bins, 0 or len(bins) is 
            returned as appropriate.        
            
    channel: int, default 0: the index of the signal channel; must be 
        0 <= channel < signal.shape[1]
        
    rtol, atol: float scalars defaults are, respectively, 1e-05 and 1e-08 as
        per numpy.isclose(); used when value is a scalar
        
    equal_nan: bool, default False; specifies if np.nan values are treated as
        equal; used when value is a scalar
        
    right: bool, default False; see documentation for numpy.digitize() for details
        used when value is a sequence
        
    Returns:
    -------
    ret: Array with signal values where signal samples in the specified channel
        channel are
        
            "close to" the specified nominal value (see the NOTE 1, above).
        
            OR 
            
            fall within the boundaries of specified in value
        
    index: Indexing array used to extract ret from the domain
    
    domain_vals: Subarray of the signal, indexed using the "index" array.
    
    CAUTION:
    For regularly sampled signals (e.g. neo.AnalogSignal or datatypes.DataSignal)
    this function will almost surely fail to return all signal values where the 
    domain is close to the specified nominal value. The success depends on the 
    sampling rate and signal quantization error.
    
    A better strategy is to search for the INTERSECTION between domain sample 
    indices where domain <= upper limit and those where domain >= lower limit.
    
    """
    from . import datatypes as dt
    
    if not isinstance(signal, (neo.AnalogSignal, neo.IrregularlySampledSignal, 
                             DataSignal, IrregularlySampledDataSignal)):
        raise TypeError("signal expected to be a signal; got %s instead" % type(signal).__name__)
    
    if not isinstance(value, (numbers.Number, tuple, list)):
        raise TypeError("value expected to be a float, or sequence of one or two floats; got %s instead" % type(value).__name__)
    
    if isinstance(value, (tuple, list)):
        if len(value) < 1 or len(value) > 2:
            raise TypeError("When a tuple, value must contain at most two elements; got %d instead" % len(value))
        
        if not all([isinstance(v, numbers.Number) for v in value]):
            raise TypeError("value sequence must contain only scalars")
    
    if not isinstance(channel, int):
        raise TypeError("channel expected to be an int; got %s instead" % type(channel).__name__)
    
    if channel < 0 or channel >= signal.shape[1]:
        raise ValueError("channel index %d out of range for a signal with %d channels" % (channel, signal.shape[1]))
    
    if not isinstance(rtol, numbers.Number):
        raise TypeError("rtol expected to be a float; got %s instead" % type(rtol).__name__)
    
    if not isinstance(atol, numbers.Number):
        raise TypeError("atol expected to be a float; got %s instead" % type(atol).__name__)
    
    if not isinstance(equal_nan, bool):
        raise TypeError("equal_nan expected to be a bool; got %s instead" % type(equal_nan).__name__)
    
    signal_values = signal.as_array(units=signal.units)[:,channel]
    
    domain = signal.times
    
    ret = [np.nan]
    
    domain_vals = [np.nan]
    
    index = [np.nan]
    
    if isinstance(value, (tuple, list)):
        digital = np.digitize(domain, value, right=right)
        bin_k = [np.where(digital == k)[0] for k in range(1, len(value))]
        
        if len(bin_k):
            index = np.concatenate(bin_k)
            
            ret = signal_values[index]
            
            domain_vals = domain[index]
            
    else:
        ndx = np.isclose(np.array(domain), value, atol=atol, rtol=rtol, equal_nan=equal_nan)
        
        if ndx.any():
            index = np.where(ndx)[0]
            
            ret = signal_values[index]
            
            domain_vals = domain[index]
            
            
    return ret, index, domain_vals

def inverse_lookup(signal, value, channel=0, rtol=1e-05, atol=1e-08, equal_nan = False, right=False):
    """Look-up for domain values given a nominal signal value.
    
    The function addresses the question "what is (are) the value(s) of the 
    signal's domain for signal samples with value close to a specific value?"
    
    For the inverse correspondence see lookup().
    
    Parameters:
    ----------
    signal: one of neo.AnalogSignal, neo.IrregularlySampledSignal, 
            datatypes.DataSignal, or datatypes.IrregularlySampledDataSignal.
        
    value: float scalar, the nominal value of the signal, or a monotonic
            sequence (tuple, list) of scalars.
            
            When a scalar, the function looks up the domain values corresponding 
            to signal samples that are close to value within the atol and rtol, 
            using numpy.isclose().
            
            NOTE 1:
            
            `a` and `b` are "close to" each other when
            
            absolute(`a` - `b`) <= (`atol` + `rtol` * absolute(`b`))
            
            When a sequence, its elements are boundaries of bins to which signal
            values belong (half-open intervals, direction specified by the 
            value of `right`); the function looks up the domain values for the 
            signal samples with indices fall in these bins, as determined using 
            numpy.digitize().
            
            NOTE 2: From numpy.digitize docstring:
            
            numpy.digitize(x, bins, right=False)[source]
                
                Return the indices of the bins to which each value in input array belongs.
                right     order of bins   returned index i satisfies  meaning
                False     increasing      bins[i-1] <= x <  bins[i]   x in [bins[i-1], bins[i])
                True      increasing      bins[i-1] <  x <= bins[i]   x in (bins[i-1], bins[i]]
                False     decreasing      bins[i-1] >  x >= bins[i]   x in [bins[i], bins[i-1])
                True      decreasing      bins[i-1] >= x >  bins[i]   x in (bins[i], bins[i-1]]

            If values in x are beyond the bounds of bins, 0 or len(bins) is 
            returned as appropriate.        

    channel: int, default 0: the index of the signal channel; must be 
        0 <= channel < signal.shape[1]
        
    rtol, atol: float scalars defaults are, respectively, 1e-05 and 1e-08 as
        per numpy.isclose(); used when value is a scalar
        
    equal_nan: bool, default False; specifies if np.nan values are treated as
        equal; used when value is a scalar
        
    right: bool, default False; see documentation for numpy.digitize() for details
        used when value is a sequence
        
    Returns:
    -------
    ret: Array with domain values where signal samples in the specified channel
        channel are
        
            "close to" the specified nominal value (see the NOTE 1, above).
        
            OR 
            
            fall within the boundaries of specified in value
        
    index: Indexing array used to extract ret from the domain
    
    sigvals: Subarray of the signal, indexed using the "index" array.
    
    CAUTION:
    For regularly sampled signals (e.g. neo.AnalogSignal or datatypes.DataSignal)
    this function will almost surely fail to return all domain values where the 
    signal is close to the specified nominal value. The success depends on the 
    sampling rate and signal quantization error.
    
    A better strategy is to search for the INTERSECTION between domain indices where
    signal is <= upper value limit and indices where signal >= lower value limit.
    
    WARNING: Do not confuse with the functionality of pynverse module.
    
    Considering the signal as being the realization of a function y = f(x) where
    x is the signal's domain and y the signal values, one might be inclined to 
    use the pynverse module by Alvaro Sanchez-Gonzalez to calculate its inverse
    function x = g(y) numerically. 
    
    However, pynverse uses functional programming to calculate the inverse of a 
    mathematical function represented as a python function, or callable, and 
    not an array realization of that function (see pynverse documentation for 
    details).
    
    """
    
    from . import datatypes as dt
    
    if not isinstance(signal, (neo.AnalogSignal, neo.IrregularlySampledSignal, 
                             DataSignal, IrregularlySampledDataSignal)):
        raise TypeError("signal expected to be a signal; got %s instead" % type(signal).__name__)
    
    if not isinstance(value, (numbers.Number, tuple, list)):
        raise TypeError("value expected to be a float, or sequence of one or two floats; got %s instead" % type(value).__name__)
    
    if isinstance(value, (tuple, list)):
        if len(value) < 1:
            raise TypeError("When a tuple, value must contain at least one element; got %d instead" % len(value))
        
        if not all([isinstance(v, numbers.Number) for v in value]):
            raise TypeError("value sequence must contain only scalars")
    
    if not isinstance(channel, int):
        raise TypeError("channel expected to be an int; got %s instead" % type(channel).__name__)
    
    if channel < 0 or channel >= signal.shape[1]:
        raise ValueError("channel index %d out of range for a signal with %d channels" % (channel, signal.shape[1]))
    
    if not isinstance(rtol, numbers.Number):
        raise TypeError("rtol expected to be a float; got %s instead" % type(rtol).__name__)
    
    if not isinstance(atol, numbers.Number):
        raise TypeError("atol expected to be a float; got %s instead" % type(atol).__name__)
    
    if not isinstance(equal_nan, bool):
        raise TypeError("equal_nan expected to be a bool; got %s instead" % type(equal_nan).__name__)
    
    
    signal_values = signal.as_array(units=signal.units)[:,channel]
    
    domain = signal.times
    
    ret = [np.nan]
    
    sigvals = [np.nan]
    
    index = [np.nan]
    
    if isinstance(value, (tuple, list)):
        # see numpy.digitize:
        #    numpy.digitize(x, bins, right=False)[source]
        #       
        #     Return the indices of the bins to which each value in input array belongs.
        #     right     order of bins   returned index i satisfies  meaning
        #     False     increasing      bins[i-1] <= x <  bins[i]   x in [bins[i-1], bins[i])
        #     True      increasing      bins[i-1] <  x <= bins[i]   x in (bins[i-1], bins[i]]
        #     False     decreasing      bins[i-1] >  x >= bins[i]   x in [bins[i], bins[i-1])
        #     True      decreasing      bins[i-1] >= x >  bins[i]   x in (bins[i], bins[i-1]]

        #    If values in x are beyond the bounds of bins, 0 or len(bins) is 
        #    returned as appropriate.        
        
        digital = np.digitize(signal_values, value, right=right)
        
        # leave out:
        # digital == 0 indices where signal values are left of the leftmost boundary
        # digital == len(value) where signal values are right of the rightmost boundary
        # np.nan falls 
        # to the left (if right is False) or right, otherwise
        bin_k = [np.where(digital==k)[0] for k in range(1,len(value))]
        
        if len(bin_k):
            index = np.concatenate(bin_k)
            
            ret = domain[index]
            
            sigvals = signal_values[index]
            
    else:
        ndx = np.isclose(signal_values, value, atol=atol, rtol=rtol, equal_nan=equal_nan)
    
        if ndx.any():
            index = np.where(ndx)[0]
            
            ret = domain[index]
            
            sigvals = signal_values[index]
    
    return ret, index, sigvals

class ElectrophysiologyDataParser(object):
    """Encapsulate acquisition parameters and protocols for electrophysiology data
    
    Intended to provide a common denominator for data acquired with various 
        electrophysiology software vendors. 
        
    WARNING API under development (i.e. unstable)
    """
    def __init__(self):
        # possible values for self._data_source_:
        # "Axon", "CEDSignal", "CEDSpike", "Ephus", "NA", "unknown"
        # default: "unknown"
        self._data_source_ = "unknown"  
        self._acquisition_protocol_ = dict()
        self._acquisition_protocol_["trigger_protocol"] = TriggerProtocol()
        self._averaged_runs_ = False
        self._alternative_DAC_command_output_ = False
        self._alternative_digital_outputs_ = False
    
    def parse_data(self, data:neo.Block, metadata:dict=None) -> None:
        if hasattr(data, "annotations"):
            self._data_source_ = data.annotations.get("software", "unknown")
            if self._data_source_ == "Axon":
                self._parse_axon_data_(data, metadata)
                
            else:
                # TODO 2020-02-20 11:32:16
                # parse CEDSignal, CEDSpike, EPhus, unknown
                pass
            
    def _parse_axon_data_(self, data:neo.Block, metadata:dict=None) -> None:
        data_protocol = data.annotations.get("protocol", None)
        
        self._averaged_runs_ = data_protocol.get("lRunsPerTrial",1) > 1
        self._n_sweeps_ = data_protocol.get("lEpisodesPerRun",1)
        self._alternative_digital_outputs_ = data_protocol.get("nAlternativeDigitalOutputState", 0) == 1
        self._alternative_DAC_command_output_ = data_protocol.get("nAlternativeDACOutputState", 0) == 1
        
        
