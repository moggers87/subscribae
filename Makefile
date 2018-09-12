tests:
	./manage.py test

static:
	export DJANGO_SETTINGS_MODULE=subscribae.settings_live
	rm -rf static
	./manage.py collectstatic --no-input
	./manage.py assets build

.PHONY: tests static
