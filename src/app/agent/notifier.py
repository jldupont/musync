"""
    Notifier Agent - Display notifications to the user
    
    Used to in situations when the user can act to correct a situation
    
    Uses 'pynotify' (desktop notification) to message
    the user in case of 'warning' and 'error' level log entries

    Messages Processed:
    ===================
    - "notify"
    - "logged"
    
    
    @author: jldupont
    Created on Jun 28, 2010
"""
import pynotify

from app.system.base import AgentThreadedBase

__all__=["NotifierAgent"]

class NotifierAgent(AgentThreadedBase):
    
    def __init__(self, app_name, icon_name):
        AgentThreadedBase.__init__(self)
        self.app_name=app_name
        self.icon_name=icon_name
        pynotify.init(app_name)        

        self.types=["w", "e", "warning", "error"]
        
    def h_notify(self, msg):
        """ 
        Direct access to the notification facility
        """
        n=pynotify.Notification(self.app_name, msg, self.icon_name)
        n.show()
        
        
    def h_logged(self, _logtype, loglevel, msg):
        #print "Notifier.h_logged, logtype(%s)" % logtype
        if loglevel in self.types:
            
            n=pynotify.Notification(self.app_name, msg, self.icon_name)
            n.set_urgency(pynotify.URGENCY_CRITICAL)
            n.show()

## Usage           
"""
_=NotifierAgent(APP_NAME, ICON_NAME)
_.start()
"""        
        