# -------------------------------------
# MAKEFILE
# -------------------------------------

# Parse docker container name prefix from working dir
ifeq ($(OS),Windows_NT)
	NAME := $(notdir $(CURDIR))
	LOCATION := $(CURDIR)
else
	NAME := $(shell basename $$PWD | sed -e s/[_\\.]//g)
	LOCATION := $(shell pwd -P)
endif

NAME := admin

PROJECT := ignored

CONTAINER_NAME ?= "django"

.DEFAULT_GOAL := help


# Project Commands
# =====================================

.PHONY: build
build: ## Build all containers
	docker-compose -p ${NAME} --verbose build

.PHONY: check
check:
	open https://console.cloud.google.com/cloud-build/dashboard

.PHONY: trello
trello:  ## If trello project exists, then the correct url for the project should be changed here
	open https://trello.com/

.PHONY: check.build
check.build: ## Launch browser to check the build status
	open https://console.cloud.google.com/cloud-build/dashboard

.PHONY: up
up: ## Bring up all containers
	docker-compose -p ${NAME} up -d

.PHONY: start
start: up

.PHONY: stop
stop:
	docker-compose -p ${NAME} stop

.PHONY: down
down:
	docker-compose -p ${NAME} down

.PHONY: init
init: envfile reqs.git reqs.py reqs.node init.django emails assets.init ## Initialize this project

.PHONY: serve
serve: ## Start development web server
	docker exec -it ${NAME}_django_1 python manage.py runserver 0.0.0.0:8002

.PHONY: serve.prod
serve.prod: ## Start production(ish) web server
	docker exec -it ${NAME}_django_1 python manage.py runserver 0.0.0.0:8002 --settings=config.settings.prod

.PHONY: debug
debug:  ## Command to enable remote debugging
	docker exec -it ${NAME}_django_1 python -m ptvsd --host 0.0.0.0 --port 3001 manage.py runserver 0.0.0.0:8002 --nothreading --noreload

.PHONY: debug.ssl
debug.ssl:  ## Command to enable remote debugging
	docker exec -it ${NAME}_django_1 python -m ptvsd --host 0.0.0.0 --port 3001 manage.py runsslserver 0.0.0.0:8002 --nothreading --noreload

.PHONY: serve.alt
serve.alt: ## Start development web server (port 7001)
	docker exec -it ${NAME}_django_1 python manage.py runserver 0.0.0.0:7001

.PHONY: serve.ssl
serve.ssl: ## Start ssl development web server (port 8000)
	docker exec -it ${NAME}_django_1 python manage.py runsslserver 0.0.0.0:8002


.PHONY: init.front
init.front: ## Install and run node server
	cd front-end && npm install && npm start

.PHONY: front
front: ## Run node server
	cd front-end && npm start

.PHONY: assets.init
assets.init: ## Initialize static assets
	cd site/static && npm run build-assets

.PHONY: assets
assets: ## Start static asset watch / compilation
	cd site/static && npm start

.PHONY: collectstatic
collectstatic: 
	docker exec -it ${NAME}_django_1 python manage.py collectstatic

.PHONY: envfile
envfile: ## copy over the .env file if it doesn't exist
	-cp -n site/env.dist site/.env

.PHONY: resetdb
resetdb: ## Reset Django / Postgres database
	docker exec -it ${NAME}_django_1 python manage.py reset_db --noinput

.PHONY: reset_db
reset_db: ## Reset Django / Postgres database
	docker exec -it ${NAME}_django_1 python manage.py reset_db --noinput


.PHONY: migrations
migrations: ## Run Django makemigrations
	docker exec -it ${NAME}_django_1 python manage.py makemigrations


.PHONY: migrate
migrate: ## Run all current migrations
	docker exec -it ${NAME}_django_1 python manage.py migrate
	
.PHONY: add_dashboard
add_dashboard: ## Run all current migrations
	docker exec -it ${NAME}_django_1 python manage.py startapp dashboard

.PHONY: po
po: ## Create / update po files
	docker exec -it ${NAME}_django_1 python manage.py makemessages -l ko -l zh_Hans

.PHONY: mo
mo: ## Compile all po -> mo files
	docker exec -it ${NAME}_django_1 python manage.py compilemessages -l ko -l zh_Hans

.PHONY: translations.out
translations.out: ## Output translations as spreadsheets
	docker exec -it ${NAME}_django_1 bash -c '/usr/app/scripts/translations/generate_xlsx.sh'

.PHONY: translations.in
translations.in: ## Input translations from spreadsheets
	docker exec -it ${NAME}_django_1 bash -c '/usr/app/scripts/translations/merge_in.sh'

.PHONY: shell
shell: ## Run a bash session on a container
	docker exec -it ${NAME}_django_1 /bin/bash

.PHONY: dbshell
dbshell: ## Run a psql session on the local database
	docker exec -u postgres -it ${NAME}_postgres_1 psql -U djangodb

.PHONY: import
import: ## Run a psql session on the local database
	docker exec -u postgres -i ${NAME}_postgres_1 psql -U djangodb djangodb < #/path/to/file/Cloud_SQL.sql
	#first drop all tables before importing a replacement db by:
	#make dbshell
	#DROP SCHEMA public CASCADE;
	#CREATE SCHEMA public;

.PHONY: djangoshell
djangoshell:
	docker exec -it ${NAME}_django_1 python manage.py shell

.PHONY: test.py
test.py: ## Run Python / Django test suite
	docker exec -it ${NAME}_django_1 pytest --create-db

.PHONY: test.js
test.js: ## Run Javascript test suite
	open http://localhost:3000
	cd site/\@static && npm test

.PHONY: reqs.git
reqs.git:
	-git submodule update --init --remote --recursive

.PHONY: reqs.py
reqs.py:
	docker exec -it ${NAME}_django_1 easy_install pdbpp
	docker exec -it ${NAME}_django_1 pip install -q -r requirements/local.txt
	docker exec -it ${NAME}_celery_1 easy_install pdbpp
	docker exec -it ${NAME}_celery_1 pip install -q -r requirements/local.txt

.PHONY: reqs.node
reqs.node:
	cd site/\@static && npm install

.PHONY: init.django
init.django: resetdb fixtures
	docker exec -it ${NAME}_django_1 python manage.py createsuperuser

.PHONY: odbc
odbc:
	docker exec -it ${NAME}_django_1 bash -c 'cd /usr/app/scripts/db/ && ./setup-odbc.sh'

.PHONY: emails
emails:
	cd site/@static && npm run build-emails

.PHONY: schema
schema:
	docker exec -it ${NAME}_django_1 bash -c 'python manage.py get_graphql_schema > apps/graphql/schema.graphql'

.PHONY: dbdump
dbdump:
	docker exec -it ${NAME}_postgres_1 bash -c './usr/app/django/scripts/db/dump-db-to-s3.sh'


.PHONY: fixtures
fixtures: resetdb
	docker exec -it ${NAME}_postgres_1 bash -c './usr/app/django/scripts/db/restore-db.sh'
	docker exec -it ${NAME}_django_1 python manage.py migrate

.PHONY: celery
celery:
	docker exec -it ${NAME}_celery_1 celery -A apps.core worker -l info

# Makefile Documentation
# =====================================
# See: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html

.PHONY: help
help: help-commands help-usage help-examples ## This help dialog

.PHONY: help-commands
help-commands:
	@echo "\nCommands:"
	@grep -E '^[a-zA-Z._-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Update this target to add additional usage
.PHONY: help-usage
help-usage:
	@echo "\nUsage:"
	@echo "make <command> [Options...]"
	@echo "make shell"
	@echo "make po"
	@echo "make mo"
	@echo "make heroku.deploy ENV_NAME=<env-name>"
	@echo "make heroku.up HEROKU_REMOTE=<dev|staging|prod>"
	@echo "make heroku.deploy HEROKU_REMOTE=<dev|staging|prod>"

# Update this target to add additinoal examples
.PHONY: help-examples
help-examples:
	@echo "\nExamples:"
	@echo "make shell"
	@echo "make shell CONTAINER_NAME=postgres"
	@echo "make po OPTS=\"-l de -l es\""
	@echo "make po OPTS=\"-a\""
	@echo "make heroku.deploy ENV_NAME=dev"
	@echo "make heroku.up HEROKU_REMOTE=dev"
	@echo "make heroku.deploy HEROKU_REMOTE=dev"
	@echo ""


# Prompts Commands
# =====================================
# See: http://stackoverflow.com/a/14316012 (user confirmation snippet)

# Usage Example:
#
# .PHONY ask-message
# ask-messages:
# 	@echo "About to do a thing."
#
# .PHONY ask
# ask: ask-message confirm
# 	@echo "Did a thing!"
#

.PHONY: confirm
confirm:
	@while [ -z "$$CONTINUE" ]; do \
		read -r -p "Continue? [y/N] " CONTINUE; \
	done ; \
	if [ ! $$CONTINUE == "y" ]; then \
	if [ ! $$CONTINUE == "Y" ]; then \
		echo "Exiting." ; exit 1 ; \
	fi \
	fi
