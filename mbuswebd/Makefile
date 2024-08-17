VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
SERVICE=mbuswebd
SYSTEMDDIR=/etc/systemd/system/
NGINX_CONF=/etc/nginx/nginx.conf
NGINX_SITES_ENABLED=/etc/nginx/sites-enabled
NGINX_CONF_BU=/etc/nginx/nginx.conf.backup



$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	@if test ! -L htutil; then\
		echo "Linking shared utilities";\
		ln -s ../htutil .;\
	fi
	@if grep -P '^import collections$$' venv/lib/python3*/site-packages/flask_nav/__init__.py; then\
		echo "Trying to correct an error in flask_nav" ;\
		sed -i 's/import collections/import collections.abc as collections/' venv/lib/python3.1*/site-packages/flask_nav/__init__.py;\
		ls;\
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
		sudo sed -i s!SERVICENAME!`realpath -s $(SERVICE).sh`! $(SYSTEMDDIR)$(SERVICE).service;\
		sudo systemctl enable $(SERVICE).service;\
		sudo systemctl start $(SERVICE).service;\
	fi
	@if ! grep "M-Bus" $(NGINX_CONF); then\
		echo "Reconfiguring nginx";\
		sudo apt install libnginx-mod-http-fancyindex;\
		sudo cp $(NGINX_CONF) $(NGINX_CONF_BU);\
		sudo systemctl stop nginx;\
		sudo cp ./nginx.conf $(NGINX_CONF);\
		sudo systemctl start nginx;\
		sudo rm $(NGINX_SITES_ENABLED)/*
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

	@if grep "M-Bus" $(NGINX_CONF); then\
			if test -f $(NGINX_CONF_BU); then\
				echo "Reconfiguring nginx to original";\
				sudo cp $(NGINX_CONF_BU) $(NGINX_CONF);\
		fi;\
	fi
	
clean:
	rm -rf __pycache__
	rm -rf $(VENV)
	rm -f htutil
