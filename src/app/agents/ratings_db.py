"""
    Ratings database
        
    Messages Processed:
    ===================
    - "in_rating":    store the entry in the db
    - "in_qrating":   returns the associated rating
    - "in_qratings":  returns the ratings list starting from "timestamp" and DESCending up to LIMIT
    - "to_update" : if the database determines that no record / new update
            
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
        
        First check if we have a different value in the database - if not, abort.
        """
        statement="""SELECT * FROM %s WHERE artist_name=? AND album_name=? AND track_name=? AND rating<>? LIMIT 1
                    """ % self.dbh.table_name
        try:
            self.dbh.executeStatement(statement, artist_name, album_name, track_name, rating)
            result=self.dbh.fetchOne(None)
        except Exception,e:
            self.pub("llog", "fpath/cache", "error", "Database reading error (%s)" % e)
            return

        ### Can't be found OR different rating... then add to the database AND signal
        ###  so that the 'cache' also put to record ready for uploading to the web-service
        if result is None:
            now=time.time()
            ### First try to update if possible
            statement="""UPDATE %s SET updated=?, rating=?
                        WHERE artist_name=? AND album_name=? AND track_name=?
                        """ % self.dbh.table_name
            try:
                self.dbh.executeStatement(statement, now, rating, artist_name, album_name, track_name)
                self.dbh.commit()
                c=self.dbh.rowCount()
                if c==1:  ## success
                    self.dprint("db: updated, a(%s) b(%s) t(%s): %s" % (artist_name, album_name, track_name, rating))
                    return
            except Exception,e:
                self.pub("llog", "fpath/db", "error", "Database update error (%s)" % e)
                return
    
            statement=""" INSERT INTO %s ( created, updated, source, 
                                            artist_name, album_name, track_name,
                                            rating)
                                    VALUES( ?, ?, ?, ?, ?, ?, ?)
                    """ % self.dbh.table_name
            try:
                self.dbh.executeStatement(statement, now, now, source, artist_name, album_name, track_name, rating)
                self.dbh.commit()
                self.dprint("db: inserted, a(%s) b(%s) t(%s): %s" % (artist_name, album_name, track_name, rating))
            except Exception,e:
                self.pub("llog", "fpath/db", "error", "Database insertion error (%s)" % e)
                return
            
            ### help the cache - the way to the web-service
            self.pub("to_update", source, ref, timestamp, artist_name, album_name, track_name, rating)


    def h_in_qrating(self, source, ref, artist_name, album_name, track_name):
        """
        From Dbus "qrating"
        """
        statement="""SELECT * FROM %s WHERE artist_name=? AND album_name=? AND track_name=? LIMIT 1
                    """ % self.dbh.table_name
        try:
            self.dbh.executeStatement(statement, artist_name, album_name, track_name)
            result=self.dbh.fetchOneEx2()
            self.pub("out_rating", result["source"], 
                                    ref, 
                                    result["updated"], 
                                    result["artist_name"], 
                                    result["album_name"], 
                                    result["track_name"], 
                                    result["rating"])
        except Exception,e:
            self.pub("llog", "fpath/db", "error", "Database reading error (%s)" % e)
        
    def h_in_qratings(self, source, ref, timestamp, count):
        """
        From Dbus "qratings"
        """
        c=min(count, self.MAX_RETRIEVE_LIMIT)
        u=time.time() if timestamp==0 else timestamp
        
        statement="""SELECT * FROM %s WHERE updated<=? ORDER DESC LIMIT %s
                """ % (self.dbh.table_name, c)
        try:
            self.dbh.executeStatement(statement, u)
            results=self.dbh.fetchAllEx(None)
            if results is None:
                self.pub("out_rating", source, 
                                        ref, 
                                        timestamp, 
                                        "", "", "", 0.0) 
                return
            
            ### Burst....
            for result in results:
                    self.pub("out_rating", result["source"], 
                                ref, 
                                result["updated"], 
                                result["artist_name"], 
                                result["album_name"], 
                                result["track_name"], 
                                result["rating"])
        except Exception,e:
            self.pub("llog", "fpath/db", "error", "Database reading error (%s)" % e)

        

    ## ====================================================================== HELPERS
    ##
    

    ## ====================================================================== TIMERS
    ##
    def t_announceUpdated(self, *_):
        """
        If there is an issue here it will be caught elsewhere anyhow
        """
        try:
            e=self.getLatestUpdated()    
            updated=e["updated"]
        except: 
            updated=0
        
        self.dprint("* out_updated: updated(%s) current count(%s)" % (updated, self.current_count))
        self.pub("out_updated", updated, self.current_count)

    def t_announceDbCount(self, *_):
        """
        Announces the count of "ratings" in the db
        
        If there is an issue here it will be caught elsewhere anyhow
        """
        try:     self.current_count=self.dbh.getRowCount()
        except:  self.current_count=0
        
        self.dprint("* ratings_count: current count(%s)" % self.current_count)
        self.pub("ratings_count", self.current_count)

        