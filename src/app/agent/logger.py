"""
    Logger Agent with rate limiting
    
    For log limited submissions:
    * limits per min/hour/day can be set for each logtype category
    
    Log type categories:
    ====================
    
    1) Filesystem path unaccessible: don't need to report this often
        as this must be a configuration error on the user's part.
        
        "fpath/*"
        
    2) Network path unaccessible: the application, in most cases, cannot
        control this condition. It doesn't really help reporting this
        message repeatedly: it would only clog the message log file.
        
        "npath/*"
        
    3) Configuration error: once per application start should be sufficient.
        The "application start" log entry should therefore be clearly logged.
        
        "cfg/*" 

    4) Runtime error: the application has "catch-all" exception catching.
        The specific nature of the exception isn't known.

        "err/*"
    
    Example configuration
    =====================
    
    ###          S   M   H   D
    ###        ----------------
    { "fpath": [ 1,  1,  1,  1  ]    # once per day
     ,"npath": [ 1,  1,  1,  24 ]    # max of 24 per day
     ,"cfg":   [ 1,  1,  1,  1  ]    # max of 1 per day 
     ,"err":   [ 1,  1,  64, 100]    # max 64 per hour, 100 per day
    }
    
    @author: jldupont
    @date: May 21, 2010
"""
import os
import copy
import logging
from app.system.base    import AgentThreadedBase

__all__=["LoggerAgent"]

## I don't like globals but I'd rather not have "self." everywhere
SEC=0
MIN=1
HOUR=2
DAY=3


class LoggerAgent(AgentThreadedBase):

    MLEVEL={"info":     logging.INFO
            ,"warning": logging.WARNING
            ,"error":   logging.ERROR
            ,"critical":logging.CRITICAL
            }
    
    DEFAULTS={ "fpath": [1, 2,  5,  10]
              ,"npath": [1, 1,  1,  24]
              ,"cfg":   [1, 1,  1,  1]
              ,"err":   [1, 1,  32, 64]
              }
    
    def __init__(self, app_name, logpath, credits={}):
        """
        @param interval: interval in seconds
        """
        AgentThreadedBase.__init__(self)
        self.credits=credits or self.DEFAULTS
        self.buckets={}
        self.dailyQuotaReached={}
        
        self._logger=None
        self.fhdlr=None
        self._shutdown=False
        self.appname=app_name
        self.logpath=os.path.expanduser(logpath)
        self._setup() 
        self._resetBuckets()       
        
    def _setup(self):
        if self._logger is not None:
            return
        
        self._logger=logging.getLogger(self.appname)
        
        path=os.path.expandvars(os.path.expanduser(self.logpath))
        self.fhdlr=logging.FileHandler(path)
        
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.fhdlr.setFormatter(formatter)
        self._logger.addHandler(self.fhdlr)
        self._logger.setLevel(logging.INFO)
        
    def h_shutdown(self):
        if self._logger:
            self._shutdown=True
            logging.shutdown([self.fhdlr])
        
    def _resetBuckets(self):
        """
        Setup the buckets with credits
        """
        self.buckets=copy.deepcopy( self.credits )
        
        ## our quick lookup dict too
        self.dailyQuotaReached={}
            
    def h_tick(self, ticks_second, 
               tick_second, tick_min, tick_hour, tick_day, 
                sec_count, min_count, hour_count, day_count):
        """
        Time base - used by the rate limiting function
        """
        if tick_second:
            self._cascadeCredits(SEC)
        if tick_min:
            self._cascadeCredits(MIN)
            self._cascadeCredits(SEC)
        if tick_hour:
            self._cascadeCredits(HOUR)
            self._cascadeCredits(MIN)
            self._cascadeCredits(SEC)            
        if tick_day:
            self._resetBuckets()
            
    def _cascadeCredits(self, bottomBucket):
        """
        Cascade a maximum number of tokens from the
        bucket sitting on top of "bottomBucket"
        """
        for bucket in self.buckets:
            maxBucketSize=self.credits[bucket][bottomBucket]
            currentBucketCredits=max(self.buckets[bucket][bottomBucket],0)
            topBucketCredits=max(self.buckets[bucket][bottomBucket+1],0)
            #self.dprint("* bucket(%s) maxSize(%s) currentCredits(%s) topCredits(%s)" %(bucket, maxBucketSize, currentBucketCredits, topBucketCredits))
                        
            ## bucket is full
            if currentBucketCredits==maxBucketSize:
                continue
            
            if self.buckets[bucket][bottomBucket]<0:
                self.buckets[bucket][bottomBucket]=0
            if self.buckets[bucket][bottomBucket+1]<0:
                self.buckets[bucket][bottomBucket+1]=0
            
            ## cascade required credits from the bucket on top
            missingCredits=maxBucketSize-currentBucketCredits
            maxCreditsWeCanGetFromTop=min(missingCredits, topBucketCredits)
            self.buckets[bucket][bottomBucket]   += maxCreditsWeCanGetFromTop
            
            if self.buckets[bucket][DAY] == 0:
                self.dailyQuotaReached[bucket]=True
                
            
            
    def h_llog(self, logtype, loglevel, logmsg):
        """
        Rate/Total Limited Logging
        """
        try:    logcat=logtype.split("/")[0]
        except: logcat="err"
        
        ## are we capped for the day??
        if self.dailyQuotaReached.get(logcat, False):
            return
        
        ## valid log category?
        try:
            credits=self.buckets[logcat][SEC]
        except:
            credits=None
        
        ## If we can't find the log category, this justifiably 
        ##  can be classified in the "err" category I believe
        if credits is None:
            logcat="err"
            try:
                credits=self.buckets.get[logcat][SEC]
            except:
                ## shouldn't happen... config error
                credits=0
        
        ## We don't have credits for now... drop!
        if credits==0:
            return
        
        self.h_log(loglevel, logmsg)
        self.buckets[logcat][SEC]  -=1
        self.buckets[logcat][MIN]  -=1
        self.buckets[logcat][HOUR] -=1
        self.buckets[logcat][DAY]  -=1
                    
    def h_log(self, *arg):
        """
        Unconstrained Logging
        """
        if self._shutdown:
            return
        
        self._setup()
        
        if len(arg) == 1:
            self._logger.log(logging.INFO, arg[0])
        else:
            level=self.MLEVEL.get(arg[0], logging.INFO)
            self._logger.log(level, arg[1])
        


"""
_=LoggerAgent(app_name, logpath, limits)
_.start()
"""
