"""
    Tests various functionality of the application
        
    Created on 2010-08-20
    @author: jldupont
"""
import time
from app.system.base import AgentThreadedWithEvents

class TesterAgent(AgentThreadedWithEvents):

    TIMERS_SPEC=[    
         ("sec", 1, "t_sec")
        ,("min", 1, "t_min")
    ]
    
    def __init__(self):
        AgentThreadedWithEvents.__init__(self)
        
    def t_sec(self, *_):
        pass
        
    def t_min(self, *_):
        pass
        
    def h_mb_detected(self, state):
        pass
        #print "%s: >>> Tester: mb_detected: %s" % (time.time(), state)
        
_=TesterAgent()
_.start()
