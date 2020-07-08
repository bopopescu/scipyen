import vigra

from core import datatypes
from core.datatypes import arbitrary_unit

class AxisCalibration(object):
    """Axis calibration.
    
    An axis calibration is uniquely determined by the axis type and the
    attributes "name", "units", "origin", and "resolution", for each axis contained
    in a VigraArray axistag property.
    
    In addition, Channel axes contain a set of name, units, origin & resolution
    parameters for each channel.
    
    The main function of the AxisCalibration objects is to associate physical
    units (and names) to a vigra array axis in a persistent way.
    
    Ways to use:
    
    1) Preferred way: construct an AxisCalibration on a vigra.VigraArray or a
    vigra.AxisTags object.
    
    The AxisCalibration will keep a reference to the VigraArray axistags property
    or to the AxisTags object passed to the constructor.
    
    In both cases, the calibration generates default values which can then by
    atomically modified by calling one of the setXXX methods, as explained below.
    
    For axisInfo object that contain in their "description" property an XML-formatted
    string (see the documentation for calibrationString()), the calibration
    data is parsed from that string.
    
    The units, origin and resolution of an axis (or an individual channel in a 
    Channels axis) are set by the setUnits, setOrigin, setResolution methods.
    
    These methods require an axis "key" string or axisInfo object to specify
    the axis for which the calibration is being modified. For Channel axes, 
    these methods also require the index of the channel for which the calibration
    is being modified.
    
    setAxisName() assigns a name to a specified axis; 
    
    setChannelName() assigns a name to an individual channel of a Channel axis
    which must exist in the AxisCalibration instance. NOTE that there can be at
    most ONE Channels axis in a VigraArray (and therefore also in an 
    AxisCalibration object).
    
    For convenience, methods to add or remove axes are provided. HOWEVER this risks
    breaking the axes bookkeeping by the vigra.VigraArray to which the axes belong.
    
    2) construct an AxisCalibration based on a vigra.AxisInfo object. 
    The units, origin, resolution and axisname can be passed as constructor 
    parameters, or assigned later. The axiskey and axistype parameters, 
    if passed to the constructor, will be ignored, their values being supplied 
    by the AxisInfo.
    
    An "independent" AxisTags object will be constructed for this AxisCalirbation 
    instance -- CAUTION: this will be uncoupled from any VigraArray and thus
    won;t be of much use outside the AxisCalibration object.
    
    3) construct an "anonymous" AxisCalibration passing the axiskey, axistype, 
    units, origin, resolution and axisname for a yet undefined axis.
    An "independent" AxisTags object will be constructed (see case 2, above) 
    containing a single AxisInfo object. Bothe the AxisTags and its single 
    AxisInfo object will be uncoupled from any VigraArrays.
    
    Such AxisCalibration objects can be used as a "vehicle" to calibrate actual
    AxisInfo objects embedded in another VigraArray, provided they are compatible
    (and their key is found inside the calibration data)
    
    In all cases, for Channels axes only, the name, units, origin and resolution
    are accessed and set to the specified channel index (0-based integer).
    
    For non-channel axes, the name (axisname), units, origin and resolution
    are accessed (and set) by the axis key str.
    
    """

    relative_tolerance = 1e-4
    absolute_tolerance = 1e-4
    equal_nan = True

    def __init__(self, data = None, 
                 axistype = None, axisname=None,
                 units = None, origin = None, resolution = None, channel = None, 
                 channelname = None):
        """
        Named parameters:
        ================
        
        data = None (default), a vigra.AxisTags object (typically asociated with 
                a vigra.VigraArray), a vigra.AxisInfo object, or a vigra.VigraArray
                object.
                
        axistype = None (default) or a vigra.AxisType enum flag (or a combination thereof);
                only used when axis is None, or a str (axiskey)
                
        axisname = None (default) or a str; only used when axis is None
        
        units = None (default) or python Quantity or UnitQuantity; only used when
            axis is None or a vigra.AxisInfo
            
        origin = None( default) or a scalar; only used when 
        
        NOTE: axis key (a str) must conform to a strict set of rules, contained
        in the axisTypeFlags dictionary, in this module
        
        """
        
        # NOTE: 2018-08-25 20:52:33
        # API revamp: 
        # 1) AxisCalibration stores a vigra.AxisTags object as a member -- 
        #   this CAN be serialized
        # 
        # 2) calibration is stored in a dictionary where the key is the axisinfo
        #   key (string) associated with that axis;
        #
        #   * under that tag key string, the axis calibration items are:
        #       "axisname", "axistype", "axiskey", "units", "origin", "resolution"
        #
        #   * for channel axes ONLY (tag key string "c"):
        #
        #       2.1) channel calibration items ("name", "units", "origin" and "resolution")
        #       are contained in a nested dictionary mapped to a 0-based integer 
        #       key (the channel "index") that is itself an item of the main 
        #       axis dictionary
        #
        #       2.2) axis calibration items "units", "origin" and "resolution"
        #       may be missing when the number of channels is > 1, or may have
        #       the same value as the channel calibration items for channel 0
        #
        #
        # 3) the AxisCalibration can thus contain calibration data for a collection
        #   of axes associated with a VigraArray object.
        #
        # 4) for an AxisInfo object to be "calibrated" (i.e., have an XML-formatted
        #   calibration string inserted in its "description" attribute) it needs to
        #   have its "key" attribute present in the main calibration dictionary of 
        #   this AxisCalibration object, and have the same typeFlags as the "axistype"
        #   item, even if the AxisInfo object is not part of the axistags collection
        #   stored within the AxisCalibration object.
        
        apiversion = (0,2)
        # NOTE: 2018-08-01 08:55:15
        # except for "units", all other values in this dictionary are PODs, 
        # not python quantities !!!
        self._calibration_ = dict()
        
        # FIXME: 2018-08-27 09:40:10
        # do we realy need the axiskey?
        # yes, if we want to use calibration as independent object
        # I know this is data duplication but I think this is a small price to pay
        
        # NOTE: 2018-09-11 16:01:09
        # allow overriding calibration with atomic elements, if specified 
        # (hence their default are set to None, but checked below against this if
        # data is not a VigraArray, AxisTags, AxisInfo, or str)
        if isinstance(data, vigra.VigraArray):
            self._axistags_ = data.axistags
            
            for axinfo in data.axistags:
                self._initialize_calibration_with_axis_(axinfo)
        
        elif isinstance(data, vigra.AxisTags):
            self._axistags_ = data
            
            for axinfo in data:
                self._initialize_calibration_with_axis_(axinfo)
                    
        elif isinstance(data, vigra.AxisInfo):
            # NOTE: 2018-08-27 11:48:32
            # construct AxisCalibration from the description attribute of data
            # using default values where necessary (see parseDescriptionString)
            # NOTE: calibration string may be wrong (from old API)
            # as a rule of thumb: rely on the axistags' properties to set relevant fields!
            #
            # NOTE: 2018-09-04 16:54:13
            # just make sure that we parse everything that's there, without assumptions
            # then set defaults for missing fields HERE
            self._axistags_ = vigra.AxisTags(data)
            
            self._initialize_calibration_with_axis_(data)
            
            
            #print("AxisCalibration from axisinfo with atomic data")
            #print(self._calibration_[data.key])
            #print("atomic data:")
            #print("units", units)
            #print("origin", origin)
            #print("resolution", resolution)
            #print("axisname", axisname)
            #print("channel", channel)
            #print("channelname", channelname)
            
            # NOTE: 2018-09-11 17:26:37
            # allow setting up atomic elements when constructing from a single AxisInfo object
            _, _axiscal = self._generate_atomic_calibration_dict_(initial_axis_cal=self._calibration_[data.key],
                                                                    axisname=axisname,
                                                                    units=units,
                                                                    origin=origin,
                                                                    resolution=resolution,
                                                                    channel=channel,
                                                                    channelname=channelname)
            
            #print( "_axiscal", _axiscal)
            
            self._calibration_[data.key].update(_axiscal)
                            
        elif isinstance(data, str):
            # construct from a calibration string
            if not AxisCalibration.hasCalibrationString(str):
                warnings.warn("The string parameter is not a proper calibration string")
                return # an empty AxisCalibration object
            
            cal = AxisCalibration.parseDescriptionString(data)
            
            key = cal.get("axiskey", "?") # rely on parsed calibration string
            
            if key not in axisTypeFlags:
                key = "?"
            
            self._calibration_[key] = dict()
            self._calibration_[key]["axiskey"] = key
            self._calibration_[key]["axisname"] = cal.get("axisname", defaultAxisTypeName(axisTypeFlags[Key]))
            self._calibration_[key]["axistype"] = cal.get("axistype", axisTypeFlags[key])
            
            if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
                channel_keys = [channel_index for channel_index in cal.keys() \
                                if isinstance(channel_index, int) and isinstance(cal[channel_index], dict)]
                
                if len(channel_keys) > 0:
                    for channel_index in channel_keys:
                        self._calibration_[key][channel_index] = dict()
                        
                        self._calibration_[key][channel_index]["name"] = cal[channel_index].get("name", None)
                        self._calibration_[key][channel_index]["units"] = cal[channel_index].get("units", pq.dimensionless)
                        self._calibration_[key][channel_index]["origin"] = cal[channel_index].get("origin", 0.0)
                        self._calibration_[key][channel_index]["resolution"] = cal[channel_index].get("resolution", 1.0)
                        
                else:
                    self._calibration_[key][0] = dict()
                    self._calibration_[key][0]["name"] = None
                    self._calibration_[key][0]["units"] = pq.dimensionless
                    self._calibration_[key][0]["origin"] = 0.0
                    self._calibration_[key][0]["resolution"] = 1.0
                    
            self._axistags_ = vigra.AxisTags(vigra.AxisInfo(key=key,
                                                              typeFlags = self._calibration_[key]["axistype"],
                                                              resolution = self._calibration_[key]["resolution"]))
            
            _, _axiscal = self._generate_atomic_calibration_dict_(initial_axis_cal=self._calibration_[data.key],
                                                                    axisname=axisname,
                                                                    units=units,
                                                                    origin=origin,
                                                                    resolution=resolution,
                                                                    channel=channel,
                                                                    channelname=channelname)
            
            self._calibration_[data.key].update(_axiscal)
                            
        else:
            # construct an AxisCalibration object from atomic elements supplied as arguments
            
            # NOTE: 2018-08-28 09:22:14
            # allow for units to be None, but then require that origin & resolution
            # are python Quantities with compatible units
            # otherwise, if units are Quantity or UnitQuantity accept origin & resolution
            # as floating point scalars OR Quantities but in the latter case raise exception
            # if their units are not compatible with those of "units" parameter
            if any(arg is None for arg in [axistype, axisname, units, origin, resolution]):
                raise TypeError("When data is None the following parameters must not be None: axistype, axisname, units, origin, resolution")
            
            _axistag, _axiscal = self._generate_atomic_calibration_dict_(axistype=axistype,
                                                                           axisname=axisname,
                                                                           units=units,
                                                                           origin=origin,
                                                                           resolution=resolution,
                                                                           channel=channel,
                                                                           channelname=channelname)
            
            self._axistags_ = _axistag
            self._calibration_[_axiscal["axiskey"]] = _axiscal
            
            ## NOTE: 2018-08-28 10:10:35
            ## figure out units/origin/r`esolution
            
        assert [ax.key in self._calibration_.keys() for ax in self._axistags_], "Mismatch between axistags keys and the keys in the calibration dictionary"
        
        # NOTE: 2018-09-05 11:16:00
        # this is likely to be redudant, but keep it so that we enforce upgrading
        # the axis calibrations in data generated with old API
        for ax in self._axistags_:
            self._axistags_[ax.key] = self.calibrateAxis(ax)
            
    def _adapt_channel_index_spec_(self, axiskey, channel):
        if axiskey not in self._calibration_.keys():
            raise KeyError("Axis key %s not found" % axiskey)
        
        if channel not in self._calibration_[axiskey].keys():
            channel_indices = [k for k in self._calibration_[axiskey].keys() if isinstance(k, int)]
            
            if len(channel_indices):
                if channel < 0 or channel >= len(channel_indices):
                    raise ValueError("Iinvalid channel index specified: %d" % channel)
                
                channel = channel_indices[channel]
                
            else:
                raise RuntimeError("No channel calibration data found for channel %d" % channel)
            
        return channel
    
    def _generate_atomic_calibration_dict_(self, initial_axis_cal = dict(),
                                             axistype = None,
                                             axisname = None,
                                             units = None, origin = None, resolution = None, 
                                             channel = None, 
                                             channelname = None):
        """Generates a calibration dictionary from atomic elements.
        
        Optionally the nested channel calibration dictionaries will albo be generated
        
        This is to allow overriding atomic calibration elements when an axistags 
        or axisinfo or vigra array (with axistags) was passed to c'tor
        """
        result = initial_axis_cal
        
        #print(result)
        
        user_units = None
        
        user_origin = None
        
        user_resolution = None
    
        # 1) set up user-given units
        if isinstance(units, (pq.Quantity, pq.UnitQuantity)):
            user_units = units.units
            
        elif isinstance(units, str):
            try:
                user_units = pq.registry.unit_registry[units]
                
            except Exception as e:
                user_units = pixel_unit
                
        elif units is None:
            # infer units from origin or resolution if it is missing from the
            # initial calibration dict; otherwise leave it as None
            
            if "units" not in result.keys():
                if isinstance(origin, pq.Quantity):
                    if origin.magnitude.size != 1:
                        raise ValueError("Origin must be a scalar Python Quantity; got %s" % origin)
                    
                    user_units = origin.units
                    
                    user_origin = float(origin.magnitude.flatten()[0])
                    
                elif isinstance(resolution, pq.Quantity):
                    if resolution.magnitude.size != 1:
                        raise ValueError("Origin must be a scalar Python Quantity; got %s" % resolution)
                    
                    user_units = resolution.units
                    
                    user_resolution = float(resolution.magnitude.flatten()[0])
                    
                else:
                    raise TypeError("When neither origin nor resolution are Python Quantities, units must be either a Quantity, UnitQuantity, or a units symbol string, or present in the initial_axis_cal dictionary")
                    
        else:
            raise TypeError("Expecting units to be a Python Quantity, UnitQuantity, a string (units symbol), or None; got %s instead" % type(units).__name__)
        
        # cache this for checking compatibility of origin & resolution units if necessary
        if isinstance(user_units, (pq.UnitQuantity, pq.Quantity)):
            units_dim = pq.quantity.validate_dimensionality(user_units)
            
        elif "units" in result.keys():
            units_dim = pq.quantity.validate_dimensionality(result["units"])
            
        else:
            raise RuntimeError("Cannot obtain units dimensionality")
        
        # 2) set up user-given origin
        if user_origin is None: # because it may have been set up above
            # make this mandatory if "origin" is not in the initial_axis_cal dictionary: # because it may have been set above
            # but leave as None otherwise
            #if "origin" not in result.keys(): #the whole point of this is to allow overriding preivious origin!!!!
            if isinstance(origin, pq.Quantity):
                if origin.magnitude.size != 1:
                    raise ValueError("Origin must be a scalar Python Quantity; got %s" % origin)
                
                # check it is compatible with user_units
                origin_dim = pq.quantity.validate_dimensionality(origin)
                
                if units_dim != origin_dim:
                    try:
                        cf = pq.quantity.get_conversion_factor(origin_dim, units_dim)
                        
                    except AssertionError:
                        raise ValueError("Cannot convert from %s to %s" % (origin_dim.dimensionality, units_dim.dimensionality))
                    
                    origin *= cf
                    
                user_origin = float(origin.magnitude.flatten()[0])
            
            elif isinstance(origin, numbers.Number):
                user_origin = float(origin)
            
            else:
                if "origin" not in result.keys():
                    raise TypeError("origin expected to be a float or Python Quantity scalar; got %s instead" % type(origin).__name__)
                
                user_origin = result["origin"]
        
        # 3) set up user-given resolution
        if user_resolution is None: # because it may have been set up above
            # make this mandatory if resolution is missing in initial dictionary
            #if "resolution" not in result.keys(): #the whole point of this is to allow overriding preivious origin!!!!
            if isinstance(resolution, pq.Quantity):
                if resolution.magnitude.size != 1:
                    raise ValueError("Resolution must be a scalar Pyhton Quantity; got %s" % resolution)
                
                resolution_dim = pq.quantity.validate_dimensionality(resolution)
                
                if units_dim != resolution_dim:
                    try:
                        cf = pq.quantity.get_conversion_factor(resolution_dim, units_dim)
                        
                    except AssertionError:
                        raise ValueError("Cannot convert from %s to %s" % (resolution_dim.dimensionality, units_dim.dimensionality))
                    
                    resolution *= cf
                    
                user_resolution = float(resolution.magnitude.flatten()[0])
                
            elif isinstance(resolution, numbers.Number):
                user_resolution = float(resolution)
                
            else:
                if "resolution" not in result.keys():
                    raise TypeError("resolution expected to be a scalar Python quantity or a float; got %s instead" % type(resolution).__name__)
                
                user_resolution = result["resolution"]
            
        
        # 4) set up axis type, name, and key
        # 
        if isinstance(axistype, str): 
            # NOTE: 2018-08-27 23:56:50
            # axistype supplied as a string; this can be:
            # a) a valid axis info key string (1 or 2 characters) defined in __all_axis_tag_keys__
            # b) a descriptive string recognizable by axisTypeFromString
            #
            # we fall back on UnknownAxisType
            
            if axistype in axisTypeFlags: # check is axistype is supplied as an axis info key string
                axiskey = axistype
                axistype = axisTypeFlags[axiskey]
                
            else: # maybe axistype is supplied as a standard descriptive string
                axistype = axisTypeFromString(axistype) # also does reverse lookup
                
                axiskey = [k for k in axisTypeFlags.keys() if axisTypeFlags[k] == axistype]
                
                if len(axiskey):
                    axiskey = axiskey[0]
                    
                else:
                    axiskey = "?"
                    
        elif isinstance(axistype, (vigra.AxisType, int)):
            # NOTE: 2018-08-28 11:07:54
            # "reverse" lookup of axisTypeFlags
            axiskey = [k for k in axisTypeFlags.keys() if axisTypeFlags[k] == axistype]
            
            if len(axiskey):
                axiskey = axiskey[0]
                
            else:
                axiskey = "?"
                
        else:
            if "axistype" not in result.keys():
                raise TypeError("axistype must be given as a str or a vigra.AxisType enumeration flag, or an int (combination of flags) when missing from the initial calibration dictionary; got %s instead" % type(axistype).__name__)
            
            else:
                axiskey = None
                
        # 5) set up any channel calibration nested dicts
        
        # if axistype is unknown (the default) and a channel is specified then 
        # coerce Channels type and key;
        
        # channels will be ignored if axis has a specified type other than Channels
        if isinstance(channel, int):
            if channel < 0:
                raise ValueError("channel index must be an integer >= 0; got %d instead" % channel)
            
            if axistype is None or axistype & vigra.AxisType.UnknownAxisType:
                axistype = vigra.AxisType.Channels
                axiskey = "c"
                
            elif axistype & vigra.AxisType.Channels == 0:
                warnings.warn("Channel index will be ignored for axis of type %s" % axistype)
        
        if axiskey is not None:
            result["axiskey"]  = axiskey
            
        else:
            if "axiskey" not in result.keys():
                raise RuntimeError("axiskey missing from initial calibration and could not be determined")
            
        if isinstance(axisname, str):
            result["axisname"] = axisname
            
        elif axisname is None and "axisname" not in result.keys():
            result["axisname"] = defaultAxisTypeName(axistype)
            
        if axistype is not None:
            if axistype != axisTypeFlags[axiskey]:
                warnings.warn("Mismatch between axis type %s and axis type key %s" % (defaultAxisTypeName(axistype), axiskey), RuntimeWarning)
            
            result["axistype"]  = axistype
            
        else:
            if "axistype" not in result.keys():
                raise RuntimeError("axistype must be specified when absent from initial calibration dictionary")
            
        # 4) if there is a channel specified and axis is of type Channels, 
        # then units/origin/resolution go there
        # othwerwise they go to whole axis
        
        # NOTE: 2018-08-28 00:08:12
        # units, origin and resolution __init__ parameters are considered
        # to apply to the whole axis, unless a channel index is specified
        # in which case they are applied to the particular channel and NOT
        # to the whole axis; see also NOTE: 2018-08-28 09:15:57
        #
        # also see NOTE: 2018-08-28 09:22:14 for how we interpret the 
        # units/origin/resolution parameters
        if result["axistype"] & vigra.AxisType.Channels:
            if isinstance(channel, int):
                # NOTE: 2018-08-28 09:15:57
                # apply units, origin, resolution to the specified channel
                if channel < 0:
                    raise ValueError("channel index must be an integer >= 0; got %d instead" % channel)
                
                if channel not in result.keys():
                    # special case for a new channel
                    # NOTE: 2018-09-11 17:08:21
                    # check all are given if new channel
                    user_units = result.get("units", None)
                    user_origin = result.get("origin", None)
                    user_resolution = result.get("resolution", None)
                    
                    if any([v is None for v in (user_units, user_origin, user_resolution)]):
                        raise TypeError("units, origin or resolution must all be specified for a new channel")
                    
                    result[channel] = dict()
                    result[channel]["name"] = channelname # may be None
                    
                # back to general case
                if isinstance(channelname, str): 
                    # previously defined channel name won't be overwritten:
                    # if it already exists then if channelname is None will NOT
                    # raise error at NOTE: 2018-09-11 17:08:21
                    result[channel]["name"] = channelname # may be None
                
                if user_units is not None:
                    # previously defined channel units won't be overwritten:
                    # if already present then if user_units is None won't raise
                    # at NOTE: 2018-09-11 17:08:21
                    result[channel]["units"] = user_units
                    
                #else:
                    #is "units" not in result[channel]["units"] = arbitrary_unit
                
                if user_origin is not None:
                    # see comments for user_units & channelname
                    result[channel]["origin"] = user_origin
                    
                #else:
                    #result[channel]["origin"] = 
                
                if user_resolution is not None:
                    # see comments for user_origin & user_units & channelname
                    result[channel]["resolution"] = user_resolution
                
            nChannels = len([k for k in result.keys() if isinstance(k, int)])
            
            # for a single channel in a channel axis we allow the units/origin/resolution
            # to be duplicated in the main axis calibration i.e. without requiring
            # a channel specificiation
            if nChannels <= 1: # 0 or 1 channel
                if user_units is not None:
                    result["units"] = user_units
                    
                if user_origin is not None:
                    result["origin"] = user_origin
                    
                if user_resolution is not None:
                    result["resolution"] = user_resolution
                
            if nChannels  == 0:
                # generate a mandatory channel if axis is Channels
                if 0 not in result.keys():
                    # special case for a new channel with index 0
                    if any([v is None for v in (user_units, user_origin, user_resolution)]):
                        raise TypeError("units, origin and resolution must be specified")
                    # allow no channel name given 
                    
                    result[0] = dict()
                    result[0]["name"] = channelname # may be None
                    
                # back to general case:
                if isinstance(channelname, str):
                    # potentially override existing channel 0 definition
                    result[0]["name"] = channelname 
                
                if user_units is not None:
                    result[0]["units"] = user_units
                
                if user_origin is not None:
                    result[0]["origin"] = user_origin
                
                if user_resolution is not None:
                    result[0]["resolution"] = user_resolution
                
        else:
            # finally for non-channel axis store data in the main calibration dict
            if user_units is not None:
                result["units"] = user_units
                
            if user_origin is not None:
                result["origin"] = user_origin
                
            if user_resolution is not None:
                result["resolution"] = user_resolution
            
        #print(axiskey, axistype)
        axistag = vigra.AxisTags(vigra.AxisInfo(key = result["axiskey"], 
                                                typeFlags = result["axistype"],
                                                resolution = result["resolution"]))
        
        return axistag, result
        
    def _upgrade_API_(self):
        def _upgrade_attribute_(old_name, new_name, attr_type, default):
            needs_must = False
            if not hasattr(self, new_name):
                needs_must = True
                
            else:
                attribute = getattr(self, new_name)
                
                if not isinstance(attribute, attr_type):
                    needs_must = True
                    
            if needs_must:
                if hasattr(self, old_name):
                    old_attribute = getattr(self, old_name)
                    
                    if isinstance(old_attribute, attr_type):
                        setattr(self, new_name, old_attribute)
                        delattr(self, old_name)
                        
                    else:
                        setattr(self, new_name, default)
                        delattr(self, old_name)
                        
                else:
                    setattr(self, new_name, default)
                    
        if hasattr(self, "apiversion") and isinstance(self.apiversion, tuple) and len(self.apiversion)>=2 and all(isinstance(v, numbers.Number) for v in self.apiversion):
            vernum = self.apiversion[0] + self.apiversion[1]/10
            
            if vernum >= 0.2:
                return
            
        
        _upgrade_attribute_("__axistags__", "_axistags_", vigra.AxisTags, vigra.AxisTags())
        _upgrade_attribute_("__calibration__", "_calibration_", dict, dict())
        
        self.apiversion = (0, 2)
            
    def _initialize_calibration_with_axis_(self, axinfo):
        self._calibration_[axinfo.key] = dict()
        
        cal = AxisCalibration.parseDescriptionString(axinfo.description)
        
        #print("AxisCalibration._initialize_calibration_with_axis_(AxisInfo) cal:", cal)
        
        # see NOTE: 2018-08-27 09:39:41
        self._calibration_[axinfo.key]["axiskey"] = axinfo.key
        
        self._calibration_[axinfo.key]["axisname"] = cal.get("axisname", defaultAxisTypeName(axinfo))
        
        # see NOTE: 2018-08-27 11:50:37
        if self._calibration_[axinfo.key]["axisname"] is None or \
            len(self._calibration_[axinfo.key]["axisname"].strip())==0:
            self._calibration_[axinfo.key]["axisname"] = defaultAxisTypeName(axinfo)
            
        #see NOTE: 2018-08-27 09:42:04
        # NOTE: override calibration string
        self._calibration_[axinfo.key]["axistype"] = axinfo.typeFlags 
        
        # see NOTE: 2018-08-27 11:43:30
        self._calibration_[axinfo.key]["units"]       = cal.get("units", pixel_unit)
        self._calibration_[axinfo.key]["origin"]      = cal.get("origin", 0.0)
        self._calibration_[axinfo.key]["resolution"]  = cal.get("resolution", 1.0)
        
        if axinfo.isChannel():
            # see NOTE: 2018-08-25 21:35:54
            channel_indices = [channel_ndx for channel_ndx in cal.keys() \
                                if isinstance(channel_ndx, int) and isinstance(cal[channel_ndx], dict)]
            
            #print("AxisCalibration._initialize_calibration_with_axis_(AxisInfo) channel_indices:", channel_indices)
            
            if len(channel_indices):
                for channel_ndx in channel_indices:
                    # see NOTE: 2018-08-27 11:51:04
                    self._calibration_[axinfo.key][channel_ndx] = dict()
                    self._calibration_[axinfo.key][channel_ndx]["name"] = cal[channel_ndx].get("name", None)
                    self._calibration_[axinfo.key][channel_ndx]["units"] = cal[channel_ndx].get("units", arbitrary_unit)
                    self._calibration_[axinfo.key][channel_ndx]["origin"] = cal[channel_ndx].get("origin", 0.0)
                    self._calibration_[axinfo.key][channel_ndx]["resolution"] = cal[channel_ndx].get("resolution", 1.0)
                    
                    if len(channel_indices) == 1:
                        # if one channel only, also copy this data to the main axis calibration dict
                        self._calibration_[axinfo.key]["units"] = self._calibration_[axinfo.key][channel_indices[0]]["units"]
                        self._calibration_[axinfo.key]["origin"] = self._calibration_[axinfo.key][channel_indices[0]]["origin"]
                        self._calibration_[axinfo.key]["resolution"] = self._calibration_[axinfo.key][channel_indices[0]]["resolution"]
                    
            else:
                self._calibration_[axinfo.key][0] = dict()
                self._calibration_[axinfo.key][0]["name"]        = None # string or None
                self._calibration_[axinfo.key][0]["units"]       = arbitrary_unit # python UnitQuantity or None
                self._calibration_[axinfo.key][0]["origin"]      = 0.0 # number or None
                self._calibration_[axinfo.key][0]["resolution"]  = 1.0 # number or None
                        
    def is_same_as(self, other, key, channel = 0, ignore=None, 
                   rtol = relative_tolerance, 
                   atol =  absolute_tolerance, 
                   equal_nan = equal_nan):
        """Compares calibration items between two axes, each calibrated by two AxisCalibration objects.
        
        AxisCalibration objects are considered similar if:
        1) the underlying axes are of the same type
        
        2) they have compatible units (meaning that their units can be easily 
            converted to each other)
            
        3) have numerically close origins and resolutions, whereby "numerically
            close" means their floating point values are within a prescribed 
            tolerance (see numpy.isclose(...) for details)
            
        4) for channel axes, clauses (2) and (3) hold for each channel
        
        These criteria can be relaxed using the "skip" parameter (see below)
        
        The description and name are deliberately NOT compared, as they are not
        considered unique determinants of the calibration.
        
        To compare objects using standard python semantics use the "==" binary operator
        
        Positional parameter:
        =====================
        
        other: AxisCalibration object
        
        Named parameters:
        =================
        
        ignore (default is None): What (if any) calibration properties may be ignored.
            Acceptable values are None or one of the following string keywords:
            "origin"
            "resolution"
            "units"
             or the sequence with any of these keywords
            
            
            
        rtol, atol, equal_nan: passed directly to numpy.isclose(...); See numpy.isclose(...) for details
        
        
        
        """
        
        if not isinstance(other, AxisCalibration):
            raise TypeError("Expecting an AxisCalibration object; got %s instead" % type(other).__name__)
        
        if isinstance(key, vigra.AxisInfo):
            key = key.key
            
        if not self.hasAxis(key):
            raise KeyError("Axis key %s not found in this object" % key)
        
        if not other.hasAxis(key):
            raise KeyError("Axis key %s not found in the object compared against" % key)
        
        if not self.axistags[key].compatible(other.axistags[key]):
            raise ValueError("The two axes are not type-compatible, although they have the same key")
        
        ignoreOrigin=False
        ignoreResolution=False
        ignoreUnits = False
        
        if isinstance(ignore, str) and ignore.lower() in ["units", "origin", "resolution"]:
            if ignore.lower() == "origin":
                ignoreOrigin = True
                
            elif ignore.lower() == "resolution":
                ignoreResolution = True
                
            elif ignore.lower() == "units":
                ignoreUnits = True
            
        elif isinstance(ignore, (tuple, list)) and all([isinstance(s, str) for s in ignore]):
            sk = [s.lower() for s in ignore]
            
            if "origin" in sk:
                ignoreOrigin = True
                
            if "resolution" in sk:
                ignoreResolution = True
                
            if "units" in sk:
                ignoreUnits = True
        
        result = self.getAxisType(key) == other.getAxisType(key)
        
        if result and not ignoreUnits:
            units_compatible = other.getUnits(key) == self.getUnits(key)
            
            if not units_compatible:
                self_dim    = pq.quantity.validate_dimensionality(self.getUnits(key))
                
                other_dim   = pq.quantity.validate_dimensionality(other.getUnits(key))
                
                if self_dim != other_dim:
                    try:
                        cf = pq.quantity.get_conversion_factor(other_dim, self_dim)
                        units_compatible = True
                        
                    except AssertionError:
                        units_compatible = False
                        
                else:
                    units_compatible = True
                    
            result &= units_compatible
        
        if result and not ignoreOrigin:
            result &= np.isclose(self.getDimensionlessOrigin(key), other.getDimensionlessOrigin(key), 
                                 rtol=rtol, atol=atol, equal_nan=equal_nan)
            
        if result and not ignoreResolution:
            result &= np.isclose(self.getDimensionlessResolution(key), other.getDimensionlessResolution(key),
                                 rtol=rtol, atol=atol, equal_nan=equal_nan)
            
        if result:
            if self.getAxisType(key) & vigra.AxisType.Channels > 0:
                result &= self.numberOfChannels() == other.numberOfChannels() # check if they have the same number of channels
                
                # NOTE: for a single channel per channel axis the channel index does not matter
                
                #if result:
                    #if self.channels > 1:
                        ## NOTE: 2018-08-01 17:49:15
                        ## perhaps one should make sure the channel indices are the same
                        #result &= all(channel in self.channelIndices for channel in other.channelIndices)
                        
                
                if result:
                    for chIndex in range(len(self.channelIndices(key))):
                        if not ignoreUnits:
                            channel_units_compatible = self.getUnits(key, self.channelIndices(key)[chIndex]) == other.getUnits(key, other.channelIndices(key)[chIndex])
                            #print(channel_units_compatible)
                            if not channel_units_compatible:
                                self_dim = pq.quantity.validate_dimensionality(self.getUnits(key, self.channelIndices(key)[chIndex]))
                                other_dim = pq.quantity.validate_dimensionality(other.getUnits(key, other.channelIndices(key)[chIndex]))
                                
                                if self_dim != other_dim:
                                    try:
                                        cf = pq.quantity.get_conversion_factor(other_dim, self_dim)
                                        channel_units_compatible = True
                                        
                                    except AssertionError:
                                        channel_units_compatible = False
                                        
                                else:
                                    channel_units_compatible = True
                                    
                            result &= channel_units_compatible
                        
                        if result and not ignoreOrigin:
                            result &= np.isclose(self.getDimensionlessOrigin(key, self.channelIndices(key)[chIndex]),
                                                other.getDimensionlessOrigin(key, other.channelIndices(key)[chIndex]),
                                                rtol=rtol, atol=atol, equal_nan=equal_nan)
                            
                        if result and not ignoreResolution:
                            result &= np.isclose(self.getDimensionlessResolution(key, self.channelIndices(key)[chIndex]),
                                                other.getDimensionlessResolution(key, other.channelIndices(key)[chIndex]),
                                                rtol=rtol, atol=atol, equal_nan=equal_nan)
                                
        return result
        
    def __repr__(self):
        result = list()
        result.append("%s:\n"             % self.__class__.__name__)
        
        for k, key in enumerate(self._calibration_.keys()):
            result.append("Axis %d:\n" % k)
            result.append("axisname: %s;\n"       % self.getAxisName(key))
            result.append("type: %s;\n"           % self.getAxisType(key))
            result.append("key: %s;\n"            % key)
            result.append("origin: %s;\n"         % self.getOrigin(key))
            result.append("resolution: %s;\n"     % self.getResolution(key))

            channels = [c for c in self._calibration_[key].keys() if isinstance(c, int)]
            
            if len(channels):
                if len(channels) == 1:
                    result.append("1 channel:\n")
                else:
                    result.append("%d channels:\n" % len(channels))
            
                for c in channels:
                    chstring = ["\tchannel %d:\n" % c]
                    chstring.append("\t\tname: %s,\n" % self.getChannelName(c))
                    chstring.append("\t\tunits: %s,\n" % self.getUnits(key, c))
                    chstring.append("\t\torigin: %s,\n" % self.getOrigin(key, c))
                    chstring.append("\t\tresolution: %s;\n" % self.getResolution(key, c))
                    
                    chstring = " ".join(chstring)
                    
                    result.append(chstring)
                
            result.append("\n")
        
        return " ".join(result)
    
    def _get_attribute_value_(self, attribute:str, key:str, channel:int=0):
        if not isinstance(attribute, str):
            raise TypeError("'attribute' parameter expected to be a str; got %s instead" % type(attribute).__name__)
        
        if not isinstance(key, str):
            raise TypeError("'key' parameter expected to be a str; got %s instead" % type(key).__name__)
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s is not calibrated by this object" % key)

        if not isinstance(channel, int):
            raise TypeError("'channel' parameter expected to be an int; got %s instead" % type(channel).__name__)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            channel = self._adapt_channel_index_spec_(key, channel)
            
            if attribute not in self._calibration_[key][channel].keys():
                raise KeyError("Unknown attribute %s for axis %s" % (attribute, self._calibration_[key]["axistype"]))
            
            return self._calibration_[key][channel][attribute]
        
        else:
            if attribute not in self._calibration_[key].keys():
                raise KeyError("Unknown attribute %s for axis %s" % (attribute, self._calibration_[key]["axistype"]))
            
            return self._calibration_[key][attribute]
    
    def _set_attribute_value_(self, attribute:str, value:object, key:str, channel:int=0):
        if not isinstance(attribute, str):
            raise TypeError("'attribute' parameter expected to be a str; got %s instead" % type(attribute).__name__)
        
        if not isinstance(key, str):
            raise TypeError("'key' parameter expected to be a str; got %s instead" % type(key).__name__)
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s is not calibrated by this object" % key)

        if not isinstance(channel, int):
            raise TypeError("'channel' parameter expected to be an int; got %s instead" % type(channel).__name__)
        
        if attribute == "axistype":
            warnings.warn("Axis type cannot be set in this way", RuntimeWarning)
            return 
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            channel = self._adapt_channel_index_spec_(key, channel)
            if attribute not in self._calibration_[key][channel].keys():
                raise KeyError("Unknown attribute %s for axis %s" % (attribute, self._calibration_[key]["axistype"]))
            
            self._calibration_[key][channel][attribute] = value
            
        else:
            if attribute not in self._calibration_[key].keys():
                raise KeyError("Unknown attribute %s for axis %s" % (attribute, self._calibration_[key]["axistype"]))
            
            self._calibration_[key][attribute] = value
    
    
    def hasAxis(self, key):
        """Queries if the axis key is calibrated by this object
        """
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        return key in self._calibration_.keys()
    
    @property
    def hasChannelAxis(self):
        return any(value["axistype"] & vigra.AxisType.Channels for value in self._calibration_.values())
    
    #@property
    def channelIndicesAndNames(self):
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not found in this AxisCalibration" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            return sorted([(item[0], item[1]["name"]) for item in self._calibration_[key].items() if isinstance(item[0],int)], key = lambda x:x[0])
        
        else:
            return [tuple()]
    
    #@property
    def channelIndices(self, key="c"):
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not found in this AxisCalibration" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            return sorted([key for key in self._calibration_[key].keys() if isinstance(key, int)])
        
        else:
            return []
    
    #@property
    def channelNames(self):
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis key %s is not calibrated by this object" % key)
        
        channel_indices = self.channelIndices(key)
        
        if len(channel_indices):
            return [self._calibration_[key][c].get("name", None) for c in channel_indices]
        
    def numberOfChannels(self):
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis key %s does not have calibration data" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels == 0:
            raise ValueError("Axis with key %s is not a Channels axis" % key)
        
        nChannels = [k for k in self._calibration_[key].keys() if isinstance(k, int)]
        
        if len(nChannels) == 0:
            return 1
        
        else:
            return len(nChannels)
        
    def getChannelName(self, channel_index):
        if self.axistags.channelIndex == len(self.axistags):
            raise KeyError("No channel axis exists in this calibration object")
        
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
            
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Channel axis does not have calibration data")
        
        if not isinstance(channel_index, int):
            raise TypeError("channel_index expected to be an int; got %s instead" % type(channel_index).__name__)
        
        channel_index = self._adapt_channel_index_spec_(key, channel_index)
        
        return self._calibration_[key][channel_index].get("name", None)
            
    def getAxisType(self, key):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not found in this AxisCalibration" % key)
        
        return self._calibration_[key].get("axistype", vigra.AxisType.UnknownAxisType)
    
    def getAxisName(self, key):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not found in this AxisCalibration" % key)
        
        return self._calibration_[key].get("axisname", None)
    
    def getCalibratedIntervalAsSlice(self, value, key, channel = 0):
        """Returns a slice object for a half-open interval of calibrated coordinates.
        
        Parameters:
        ==========
        value: tuple, list or numpy array with two elements representing a pair
                of start, stop (exclusive) interval values: [start, stop)
                
            the elements can be scalar floats, or python Quantities with the 
            same units as the axis specified by "key"; both elements must be the
            same Python data type.
        
        key: vigra.AxisInfo, a str (valid AxisInfo key string) or an int
            In either case the key should resolve to an axis info stored in this
            AxisCalibration object
            
        Returns:
        =======
        a slice object useful for slicing the axis given by "key"
        
        See also imageprocessing.imageIndexObject
        
        """
        if isinstance(key, vigra.AxisInfo):
            if key not in self._axistags_:
                raise KeyError("AxisInfo with key %s not found" % key.key)
            key = key.key
            
        elif isinstance(key, int):
            axinfo = self._axistags_[key]
            key = axinfo.key
            
        elif not isinstance(key, str):
            raise TypeError("key expected to be a str (AxisInfo key), an int or an axisinfo")
            
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis %s not found in this AxisCalibration object" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            if channel not in self._calibration_[key].keys():
                raise KeyError("Channel %d not found for axis %s with key %s" % (channel, self._calibration_[key]["axisname"], self._calibration_[key]["axiskey"]))
        
            myunits = self._calibration_[key][channel]["units"]
            
        else:
            myunits = self._calibration_[key]["units"]
        
        if isinstance(value, (tuple, list)):
            value = list(value)
            
            if len(value) != 2:
                raise TypeError("Expecting a sequence of two elements; got %d instead" % len(value))
            
            if all([isinstance(v, numbers.Real) for v in value]):       # convert sequence of two floats to a quantity array
                value = np.array(value) * myunits
                
            elif all([isinstance(v, pq.Quantity) for v in value]):      # convert sequence of two quantities to a quantity array
                if not all([units_convertible(v, myunits) for v in value]):
                    raise TypeError("Interval units not compatible with this axis units %s" % myunits)
                
                units = value[0].units
                
                if value[0].ndim != 1:
                    value[0] = value[0].flatten()
                
                if value[1].ndim != 1:
                    value[1] = value[1].flatten()
                    
                value = np.array([v.magnitude for v in value]) * units
                
        elif isinstance(value, pq.Quantity):                            # check it is already a quantity array
            if not units_convertible(value, myunits):
                raise TypeError("interval units %s are not compatible with this axis units %s" % (value.units, myunits))
            
            if value.size != 2:
                raise TypeError("When an array, 'value' must have two elements only; got %d instead" % value.size)
            
            value = value.flatten()
            
        elif isinstance(value, np.ndarray):                             # make it a quantity array
            if value.size != 2:
                raise TypeError("When an array, 'value' must have two elements only; got %d instead" % value.size)
            
            value = value.flatten() * myunits
            
        else:
            raise TypeError("Value expected to be a sequence or numpy array of two real scalars or Python Quantity objects; got %s instead" % type(value).__name__)
        
        start, stop = value / self.getResolution(key)
        
        return slice(int(start), int(stop))
    
    def setAxisName(self, value, key):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not found in this AxisCalibration" % key)
        
        if isinstance(value, (str, type(None))):
            self._calibration_[key]["axisname"] = value
            
        else:
            raise TypeError("axis name must be a str or None; got %s instead" % type(value).__name__)
        
    def getUnits(self, key:(str, vigra.AxisInfo), channel:int = 0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
            
        return self._get_attribute_value_("units", key, channel)
    
    def setUnits(self, value, key:(str, vigra.AxisInfo), channel:int=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if not isinstance(value, (pq.Quantity, pq.unitquantity.UnitQuantity)):
            raise TypeError("Expecting a python Quantity or UnitQuantity; got %s instead" % type(value).__name__)

        self._set_attribute_value_("units", value, key, channel)

    def getDimensionlessOrigin(self, key, channel=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
            
        return self._get_attribute_value_("origin", key, channel)
    
    def getOrigin(self, key, channel=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s is not calibrated by this object" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            channel = self._adapt_channel_index_spec_(key, channel)
            return self._calibration_[key][channel]["origin"] * self._calibration_[key][channel]["units"]
        
        return self._calibration_[key]["origin"] * self._calibration_[key]["units"]
    
    def setOrigin(self, value, key, channel=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not found in this AxisCalibration" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            channel = self._adapt_channel_index_spec_(key, channel)
            
            myunits = self._calibration_[key][channel]["units"]
            
        else:
            myunits = self._calibration_[key]["units"]
        
        if isinstance(value, numbers.Number):
            if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
                self._calibration_[key][channel]["origin"] = value
                
            else:
                self._calibration_[key]["origin"] = value
            
        elif isinstance(value, pq.Quantity):
            if value.magnitude.size != 1:
                raise ValueError("origin must be a scalar quantity; got %s" % value)
            
            # NOTE: 2018-08-28 10:51:59
            # allow negative origins (offsets!)
            #if value.magnitude < 0:
                #raise ValueError("origin cannot be negative; got %s" % value)
            
            self_dim = pq.quantity.validate_dimensionality(myunits)
            
            origin_dim = pq.quantity.validate_dimensionality(value.units)
            
            if self_dim != origin_dim:
                try:
                    cf = pq.quantity.get_conversion_factor(origin_dim, self_dim)
                    
                except AssertionError:
                    raise ValueError("Cannot convert from %s to %s" % (origin_dim.dimensionality, self_dim.dimensionality))
                
                value *= cf
                
            if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
                self._calibration_[key][channel]["origin"] = value.magnitude.flatten()[0]
                
            else:
                self._calibration_[key]["origin"] = value.magnitude.flatten()[0]
            
        else:
            raise TypeError("origin expected to be a float; got %s instead" % type(value).__name__)
    
    def getResolution(self, key, channel=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not calibrated by this object" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            channel = self._adapt_channel_index_spec_(key, channel)
            
            return self._calibration_[key][channel]["resolution"] * self._calibration_[key][channel]["units"]
        
        return self._calibration_[key]["resolution"] * self._calibration_[key]["units"]
    
    def getDimensionlessResolution(self, key, channel=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        return self._get_attribute_value_("resolution", key, channel)
    
    def setResolution(self, value, key, channel=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s not found in this AxisCalibration" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            channel = self._adapt_channel_index_spec_(key, channel)
            
            myunits = self._calibration_[key][channel]["units"]
            
        else:
            myunits = self._calibration_[key]["units"]
            
        
        if isinstance(value, numbers.Number):
            if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
                self._calibration_[key][channel]["resolution"] = value
                
            else:
                self._calibration_[key]["resolution"] = value
            
        elif isinstance(value, pq.Quantity):
            if value.magnitude.size != 1:
                raise ValueError("resolution must be a scalar quantity; got %s" % value)
            
            self_dim = pq.quantity.validate_dimensionality(myunits)
            res_dim = pq.quantity.validate_dimensionality(value.units)
            
            if self_dim != res_dim:
                try:
                    cf = pq.quantity.get_conversion_factor(res_dim, self_dim)
                    
                except AssertionError:
                    raise ValueError("Cannot convert from %s to %s" % (res_dim.dimensionality, self_dim.dimensionality))
                
                value *= cf
                
            if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
                self._calibration_[key][channel]["resolution"] = value.magnitude.flatten()[0]
                
            else:
                self._calibration_[key]["resolution"] = value.magnitude.flatten()[0]
            
        else:
            raise TypeError("resolution expected to be a float or a python Quantity; got %s instead" % type(value).__name__)
        
    @property
    def axiskeys(self):
        """A list of axiskeys
        """
        keys = [key for key in self._calibration_]
        
        if any([k not in self._axistags_ for k in keys]):
            raise RuntimeError("Mismatch between the axistags keys and calibration keys")
        
        return keys
    
    @property
    def keys(self):
        """Aalias to self.axiskeys
        """
        return self.axiskeys
    
    @property
    def axistags(self):
        """Read-only
        """
        return self._axistags_
    
    #@property
    def typeFlags(self, key):
        """Read-only
        """
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s is not calibrated by this object" % key)
        
        return self._calibration_[key]["axistype"]
    
    def addAxis(self, axisInfo, index = None):
        """Register a new axis with this AxisCalibration object.
        
        If the axis already exists, raises a RuntimeError.
        
        The calibration values for the new axis can be atomically set using
        the setXXX methods
        
        By default a Channels axis will get a single channel (singleton axis).
        More channels can then be added using setChannelCalibration(), and calibration
        data for each channel can be modified using other setXXX methods
            
        WARNING: this function breaks axes bookkeeping by the VigraArray object
        that owns the axistags!!!
        
        Parameters:
        ===========
        axisInfo: vigra.AxisInfo object
        
        Named parameters:
        ================
        index: int or None (default) index of the axis
            when an int, it must be in the closed interval
            [0, len(self.axistags)]
        
        """
        if not isinstance(axisInfo, vigra.AxisInfo):
            raise TypeError("Expecting an AxisInfo object; got %s instead" % type(axisInfo).__name__)
        
        if axisInfo.key in self.axistags.keys() or axisInfo.key in self._calibration_.keys():
            raise RuntimeError("Axis %s already exists" % axisInfo.key)
        
        if index is None:
            self.axistags.append(axInfo)
            
        elif isinstance(index, int):
            if index < 0:
                raise ValueError("index must be between 0 and %d, inclusive" % len(self.axistags))
            
            if index == len(self.axistags):
                self.axistags.append(axInfo)
                
            elif index < len(self.axistags):
                self.axistags.insert(axInfo)
                
        # parse calibration string from axisInfo, it if exists
        self._initialize_calibration_with_axis_(axInfo)
        
    def removeAxis(self, axis):
        """Removes the axis and its associated calibration data
        
        Raises KeyError is axis is not found
        
        WARNING: this function breaks axes bookkeeping by the VigraArray object
        that owns the axistags!!!
        
        Parameters:
        ==========
        axis: str or vigra.AxisInfo; when a str, it must be a valid AxisInfo key.
        """
        if isinstance(axis, vigra.AxisInfo):
            key = axis.key
            if axis not in self._axistags_:
                raise KeyError("Axis %s not found" % key)
            
        elif isinstance(axis, str):
            key = axis
            if key not in self._axistags_.keys():
                raise KeyError("Axis %s not found" % key)
                
            axis = self._axistags_[key]
            
        if key not in self._calibration_.keys():
            raise KeyError("Axis %s has no calibration data" % key)
                
                
        self._calibration_.pop(key, None)
        del(self._axistags_[key])
        
    def synchronize(self):
        """Synchronizes the calibration data with the axistags instance contained within this AxisCalibration object.
        
        This should be called after any VigraArray methods that change the
        axes layout (e.g. inserting a singleton axis, or removing an axis, e.g.
        creating a lesser dimension view, etc) and therefore modify the axistags
        reference contained in this object.
        
        The axistags take priority: 
        
        * if, as a result of Vigra library functions,
        the axistags have GAINED a new axis, this will get default calibration
        values that can be modified atomically by calling one of the setXXX()
        methods of the AxisCalibration object/
        
        NOTE: a Channels axis will get calibration data for channel 0; calibration
        data for more channel can be added manually, by calling 
        setChannelCalibration()
        
        * if the axistags have LOST an axis, its calibration data will be removed
        
        """
        new_axes = [axInfo for axInfo in self._axistags_ if axInfo.key not in self._calibration_.keys()]

        for axInfo in new_axes:
            self._initialize_calibration_with_axis_(axInfo)
            self.calibrateAxis(axInfo)
        
        obsolete_keys = [key for key in self._calibration_.keys() if key not in self._axistags_.keys()]
        
        for key in obsolete_keys:
            self._calibration_.pop(key, None)
                
    def calibrationString(self, key):
        """Generates an axis calibration string for axis with specified key (and channel for a Channels axis)

        Returns an xml string with one of the following formats, depending on axis type:
        
        1) non-channels axis:
        <axis_calibration>
            <axistype>int</axistype>
            <axiskey>str</axiskey>
            <axisname>str</axisname>
            <units>str0</units>
            <origin>float</origin>
            <resolution>float</resolution>
        </axis_calibration>
        
        2) channel axis:
        <axis_calibration>
            <axistype>int</axistype>
            <axiskey>str</axiskey>
            <axisname>str</axisname>
            <channelX>
                <name>str</name>
                <units>str0</units>
                <origin>float</origin>
                <resolution>float</resolution>
            </channelX>
            <channelY>
                <name>str</name>
                <units>str0</units>
                <origin>float</origin>
                <resolution>float</resolution>
            </channelY
        </axis_calibration>
        """
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("No calibration data for axis key %s" % key)
        
        strlist = ["<axis_calibration>"]
        
        strlist += xmlutils.composeStringListForXMLElement("axiskey", self._calibration_[key]["axiskey"])
        
        #strlist.append("<axiskey>")
        #strlist.append("%s" % self._calibration_[key]["axiskey"])
        #strlist.append("</axiskey>")
        
        strlist += xmlutils.composeStringListForXMLElement("axisname", self._calibration_[key]["axisname"])
        
        #strlist.append("<axisname>")
        #strlist.append("%s" % self._calibration_[key]["axisname"])
        #strlist.append("</axisname>")
        
        strlist += xmlutils.composeStringListForXMLElement("axistype", "%s" % self._calibration_[key]["axistype"])
        #strlist.append("<axistype>")
        #strlist.append("%s" % self._calibration_[key]["axistype"])
        #strlist.append("</axistype>")
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            channel_indices = [ch_key for ch_key in self._calibration_[key].keys() if isinstance(ch_key, int)]
            
            if len(channel_indices):
                for channel_index in channel_indices:
                    strlist.append("<channel%d>" % channel_index)
                    strlist.append("<name>")
                    strlist.append("%s" % self._calibration_[key][channel_index]["name"])
                    strlist.append("</name>")
                    
                    strlist.append("<units>")
                    strlist.append("%s" % self._calibration_[key][channel_index]["units"].__str__().split()[1].strip())
                    strlist.append("</units>")
                    
                    strlist.append("<origin>")
                    strlist.append(str(self._calibration_[key][channel_index]["origin"]))
                    strlist.append("</origin>")
                    
                    strlist.append("<resolution>")
                    strlist.append(str(self._calibration_[key][channel_index]["resolution"]))
                    strlist.append("</resolution>")
                    
                    strlist.append("</channel%d>" % channel_index)
                    
            else:
                strlist.append("<channel0>")
                
                strlist.append("<name>")
                strlist.append(self._calibration_[key]["axisname"])
                strlist.append("</name")
                
                strlist.append("<units>")
                strlist.append("%s" % self._calibration_[key]["units"].__str__().split()[1].strip())
                strlist.append("</units>")
                
                strlist.append("<origin>")
                strlist.append(str(self._calibration_[key]["origin"]))
                strlist.append("</origin>")
                
                strlist.append("<resolution>")
                strlist.append(str(self._calibration_[key]["resolution"]))
                strlist.append("</resolution>")
                
                strlist.append("</channel0>")
        
        strlist.append("<units>")
        strlist.append("%s" % self._calibration_[key]["units"].__str__().split()[1].strip())
        strlist.append("</units>")
        
        strlist.append("<origin>")
        strlist.append(str(self._calibration_[key]["origin"]))
        strlist.append("</origin>")
        
        strlist.append("<resolution>")
        strlist.append(str(self._calibration_[key]["resolution"]))
        strlist.append("</resolution>")
        
        strlist.append("</axis_calibration>")
        
        return ''.join(strlist)
    
    @staticmethod
    def parseCalibrationString(s):
        """Alias to AxisCalibration.parseDescriptionString(s)
        """
        return AxisCalibration.parseDescriptionString(s)

    @staticmethod
    def parseDescriptionString(s):
        """Parses a string for axis calibration information and name.
        
        Positional parameters:
        ======================

        s = an XML - formatted string (as returned by calibrationString), or a 
            free-form string _CONTAINING_ an XML - formatted string as returned 
            by calibrationString.
            
        The function tries to detect whether the argument string 's' contains a
        "calibration string" with the format as returned by calibrationString 
        then parses that substring to return a (unit,origin) tuple.
        
        If such a (sub)string is not found, the function returns the default 
        values of (dimensionless, 0.0). If found, the (sub)string must be 
        correctly formatted (i.e. start/end tags must exist) otherwise the 
        function raises ValueError.
        
        Returns :
        =========
        
        A dictionary with keys: "units", "origin", "resolution", "name"
            and possibly "channelX" with X a 0-based integral index
            where each channelX key in turn maps to a dictionary 
            with the four key members ("units", "origin", "resolution", "name")
            
            All fields get default values if missing in the string parameter:
            
            units = dimensionless
            
            origin = 0.0
            
            resolution = 1.0
            
            axisname = None
            
        If the calibration string contains channels ("channelX" tags), the
        calibration data for each channel will be returned as a nested dictionary
        mapped to 0-based integer keys. The nested dictionary fields (same as
        above except for "name" instead of "axisname") will also get default
        values (as above) if missing from the string. 
        
        
            
        
        The values are:
            units: a pq.Quantity (or pq.UnitQuantity)
            origin: a float >= 0
            resolution: a float >= 0
            "name": None or a str == the axis' name
            
            channelX: a dictionary with keys: "units", "origin", "resolution", "name"
            with values as above (name is the channelX's name)
        
        """
        import quantities as pq # make quantities local
        import xml.etree.ElementTree as ET
        
        def _parse_calibration_set_(element, isChannel=False):
            """Looks for elements with the following tags: name, units, origin, resolution
            """
            
            result = dict()
            
            children = element.getchildren()
            #if len(children) != 3:
                #raise ValueError("Expecting an XML element with three children; got %s instead" % len(children))
            
            children_tags = [c.tag for c in children]
            
            # NOTE: 2018-08-22 15:28:30
            # relax the stringency; give units, orgin, resolution and name default values
            
            # reject tag names that do not belong here
            #if any([c not in set(mandatory_tags + optional_tags) for c in children_tags]):
                #raise ValueError("Expecting tags to be one of 'units', 'origin', 'resolution', 'name'")
            
            ## check that mandatory tags are present
            #if any([c not in set(children_tags) for c in mandatory_tags]):
                #raise ValueError("At least one of 'units', 'origin', 'resolution' should be present ")
            
            u = None
            
            if "units" in children_tags:
                unit_element = children[children_tags.index("units")]
                u_ = unit_element.text
                
                #print("u_", u_)
                
                if len(u_) > 0:
                    u = unit_quantity_from_name_or_symbol(u_)
                    
                    #try:
                        #u = eval(u_, pq.__dict__)
                        
                    #except Exception as err:
                        #print("".format(err))
                        #print("Unexpected error:", sys.exc_info()[0])
                        #warnings.warn("String %s could not be evaluated to a Python Quantity" % u_, RuntimeWarning)
                            
            if u is None: 
                # NOTE: default value depends on whether this is a channel axis 
                # or not. 
                # NOTE: both arbitrary_unit and pixel_unit are in fact derived
                # from pq.dimensionless
                if isChannel:
                    u = arbitrary_unit
                
                else:
                    u = pixel_unit
                    
            result["units"] = u
                
            o = None
            
            if "origin" in children_tags:
                origin_element = children[children_tags.index("origin")]
                o_ = origin_element.text
                
                if len(o_) > 0:
                    try:
                        o = eval(o_)
                        
                    except Exception as err:
                        traceback.print_exc()
                        #print("".format(err))
                        #print("Unexpected error:", sys.exc_info()[0])
                        warnings.warn("String could not be evaluated to a number or None", RuntimeWarning)
                        # NOTE fall through and leave o as None
                    
            if o is None:
                o = 0.0
                
            result["origin"] = 0.0
            
            r = None
            
            if "resolution" in children_tags:
                
                resolution_element = children[children_tags.index("resolution")]
                r_ = resolution_element.text
            
                if len(r_) > 0:
                    try:
                        r = eval(r_)
                        
                    except Exception as err:
                        traceback.print_exc()
                        #print("".format(err))
                        #print("Unexpected error:", sys.exc_info()[0])
                        print("String could not be evaluated to a number or None")
                        # NOTE fall through and leave r as None
                        
                
            if r is None:
                r = 1.0
                
            result["resolution"] = r
                
            if "name" in children_tags:
                name_element = children[children_tags.index("name")]
                name = name_element.text
                if not isChannel:
                    warnings.warn("'name' child found in %s for a non-channel axis" % element.tag, RuntimeWarning)
                
            elif "axisname" in children_tags:
                name_element = children[children_tags.index("axisname")]
                name = element.text
                if isChannel:
                    warngins.warn("'axisname' child found in %s element for a channel axis" % element.tag, RuntimeWarning)
                
            else:
                name  = None
                
            if isChannel:
                result["name"] = name
                
            else:
                result["axisname"] = name
            
            #print("parseDescriptionString _parse_calibration_set_ result:", result)

            return result
                
        if not isinstance(s, str):
            raise TypeError("Expected a string; got a %s instead." % type(s).__name__)
        
        # NOTE: 2018-08-22 22:38:24
        # thesse are the minimum requirements
        # if axistype turn out to be Channels, then we don't need units/origin/resolution
        # unless there is only one channel !
        
        result = dict() # a dictionary containig calibration data for this axis
        
        calibration_string = None
        
        name_string = None
        
        axiskey = None
        
        axisname = None
        
        axistype = None
        
        axisunits = None
        
        axisorigin = None
        
        axisresolution = None
        
        channels_dict = dict()
                
        # 1) find axis calibration string <axis_calibration> ... </axis_calibration>
        start = s.find("<axis_calibration>")
        
        if start > -1:
            stop  = s.find("</axis_calibration>")
            if stop > -1:
                stop += len("</axis_calibration>")
                calibration_string = s[start:stop]
        
        #print("parseDescriptionString calibration_string: %s" % calibration_string)
        
        # 2) parse axis calibration string if found
        if isinstance(calibration_string, str) and len(calibration_string.strip()) > 0:
            # OK, now extract the relevant xml string
            try:
                main_calibration_element = ET.fromstring(calibration_string)
                
                # make sure we're OK
                if main_calibration_element.tag != "axis_calibration":
                    raise ValueError("Wrong element tag; was expecting 'axis_calibration', instead got %s" % element.tag)
                
                element_children = main_calibration_element.getchildren()
                
                for child_element in element_children:
                    # these can be <childrenX> tags (X is a 0-based index) or a <name> tag
                    # ignore everything else
                    if child_element.tag.lower().startswith("channel"):
                        # found a channel XML element => this is a channel axis
                        
                        # use "channel" as boundary for split
                        cx = child_element.tag.lower().split("channel")
                        
                        # there may be no channel number
                        if len(cx[1].strip()):
                            chindex = eval(cx[1].strip())
                            
                        else: # no channel number => assign channel index 0 by default
                            chindex = len(channels_dict)
                            
                        try:
                            value = _parse_calibration_set_(child_element, True)
                            channels_dict[chindex] = value
                            
                            if channels_dict[chindex]["units"] == pq.dimensionless:
                                channels_dict[chindex]["units"] = arbitrary_unit
                            
                        except Exception as e:
                            # ignore failures
                            continue
                        
                    elif child_element.tag.lower() == "axiskey":
                        axiskey = child_element.text
                        
                    elif child_element.tag.lower() == "axistype":
                        axistype = axisTypeFromString(child_element.text)
                    
                    elif child_element.tag.lower() in ("axisname", "name"):
                        axisname = child_element.text # axis name!
                        
                    elif child_element.tag.lower() == "units":
                        axisunits = unit_quantity_from_name_or_symbol(child_element.text)
                        
                    elif child_element.tag == "origin":
                        if len(child_element.text) == 0:
                            axisorigin = 0.0
                        
                        else:
                            try:
                                axisorigin = eval(child_element.text)
                                
                            except Exception as err:
                                traceback.print_exc()
                                #print("".format(err))
                                #print("Unexpected error:", sys.exc_info()[0])
                                warnings.warn("String could not be evaluated to a number or None", RuntimeWarning)
                                    
                                axisorigin = 0.0
                        
                    elif child_element.tag == "resolution":
                        if len(child_element.text) == 0:
                            axisresolution = 1.0
                            
                        else:
                            try:
                                axisresolution = eval(child_element.text)
                                
                            except Exception as err:
                                traceback.print_exc()
                                #print("".format(err))
                                #print("Unexpected error:", sys.exc_info()[0])
                                warnings.warn("String could not be evaluated to a number or None", RuntimeWarning)
                                
                                axisresolution = 1.0
                                
            except Exception as e:
                traceback.print_exc()
                print("cannot parse calibration string %s" % calibration_string)
                raise e
            
        # 3) find name string <name> ... </name> for data from old API
                
        start = s.find("<name>")
        
        if start  > -1:
            stop = s.find("</name>")
            
            if stop > -1:
                stop += len("</name>")
                name_string = s[start:stop]
        
        #print("parseDescriptionString Name string: %s" % name_string)
        
        # NOTE: 2018-08-22 15:13:32
        # old API has axis & channel names in a separate string
        if isinstance(name_string, str) and len(name_string.strip()):
            try:
                name_element = ET.fromstring(name_string)
                
                if name_element.tag != "name":
                    raise ValueError("Wrong element tag: expecting 'name', got %s instead" % name_element.tag)
                
                for child_element in name_element.getchildren():
                    if child_element.tag.startswith("channel"):
                        # check for a name element then add it if not already in result
                        cx = child_element.tag.split("channel")
                        
                        if len(cx[1].strip()):
                            chindex = eval(cx[1].strip())
                            
                        else:
                            chindex = len(channels_dict)
                            
                        # use this as name in case construct is
                        #<name><channelX>xxx</channelX></name>
                        chname = child_element.text
                        
                        #print(chname)
                        
                        ch_calibration = _parse_calibration_set_(child_element, True)
                        
                        #print("ch_calibration", ch_calibration)
                        
                        if ch_calibration["name"] is None:
                            ch_calibration["name"] = chname
                        
                        if ch_calibration["units"] == pq.dimensionless:
                            ch_calibration["units"] = arbitrary_unit
                        
                        if chindex in channels_dict.keys():
                            warnings.warn("AxisCalibration.parseDescriptionString: channel calibration for channel %d defined between separate <name>...</name> tags will overwrite the one defined in the main axis calibration string" % chindex, RuntimeWarning)
                            channels_dict[chindex].update(ch_calibration)
                            
                        else:
                            channels_dict[chindex] = ch_calibration
                            
            except Exception as e:
                traceback.print_exc()
                print("could not parse name string %s" % name_string)
                raise e
                
        # 4) check for inconsistencies
        if axisunits is None:
            axisunits = pixel_unit
            
        if axisorigin is None:
            axisorigin = 0.0
            
        if axisresolution is None:
            axisresolution = 1.0
        
        if axistype == vigra.AxisType.UnknownAxisType and axiskey != "?":
            axiskey = axisTypeFlags.get(axistype, "?")
                
        # infer axistype from axiskey, check if is the same as axistype
        typebykey = [k for k in axisTypeFlags if axisTypeFlags[k] == axistype]
        
        if len(typebykey) == 0:
            axiskey = "?"
            axistype = vigra.AxisType.UnknownAxisType
            
        else:
            if axistype != typebykey:
                axiskey = axisTypeFlags[axistype]
        
        # 5) finally, populate the result
        
        result["axisname"]  = axisname
        result["axiskey"]   = axiskey
        result["axistype"]  = axistype
        
        # NOTE: overridden in __init__!
        #if axistype & vigra.AxisType.Channels: 
        if len(channels_dict) == 0:
            # no channel defined for a Channel Axis
            result[0] = dict()
            result[0]["name"] = axisname
            
            # NOTE: overriden in __init__!
            #if axisunits == pq.dimensionless:
                #axisunits = arbitrary_unit
                
            result[0]["units"] = axisunits
            result[0]["origin"] = axisorigin
            result[0]["resolution"] = axisresolution
            
        else:
            for channel_index in channels_dict.keys():
                result[channel_index] = channels_dict[channel_index]
            
                
        # NOTE: overridden in __init__ to sort things out
        #else:
            #if axisunits == pq.dimensionless:
                #axisunits = pixel_unit
                
        result["units"]     = axisunits
        result["origin"]    = axisorigin
        result["resolution"]= axisresolution
            
        #print("parseDescriptionString result:", result)
        
        return result
        
    @staticmethod
    def hasNameString(s):
        if not isinstance(s, str):
            raise TypeError("expecting a str; got %s instead" % type(s).__name__)
        
        return "<name>" in s and "</name>" in s
    
    @staticmethod
    def hasCalibrationString(s):
        """Simple test for what MAY look like a calibration string.
        Does nothing more than saving some typing; in particular it DOES NOT verify
        that the calibration string is conformant.
        
        NOTE: Parameter checking is implicit
        
        """
        return "<axis_calibration>" in s and "</axis_calibration>" in s

    @staticmethod
    def isAxisCalibrated(axisinfo):
        """Syntactic shorthand for hasCalibrationString(axisinfo.description).
        
        NOTE: Parameter checking is implicit
        
        """
        return AxisCalibration.hasCalibrationString(axisinfo.description)
    
    @staticmethod
    def removeCalibrationData(axInfo):
        if not isinstance(axInfo, vigra.AxisInfo):
            raise TypeError("Expecting a vigra.AxisInfo object; got %s instead" % type(axInfo).__name__)

        axInfo.description = AxisCalibration.removeCalibrationFromString(axInfo.description)
        
        return axInfo
    
    @staticmethod
    def removeCalibrationFromString(s):
        """Returns a copy of the string with any calibration substrings removed.
        Convenience function to clean up AxisInfo description strings.
        
        NOTE: Parameter checking is implicit
        
        """
        
        if not isinstance(s, str):
            raise TypeError("Expecting a string; got %s instead" % type(s).__name__)
        
        name_start = s.find("<name>")
        
        if name_start  > -1:
            name_stop = s.find("</name>")
            
            if name_stop > -1:
                name_stop += len("</name>")
                
            else:
                name_stop = name_start + len("<name>")
                
            d = [s[0:name_start].strip()]
            d.append([s[name_stop:].strip()])
            
            s = " ".join(d)
        
        calstr_start = s.find("<axis_calibration>")
        
        if calstr_start > -1:
            calstr_end = s.rfind("</axis_calibration>")
            
            if calstr_end > -1:
                calstr_end += len("</axis_calibration>")
                
            else:
                calstr_end = calstr_start + len("<axis_calibration>")
                
            s1 = [s[0:calstr_start].strip()]
            
            s1.append(s[calstr_end:].strip())
            
            return " ".join(s1)
        
        else:
            return s

    def setChannelName(self, channel_index, value):
        """Sets the name for the given channel of an existing Channels axis in this calibration object.
        
        Raises KeyError if no Channel axis exists, or if channel_index is not found
        """
        if self.axistags.channelIndex == len(self.axistags):
            raise KeyError("No channel axis exists in this calibration object")
        
        #if isinstance(key, vigra.AxisInfo):
            #key = key.key
            
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
            
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Channel axis %s does not have calibration data" % key)
        
        if isinstance(value, (str, type(None))):
            if channel_index in self._calibration_[key].keys():
                self._calibration_[key][channel_index]["name"] = value
                
            else:
                user_calibration = dict()
                user_calibration["name"] = value
                user_calibration["units"] = arbitrary_unit
                user_calibration["origin"] = 0.0
                user_calibration["resolution"] = 1.0
                self._calibration_[key][channel_index] = user_calibration
            
        else:
            raise TypeError("channel name must be a str or None; got %s instead" % type(value).__name__)
        
    def setChannelCalibration(self, channel_index, name=None, units=arbitrary_unit, origin=0.0, resolution=1.0):
        """Sets up channel calibration items (units, origin and resolution) for channel with specified index
        
        If channel_index does not yet exist, it is added to the channel axis calibration
        
        """
        if self.axistags.channelIndex == len(self.axistags):
            raise KeyError("No channel axis exists in this calibration object")
        
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
            
        if not isinstance(channel_index, int):
            raise TypeError("new channel index expected to be an int; got %s instead" % type(channel_index).__name__)
        
        if channel_index < 0:
            raise ValueError("new channel index must be >= 0; got %s instead" % channel_index)
        
        if key not in self._calibration_.keys():
            raise RuntimeError("Channel axis does not have calibration data")
        
        user_calibration = dict()
        
        if isinstance(name, (str, type(None))):
            user_calibration["name"] = name
            
        else:
            raise TypeError("name expected to be a str or None; got %s instead" % type(name).__name__)
        
        if not isinstance(units, (pq.Quantity, pq.UnitQuantity)):
            raise TypeError("Channel units are expected ot be a python Quantity or UnitQuantity; got %s instead" % type(units).__name__)
        
        user_calibration["units"] = units
        
        if isinstance(origin, numbers.Number):
            user_calibration["origin"] = origin
        
        elif isinstance(origin, pq.Quantity):
            if origin.magnitude.size != 1:
                raise ValueError("origin must be a scalar Python Quantity; got %s instead" % origin)
            
            if user_calibration["units"] == pq.dimensionless:
                # allow origin to set units if not set by units
                user_calibration["units"] = origin.units
                
            else:
                # check origin and units are compatible
                mydims = pq.quantity.validate_dimensionality(user_calibration["units"])
                origindims = pq.quantity.validate_dimensionality(origin.units)
                
                if mydims != origindims:
                    try:
                        cf = pq.quantity.get_conversion_factor(origindims, mydims)
                        
                    except AssertionError:
                        raise ValueError("Cannot convert from origin units (%s) to %s" % (origindims.dimensionality, mydims.dimensionality))
                    
                    origin *= cf
                    
            user_calibration["origin"] = origin.magnitude.flatten()[0]
                
        else:
            raise TypeError("origin must be a float scalar or a scalar Python Quantity; got %s instead" % type(origin).__name__)
            
                
        if isinstance(resolution, numbers.Number):
            user_calibration["resolution"] = resolution #* user_calibration["units"]
            
        elif isinstance(resolution, pq.Quantity):
            if resolution.magnitude.size  != 1:
                raise ValueError("resolution must be a scalar quantity; got %s instead" % resolution)
            
            mydims = pq.quantity.validate_dimensionality(user_calibration["units"])
            resdims = pq.quantity.validate_dimensionality(resolution.units)
            
            if mydims != resdims:
                try:
                    cf = pq.quantity.get_conversion_factor(resdims, mydims)
                    
                except AssertionError:
                    raise ValueError("Cannot convert from resolution units (%s) to %s" % (resdims.dimensionality, mydims.dimensionality))
                
                resolution *= cf
                
            user_calibration["resolution"] = resolution.magnitude.flatten()[0]
            
        else:
            raise TypeError("resolution expected to be a scalar float or Python Quantity; got %s instead" % type(resolution).__name__)
            
        if channel_index in self._calibration_[key].keys():
            self._calibration_[key][channel_index].update(user_calibration)
            
        else:
            self._calibration_[key][channel_index] = user_calibration
        
    def removeChannelCalibration(self, channel_index):
        if self.axistags.channelIndex == len(self.axistags):
            raise KeyError("No channel axis exists in this calibration object")
        
        channelAxis = self.axistags[self.axistags.channelIndex]
        
        key = channelAxis.key
            
        if not isinstance(channel_index, int):
            raise TypeError("new channel index expected to be an int; got %s instead" % type(channel_index).__name__)
        
        channel_indices = [k for k in self._calibration_[key].keys() if isinstance(k, int)]
        
        if key not in self._calibration_.keys():
            raise KeyError("Channel axis has no calibration")
        
        if len(channel_indices) == 0:
            raise KeyError("No channel calibrations defined for axis %s with key %s" % (self._calibration_[key]["axisname"], self._calibration_[key]["axiskey"]))
        
        if channel_index not in self._calibration_[key].keys():
            if channel_index < 0 or channel_index >= len(channel_indices):
                raise KeyError("Channel %d not found for axis %s with key %s" % (channel_index, self._calibration_[key]["axisname"], self._calibration_[key]["axiskey"]))
                
            channel_index = channel_indices[channel_index]
            raise KeyError("Channel %d not found for the channel axis" % channel_index)
        
        del self._calibration_[key][channel_index]
        
    def rescaleUnits(self, value, key, channel=0):
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if isinstance(value, (pq.Quantity, pq.UnitQuantity)):
            try:
                origin = self.getOrigin(key, channel)
                origin.rescale(value)
                
            except AssertionError:
                raise ValueError("Cannot convert from current units (%s) to %s" % (self.getUnits(key, channel), value.units))
            
            try:
                resolution = self.getResolution(key, channel)
                resolution.rescale(value)
                
            except AssertionError:
                raise ValueError("Cannot convert from current units (%s) to %s" % (self.getUnits(key, channel), value.units))
            
            if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
                if channel not in self._calibration_[key].keys():
                    channel_indices = [k for k in self._calibration_[key].keys() is isinstance(k, int)]
                    if len(channel_indices) == 0:
                        raise RuntimeError("No channel calibration data found")
                    
                    if channel < 0 or channel >= len(channel_indices):
                        raise RuntimeError("No calibration data for channel %d" % channel)
                    
                    channel = channel_indices[channel]
                    
                self._calibration_[key][channel]["units"] = value.units
                self._calibration_[key][channel]["origin"] = origin.magnitude.flatten()[0]
                self._calibration_[key][channel]["resolution"] = resolution.flatten()[0]
                
            else:
                self._calibration_[key]["units"] = value.units
                self._calibration_[key]["origin"] = origin.magnitude.flatten()[0]
                self._calibration_[key]["resolution"] = resolution.flatten()[0]
                
        else:
            raise TypeError("Expecting a Python Quantity or UnitQuantity; got %s instead" % type(value).__name__)
        
    def calibrateAxes(self):
        """Attachches a calibration string to all axes registered with this object
        """
        for ax in self._axistags_:
            self.calibrateAxis(ax)
        
    def calibrateAxis(self, axInfo):
        """Attaches a dimensional calibration to an AxisInfo object.
        Calibration is inserted as an xml-formatted string.
        (see AxisCalibration.calibrationString())
        
        The axInfo AxisInfo object does not need to be part of the axistags 
        collection calibrated by this AxisCalibration object i.e., "external" 
        (independent) AxisInfo objects can also get a calibration string in their 
        description attribute.
        
        The only PREREQUISITE is that the "key" and "typeFlags" attributes of the
        axInfo parameter MUST be mapped to calibration data in this AxisCalibration
        object.
        
        Positional parameters:
        ====================
        axInfo = a vigra.AxisInfo object
        
        Returns:
        ========
        
        A reference to the axInfo with modified description string containing calibration
        information.
        
        What this function does:
        ========================
        The function creates an XML-formatted calibration string (see 
        AxisCalibration.calibrationString(key)) that will be inserted in the 
        description attribute of the axInfo parameter
            
        NOTE (1) If axInfo.description already contains a calibration string, it will 
        be replaced with a new calibration string. No dimensional analysis takes place.
        
        NOTE (2) The default value for the resolution in vigra.AxisInfo is 0.0, which 
        is not suitable. When axInfo.resolution == 0.0, and no resolution parameter
        is supplied, the function will set its value to 1.0; otherwise, resolution 
        will take the value provided in the axInfo.
        
        """
        if not isinstance(axInfo, vigra.AxisInfo):
            raise TypeError("First argument must be a vigra.AxisInfo; got %s instead" % type(axInfo).__name__)
        
        # check if an axistag like the one in axInfo is present in this calibration object
        # NOTE: this does NOT mean that axInfo is registered with this calibration object
        # but we need ot make sure we copy the calibration data across like axes
        if axInfo.key not in self._calibration_.keys() or axInfo.key not in self._axistags_:
            raise KeyError("No calibration data found for axis with key: %s and typeFlags: %s)" % (axInfo.key, axInfo.typeFlags))
            
        if axInfo.typeFlags != self._calibration_[axInfo.key]["axistype"]:
            raise ValueError("The AxisInfo parameter with key %s has a different type (%s) than the one for which calibrationd data exists (%s)" \
                            % (axInfo.key, axInfo.typeFlags, self._calibration_[axInfo.key]["axistype"]))
            
        calibration_string = self.calibrationString(axInfo.key)
        # check if there already is (are) any calibration string(s) in axInfo description
        # then replace them with a single xml-formatted calibration string
        # generated above
        # otherwise just append the calibration string to the description
        
        # 1) first, remove any name string
        name_start = axInfo.description.find("<name>")
        
        if name_start  > -1:
            name_stop = axInfo.description.find("</name>")
            
            if name_stop > -1:
                name_stop += len("</name>")
                
            else:
                name_stop = name_start + len("<name>")
                
            d = [axInfo.description[0:name_start].strip()]
            d.append(axInfo.description[name_stop:].strip())
            
            axInfo.description = " ".join(d)
        
        # 2) then find if there is a previous calibration string in the description
        calstr_start = axInfo.description.find("<axis_calibration>")
        
        if calstr_start > -1: # found previous calibration string
            calstr_end = axInfo.description.rfind("</axis_calibration>")
            
            if calstr_end > -1:
                calstr_end += len("</axis_calibration>")
                
            else:
                calstr_end  = calstr_start + len("<axis_calibration>")
                
            # remove previous calibration string
            # not interested in what is between these two (susbstring may contain rubbish)
            # because we're replacing it anyway
            # just keep the non-calibration contents of the axis info description 
            s1 = [axInfo.description[0:calstr_start].strip()]
            s1.append(axInfo.description[calstr_end:].strip())
            
            s1.append(self.calibrationString(axInfo.key))
            
        else: 
            s1 = [axInfo.description]
            s1.append(self.calibrationString(axInfo.key))
            
        axInfo.description = " ".join(s1)
        
        #print("calibrateAxis: %s" % axInfo.description)
        if not axInfo.isChannel():
            # also update the axis resolution -- but only if axis is not a channel axis
            # (channel resolution is set into <channelX> </channelX> tags)
            axInfo.resolution = self.getDimensionlessResolution(axInfo.key)
            
        else:
            # the resolution of the first channel should be acceptable in most cases
            axInfo.resolution = self.getDimensionlessResolution(axInfo.key, 0)
            
        return axInfo # for convenience
    
    def getCalibratedAxisLength(self, image, key, channel = 0):
        if isinstance(key, vigra.AxisInfo):
            return self.getCalibratedAxialDistance(image.shape[image.axistags.index(key.key)], key, channel)
            
        else:
            return self.getCalibratedAxialDistance(image.shape[image.axistags.index(key)], key, channel)
    
    def getDistanceInSamples(self, value, key, channel=0):
        """Conversion of a calibrated distance in number of samples along the axis.
        """
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis %s not found in this AxisCalibration object" % key)
        
        if isinstance(value, numbers.Real):
            value *= self._calibration_[key][channel]["units"]
            
        elif not isinstance(value, pq.Quantity):
            raise TypeError("Expecting a python Quantity; got %s instead" % type(value).__name__)
        
        if value.size != 1:
            raise TypeError("Expecting a scalar quantity; got %s instead" % value.size)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            if channel not in self._calibration_[key].keys():
                raise KeyError("Channel %d not found for axis %s with key %s" % (channel, self._calibration_[key]["axisname"], self._calibration_[key]["axiskey"]))
            
            myunits = self._calibration_[key][channel]["units"]
            myresolution = self._calibration_[key][channel]["resolution"]
            
        else:
            myunits = self._calibration_[key]["units"]
            myresolution = self._calibration_[key]["resolution"]
        
        value_dim = pq.quantity.validate_dimensionality(value.units)
        self_dim  = pq.quantity.validate_dimensionality(myunits)
        
        if value_dim != self_dim:
            try:
                cf = pq.quantity.get_conversion_factor(self_dim, value_dim)
                
            except AssertionError:
                raise ValueError("Cannot compare the value's %s units with %s" % (value_dim.dimensionality, self._dim.dimensionality))
            
            value *= cf
            
        result = float((value / self.getDimensionlessResolution(key, channel)))
        
        return result
    
    def getCalibratedAxialDistance(self, value, key, channel=0):
        """Converts distance in sample along an axis into a calibrated distance in axis units
        """
        if not isinstance(value, numbers.Number):
            raise TypeError("expecting a scalar; got %s instead" % type(value).__name__)
        
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        return (value * self.getDimensionlessResolution(key, channel)) * self.getUnits(key, channel)
    
    def getCalibratedAxisCoordinate(self, value, key, channel=0):
        if not isinstance(value, numbers.Number):
            raise TypeError("expecting a scalar; got %s instead" % type(value).__name__)
        
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        return (value * self.getDimensionlessResolution(key, channel) + self.getDimensionlessOrigin(key, channel)) * self.getUnits(key, channel)
    
    def getCalibrationTuple(self, key, channel=0):
        """Returns (units, origin, resolution) tuple for axis with specified key.
        For Channels axis, returns the tuple for the specified channel.
        """
        if isinstance(key, vigra.AxisInfo):
            key = key.key
        
        if key not in self._calibration_.keys() or key not in self._axistags_:
            raise KeyError("Axis with key %s is not calibrated by this object" % key)
        
        if self._calibration_[key]["axistype"] & vigra.AxisType.Channels:
            if channel not in self._calibration_[key].keys():
                raise KeyError("Channel %d not found for axis %s with key %s" % (channel, self._calibration_[key]["axisname"], self._calibration_[key]["axiskey"]))
            
            return(self._calibration_[key][channel]["units"], self._calibration_[key][channel]["origin"], self._calibration_[key][channel]["resolution"])
        
        return(self._calibration_[key]["units"], self._calibration_[key]["origin"], self._calibration_[key]["resolution"])

        
        if isinstance(channel, int):
            if channel not in self._calibration_.keys():
                raise ValueError("channel %d has no calibration data" % channel)
            
            return ()
        
        elif channel is None:
            return (self.origin, self.resolution)
        
        else:
            raise TypeError("channel expected to be an int or None; got %s instead" % type(channel).__name__)
        
