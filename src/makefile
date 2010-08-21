#
# @author Jean-Lou Dupont
# http://www.systemical.com/
#
PRJ=musync

PYTHON=`which python`
BASE=/usr/lib/sync-playlists

all:
	@echo "make install"
	@echo "make clean"
	@echo "make buildsrc"

clean:
	@rm -rf $(DESTDIR)$(BASE)/*.pyc
		
install:

	## CREATE THE REQUIRED DIRECTORY HIERARCHY
	@install -d $(DESTDIR)$(BASE)
	@install -d $(DESTDIR)$(BASE)/app
	@install -d $(DESTDIR)$(BASE)/app/agents
	@install -d $(DESTDIR)$(BASE)/app/system
	
	## REQUIRED FOR CREATING THE .DEB PACKAGE
	@install -d $(DESTDIR)/usr/share/applications
	@install -d $(DESTDIR)/usr/share/icons
	@install -d $(DESTDIR)/usr/bin
	@install -d $(DESTDIR)/usr/lib

	@install -D $(CURDIR)/app/*.py            $(DESTDIR)$(BASE)/app/
	@install -D $(CURDIR)/app/agents/*.py     $(DESTDIR)$(BASE)/app/agents
	@install -D $(CURDIR)/app/agents/*.glade  $(DESTDIR)$(BASE)/app/agents
	@install -D $(CURDIR)/app/system/*.py     $(DESTDIR)$(BASE)/app/system

	@install -D $(CURDIR)/*.py                $(DESTDIR)$(BASE)/
	@install -D $(CURDIR)/*.desktop           $(DESTDIR)/usr/share/applications/
	@install -D $(CURDIR)/*.png               $(DESTDIR)/usr/share/icons/ 

	## INSTALL BIN
	@install $(CURDIR)/$(PRJ) $(DESTDIR)/usr/bin/

	## SPEED-UP STARTUP... marginal
	@python -m compileall ${DESTDIR}$(BASE)/
	
buildsrc:
	debuild -S