"""
    Musicbrainz-proxy Dbus Agent
    
    Messages Processed:
    - "mb_track?" : to send through Dbus using "qTrack" signal
    
    Messages Generated:
    - "mb_tracks": issued as a result of receiving a "Tracks" signal on Dbus
    
    Created on 2010-08-15
    @author: jldupont
"""
import dbus.service
    
from app.system.base import AgentThreadedBase
from app.system import mswitch

__all__=[]


class MBSignalRx(dbus.service.Object):
    PATH="/Tracks"
    
    def __init__(self, agent):
        dbus.service.Object.__init__(self, dbus.SessionBus(), self.PATH)
        self.agent=agent
        
        dbus.Bus().add_signal_receiver(self.sTracks,
                                       signal_name="Tracks",
                                       dbus_interface="com.jldupont.musicbrainz.proxy",
                                       bus_name=None,
                                       path="/Tracks"
                                       )            
    
    @dbus.service.signal(dbus_interface="com.jldupont.musicbrainz.proxy", signature="ssss")
    def qTrack(self, ref, artist_name, track_name, priority):
        """
        Signal emitter for "/Tracks/qTrack"
        """

    def sTracks(self, source, ref, list_dic):
        """
        DBus signal handler - /Tracks/Tracks
        """
        mswitch.publish(self.agent, "mb_tracks", source, ref, list_dic)



class DbusAgent(AgentThreadedBase):
    
    def __init__(self):
        AgentThreadedBase.__init__(self)

        self.srx=MBSignalRx(self)
                   
    def hq_mb_track(self, ref, artist, title):
        """
        Handler for the 'mb_track?' message
        
        Sends a message on DBus
        """
        if (artist is None) or (title is None):
            return
    
        self.srx.qTrack(ref, artist, title)
            
_=DbusAgent()
_.start()
