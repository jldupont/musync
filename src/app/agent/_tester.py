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
        #print "t_sec"
        self.pub("llog", "fpath/test", "warning", "t_sec1")
        self.pub("llog", "fpath/test", "warning", "t_sec2")
        self.pub("llog", "fpath/test", "warning", "t_sec3")
        
    def t_min(self, *_):

        self.pub("llog", "fpath/test", "warning", "t_min1")
        self.pub("llog", "fpath/test", "warning", "t_min2")
        self.pub("llog", "fpath/test", "warning", "t_min3")
        
        
_=TesterAgent()
_.start()
