#!/usr/bin/make -f

SERVICE := responsivesecurity
DESTDIR ?= dist_root
SERVICEDIR ?= /srv/$(SERVICE)

UWSGI_MOD ?= python3
UWSGI_USER ?= responsivesecurity
UWSGI_GROUP ?= responsivesecurity

.PHONY: all install clean


all: setup/uwsgi/responsivesecurity.ini

install: all
	install -d -m 755                                    $(DESTDIR)/etc/uwsgi/apps-enabled/
	install -m 444 setup/uwsgi/responsivesecurity.ini    $(DESTDIR)/etc/uwsgi/apps-enabled/
	install -d -m 755                                    $(DESTDIR)/etc/nginx/sites-enabled/
	install -m 444 setup/nginx/responsivesecurity.conf   $(DESTDIR)/etc/nginx/sites-enabled/
	install -d -m 755                                    $(DESTDIR)/usr/lib/python3.5/
	install -m 644 setup/secrets.py                      $(DESTDIR)/usr/lib/python3.5/
	install -d -m 755                                    $(DESTDIR)$(SERVICEDIR)/
	install -m 644 service/*.py                          $(DESTDIR)$(SERVICEDIR)/
	cp --reflink=auto  service/hashes.lst.sorted         $(DESTDIR)$(SERVICEDIR)/
	install -m 644 service/gameserver_public_key.txt     $(DESTDIR)$(SERVICEDIR)/
	install -m 755 -d                                    $(DESTDIR)$(SERVICEDIR)/client/
	install -m 644 service/client/*                      $(DESTDIR)$(SERVICEDIR)/client/
	install -m 755 -d                                    $(DESTDIR)$(SERVICEDIR)/data/
	install -m 755 -d                                    $(DESTDIR)$(SERVICEDIR)/static/
	install -m 644 service/static/*                      $(DESTDIR)$(SERVICEDIR)/static/
	install -m 755 -d                                    $(DESTDIR)$(SERVICEDIR)/templates/
	install -m 644 service/templates/*                   $(DESTDIR)$(SERVICEDIR)/templates/

clean:
	rm -rf dist_root setup/uwsgi/responsivesecurity.ini 
	find . -name __pycache__ -exec rm -rf {} +
	find . -name '*.pyc' -delete

%: %.in
	m4 -DUSER=$(UWSGI_USER) -DGROUP=$(UWSGI_GROUP) -DUWSGI_MOD=$(UWSGI_MOD) $< > $@
