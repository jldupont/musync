"""
    Tests various functionality of the application
        
    Created on 2010-08-20
    @author: jldupont
"""
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
        print ">>> Tester: mb_detected: %s" % state
        
_=TesterAgent()
_.start()
