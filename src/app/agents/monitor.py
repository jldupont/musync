"""
    Monitoring Agent
    
    - Verifies the presence of Musicbrainz-proxy-dbus application
    
    Messages Processed:
    ===================
    - "mb_tracks"
    
    Message Generated:
    =================
    - "mb_detected"
        

    Created on 2010-08-23
    @author: jldupont
"""

from app.system.base import AgentThreadedWithEvents


class MonitoringAgent(AgentThreadedWithEvents):

    TIMERS_SPEC=[    
         #("sec",  5, "t_sec")
        ("min",  1, "t_checkMb")
    ]
    
    THRESHOLDS = {
        "mb": 2
    }
    
    def __init__(self):
        AgentThreadedWithEvents.__init__(self)
        self.mb_detected=False

        self.counters={ "mb": 0
                       }
        self.events={ "mb_detected": None
                     }
        
    def hs_mb_tracks(self):
        """
        If we 'hear' this sort of message, that means
        Musicbrainz-proxy is up and running
        """
        if self.events["mb_detected"]!=True:
            self.pub("mb_detected", True)
            self.events["mb_detected"]=True
            self.counters["mb"]=0
        
    def t_checkMb(self, *_):
        """
        Apply some hysterisis
        """
        if self.events["mb_detected"]!=False or self.events["mb_detected"]==None:
            self.counters["mb"] += 1
            if self.counters["mb"] > self.THRESHOLDS["mb"]:
                self.events["mb_detected"]=False
                self.pub("mb_detected", False)

        
_=MonitoringAgent()
_.start()
