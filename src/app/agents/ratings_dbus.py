"""
    Ratings Dbus Agent

    com.systemical.services/ratings/[rating;qrating]
    
    Messages Processed:
    - "out_rating"  : transit to "/ratings/rating" Dbus message
    - "out_updated" : transit to "/ratings/updated" Dbus message
    
    Messages Generated:
    - "in_rating"
    - "in_qrating"
    - "in_qratings"
    
    ==========================================================
    
    Dbus Interface:
    * (IN/OUT) rating(source, ref, timestamp, artist_name, album_name, track_name, rating) 

            Upon receiving this signal, the Sync-Playlists will store the rating
            associated with the specified track.

            @param source: (string)   the 'source' application generating this rating
            @param ref: (string) (not used on input) opaque reference returned in response to "qrating"
            @param timestamp: (integer) the time in seconds since the epoch, in UTC
            @param artist_name: (string)
            @param album_name: (string)
            @param track_name: (string)
            @param rating: (integer) [0:100]
            
            This signal can be sent with 'artist_name', 'album_name', 'track_name' equal to "" (empty)
            in response to "qratings" returning no results.

    * (IN) qratings(source, ref, timestamp, count)
    
            Ratings? from 'timestamp' and descending in time, return a maximum of 'count' records
            
            @param source: (string) the 'source' application - filter out entries from this origin
            @param ref: (string) an opaque reference parameter to pass in the response 'rating' signal
            @param timestamp: (integer) the in seconds since the epoch, in UTC
            @param count: (integer) the maximum number records to return
            
            The response will come in form of "rating" signal(s).
            When using 'timestamp=0', the current time is used i.e. latest entries will be returned.
            
    * (IN) qrating(source, ref, artist_name, album_name, track_name)
    
            Rating?  Question signal for which Musync will retrieve, if available,
            the rating associated with the specified track.  Musync will reply
            using the "rating" signal (described above).
            
    * (OUT) updated(timestamp, ratings_count)
    
            Signal indicating when was the last update performed on the local database
            @param timestamp: (integer) the time in seconds since the epoch, in UTC
            
            This signal is autonomously generated at regular interval.

    
    Created on 2010-08-15
    @author: jldupont
"""
import dbus.service
    
from app.system.base import AgentThreadedBase
from app.system import mswitch

__all__=[]


class RatingsSignalRx(dbus.service.Object):
    """
    DBus signals for the /ratings path
    """
    PATH="/ratings"
    
    def __init__(self, agent):
        dbus.service.Object.__init__(self, dbus.SessionBus(), self.PATH)
        self.agent=agent

        dbus.Bus().add_signal_receiver(self.rx_rating,
                                       signal_name="rating",
                                       dbus_interface="com.systemical.services",
                                       bus_name=None,
                                       path="/ratings"
                                       )
                    
        dbus.Bus().add_signal_receiver(self.rx_qratings,
                                       signal_name="qratings",
                                       dbus_interface="com.systemical.services",
                                       bus_name=None,
                                       path="/ratings"
                                       )            
        
        dbus.Bus().add_signal_receiver(self.rx_qrating,
                                       signal_name="qrating",
                                       dbus_interface="com.systemical.services",
                                       bus_name=None,
                                       path="/ratings"
                                       )            


    ## ==========================================================================================
    ## SIGNAL EMITTERS

    @dbus.service.signal(dbus_interface="com.systemical.services", signature="ssisssd")
    def rating(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        """
        Signal emitter for "/ratings/rating"
        """

    @dbus.service.signal(dbus_interface="com.systemical.services", signature="ii")
    def updated(self, timestamp, ratings_count):
        """
        Signal emitter for "/ratings/updated"
        """
        
        
    ## ==========================================================================================
    ## SIGNAL RECEIVERS
    def rx_qratings(self, source, ref, timestamp, count):
        mswitch.publish(self, "in_qratings", source, ref, timestamp, count)

    def rx_qrating(self, source, ref, artist_name, album_name, track_name):
        mswitch.publish(self, "in_qrating", source, ref, artist_name, album_name, track_name)

    def rx_rating(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        mswitch.publish(self, "in_rating", source, ref, timestamp, artist_name, album_name, track_name, rating)




class DbusAgent(AgentThreadedBase):
    
    def __init__(self):
        AgentThreadedBase.__init__(self)
        self.srx=RatingsSignalRx(self)

    def h_out_rating(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        self.srx.rating(source, timestamp, artist_name, album_name, track_name, rating) 

    def h_out_updated(self, timestamp, ratings_count):
        self.srx.updated(timestamp, ratings_count)


_=DbusAgent()
_.start()
