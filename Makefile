-include .env
export

# SkinSync tasks. Requires Docker with Compose v2.
COMPOSE = docker compose
OBF_URL = https://static.openbeautyfacts.org/data/en.openbeautyfacts.org.products.csv.gz

.PHONY: up down logs seed seed-demo seed-test-prices remove-test-prices import-obf test test-api test-e2e lint migrate prod observability backup

up:            ## build and start the stack (http://localhost, mail at :8025)
	$(COMPOSE) up -d --build
down:
	$(COMPOSE) down
logs:
	$(COMPOSE) logs -f api worker web
migrate:
	$(COMPOSE) exec api alembic upgrade head
seed:          ## bootstrap knowledge, admin user, and demo data if SKINSYNC_DEMO_MODE=true
	$(COMPOSE) exec api python -m skinsync.cli bootstrap
	$(COMPOSE) exec -e SKINSYNC_ADMIN_PASSWORD api python -m skinsync.cli create-admin $${SKINSYNC_ADMIN_EMAIL:-admin@example.com}
	-$(COMPOSE) exec api python -m skinsync.cli seed-demo
seed-test-prices:   ## DEV ONLY: random, labelled "TEST PRICE — not real" prices for unpriced products
	$(COMPOSE) exec api python -m skinsync.cli seed-test-prices
remove-test-prices: ## delete every synthetic test price
	$(COMPOSE) exec api python -m skinsync.cli remove-test-prices
import-obf:    ## download the Open Beauty Facts export and import skincare products (ODbL)
	mkdir -p data && curl -fL -o data/obf.csv.gz $(OBF_URL)
	$(COMPOSE) cp data/obf.csv.gz api:/tmp/obf.csv.gz
	$(COMPOSE) exec api python -m skinsync.ingest.obf --file /tmp/obf.csv.gz
test: test-api
test-api:      ## backend tests (needs PostgreSQL + Redis on localhost; see README)
	cd apps/api && python -m pytest -q
test-e2e:      ## browser tests against a running stack
	cd apps/web && E2E_BASE_URL=$${E2E_BASE_URL:-http://localhost} npx playwright test
lint:
	cd apps/api && ruff check skinsync tests && bandit -q -c pyproject.toml -r skinsync -ll
	cd apps/web && npx tsc --noEmit
prod:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d --build
observability:
	$(COMPOSE) --profile observability up -d
backup:        ## dump the database to backups/
	mkdir -p backups && $(COMPOSE) exec -T postgres pg_dump -U skinsync -Fc skinsync > backups/skinsync-$$(date +%Y%m%d-%H%M%S).dump
