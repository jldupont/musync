"""
    UI Agent

    Authorization Process:
    - retrieve access token from config file
    - valid / invalid ?
      - if invalid, tell user to Authorize
      
    Authorize:
    - get request token
    - open Web browser window with url to authorize
      - ask user to enter Verification code
    
    Messages Emitted:
    - "tick"
    - "__quit__"
    - "start_authorize"
    - "start_verification"
    
    Messages Processed:
    - "mb_tracks"  (coming from Dbus)
    - "authorization"
    - "oauth"
    - "error_oauth"
    
    
    @author: jldupont
    @date: May 28, 2010
"""
import os
import gtk  #@UnusedImport
import app.system.mswitch as mswitch
from app.system.ui_base import UiAgentBase

path=os.path.dirname(__file__)
GLADE_FILE=path+"/ui.glade"
        
class UiWindow(object):
    
    ## widgets to "wire-in"
    widgets=[ "bAuthorize", "bVerify"
                ,"eVerificationCode"
                ,"cbAuthorized", "cbMusicbrainz"
             ]
    
    def __init__(self, glade_file):

        self.builder = gtk.Builder()
        self.builder.add_from_file(glade_file)
        self.window = self.builder.get_object("ui_window")
        self.window.set_deletable(False)

        self._grabWidgets()  
        self._setClickedHandlers()      
        
        self.window.connect("destroy-event", self.do_destroy)
        self.window.connect("destroy",       self.do_destroy)
        self.window.present()
        
    def _grabWidgets(self):
        for w in self.widgets:
            self.__dict__[w]=self.builder.get_object(w)
            self.__dict__[w].set_property("name", w)
            
    def _setClickedHandlers(self):
        for w in self.widgets:
            if w.startswith("b"):
                ch=getattr(self, "_ch"+w[1:])
                self.__dict__[w].connect("clicked", ch)
        
    def do_destroy(self, *_):
        mswitch.publish(self, "app_close")
        
    ## ===============================================================
    def _chVerify(self, *_):
        """ Starts the verification phase
        """
        vc=self.eVerificationCode.get_text()
        mswitch.publish(self, "start_verify", vc)

    def _chAuthorize(self, *_):
        """ Starts the authorization phase
        """  
        mswitch.publish(self, "start_authorize")


    def _updateState(self, state):
        if state=="wait_auth":
            self.bAuthorize.set_sensitive(True)            
            self.bVerify.set_sensitive(False)
            self.cbAuthorized.set_active(False)
            
        if state=="wait_verify":
            self.bAuthorize.set_sensitive(False)
            self.bVerify.set_sensitive(True)
            self.cbAuthorized.set_active(False)
            
        if state=="verified":
            self.bAuthorize.set_sensitive(False)
            self.bVerify.set_sensitive(False)
            self.eVerificationCode.set_text("")
            self.cbAuthorized.set_active(True)
            
    def do_hide(self):
        """ Hides the ui window
        """
        self.window.hide()

    def mb_detected(self):
        self.cbMusicbrainz.set_sensitive(True)
        self.cbMusicbrainz.set_active(True)
        self.cbMusicbrainz.set_sensitive(False)


class UiAgent(UiAgentBase):
    def __init__(self, time_base):
        UiAgentBase.__init__(self, time_base)
        
        self.glade_file=GLADE_FILE
        self.ui_window_class=UiWindow
        
        self.state="wait_auth"
        self.mb_detected=False

    def h_mb_tracks(self, *_):
        """
        Detection of Musicbrainz-proxy-dbus
        
        @todo: add hysterisis? 
        """
        self.mb_detected=True
        self._do_update_mb()

    def h_start_authorize(self, *_):
        self.state="wait_verify"
        self._do_update_state()
        
    def h_error_oauth(self):
        """ When an access error occurs, we need
            to reset the authorization process
        """
        self.state="wait_auth"
        self._do_update_state()

    def h_oauth(self, key, secret):
        """
        If we get this message, it means that the authorization
        process when fine - switch to state
        """
        self.state="verified"
        self._do_update_state()

    def do_updates(self):
        self._do_update_mb()
        self._do_update_state()

    def _do_update_mb(self):
        if self.window:
            if self.mb_detected:
                self.window.mb_detected()

    def _do_update_state(self):
        if self.window:
            self.window._updateState(self.state)

        

        

if __name__=="__main__":
    """ For testing purposes
    """
    #import gobject
    ui=UiAgent(250)
    #gobject.timeout_add(TIME_BASE, ui.tick)
    
    gtk.main()
    
