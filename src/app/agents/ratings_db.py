"""
    Ratings database
        
    Messages Processed:
    ===================
    - "in_rating":    store the entry in the db
    - "in_qrating":   returns the associated rating
    - "in_qratings":  returns the ratings list starting from "timestamp" and DESCending up to LIMIT
        
    Created on 2010-08-19
    @author: jldupont
"""
import time
from app.system.db import DbHelper
from app.system.base import AgentThreadedWithEvents

__all__=["RatingsDbAgent"]

class RatingsDbAgent(AgentThreadedWithEvents):
    
    MAX_RETRIEVE_LIMIT=1000
    
    TIMERS_SPEC=[ ("min", 1, "t_announceDbCount")
                 ,("min", 1, "t_announceUpdated")  
                 #,("sec", 10, "t_countRatings")
                 ]

    TABLE_PARAMS=[("id",           "integer primary key")
                  ,("created",     "integer")
                  ,("updated",     "integer")
                  ,("source",      "text")
                  ,("wsid",        "text")
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

    ## ======================================================================
    ## MESSAGE HANDLERS
    
    def h_in_rating(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        """
        From Dbus "rating"
        """
        now=time.time()
        ### First try to update if possible
        statement="""UPDATE %s SET updated=?, rating=?
                    WHERE artist_name=? AND album_name=? AND track_name=?
                    """ % self.dbh.table_name
        self.dbh.executeStatement(statement, now, rating, artist_name, album_name, track_name)
        self.dbh.commit()
        c=self.dbh.rowCount()
        if c==1:  ## success
            return
        
        statement=""" INSERT INTO %s ( created, updated, source, 
                                        artist_name, album_name, track_name,
                                        rating)
                                VALUES( ?, ?, ?, ?, ?, ?, ?)
                """ % self.dbh.table_name
        self.dbh.executeStatement(statement, now, now, source, artist_name, album_name, track_name, rating)
        self.dbh.commit()
        

    def h_in_qrating(self, source, ref, artist_name, album_name, track_name):
        """
        From Dbus "qrating"
        """
        statement="""SELECT * FROM %s WHERE artist_name=? AND album_name=? AND track_name=? LIMIT 1
                    """ % self.dbh.table_name
        self.dbh.executeStatement(statement, artist_name, album_name, track_name)
        result=self.dbh.fetchOneEx2()
        self.pub("out_rating", result["source"], 
                                ref, 
                                result["updated"], 
                                result["artist_name"], 
                                result["album_name"], 
                                result["track_name"], 
                                result["rating"])
        
    def h_in_qratings(self, source, ref, timestamp, count):
        """
        From Dbus "qratings"
        """
        c=min(count, self.MAX_RETRIEVE_LIMIT)
        u=time.time() if timestamp==0 else timestamp
        
        statement="""SELECT * FROM %s WHERE updated<=? ORDER DESC LIMIT %s
                """ % (self.dbh.table_name, c)
        self.dbh.executeStatement(statement, u)
        result=self.dbh.fetchAllEx2()
        

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

        