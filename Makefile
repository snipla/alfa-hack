.PHONY: help up stop down restart hard-restart reload test logs shell status rebuild

COMPOSE_WEB = docker compose -f docker-compose.web.yml
REMOTE_DOCKER = docker --context shtrmx.ru compose
LOCAL_DOCKER = docker compose

SERVICE_WEB = nginx

MUTAGEN_NAME = alfa-config
LOCAL_DIR = ./.config
REMOTE_HOST = root@shtrmx.ru:/opt/alpha

### Developing

### syncing 
sync:
	@if mutagen sync list $(MUTAGEN_NAME) >/dev/null 2>&1; then \
		mutagen sync monitor $(MUTAGEN_NAME); \
	else \
		mutagen sync create \
			--name=$(MUTAGEN_NAME) \
			--sync-mode=two-way-resolved \
			--ignore-vcs \
			--ignore="*.log" \
			--ignore="__pycache__" \
			--ignore="*.pyc" \
			--ignore=".pytest_cache" \
			--ignore=".env.local" \
			--default-file-mode=0644 \
			--default-directory-mode=0755 \
			$(LOCAL_DIR) \
			$(REMOTE_HOST); \
		mutagen sync monitor $(MUTAGEN_NAME); \
	fi


sync-restart: sync-stop sync

sync-stop:
	-mutagen sync terminate $(MUTAGEN_NAME)

sync-status:
	mutagen sync list $(MUTAGEN_NAME)

sync-monitor:
	mutagen sync monitor $(MUTAGEN_NAME)

### Nginx actions

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
	$(COMPOSE_WEB) exec $(SERVICE) nginx -s reload

nginx-test:
	$(COMPOSE_WEB) exec $(SERVICE) nginx -t

nginx-logs:
	$(COMPOSE_WEB) logs -f $(SERVICE)

nginx-shell:
	$(COMPOSE_WEB) exec $(SERVICE) sh

nginx-status:
	$(COMPOSE_WEB) ps

nginx-rebuild:
	$(COMPOSE_WEB) up --build -d 
	$(COMPOSE_WEB) restart $(SERVICE)