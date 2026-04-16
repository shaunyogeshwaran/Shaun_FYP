PYTHON ?= $(shell command -v python3 2>/dev/null || echo python)
PID_BACKEND := /tmp/aflhr_backend.pid
PID_FRONTEND := /tmp/aflhr_frontend.pid
PID_DOCS := /tmp/aflhr_docs.pid
BACKEND_PORT := 8000
FRONTEND_PORT := 5173
DOCS_PORT := 4000

.PHONY: start stop restart status backend frontend install smoke help

# ── Default ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  make start      Start backend + frontend + docs"
	@echo "  make stop       Stop backend + frontend + docs"
	@echo "  make restart    Stop then start"
	@echo "  make status     Show what's running"
	@echo "  make install    Install all dependencies"
	@echo "  make smoke      Smoke test (precompute 20 samples)"
	@echo ""

# ── Start ──────────────────────────────────────────────────────────────────────
start: stop
	@echo "Starting backend on port $(BACKEND_PORT)..."
	@$(PYTHON) -m uvicorn api:app --port $(BACKEND_PORT) --log-level warning > /tmp/aflhr_backend.log 2>&1 & echo $$! > $(PID_BACKEND)
	@echo "Waiting for backend (loading models, ~20s)..."
	@for i in $$(seq 1 30); do \
		sleep 2; \
		curl -sf http://localhost:$(BACKEND_PORT)/api/health > /dev/null 2>&1 && echo "  ✓ Backend ready" && break; \
		[ $$i -eq 30 ] && echo "  ✗ Backend failed — check: tail /tmp/aflhr_backend.log"; \
	done
	@echo "Starting frontend on port $(FRONTEND_PORT)..."
	@cd frontend && npm run dev -- --port $(FRONTEND_PORT) --strictPort > /tmp/aflhr_frontend.log 2>&1 & echo $$! > $(PID_FRONTEND)
	@sleep 4
	@grep -q "Local:" /tmp/aflhr_frontend.log \
		&& echo "  ✓ Frontend ready" \
		|| (echo "  ✗ Frontend failed — check: tail /tmp/aflhr_frontend.log" && cat /tmp/aflhr_frontend.log)
	@echo "Starting docs on port $(DOCS_PORT)..."
	@cd docs && npx docusaurus start --port $(DOCS_PORT) --no-open > /tmp/aflhr_docs.log 2>&1 & echo $$! > $(PID_DOCS)
	@sleep 4
	@curl -sf http://localhost:$(DOCS_PORT) > /dev/null 2>&1 \
		&& echo "  ✓ Docs ready" \
		|| echo "  ✗ Docs failed — check: tail /tmp/aflhr_docs.log"
	@echo ""
	@echo "  → App:  http://localhost:$(FRONTEND_PORT)"
	@echo "  → Docs: http://localhost:$(DOCS_PORT)"
	@echo "  → API:  http://localhost:$(BACKEND_PORT)/docs"
	@echo ""

# ── Stop ───────────────────────────────────────────────────────────────────────
stop:
	@pkill -f "uvicorn api:app" 2>/dev/null && echo "Stopped backend" || true
	@kill $$(cat $(PID_FRONTEND) 2>/dev/null) 2>/dev/null && echo "Stopped frontend" || true
	@kill $$(cat $(PID_DOCS) 2>/dev/null) 2>/dev/null && echo "Stopped docs" || true
	@rm -f $(PID_BACKEND) $(PID_FRONTEND) $(PID_DOCS)
	@sleep 2

# ── Restart ────────────────────────────────────────────────────────────────────
restart: stop start

# ── Status ─────────────────────────────────────────────────────────────────────
status:
	@echo "--- Ports ---"
	@lsof -i :$(BACKEND_PORT) -i :$(FRONTEND_PORT) -i :$(DOCS_PORT) -P 2>/dev/null | grep LISTEN || echo "  Nothing running"
	@echo "--- Backend health ---"
	@curl -sf http://localhost:$(BACKEND_PORT)/api/health 2>/dev/null || echo "  Backend unreachable"

# ── Install ────────────────────────────────────────────────────────────────────
install:
	$(PYTHON) -m pip install -r requirements.txt
	cd frontend && npm install
	cd docs && npm install
	@cp -n .env.example .env 2>/dev/null && echo "Created .env — add your GROQ_API_KEY" || echo ".env already exists, skipping"

# ── Smoke test ─────────────────────────────────────────────────────────────────
smoke:
	$(PYTHON) evaluate.py --precompute --split dev --version v2 --limit 20
