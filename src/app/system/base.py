"""
    Base class for threaded Agents
    
    * high/low priority message queues
    * message bursting controlled
    * message dispatching based on Agent 'interest'
    
    @author: jldupont
    @date: May 17, 2010
    @revised: June 18, 2010
    @revised: August 22, 2010 : filtered-out "send to self" case
"""

from threading import Thread
from Queue import Queue, Empty
import uuid

import mswitch

__all__=["AgentThreadedBase", "AgentThreadedWithEvents", "debug", "mdispatch"]

debug=False


def mdispatch(obj, obj_orig, envelope):
    """
    Dispatches a message to the target
    handler inside a class instance
    """
    _orig, mtype, payload = envelope
    orig, msg, pargs, kargs = payload
    
    ## Avoid sending to self
    if orig == obj_orig:
        return (False, mtype, None)

    if mtype=="__quit__":
        return (True, mtype, None)

    handled=False

    if mtype.endswith("?"):
        handlerName="hq_%s" % mtype[:-1]
    else:
        handlerName="h_%s" % mtype
    handler=getattr(obj, handlerName, None)
    
    if handler is None:
        handler=getattr(obj, "h_default", None)    
        if handler is not None:
            handler(mtype, msg, *pargs, **kargs)
            handled=True
    else:
        handler(msg, *pargs, **kargs)
        handled=True

    """
    if handler is None:
        if debug:
            print "! No handler for message-type: %s" % mtype
    """
    
    return (False, mtype, handled)


class AgentThreadedBase(Thread):
    """
    Base class for Agent running in a 'thread' 
    """
    
    LOW_PRIORITY_BURST_SIZE=5
    
    def __init__(self, debug=False):
        Thread.__init__(self)
        self.mmap={}
        
        self.debug=debug
        self.id = uuid.uuid1()
        self.iq = Queue()
        self.isq= Queue()
        
    def dprint(self, msg):
        if debug:
            print "+ %s: %s" % (self.__class__, msg)
        
    def pub(self, msgType, msg, *pargs, **kargs):
        mswitch.publish(self.id, msgType, msg, *pargs, **kargs)
        
    def run(self):
        """
        Main Loop
        """
        print "Agent (%s) starting" % str(self.__class__)
        
        ## subscribe this agent to all
        ## the messages of the switch
        mswitch.subscribe(self.id, self.iq, self.isq)
        
        quit=False
        while not quit:
            #print str(self.__class__)+ "BEGIN"
            while True:
                try:
                    envelope=self.isq.get(block=True, timeout=0.1)
                    mquit=self._process(envelope)
                    if mquit:
                        quit=True
                        break
                    continue
                except Empty:
                    break
                

            burst=self.LOW_PRIORITY_BURST_SIZE
            while True and not quit:                
                try:
                    envelope=self.iq.get(block=False)#(block=True, timeout=0.1)
                    mquit=self._process(envelope)
                    if mquit:
                        quit=True
                        break

                    burst -= 1
                    if burst == 0:
                        break
                except Empty:
                    break
        print "Agent(%s) ending" % str(self.__class__)
                
    def _process(self, envelope):
        _orig, mtype, _payload = envelope
        
        #if mtype!="tick":
        #    print "base._process: mtype: " + str(mtype)
        
        interested=self.mmap.get(mtype, None)
        if interested==False:
            return False
        
        quit, _mtype, handled=mdispatch(self, self.id, envelope)
        if quit:
            shutdown_handler=getattr(self, "h_shutdown", None)
            if shutdown_handler is not None:
                shutdown_handler()

        if handled is not None:
            self.mmap[mtype]=handled
            
        ### signal this Agent's interest status (True/False)
        ### to the central message switch
        if interested is None:
            if mtype!="__quit__":
                mswitch.publish(self.__class__, "__interest__", (mtype, handled, self.iq))
            
        ### This debug info is extermely low overhead... keep it.
        if interested is None and handled:
            print "Agent(%s) interested(%s)" % (self.__class__, mtype)
            print "Agent(%s) map: %s" % (self.__class__, self.mmap)

        return quit
            

class AgentThreadedWithEvents(AgentThreadedBase):
    """
    A base class for threaded Agents with timer based events support
    
    @param timers_spec: dictionary where each key represents a timer entry
    
    Timer Entry:
    ============
        [seconds_timeout, minutes_timeout, hours_timeout, days_timeout]
        
        E.g.
        ("sec", 2, callback) : will fire "callback" every 2 seconds
        ("min", 5, callback) : will fire "callback" every 5 minutes
    """
    def __init__(self, timers_spec=[]):
        AgentThreadedBase.__init__(self)
        
        try:    ts=self.__class__.TIMERS_SPEC
        except: ts=[]
        
        self.timers_spec=timers_spec or ts
        self._timers={"sec":[], "min": [], "hour":[], "day": []}

        try:        
            self._processTimersSpec()
        except:
            raise RuntimeError("timers_spec misconfigured for Agent: %s" % self.__class__)
        
    def _processTimersSpec(self):
        """
        Process the timers_spec required for the Agent
        """
        for timer in self.timers_spec:
            base, interval, callback_name=timer
            entries=self._timers.get(base, [])
            entries.append((interval, callback_name))
        
        
    def h___tick__(self, _ticks_per_second, 
               second_marker, min_marker, hour_marker, day_marker,
               sec_count, min_count, hour_count, day_count):
        """
        CRON like support
        """
        #print "h_tick: sec_count(%s) min_count(%s) hour_count(%s) day_count(%s)" % (sec_count, min_count, hour_count, day_count)
        #print "h_tick: sec(%s) min(%s) hour(%s) day(%s)" % (second_marker, min_marker, hour_marker, day_marker)
        if second_marker:
            self._processTimers(sec_count, "sec")
        if min_marker:
            self._processTimers(min_count, "min")
        if hour_marker:
            self._processTimers(hour_count, "hour")
        if day_marker:
            self._processTimers(day_count, "day")
        
    def _processTimers(self, count, base):
        for entry in self._timers[base]:
            interval, callback_name = entry
            if (count % interval==0):
                callback=getattr(self, callback_name)
                callback(base, count)
                

