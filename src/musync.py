"""
    MuSync
    
    @author: jldupont
"""
import os
import sys

APP_NAME = "musync"
APP_ICON = APP_NAME
ICON_PATH="/usr/share/icons/"
ICON_FILE=APP_NAME+".png"
LOG_PATH="~/"+APP_NAME+".log"
DB_PATH ="~/"+APP_NAME+".sqlite"
HELP_URL="http://www.systemical.com/doc/opensource/"+APP_NAME
TIME_BASE=250  ##milliseconds
TICKS_SECOND=1000/TIME_BASE
WS_RATINGS_END_POINT="services.systemical.com/ratings/v1"
CONSUMER_KEY="services.systemical.com"
CONSUMER_SECRET="PkyFMaAhcPacERXjRWFv1a/U"
SERVER = 'services.systemical.com'
PORT = 80
OAUTH_BASE = "http://services.systemical.com/_ah/"


###<<< DEVELOPMENT MODE SWITCHES
MSWITCH_OBSERVE_MODE=False
MSWITCH_DEBUGGING_MODE=False
MSWITCH_DEBUG_INTEREST=False
DEV_MODE=True
###>>>

## For development environment
ppkg=os.path.abspath( os.getcwd() +"/app")
if os.path.exists(ppkg):
    sys.path.insert(0, ppkg)

try:
    import oauth #@UnusedImport
except:
    from app.agents.notifier import notify
    notify(APP_NAME, APP_ICON, "Requires 'python-oauth' package")
    sys.exit(1)
    

import gobject
import dbus.glib
from dbus.mainloop.glib import DBusGMainLoop
import gtk

try:
    gobject.threads_init()  #@UndefinedVariable
    dbus.glib.init_threads()
    DBusGMainLoop(set_as_default=True)
    
    from app.system import base as base
    base.debug=DEV_MODE
    base.debug_interest=MSWITCH_DEBUG_INTEREST
    from app.system import mswitch #@UnusedImport
    mswitch.observe_mode=MSWITCH_OBSERVE_MODE
    mswitch.debugging_mode=MSWITCH_DEBUGGING_MODE
    
    ### ===========================================================
    ### Agents which require configuration
    ###
    from app.agents.notifier import NotifierAgent
    import app.agents.ratings_dbus  #@UnresolvedImport @UnusedImport
    from app.agents.ratings_cache import RatingsCacheAgent
    _rca=RatingsCacheAgent(DB_PATH, DEV_MODE)
    _rca.start()
    
    from app.agents.ratings_db import RatingsDbAgent
    _rda=RatingsDbAgent(DB_PATH, DEV_MODE)
    _rda.start()
    
    import app.agents.mb_dbus       #@UnresolvedImport @UnusedImport
    
    from app.agents.tray import TrayAgent
    _ta=TrayAgent(APP_NAME, ICON_PATH, ICON_FILE, HELP_URL)
    
    _na=NotifierAgent(APP_NAME, APP_ICON)
    _na.start()
    
    from app.agents.logger import LoggerAgent
    _la=LoggerAgent(APP_NAME, LOG_PATH)
    _la.start()
    
    #from app.agents.ratings_cache import UploadCacheAgent
    #_uca=UploadCacheAgent(DB_PATH, DEV_MODE)
    #_uca.start()
    
    #from app.agents.cache import CacheAgent
    #_ca=CacheAgent(DB_PATH, DEV_MODE)
    #_ca.start()
    
    from app.agents._tester import TesterAgent  #@UnusedImport
    import app.agents.monitor #@UnresolvedImport @UnusedImport
    
    from app.agents.uploader import UploaderAgent
    _upa=UploaderAgent(WS_RATINGS_END_POINT, SERVER, PORT, CONSUMER_KEY, CONSUMER_SECRET, DEV_MODE)
    _upa.start()
    
    ### ===========================================================
    ###
    
    #from app.agents import adbus
    from app.agents.authorize import AuthorizeAgent  #@UnusedImport
    _authAgent=AuthorizeAgent(APP_NAME, SERVER, PORT, CONSUMER_KEY, CONSUMER_SECRET, OAUTH_BASE)
    _authAgent.start()
    
    from app.agents.ui import UiAgent
    _uia=UiAgent(TIME_BASE)
    gobject.timeout_add(TIME_BASE, _uia.tick)
    
    gtk.main()
    
except Exception,e:
    from app.agents.notifier import notify #@Reimport
    notify(APP_NAME, APP_ICON, "There was an error: %s" % e)
    sys.exit(1)
