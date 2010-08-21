"""
    Ratings Cache Agent

    Caches the "rating" parameters associated with music tracks locally. This is
    the stepping stone before uploading the "ratings" to the web service on Systemical.com.
    
    - Stores the "rating" updates in the local database
    - Answers queries coming from the message bus

    Messages Processed:
    ===================
    - "in_rating"
    - "rating_uploaded"
        
    Messages Emitted:
    =================
    
    
    INSERT INTO cache () VALUES ()
    

    @author: jldupont
    @date: august 2010
"""
import time

from app.system.db import DbHelper
from app.system.base import AgentThreadedWithEvents

__all__=["RatingsCacheAgent",]


class RatingsCacheAgent(AgentThreadedWithEvents):
    
    TIMERS_SPEC=[ ("min", 1, "t_processMbid")
                 #,("sec", 10, "t_countRatings")
                 ]

    TABLE_PARAMS=[("id",           "integer primary key")
                  ,("created",     "integer")
                  ,("updated",     "integer")
                  ,("source",      "text")
                  ,("artist_name", "text")
                  ,("album_name",  "text")
                  ,("track_name",  "text")
                  ,("track_mbid",   "text")
                  ,("rating",      "float")
                  ]
    
    BATCH_MBID_MAX=50
    
    def __init__(self, dbpath, dev_mode=False):
        AgentThreadedWithEvents.__init__(self)

        self.dbh=DbHelper(dbpath, "ratings_cache", self.TABLE_PARAMS)

    def h_in_rating(self, source, _ref, timestamp, artist_name, album_name, track_name, rating):
        """
        Caches the rating locally
        
        This message is issued as a result of receiving the "/Ratings/rating" DBus signal
        """
        now=time.time()        
        statement="""UPDATE %s SET updated=?, rating=? 
                    WHERE artist_name=? AND album_name=? AND track_name=?""" % self.dbh.table_name
        try:
            self.dbh.executeStatement(statement, timestamp, rating, 
                                      artist_name, album_name, track_name)
            self.dbh.commit()
            
            
        except Exception,e:
            self.pub("log", "error", "%s: error writing to database for inserting a rating (%s)" % (self.__class__, e))
            return

        rc=self.dbh.rowCount()
        if rc>0:
            self.dprint("! rating updated in cache: artist(%s) album(%s) track(%s) rating(%s)" % (artist_name, album_name, track_name, rating))
            return            
        
        if rc==0:
            statement="""INSERT INTO %s (created, updated,
                                source,
                                artist_name, 
                                album_name, 
                                track_name,
                                track_mbid,
                                rating) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)""" % self.dbh.table_name
            try:
                self.dbh.executeStatement(statement, now, timestamp, 
                                          artist_name, album_name, track_name, "", rating)
                self.dbh.commit()
                
                self.dprint("! rating inserted in cache: artist(%s) album(%s) track(%s) rating(%s)" % (artist_name, album_name, track_name, rating))
            except Exception,e:
                self.pub("log", "error", "%s: error writing to database for inserting a rating (%s)" % (self.__class__, e))

    def _updateMbid(self, artist_name, track_name, track_mbid):
        """
        Updates the track_mbid parameter of specified tracks
        """
        statement="""UPDATE %s SET 
                    track_mbid=?
                    WHERE artist_name=? AND track_name=?""" % self.dbh.table_name
        self.dbh.executeStatement(statement, track_mbid, artist_name, track_name)
        self.dbh.commit()

    ## ===============================================================================
    ## =============================================================================== HANDLERS
    ## ===============================================================================

    def h_rating_uploaded(self, id, *_):
        """
        Delete an entry when it is safely uploaded
        
        If this fails, no matter: it will be caught & retried later
        """
        self.dbh.deleteById(id)
        self.dbh.commit()

    def hq_next_to_upload(self, limit):
        """
        Returns the next entry to upload
        """
        statement="""SELECT * from %s ORDER BY updated ASC LIMIT ?""" % self.dbh.table_name
        self.dbh.executeStatement(statement, limit)
        entries=self.dbh.fetchAllEx()
        
        self.pub("to_upload", entries)

    def h_mb_tracks(self, _source, ref, list_dic):
        """
        Update the mbid fields of the entries
        """
        if list_dic is None:
            return
        
        try:
            for track_details in list_dic:
                artist_name=track_details["artist_name"]
                track_name=track_details["track_name"]
                track_mbid=track_details["track_mbid"]
                self._updateMbid(artist_name, track_name, track_mbid)
        except Exception,e:
            self.pub("llog", "err", "error", "RatingsCache: problem updating 'track_mbid' (%s)" % e)
    ## ===============================================================================
    ## =============================================================================== EVENTS
    ## ===============================================================================


    def t_processMbid(self, *_):
        """
        Timer elapsed - Mbid processing
        """
        statement="""SELECT * FROM %s
                    WHERE track_mbid='' LIMIT ?""" % self.dbh.table_name

        self.dbh.executeStatement(statement, self.BATCH_MBID_MAX)
        entries=self.dbh.fetchAllEx([])
        for entry in entries:
            ref="musync:%s" % entry["id"]
            self.pub("mb_track?", ref, entry["artist_name"], entry["track_name"], "low")
        

"""        
_=RatingsCacheAgent(DBPATH)
_.start()
"""
