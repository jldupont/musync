"""
    Base class for UI Agents
    
    Also provides the system clock
        
    Created on 2010-08-19
    @author: jldupont
"""
import gtk
from Queue import Queue, Empty
from app.system import mswitch
from app.system.base import mdispatch

__all__=["UiAgentBase"]

class UiAgentBase(object):
    
    LOW_PRIORITY_MESSAGE_BURST_SIZE=5
    
    def __init__(self, time_base):
        """
        @param time_base: in milliseconds
        @param glade_file: absolute file path to the ui glade XML file
        @param ui_window_class: class object for the ui window 
        """
        self.time_base=time_base 
        self.ticks_second=1000/time_base

        self.iq=Queue()
        self.isq=Queue()
        mswitch.subscribe(self.iq, self.isq)

        self.tick_count=0
        self.sec_count=0
        self.min_count=0
        self.hour_count=0
        self.day_count=0

        self.window=None
        
    def h_app_show(self, *_):
        """ We should show the main application window
        """
        if self.window is None:
            self.window=self.ui_window_class(self.glade_file)
            self.do_updates()
            
    def h_app_close(self, *_):
        """ Seems that the application window was closed...
        """
        self.window=None

    def h_app_exit(self, *_):
        self.on_destroy()

    def on_destroy(self):
        gtk.main_quit()
        
    def do_updates(self):
        """
        The ui window must be updated
        """
        raise RuntimeError("must be implemented")

    def tick(self, *_):
        """
        Performs message dispatch
        """
        tick_min=False
        tick_hour=False
        tick_day=False
        tick_second = (self.tick_count % self.ticks_second) == 0 
        self.tick_count += 1
        
        if tick_second:
            self.sec_count += 1

            tick_min=(self.sec_count % 60)==0
            if tick_min:
                self.min_count += 1
                
                tick_hour=(self.min_count % 60)==0
                if tick_hour:
                    self.hour_count += 1
                    
                    tick_day=(self.hour_count % 24)==0
                    if tick_day:
                        self.day_count += 1
        
        #print "tick! ", tick_second
        mswitch.publish("__main__", "tick", self.ticks_second, 
                        tick_second, tick_min, tick_hour, tick_day, 
                        self.sec_count, self.min_count, self.hour_count, self.day_count)
        
        while True:
            try:     
                envelope=self.isq.get(False)
                quit, mtype, handled=mdispatch(self, "__main__", envelope)
                if handled==False:
                    mswitch.publish(self.__class__, "__interest__", (mtype, False, self.isq))
                if quit:
                    self.on_destroy()
                    break
                
            except Empty:
                break
            continue            
        
        burst=self.LOW_PRIORITY_MESSAGE_BURST_SIZE
        
        while True:
            try:     
                envelope=self.iq.get(False)
                quit, mtype, handled=mdispatch(self, "__main__", envelope)
                if handled==False:
                    mswitch.publish(self.__class__, "__interest__", (mtype, False, self.iq))
                if quit:
                    self.on_destroy()
                    break
                    
                burst -= 1
                if burst == 0:
                    break
            except Empty:
                break
            
            continue

        return True
