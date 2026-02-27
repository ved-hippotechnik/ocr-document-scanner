.PHONY: install run-backend run-frontend run test lint clean db-migrate

# ── Install ─────────────────────────────────────────────────────────────────
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# ── Run ─────────────────────────────────────────────────────────────────────
run-backend:
	cd backend && FLASK_ENV=development python run.py

run-frontend:
	cd frontend && npm start

run: ## Run both backend and frontend (requires two terminals or tmux)
	@echo "Run 'make run-backend' and 'make run-frontend' in separate terminals"

# ── Test ────────────────────────────────────────────────────────────────────
test-backend:
	cd backend && python -m pytest tests/ -v

test-frontend:
	cd frontend && npm test -- --watchAll=false

test: test-backend test-frontend

# ── Lint ────────────────────────────────────────────────────────────────────
lint-backend:
	cd backend && python -m flake8 app/ --max-line-length=120 --exclude=__pycache__,migrations

lint-frontend:
	cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=0

lint: lint-backend lint-frontend

# ── Database ────────────────────────────────────────────────────────────────
db-migrate:
	cd backend && flask db upgrade

db-reset:
	cd backend && rm -f instance/ocr_scanner.db && flask db upgrade

# ── Docker ──────────────────────────────────────────────────────────────────
docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

# ── Clean ───────────────────────────────────────────────────────────────────
clean:
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/node_modules/.cache
	rm -rf backend/.pytest_cache

# ── Health check ────────────────────────────────────────────────────────────
check:
	@echo "Backend health:"
	@curl -s http://localhost:5001/health | python -m json.tool 2>/dev/null || echo "Backend not running"
	@echo "\nFrontend:"
	@curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3000 2>/dev/null || echo "Frontend not running"
