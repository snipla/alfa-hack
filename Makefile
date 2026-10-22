.PHONY: help up stop down restart hard-restart reload test logs shell status rebuild

COMPOSE_WEB = docker compose -f docker-compose.web.yml
SERVICE_WEB = nginx


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