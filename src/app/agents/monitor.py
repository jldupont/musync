"""
    Monitoring Agent
    
    - Verifies the presence of Musicbrainz-proxy-dbus application
    
    Messages Processed:
    ===================
    - "mb_tracks"
    
    Message Generated:
    =================
    - "mb_detected"(state) : the state of detection of 'musicbrainz-proxy-dbus' service
        

    Created on 2010-08-23
    @author: jldupont
"""

from app.system.base import AgentThreadedWithEvents


class MonitoringAgent(AgentThreadedWithEvents):

    TIMERS_SPEC=[    
         #("sec",  5, "t_sec")
         ("min",   1, "t_checkMb")
        ,("sec",  10, "t_checkMbCount")
    ]
    
    THRESHOLDS = {
        "mb": 2
    }
    ADVERTISEMENTS ={
        "mb": 3   ## x intervals
    }
    
    def __init__(self):
        AgentThreadedWithEvents.__init__(self)
        self.mb_detected=False

        self.counters={ "mb": 0, "mb_last_advertised":0, "mb_detected_count": 0
                       }
        self.events={ "mb_detected": False
                     }
    def h_mb_detected_count(self, count):
        #print "h_mb_detected_count: "+str(count)
        if self.counters["mb_detected_count"] != count:
            self.counters["mb_detected_count"]=count
            
            self.pub("mb_detected", True)
            self.events["mb_detected"]=True
            self.counters["mb"]=0
        
    def hs_mb_tracks(self):
        """
        If we 'hear' this sort of message, that means
        Musicbrainz-proxy is up and running
        """
        if self.events["mb_detected"]!=True:
            self.pub("mb_detected", True)
            self.events["mb_detected"]=True
            self.counters["mb"]=0
            
    ## ==========================================================
    ## TIMER HANDLERS

        
    def t_checkMb(self, *_):
        """
        Apply some hysterisis
        """
        if self.events["mb_detected"]!=False or self.events["mb_detected"]==None:
            self.counters["mb"] += 1
            if self.counters["mb"] > self.THRESHOLDS["mb"]:
                self.events["mb_detected"]=False
                self.pub("mb_detected", False)

    def t_checkMbCount(self, *_):
        self.pub("mb_detected_count?")

        ##Advertise "mb_detected" at regular interval
        if self.counters["mb_last_advertised"] > self.ADVERTISEMENTS["mb"]:
            self.pub("mb_detected", self.events["mb_detected"])
            self.counters["mb_last_advertised"]=0
        else:
            self.counters["mb_last_advertised"] += 1
        
        
_=MonitoringAgent()
_.start()
