"""
    Ratings Dbus Agent

    com.systemical.services/ratings/[rating;qrating]
    
    Messages Processed:
    - "rating"
    - "out_rating"  : transit to "/ratings/rating" Dbus message
    - "out_updated" : transit to "/ratings/updated" Dbus message
    
    Messages Generated:
    - "qrating"
    
    ==========================================================
    
    Dbus Interface:
    * (IN/OUT) rating(source, timestamp, artist_name, album_name, track_name, rating) 

            Upon receiving this signal, the Sync-Playlists will store the rating
            associated with the specified track.

            @param source: (string)   the 'source' application generating this rating
            @param timestamp: (string) the time in seconds since the epoch, in UTC
            @param artist_name: (string)
            @param album_name: (string)
            @param track_name: (string)
            @param rating: (integer) [0:100]
            
            Rating signals received with out-dated timestamp are discarded.
            
    * (IN) qrating(artist_name, album_name, track_name)
    
            Rating?  Question signal for which Sync-Playlists will retrieve, if available,
            the rating associated with the specified track.  Sync-Playlists will reply
            using the "rating" signal (described above).

    * (OUT) updated(timestamp)
    
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
        
        dbus.Bus().add_signal_receiver(self.rx_qrating,
                                       signal_name="qrating",
                                       dbus_interface="com.systemical.services",
                                       bus_name=None,
                                       path="/ratings"
                                       )            


    ## ==========================================================================================
    ## SIGNAL EMITTERS

    @dbus.service.signal(dbus_interface="com.systemical.services", signature="sisssd")
    def rating(self, source, timestamp, artist_name, album_name, track_name, rating):
        """
        Signal emitter for "/ratings/rating"
        """

    @dbus.service.signal(dbus_interface="com.systemical.services", signature="i")
    def updated(self, timestamp):
        """
        Signal emitter for "/ratings/updated"
        """
        
        
    ## ==========================================================================================
    ## SIGNAL RECEIVERS

    def rx_rating(self, source, timestamp, artist_name, album_name, track_name, rating):
        mswitch.publish(self, "rating", source, timestamp, artist_name, album_name, track_name, rating)

    def rx_qrating(self, artist_name, album_name, track_name):
        mswitch.publish(self, "qrating", artist_name, album_name, track_name)



class DbusAgent(AgentThreadedBase):
    
    def __init__(self):
        AgentThreadedBase.__init__(self)
        self.srx=RatingsSignalRx(self)

    def h_out_rating(self, source, timestamp, artist_name, album_name, track_name, rating):
        self.srx.rating(source, timestamp, artist_name, album_name, track_name, rating) 

    def h_out_updated(self, timestamp):
        self.srx.updated(timestamp)


_=DbusAgent()
_.start()
