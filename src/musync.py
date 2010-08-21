"""
    MuSync
    
    @author: jldupont
"""

APP_NAME = "musync"
APP_ICON = APP_NAME
ICON_PATH="/usr/share/icons/"
ICON_FILE=APP_NAME+".png"
LOG_PATH="~/"+APP_NAME+".log"
DB_PATH ="~/"+APP_NAME+".sqlite"
HELP_URL="http://www.systemical.com/doc/opensource/"+APP_NAME
DEV_MODE=True
TIME_BASE=250  ##milliseconds
TICKS_SECOND=1000/TIME_BASE
       
import os
import sys

## For development environment
ppkg=os.path.abspath( os.getcwd() +"/app")
if os.path.exists(ppkg):
    sys.path.insert(0, ppkg)

import gobject
import dbus.glib
from dbus.mainloop.glib import DBusGMainLoop
import gtk

gobject.threads_init()  #@UndefinedVariable
dbus.glib.init_threads()
DBusGMainLoop(set_as_default=True)

from app.system import base as base
base.debug=DEV_MODE
from app.system import mswitch #@UnusedImport

### ===========================================================
### Agents which require configuration
###
from app.agents.notifier import NotifierAgent
import app.agents.ratings_dbus  #@UnusedImport
import app.agents.ratings_cache #@UnusedImport
import app.agents.mb_dbus       #@UnusedImport

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

### ===========================================================
###

#from app.agents import adbus
from app.agents import authorize  #@UnusedImport
from app.agents.ui import UiAgent
_uia=UiAgent(TIME_BASE)
gobject.timeout_add(TIME_BASE, _uia.tick)

gtk.main()
