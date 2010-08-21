"""
    Ratings database
        
    Created on 2010-08-19
    @author: jldupont
"""

from app.system.db import DbHelper
from app.system.base import AgentThreadedWithEvents

__all__=["RatingsDbAgent"]

class RatingsDbAgent(AgentThreadedWithEvents):
    
    TIMERS_SPEC=[ ("min", 1, "t_announceDbCount")
                 ,("min", 1, "t_announceUpdated")  
                 #,("sec", 10, "t_countRatings")
                 ]

    TABLE_PARAMS=[("id",           "integer primary key")
                  ,("created",     "integer")
                  ,("updated",     "integer")
                  ,("source",      "text")
                  ,("artist_name", "text")
                  ,("album_name",  "text")
                  ,("track_name",  "text")
                  ,("track_mbid",  "text")
                  ,("rating",      "float")
                  ]
    
    def __init__(self, dbpath, dev_mode=False):
        AgentThreadedWithEvents.__init__(self)
        
        self.current_count=0
        self.dbh=DbHelper(dbpath, "ratings_db", self.TABLE_PARAMS)

    ## ====================================================================== HELPERS
    ##
     

    ## ====================================================================== TIMERS
    ##
    def t_announceUpdated(self):
        e=self.getLatestUpdated()
        try:    updated=e["updated"]
        except: updated=None
        
        self.pub("out_updated", updated, self.current_count)

    def t_announceDbCount(self, *_):
        """
        Announces the count of "ratings" in the db
        """
        self.current_count=self.dbh.getRowCount()
        self.pub("ratings_count", self.current_count)

        