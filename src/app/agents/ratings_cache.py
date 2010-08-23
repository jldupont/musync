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
    - "to_update" : received from 'ratings_db' once an entry has been cleared for upload
        
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
                 ,("min", 1, "t_processDetectMb")
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
    
    BATCH_MBID_MAX=200
    MB_DETECT_GONE_THRESHOLD=3 ## minutes
    
    def __init__(self, dbpath, dev_mode=False):
        AgentThreadedWithEvents.__init__(self)
        self.mb_minutes_since_last_saw=0
        self.mb_present=False
        
        self.dbh=DbHelper(dbpath, "ratings_cache", self.TABLE_PARAMS)
        
    #source, ref, timestamp, artist_name, album_name, track_name, rating)
    def h_to_update(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        """
        Caches the rating locally once the database has determine it is OK to do so
        """
            
        now=time.time()        
        statement="""UPDATE %s SET updated=?, rating=? 
                    WHERE artist_name=? AND album_name=? AND track_name=?""" % self.dbh.table_name
        try:
            self.dbh.executeStatement(statement, timestamp, rating, 
                                      artist_name, album_name, track_name)
            self.dbh.commit()
        except Exception,e:
            self.pub("llog", "fpath/cache", "error", "Database insertion error (%s)" % e)
            self.dprint("cache: update error: %s" % e)
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
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""" % self.dbh.table_name
            try:
                self.dbh.executeStatement(statement, now, timestamp, source,
                                          artist_name, album_name, track_name, "", rating)
                self.dbh.commit()
            except Exception,e:
                self.pub("llog", "fpath/cache", "error", "Database insertion error (%s)" % e)
                self.dprint("cache: insertion error: %s" % e)
                return

            self.dprint("! rating inserted in cache: artist(%s) album(%s) track(%s) rating(%s)" % (artist_name, album_name, track_name, rating))
                
    def _updateMbid(self, artist_name, track_name, track_mbid):
        """
        Updates the track_mbid parameter of specified tracks
        """
        statement="""UPDATE %s SET 
                    track_mbid=?
                    WHERE artist_name=? AND track_name=?""" % self.dbh.table_name
        try:
            self.dbh.executeStatement(statement, track_mbid, artist_name, track_name)
            self.dbh.commit()
        except Exception,e:
            self.pub("llog", "fpath/cache", "error", "Database update error (%s)" % e)

    ## ===============================================================================
    ## =============================================================================== HANDLERS
    ## ===============================================================================

    def h_rating_uploaded(self, id, *_):
        """
        Delete an entry when it is safely uploaded
        
        If this fails, no matter: it will be caught & retried later
        """
        try:
            self.dbh.deleteById(id)
            self.dbh.commit()
        except:
            pass

    def hq_next_to_upload(self, limit):
        """
        Returns the next entry to upload
        """
        try:
            statement="""SELECT * from %s ORDER BY updated ASC LIMIT ?""" % self.dbh.table_name
            self.dbh.executeStatement(statement, limit)
            entries=self.dbh.fetchAllEx()
        except Exception,e:
            self.pub("llog", "fpath/cache", "error", "Database reading error (%s)" % e)
            return
        
        self.pub("to_upload", entries)

    def h_mb_tracks(self, _source, ref, list_dic):
        """
        Update the mbid fields of the entries
        
        We only get the response(s) to the question(s) we have asked.
        The other 'tracks' messages flying on Dbus are filtered-out at the Dbus Agent
        """
        if list_dic is None:
            return
        
        self.mb_present=True
        self.mb_minutes_since_last_saw=0
        
        try:
            for track_details in list_dic:
                artist_name=track_details["artist_name"]
                track_name=track_details["track_name"]
                track_mbid=track_details["track_mbid"]
                self._updateMbid(artist_name, track_name, track_mbid)
        except Exception,e:
            self.pub("llog", "fpath/cache", "error", "RatingsCache: problem updating 'track_mbid' (%s)" % e)
            
    ## ===============================================================================
    ## =============================================================================== EVENTS
    ## ===============================================================================


    def t_processMbid(self, *_):
        """
        Timer elapsed - Mbid processing
        """
        statement="""SELECT * FROM %s
                    WHERE track_mbid='' LIMIT ?""" % self.dbh.table_name

        try:
            self.dbh.executeStatement(statement, self.BATCH_MBID_MAX)
            entries=self.dbh.fetchAllEx([])
        except Exception,e:
            self.pub("llog", "fpath/cache", "error", "Database reading error (%s)" % e)
            return
            
        for entry in entries:
            ref="musync:%s" % entry["id"]
            self.pub("mb_track?", ref, entry["artist_name"], entry["track_name"], "low")
        

    def t_processDetectMb(self, *_):
        """
        """
        self.mb_minutes_since_last_saw += 1
        if self.mb_minutes_since_last_saw > self.MB_DETECT_GONE_THRESHOLD:
            self.mb_present=False

"""        
_=RatingsCacheAgent(DBPATH)
_.start()
"""
