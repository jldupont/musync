"""
    Ratings Cache Agent

    Caches the "rating" parameters associated with music tracks locally. This is
    the stepping stone before uploading the "ratings" to the web service on Systemical.com.
    
    - Stores the "rating" updates in the local database
    - Answers queries coming from the message bus

    Messages Processed:
    ===================
    - "in_rating"
    - "rating_uploaded" : signals that a specific entry as been uploaded to the web-service
    - "to_update" : received from 'ratings_db' once an entry has been cleared for upload
        
    Messages Emitted:
    =================
    - "to_upload" : list of entries to upload to web-service
    

    @author: jldupont
    @date: august 2010
"""
import time

from app.system.db import DbHelper
from app.system.base import AgentThreadedWithEvents

__all__=["RatingsCacheAgent",]


class RatingsCacheAgent(AgentThreadedWithEvents):
    
    TIMERS_SPEC=[ ("min", 1, "t_processMbid")
                 ,("min", 1, "t_findUploads")
                 #,("min", 1, "t_processDetectMb")
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
    
    BATCH_UPLOAD_MAX=100
    BATCH_MBID_MAX=200
    #MB_DETECT_GONE_THRESHOLD=3 ## minutes
    
    def __init__(self, dbpath, dev_mode=False):
        AgentThreadedWithEvents.__init__(self)
        self.dbh=DbHelper(dbpath, "ratings_cache", self.TABLE_PARAMS)
        self.mb_detected=False
        
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

    def _getUploadBatch(self, known_mbid=True, limit=200):
        """
        Retrieves a list of entries ready for upload
        
        The entries can either be selected by 'known track_mbid, top of list' 
        or just 'top of list'
        """
        lim=min(limit, self.BATCH_UPLOAD_MAX)
        
        if known_mbid:
            statement="""SELECT * FROM %s 
                        WHERE track_mbid<>'' AND track_mbid<>'?' ORDER BY updated ASC LIMIT %s""" % (self.dbh.table_name, lim)
        else:
            statement="""SELECT * FROM %s 
                        ORDER BY updated ASC LIMIT %s""" % (self.dbh.table_name, lim)
            
        try:
            self.dbh.executeStatement(statement)
            results=self.dbh.fetchAllEx([])
        except Exception,e:
            self.pub("llog", "fpath/cache", "error", "Database reading error (%s)" % e)
            self.dprint("cache: database read error: %s" % e)
            results=[]
        
        return results


    ## ===============================================================================
    ## =============================================================================== HANDLERS
    ## ===============================================================================
    def h_mb_detected(self, state):
        """
        Debouncing & hysterisis all done
        when using this message
        """
        self.mb_detected=state

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

    def h_mb_tracks(self, _source, ref, list_dic):
        """
        Update the mbid fields of the entries
        
        We only get the response(s) to the question(s) we have asked.
        The other 'tracks' messages flying on Dbus are filtered-out at the Dbus Agent
        """
        if list_dic is None:
            return
        
        #print "--- ratings_cache.h_mb_tracks: ref: %s, list_dic: %s" % (ref, list_dic)
        
        try:
            for track_details in list_dic:
                artist_name=track_details["artist_name"]
                #album_name=track_details["album_name"]
                track_name=track_details["track_name"]
                track_mbid=track_details["track_mbid"]
                if track_mbid=="":
                    track_mbid="?"
                    self.pub("log", "Track Mbid not found: artist(%s) title(%s)" % (artist_name, track_name))
                self._updateMbid(artist_name, track_name, track_mbid)
                #print "Track updated: artist(%s) title(%s)" % (artist_name, track_name)
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
        
    """
    def t_processDetectMb(self, *_):
        self.mb_minutes_since_last_saw += 1
        if self.mb_minutes_since_last_saw > self.MB_DETECT_GONE_THRESHOLD:
            self.mb_present=False
    """
    
    def t_findUploads(self, *_):
        """
        Determines which entries are ready to be uploaded
        """
        if self.mb_detected:
            batch=self._getUploadBatch(known_mbid=True, limit=0)  ## get max
        else:
            batch=self._getUploadBatch(known_mbid=False, limit=0) ## get max

        if len(batch) > 0:
            self.pub("ratings_to_upload", batch)    
"""        
_=RatingsCacheAgent(DBPATH)
_.start()
"""
