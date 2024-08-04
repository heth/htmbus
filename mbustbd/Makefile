VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
SERVICE=mbustbd
SYSTEMDDIR=/etc/systemd/system/



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
	
clean:
	rm -rf __pycache__
	rm -rf $(VENV)
	rm -f htutil
