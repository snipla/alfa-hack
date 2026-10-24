.PHONY: help lint guard-clean \
	infra infra-down \
	dev dev-back dev-front dev-ml-back dev-down \
	dev-cli dev-back-cli dev-front-cli \
	prod-build prod-down \
	prod-cli prod-back-cli prod-front-cli\
	sync sync-restart sync-reset sync-stop sync-status sync-monitor \
	nginx-up nginx-stop nginx-down nginx-hard-restart nginx-restart nginx-reload nginx-test nginx-logs nginx-shell nginx-status nginx-rebuild

-include .env

VERSION ?= $(shell git rev-parse --short HEAD)
export VERSION

DOCKER_CONTEXT_CLEAN := $(or $(patsubst "%",%,$(patsubst '%',%,$(strip $(DOCKER_CONTEXT)))),default)
DOMAIN_CLEAN := $(or $(patsubst "%",%,$(patsubst '%',%,$(strip $(DOMAIN)))),shtrmx.ru)

LOCAL = docker --context default compose
REMOTE = docker --context $(DOCKER_CONTEXT_CLEAN) compose

INFRA = $(REMOTE) -f docker-compose.yml -p alfa-infra
COMPOSE_WEB = $(REMOTE) -f docker-compose.web.yml
DEV = $(REMOTE) -f docker-compose.dev.yml -p dev
PROD = $(REMOTE) -f docker-compose.prod.yml -p prod

SERVICE_WEB = nginx
SERVICE ?= $(SERVICE_WEB)

MUTAGEN_LABEL = project=alfa-hack
MUTAGEN_CONFIG_NAME = alfa-config
LOCAL_DIR = ./.config
REMOTE_HOST_SSH ?= root@$(DOMAIN_CLEAN)
REMOTE_BASE_DIR = /opt/alfa
REMOTE_HOST = $(REMOTE_HOST_SSH):$(REMOTE_BASE_DIR)
REMOTE_ENV_HOST = $(REMOTE_HOST)/enviroment
ENV_SERVICES = backend backend-ml frontend

### Infrastructure (MariaDB + Nginx)

infra: nginx-up
	$(INFRA) up -d --wait --remove-orphans

infra-down:
	$(INFRA) down

### Development

dev: infra
	$(DEV) up --watch --build

dev-back: infra
	$(DEV) up --build backend-dev --watch

dev-front: infra
	$(DEV) up -d --build php-frontend-dev --watch

dev-ml-back: infra
	$(DEV) up -d --build backend-ml-dev --watch

dev-down:
	$(DEV) down

# clis

dev-back-cli:
	$(DEV) exec -it backend-dev bash

dev-front-cli:
	$(DEV) exec -it php-frontend-dev bash

### Production

prod-build: infra
	$(PROD) up --build -d --wait --remove-orphans

prod-down:
	$(PROD) down

# clis

prod-cli: prod-back-cli

prod-back-cli:
	$(PROD) exec -it backend bash

prod-front-cli:
	$(PROD) exec -it php-frontend bash

### Syncing 

sync:
	@ssh $(REMOTE_HOST_SSH) "mkdir -p $(REMOTE_BASE_DIR)/mariadb $(REMOTE_BASE_DIR)/enviroment/root $(foreach svc,$(ENV_SERVICES),$(REMOTE_BASE_DIR)/enviroment/$(svc))"
	@if ! mutagen sync list $(MUTAGEN_CONFIG_NAME) >/dev/null 2>&1; then \
		mutagen sync create \
			--name=$(MUTAGEN_CONFIG_NAME) \
			--label=$(MUTAGEN_LABEL) \
			--sync-mode=two-way-resolved \
			--ignore-vcs \
			--ignore="mariadb" \
			--ignore="enviroment" \
			--ignore="*.log" \
			--ignore="__pycache__" \
			--ignore="*.pyc" \
			--ignore=".pytest_cache" \
			--ignore=".env.local" \
			--default-file-mode=0644 \
			--default-directory-mode=0755 \
			$(LOCAL_DIR) \
			$(REMOTE_HOST); \
	fi
	@if ! mutagen sync list alfa-env-root >/dev/null 2>&1; then \
		mutagen sync create \
			--name=alfa-env-root \
			--label=$(MUTAGEN_LABEL) \
			--sync-mode=two-way-resolved \
			--ignore="*" \
			--ignore="!.env" \
			--ignore="!.env.dev" \
			--default-file-mode=0600 \
			--default-directory-mode=0755 \
			. \
			$(REMOTE_ENV_HOST)/root; \
	fi
	@for svc in $(ENV_SERVICES); do \
		if ! mutagen sync list alfa-env-$$svc >/dev/null 2>&1; then \
			mutagen sync create \
				--name=alfa-env-$$svc \
				--label=$(MUTAGEN_LABEL) \
				--sync-mode=two-way-resolved \
				--ignore="*" \
				--ignore="!.env" \
				--ignore="!.env.dev" \
				--default-file-mode=0600 \
				--default-directory-mode=0755 \
				./$$svc \
				$(REMOTE_ENV_HOST)/$$svc; \
		fi; \
	done
	@if mutagen sync list --label-selector=$(MUTAGEN_LABEL) 2>/dev/null | grep -q "Status: Halted"; then \
		mutagen sync reset --label-selector=$(MUTAGEN_LABEL); \
	else \
		mutagen sync resume --label-selector=$(MUTAGEN_LABEL) 2>/dev/null || true; \
	fi
	$(MAKE) sync-monitor

sync-restart: sync-stop sync

sync-reset:
	mutagen sync reset --label-selector=$(MUTAGEN_LABEL)

sync-stop:
	-mutagen sync terminate --label-selector=$(MUTAGEN_LABEL)

sync-status:
	mutagen sync list --label-selector=$(MUTAGEN_LABEL)

sync-monitor:
	watch -n 1 -c "mutagen sync list --label-selector=$(MUTAGEN_LABEL)"

### Nginx

nginx-up:
	$(COMPOSE_WEB) up -d

nginx-stop:
	$(COMPOSE_WEB) stop

nginx-down:
	$(COMPOSE_WEB) down

nginx-hard-restart:
	$(COMPOSE_WEB) down
	$(COMPOSE_WEB) up -d

nginx-restart:
	$(COMPOSE_WEB) restart $(SERVICE)

nginx-reload:
	$(COMPOSE_WEB) exec $(SERVICE) sh -c "/docker-entrypoint.d/20-envsubst-on-templates.sh && nginx -s reload"

nginx-test:
	$(COMPOSE_WEB) exec $(SERVICE) sh -c "/docker-entrypoint.d/20-envsubst-on-templates.sh && nginx -t"

nginx-logs:
	$(COMPOSE_WEB) logs -f $(SERVICE)

nginx-shell:
	$(COMPOSE_WEB) exec -it $(SERVICE) sh

nginx-status:
	$(COMPOSE_WEB) ps

nginx-rebuild:
	$(COMPOSE_WEB) up --build -d 
	$(COMPOSE_WEB) restart $(SERVICE)
