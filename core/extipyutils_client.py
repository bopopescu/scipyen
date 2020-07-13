# -*- coding: utf-8 -*-
"""Module with utilities for an external IPython kernel.
To be used on the client side (i.e. Scipyen app side)
"""
# on the client side, in a received execute_reply message the keys of
# msg["content"]["user_expressions"] are identical to those in the
# sent execute_request message["content"]["user_expressions"] NOTE that such
# execute_request message is sent when client.execute(...) is called, and the 
# user_expressions field of the message gets the valueof the user_expressions
# parameter ot that call.

# NOTE 2020-07-11 10:26:38
# Strategies for getting information about the properties of an object located
# in the remote kernel namespace
# 
# A. Break it down in steps:
#
# 1. define a custom function in the remote kernel namespace by sending this
# string as a code string (1st execute() call)
#
# 2. run the newly created function in the remote kernel, this time as part
# of an "user_expressions" dict (2nd execute() call)
#
# 3. (optionally) delete the custom function from the remote kernel namespace
# to avoid clutter (3rd execute() call).
#
# B. Copy the data to the local namespace, get its properties there, then
# delete the data.
#
# C. For selected operations only we could simply import the relevant modules
# and/or functions at launching the remote kernel, especially if they are also
# useful for operations inside the remote kernel namespace.
# 
# An example would be core.utilities.summarize_object_properties() function
# that retrieves informative properties of an object as type, size, etc).

# Advantages of strategy A:
# 1. does not require data serialization, 
# 2. avoids cluttering the remote kernel namespace with modules that are 
# only for accomplishing the particular operation
# 3. can be scaled to several steps, if necessary
# 
# Prerequisites for strategy A:
# a. the operation to be accomplished by the client can be broken down in steps
# b. data relevant to the client is received via the "user_expressions" dict 
#    of "execute_reply" messages (e.g. step 2 above)
# c. the "execute_reply" messages containing relevant "user_expressions" need 
#    to be easily distinguished from other "execute_reply" messages (e.g. using
#    naming conventions for the keys in "user_expressions" dict) 
# d. moreover, the "user expressions" code generating data in the relevant
#    "execute_reply" messages should not rely on data from previous "execute_reply"
#    "user_expressions" content (these messages are received and processed 
#    on the client side asynchronously, via Qt signal/slot mechanism, and
#    therefore such dependencies would require a clever mechanism 
#    (coroutines etc. TODO: investigate this)
#
# Strategy B is less cumbersome that Strategy A, but can create heavy traffic
# between the remote kernel and the client, because is relies on data
# serialization & transfer (so even if this happens on the same physical 
# machine, we still may end up transferring megabytes of data and incur 
# serialization/deserialization overheads.)
#
# Strategy C is probably the easiest (and most economical) but could be
# easily abused by importing into the remote namespace functions and modules 
# that end up only being used by the client, in the local namespace.

import os, sys, pickle, inspect, typing
from functools import wraps
from core.traitcontainers import DataBag
#from contextlib import contextmanager
#print(sys.path)

__module_path__ = os.path.abspath(os.path.dirname(__file__))

# NOTE: 2016-04-03 00:17:42
__module_name__ = os.path.splitext(os.path.basename(__file__))[0]

nrn_ipython_initialization_file = os.path.join(os.path.dirname(__module_path__),"neuron_python", "nrn_ipython.py")
nrn_ipython_initialization_cmd = "".join(["run -i -n ", nrn_ipython_initialization_file])

init_commands = ["import sys, os, io, warnings, numbers, types, typing, re, importlib",
                 "import traceback, keyword, inspect, itertools, functools, collections",
                 "import signal, pickle, json, csv",
                 "from importlib import reload",
                 "".join(["sys.path.insert(2, '", os.path.dirname(__module_path__), "')"]),
                 "from core import extipyutils_host as hostutils"
                 #"from IPython.lib.deepreload import reload as dreload",
                 #"sys.path=['" + sys.path[0] +"'] + sys.path",
                 ]



class ForeignCall(DataBag):
    """Usage:
    call = ForeignCall(user_expressions={"test":"etc"})
    
    kernel_client.execute(*call())
    
    kernel_client.execute(**call.dict())
    
    """
    def __init__(self, code="", silent=True, store_history=False, user_expressions=None,
                 allow_stdin=None, stop_on_error=True):
        
        super().__init__(code=code, silent=silent, store_history=store_history,
                         user_expressions=user_expressions,
                         allow_stdin=allow_stdin, stop_on_error=stop_on_error)
            
    def __call__(self):
        yield from (self.code,
                self.silent,
                self.store_history,
                self.user_expressions,
                self.allow_stdin,
                self.stop_on_error,
                )
    
    def dict(self):
        return {"code":self.code,
                "silent":self.silent,
                "store_history":self.store_history,
                "user_expressions":self.user_expressions,
                "allow_stdin": self.allow_stdin,
                "stop_on_error":self.stop_on_error,
                }
    
    def copy(self):
        return ForeignCall(self.code, self.silent, self.store_history,
                           self.user_expressions, self.allow_stdin,
                           self.stop_on_error)

#### BEGIN expression generators    

def make_user_expression(**kwargs):
    """TODO Generates a single user_expressions string for execution in a remote kernel.

    The user_expressions parameter to the kernel local client's execute() is a 
    dict mapping some name (local to the calling namespace) to a command string
    that is to be evaluated in the remote kernel namespace. 
    
    user_expressions = {"output": expression_cmd}
    
    Upon execute() call, the remote kernel executes the 'expression_cmd' and
    the returned object is mapped to the "output" key in user_expressions, 
    embedded in the 'execute_reply' message received from the remote kernel 
    via the kernel client's shell channel.
    
    The message received from the remote kernel contains:
    (NOTE that only the relevant key/value pairs are listed below)
    
    message["content"]["user_expressions"]: a dict with the following key/value
    pairs:
    
    local_name ->  user_sub_expression dict(): a nested dict with the key/value  pairs:
    
        "status" -> str = OK when the message passing from the kernel was successful
        
        "data" -> dict() -  with the mapping:
        
            "status" -> str = "ok" when 'expression_cmd' execution was successful
            
            "text/plain" -> str  = string representation of the result of 
                                    'expression_cmd' execution in the remote 
                                    kernel namespace. 
                                    
                                    This may be a byte array, when is the result 
                                    of serialization in the remote kernel
                                    namespace (see below).
                                    
    A successful execute(...) call is indicated when the next conditions are
    simultaneously satisfied:
    
        message["content"]["status"] == "ok"
        
        message["content"]["user_expressions"][local_name]["status"] == "ok"
        
    As stated above, the string representation of the result is in
    
    message["content"]["user_expressions"][local_name]["data"]["text/plain"]
    
    In the example above, local_name is "output".
                                    
    Sometimes it is useful to get the objects returned by evaluating 'expression_cmd',
    not just their string representation. This is possible only for objects that
    can be serialized (using the pickle module).
    
    In this case, 'expression_cmd' must instruct the remote kernel to "pack" 
    the remote execution result itself into a serializable object, such as a 
    dictionary, then pickle it (as bytes) to a string. 
    
    Such a "pickled" command has the (strict) syntax:
    
    "pickle.dumps({...})" 
    
        where {...} is the python text code for generating the dictionary in the
        remote kernel namespace
    
    For example, given the expression "dir()", the following:
    
        pickled_sub_expression_cmd = "pickle.dumps({'namespace': dir()})"
        
        binds the result of dir() (a list of str - the contents of the remote
        kernel namespace) to the symbol "namespace".
        
    In turn, the containing user_expressions on the call side would be:
        {'namespace':pickled_sub_expression_cmd}
        
    and the string representation of the serialized dict 
        {"namespace":<result of dir()>} will be assigned to
    
        message["contents"]["user_expressions"]["namespace"]["data"]["text/plain"]
        
        in the execute_reply message (provided execution was successful).
        
    Using a dictionary on the remote kernel "side" is not mandatory. A dict will
    bind the result to a symbol or a name, the key of the remote dictionary), 
    with the price that the result of the actual pickled expression of introducing
    a deeper level of nesting in the execute_reply message.
    
    
    This string (containing serialized bytes) is then mapped to the "text/plain"
    key in the "data" sub-dictionary of the particular user expression mapped
    to the appropriate local key name (in the example given here, "output")
    
    The serialized bytes will be placed as a string, in
    
        message["content"]["user_expressions"]["output"]["data"]["text/plain"]
    
    These can be deserialized in the calling namespace by executing pickle.loads(eval(x))
    
    where "x" is message["content"]["user_expressions"]["output"]["data"]["text/plain"]`
    
    
    Parameters:
    ----------
    **kwargs:
    
    
    
    Returns:
    --------
    
    A str with the contents of the expression_cmd
    
    
    Where:
        key is a quoted str (i.e. must evaluate to a string in the remote kernel)
        
        expression is a str that must evaliuate to a valid expression in the remote kernel
    
    """
    
    pass

def pickle_wrap_expr(expr):
    if not isinstance(expr, str):
        raise TypeError("expecting a str, got %s" % type(expr).__name__)
    
    return "".join(["pickle.dumps(",expr,")"])
    
def define_foreign_data_props_getter_fun_str(dataname:str, namespace:str="Internal") -> str:
    """Defines a function to retieve object properties in the foreign namespace.
    
    The function is wrapped by a context manager so that any module imports are
    are not reflected in the foreign namespace.
    
    The function should be removed from the foreign ns after use.
    """
    return "\n".join(["@hostutils.contextExecutor()", # core.extipyutils_host is imported remotely as hostutils
    "def f(objname, obj):",                           # use regular function wrapped in a context manager
    "    from core.utilities import summarize_object_properties",
    "    return summarize_object_properties(objname, obj, namespace='%s')" % namespace,
    "", # ensure NEWLINE
    ])

def define_foreign_data_props_getter_gen_str(dataname:str, namespace:str="Internal") -> str:
    """Defines a generator to retrieve object properties in the foreign namespace.
    
    The function is decorated with @contextmanager hence behaves like such, and
    any module imports are not reflected in the foreign namespace.
    
    The downside of this strategy is that it creates temporary data in the foreign
    namespace, which will have to be removed alongside with the generator, after 
    use.
    """
    return "\n".join(["@hostutils.contextmanager", # core.extipyutils_host is imported remotely as hostutils
    "def f_gen(objname, obj):",             # use a generator func
    "    from core.utilities import summarize_object_properties",
    "    yield summarize_object_properties(objname, obj, namespace='%s')" % namespace,
    "",                                                     # ensure NEWLINE
     ])
    
#### END expression generators

#### BEGIN call generators

def cmds_get_foreign_data_props(dataname:str, namespace:str="Internal") -> list:
    """Creates a list of execute calls retrieving data properties in foregn ns
    
    """
    # see NOTE 2020-07-11 10:26:3`8
    #
    # NOTE: user_expressions code should be one-liners; it does not accept
    # compound statements such as function definitions, with context manager 
    # statements even when written on one line (there is a mandatory colon, ":")
    # etc.
    exec_calls = list()
    
    special = "properties_of_"
    
    # Using strategy A (see NOTE 2020-07-11 10:26:38):
    
    #### BEGIN variant 1 - works
    # execution expression to define the function that retrieves the data properties
    cmd = define_foreign_data_props_getter_fun_str(dataname,namespace)
    
    # executes the definition of the function
    exec_calls.append(ForeignCall(code=cmd))
    #exec_calls.append({"code":cmd, "silent": True, "store_history":False, 
                       #"user_expressions": None})
    
    # calls the function defined above then captures the result in user_expressions
    exec_calls.append(ForeignCall(user_expressions={"%s_%s" % (special, dataname): "".join(["f('", dataname, "', ", dataname, ")"])}))
    #exec_calls.append({"code": "", "silent": True, "store_history":False, 
                       #"user_expressions": {"%s_%s" % (special, dataname): "".join(["f('", dataname, "', ", dataname, ")"])}})
    
    # cleans up after use.
    exec_calls.append(ForeignCall(code="del f"))
    #exec_calls.append({"code": "del f", "silent": True, "store_history":False, 
                       #"user_expressions": None})
    
    #### END variant 1
    
    ##### BEGIN variant 3 - no joy - remote kernel reports attribute error __enter__
    # when using a generator instead of a function -- why ??!
    #cmd1 = "\n".join(["@hostutils.contextExecutor()", # core.extipyutils_host is imported remotely as hostutils
    #"def f_gen(objname, obj):",             # use a generator func
    #"    from core.utilities import summarize_object_properties",
    #"    yield summarize_object_properties(objname, obj)",
    #"",                                                     # ensure NEWLINE
     #])
    #exec_calls.append({"code": cmd1, "user_expressions":None})
    #exec_calls.append({"code": "".join(["with f_gen('", dataname, "', ", dataname, ") as ", "obj_props_%s:" % dataname, " pass"]),
                       #"user_expressions": None})
    #exec_calls.append({"code": "",
                       #"user_expressions": {"obj_props_%s:" % dataname: "obj_props_%s" % dataname}})
    
    ##exec_calls.append({"code":"del f_gen"})
    
    ##### END variant 2
    return exec_calls
    
def cmds_get_foreign_data_props2(dataname:str, namespace:str="Internal") -> list:
    """Creates a list of execute calls retrieving data properties in foregn ns
    
    """
    #### BEGIN variant 2 - works but the with statement must be executed (hence
    # passed as code , not as part of user_expressions)
    # a bit more convoluted, as it creates sub_special_%(dataname) in the foreign namespace
    special = "properties_of_"
    sub_special = "obj_props_"
    
     # defines a generator fcn decorated with contextmanager
    cmd1 = define_foreign_data_props_getter_gen_str(dataname, namespace)
    
    # creates the with ... as ... statement; upon execution it creates the 
    # sub_special_%(dataname) in the foreign namespace
    cmd2 = "".join(["with f_gen('", dataname, "', ", dataname, ") as ", "%s_%s:" % (sub_special,dataname), " pass"])
    
    # executes the definition of the generator fcn (cmd1)
    exec_calls.append(ForeignCall(code = cmd1))
    #exec_calls.append({"code": cmd1, "silent": True, "store_history":False, 
                       #"user_expressions": None})
    
    # executes the with context manager statement (cmd2)
    exec_calls.append(ForeignCall(code=cmd2))
    #exec_calls.append({"code": cmd2, "silent": True, "store_history":False, 
                       #"user_expressions": None})
    
    # assigns the result of the previous exec, to user_expressions
    exec_calls.append(ForeignCall(user_expressions ={"%s_%s" % (special, dataname): "%s_%s" % (sub_special,dataname)}))
    
    # clean up after use
    exec_calls.append(ForeignCall(code = "del(f_gen, %s_%s)" % (sub_special,dataname)))
    
    #exec_calls.append({"code": "del(f_gen, %s_%s)" % (sub_special,dataname), "silent": True, "store_history":False, 
                       #"user_expressions": None})
    
    
    #### END variant 3
    
    return exec_calls
    
def cmd_fetch_copy_of_foreign_variable(varname:str, as_call=True) -> typing.Union[ForeignCall, dict]:
    """Create user expression to fetch varname from a foreign kernel's namespace.
    
    The foreign kernel is the with which the kernel client executing this command
    is communicating.
    
    Parameters:
    -----------
    varname : str - the name (identifier) to which a variable we wish to fetch
            from the remote kernel namespace, is bound.
            
    as_call: bool, default True
    
        When True, returns a ForeignCall which can be passed to execute, e.g.
        ExternalIPython.execute(*call())
        
        Otherwise, return a dict usable as a user_expressions key/value mapping
    
    Returns:
    --------
    
    If as_call is False:
        A dict with a single key, "varname", mapped to a command string that, when
        executed in the remote kernel, will be substituted with the serialized
        (pickled) variable named "varname" (as a byte string) upon evaluation
        by the remote kernel.
        
        The seralized data is then captured in the "execute_reply" message received
        from the remote kernel via its client's shell channel.
        
        
    To be evaluated in the remote kernel and the result captured in Scipyen, the 
    dict must be included inside the "user_expressions" parameter to execute()
    method of the client for the remote kernel.
    
    Once captured in the "execute_reply" message, the variable can be deserialized
    in Scipyen's workspace, by passing the received "execute_reply" message to the 
    using unpack_data_recvd_on_shell_chnl() function.
    
    If as_call is True:
        A ForeignCall object with user_expression set to the dict as explained above.
    
    
    NOTE: This mechanism creates in the caller's namespace copies of the data 
    existing in the remote kernel (byte-to-byte identical to their originals).
    
    To fetch several variables use cmd_fetch_copies_of_foreign_variables().
    
    See also unpack_data_recvd_on_shell_chnl.
    
    For details about messaging in Jupyter see:
    
    https://jupyter-client.readthedocs.io/en/latest/messaging.html
    
    """
    special = "pickled_"
    
    #expr = {"%s_%s" % (special,varname):"".join(["pickle.dumps({'",varname,"':",varname,"})",])}
    
    remote_expr = "{'",varname,"':",varname,"}"
    
    expr = {"%s_%s" % (special,varname):pickle_wrap_expr(remote_expr)}
    
    if as_call:
        return ForeignCall(user_expressions = expr)
    
    else:
        return expr

def cmd_fetch_copies_of_foreign_variables(*args, as_call=True) -> typing.Union[ForeignCall, dict]:
    """Create user expressions to fetch several variables from a foreign kernel.
    
    The foreign kernel is the with which the kernel client executing this command
    is communicating.
    
    Parameter:
    ---------
    args - variable sequence of strings - the names of the variables we want to
            fetch from the remote kernel
            
            This function calls cmd_fetch_copy_of_foreign_variable() for each element 
            in args then merges the results in a dict.
            
            
    as_call: bool, optional (default True)
        Whe True, returns a ForeignCall; otherwise, returns a user-expresions dict
            
    Returns:
    ---------
    
    If as_call is False:
        A dict with several key:value pairs, where each key is a (unique) varname
        in *args, and values are command strings to be evaluated by the remote 
        kernel in its own namespace.
        
        When evaluated, the commands trigger the serialization (pickling) of the
        named variables in the remote kernel.
            
    Similar to cmd_fetch_copy_of_foreign_variable() function, the dict returned 
    here needs to be included in the "user_expressions" parameter of the kernel's 
    client execute() method.
    
    The fetched variables are shuttled back into client code in serialized form 
    (pickled str bytes) via the "execute_reply" shell channel message. From there
    variables are recovered by passing the "execute_reply" message to the 
    unpack_data_recvd_on_shell_chnl() function.
    
    When as_call is true (default):
        A ForeignCall with the user_expressions set to the dict with structure
        as explained above.
    
    
    See also unpack_data_recvd_on_shell_chnl.
    
    For details about messaging in Jupyter see:
    
    https://jupyter-client.readthedocs.io/en/latest/messaging.html
    
    """
    import itertools
    vardicts = (cmd_fetch_copy_of_foreign_variable(arg, as_call=False) for arg in args)
    
    expr = dict((x for x in itertools.chain(*(a.items() for a in vardicts))))
    
    if as_call:
        return ForeignCall(user_expressions = expr)

    return expr

def cmd_push_copy_of_data_to_foreign(dataname, data:typing.Any, as_call=True) -> str:
    """Creates a user expression to place a copy of data to a remote kernel space.
    
    The data will be bound, in the remote namespace, to the identifier specified
    by "dataname".
    
    Parameters:
    -----------
    dataname: str
    data: typing.Any - Must be serializable.
    
    Unlike the result from cmd_fetch_copy_of_foreign_variable(s), the command string 
    returned by this function can be passed to the remote kernel for evaluation
    as the "code" parameter of the client's execute() method.
    
    ATTENTION Existing data in the remote kernel that is bound to an identical 
    identifier WILL be overwritten ATTENTION.
    
    """
    pickle_str = str(pickle.dumps({dataname:data}))
    
    cmd = " ".join([dataname, "=", "pickle.loads(eval(" + pickle_str + "))"])
    
    if as_call:
        return {"code":cmd, "silent":True, "store_history":False, "user_expressions":None}
    
    return cmd
    
    
def cmd_foreign_namespace_listing(namespace:str="Internal", as_call=True) -> dict:
    """Creates a user_expression containing the variable names in a foreign namespace.
    """
    
    expr = {"ns_listing_of_%s" % namespace : "dir()"}
    
    if as_call:
        return ForeignCall(user_expressions = expr)
    
    return expr
    
#### END call generators


def unpack_data_recvd_on_shell_chnl(msg:dict) -> dict:
    """Extracts data shuttled from the remote kernel via " execute_reply" message.
    
    The data are present as text/plain mime type data in the received execute_reply
    message, inside its "content"/"user_expressions" nested dictionary.
    
    Messages received in response to requests for variable transfer (copy) will
    contain in the "user_expressions" keys named as "pickled_%s" where "%s" stands 
    for the variable identifier in the remote kernel namespace. 
    
    This is so that this function can decide whether the data received is a 
    string representation of the seriazied variable (as a byte string) or just 
    plain text information. 
    
    In the former case, the fucntion de-serialized the bytes into a copy of the 
    variable and binds it to %s (i..e, the same identifier to which the variable 
    is bound in the remote namespace).

    In the latter case, the string associated to the "text/plain" data is assigned
    to the %s identifier in the caller namespace
    
    ATTENTION 
    If ths identifier is already bound to another variable in the caller namespace,
    this may result in this (local) variable being overwritten by the copy of the 
    remote variable. 
    
    It is up to the caller to decide what to do in this situation.
    ATTENTION
    
    For details about messaging in Jupyter see:
    
    https://jupyter-client.readthedocs.io/en/latest/messaging.html

    """
    # NOTE: "specials" are (%s being substituted with the value of the identifier
    #       shown in parenthesis):
    #
    # "pickled_%s"          (varname)
    #
    # "properties_of_%s"    (varname)
    #
    # "ns_listing_of_%s"    (kernel_tab_name)
    #
    # ATTENTION The specials are set by the functions than generate the commands
    # generating the user_expressions dictionaries.
    
    
    ret = dict()
    # peel-off layers one by one so we can always be clear of what this does
    msg_status = msg["content"]["status"]
    usr_expr = msg["content"]["user_expressions"]
    if msg_status == "ok":
        for key, value in usr_expr.items():
            value_status = value["status"]
            if value_status == "ok":
                data_str = value["data"]["text/plain"] # this nested dict exists only if value_status is OK
                if key.startswith("pickled_"): # by OUR OWN convention, see cmd_fetch_copy_of_foreign_variable
                    data_dict = pickle.loads(eval(data_str))
                    
                else:
                    data_dict = {key:eval(data_str)}
                    
                ret.update(data_dict)
                
            
            elif value_status == "error":
                ret.update({"error_%s" % key: {"ename":value["ename"],
                                               "evalue": value["evalue"],
                                               "traceback": value["traceback"]}})
                
            else:
                ret.update({"%s_%s" % (value_status, key): value_status})
                    
    elif msg_status == "error":
        ret.update({"error_%s" % msg["msg_type"]: {"ename": msg["content"]["ename"],
                                                   "evalue": msg["content"]["evalue"],
                                                   "traceback": msg["content"]["traceback"]}})
        
    else:
        ret.update({"%s_%s" % (msg_status, msg["msg_type"]): msg_status})
    
    return ret

def execute(client, *args, **kwargs):
    """Execute code in the kernel, sent via the specified kernel client.
        
    Parameters
    ----------
    client: a kernel client
    
    *args, **kwargs - passed directly to client.execute(...), are as follows:
    
        code : str
        
            A string of code in the kernel's language.
        
        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.
        
        store_history : bool, optional (default True)
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.
        
        user_expressions : dict, optional
            A dict mapping names to expressions to be evaluated in the user's
            dict. The expression values are returned as strings formatted using
            :func:`repr`.
        
        allow_stdin : bool, optional (default self.allow_stdin)
            Flag for whether the kernel can send stdin requests to frontends.
        
            Some frontends (e.g. the Notebook) do not support stdin requests.
            If raw_input is called from code executed from such a frontend, a
            StdinNotImplementedError will be raised.
        
        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.
    
    Returns
    -------
    The msg_id of the message sent.


    """
    
    return client.execute(*args, **kwargs)




