VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
SERVICE=mbusbed
SYSTEMDDIR=/etc/systemd/system/
CSVDIR=/var/www/data/



$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	@if test ! -L htutil; then\
		echo "Linking shared utilities";\
		ln -s ../htutil .;\
	fi



run:
	. $(VENV)/bin/activate
	$(PYTHON) $(SERVICE).py

install: $(SERVICE).service
	@if test ! -d $(CSVDIR); then\
		echo "Creating CSV directory";\
		sudo mkdir -p $(CSVDIR);\
		chown mbus:mbus $(CSVDIR);\
	fi
	@if test -f $(SYSTEMDDIR)/$(SERVICE).service; then\
		echo "$(SYSTEMDDIR)/$(SERVICE).service already exists - run 'make uninstall' first";\
		exit 1;\
	fi
	@if test ! -x $(PYTHON); then\
		echo "ERROR: Missing $(PYTHON) - Install virtual environment - run 'make' before 'make install'";\
		exit 1;\
	fi
	@if test -f $(SERVICE).service; then\
		echo "Creating systemd service file";\
		sudo cp $(SERVICE).service $(SYSTEMDDIR);\
		sudo sed -i s!PYTHONNAME!`realpath -s venv/bin/python3`! $(SYSTEMDDIR)$(SERVICE).service;\
		sudo sed -i s!SERVICENAME!`realpath $(SERVICE).py`! $(SYSTEMDDIR)$(SERVICE).service;\
		sudo systemctl enable $(SERVICE).service;\
		sudo systemctl start $(SERVICE).service;\
	fi

	@if test ! -d $(CSVDIR); then\
		echo "Creating CSV directory";\
		sudo mkdir $(CSVDIR);\
		sudo chown -R mbus:mbus $(CSVDIR);\
		sudo chmod 775 $(CSVDIR);\
	fi
	@if test ! -x /usr/local/bin/mbus-serial-request-data; then\
		echo "Install rscada/limbus from https://github.com/rscada/libmbus.git";\
		echo "Follow instalations insctructions: https://github.com/rscada/libmbus";\
	fi

uninstall:
	@if test ! -f $(SYSTEMDDIR)/$(SERVICE).service; then\
		echo "$(SYSTEMDDIR)/$(SERVICE).service does not exists - run 'make install' first";\
		exit;\
	else\
		sudo systemctl stop $(SERVICE).service;\
		sudo systemctl disable $(SERVICE).service;\
		sudo rm  $(SYSTEMDDIR)/$(SERVICE).service ;\
		sudo systemctl daemon-reload;\
	fi
	@if test  -x /usr/local/bin/mbus-serial-request-data; then\
		echo "Remember to remove libmbus";\
	fi
	
clean:
	sudo rm -rf __pycache__
	sudo rm -rf $(VENV)
	sudo rm -f htutil
	sudo rm -rf $(CSVDIR)
