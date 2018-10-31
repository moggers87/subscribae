GIT_VERSION := $(shell git describe --dirty)

.PHONY: tests
tests: install-deps
	$(MAKE) clean-pyc
	$(MAKE) static-dev
	./manage.py test

.PHONY: install-pip-deps
install-pip-deps:
	./install_deps

.PHONY: install-npm-deps
install-npm-deps:
	npm install

.PHONY: install-deps
install-deps: install-pip-deps install-npm-deps

.PHONY: update-prod-deps
update-prod-deps:
	pip-compile -U --output-file requirements/prod.txt requirements/prod.in

.PHONY: update-dev-deps
update-dev-deps:
	pip-compile -U --output-file requirements/dev.txt requirements/dev.in

.PHONY: update-npm-deps
update-npm-deps:
	npm update

.PHONY: update-deps
update-deps: update-dev-deps update-prod-deps update-npm-deps

.PHONY: static-dev
static-dev:
	./manage.py collectstatic --no-input --clear -v0
	./manage.py assets build
	touch subscribae/wsgi.py

.PHONY: static-live
static-live: install-deps
	DJANGO_SETTINGS_MODULE=subscribae.settings_live ./manage.py collectstatic --no-input --clear
	DJANGO_SETTINGS_MODULE=subscribae.settings_live ./manage.py assets build

.PHONY: upload
upload: static-live
	./appcfg.py -V "$(GIT_VERSION)" update .
	echo "https://$(GIT_VERSION)-dot-subscribae.appspot.com/"

.PHONY: clean-pyc
clean-pyc:
	find . -name \*.pyc -delete
