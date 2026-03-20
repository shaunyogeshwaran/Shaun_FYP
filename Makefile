PYTHON := /opt/anaconda3/bin/python
PID_BACKEND := /tmp/aflhr_backend.pid
PID_FRONTEND := /tmp/aflhr_frontend.pid
BACKEND_PORT := 8000
FRONTEND_PORT := 5173

.PHONY: start stop restart status backend frontend install smoke help

# ── Default ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  make start      Start backend + frontend"
	@echo "  make stop       Stop backend + frontend"
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
	@echo ""
	@echo "  → http://localhost:$(FRONTEND_PORT)"
	@echo ""

# ── Stop ───────────────────────────────────────────────────────────────────────
stop:
	@pkill -f "uvicorn api:app" 2>/dev/null && echo "Stopped backend" || true
	@pkill -f "vite" 2>/dev/null && echo "Stopped frontend" || true
	@rm -f $(PID_BACKEND) $(PID_FRONTEND)
	@sleep 2

# ── Restart ────────────────────────────────────────────────────────────────────
restart: stop start

# ── Status ─────────────────────────────────────────────────────────────────────
status:
	@echo "--- Ports ---"
	@lsof -i :$(BACKEND_PORT) -i :$(FRONTEND_PORT) -P 2>/dev/null | grep LISTEN || echo "  Nothing running"
	@echo "--- Backend health ---"
	@curl -sf http://localhost:$(BACKEND_PORT)/api/health 2>/dev/null || echo "  Backend unreachable"

# ── Install ────────────────────────────────────────────────────────────────────
install:
	$(PYTHON) -m pip install -r requirements.txt
	cd frontend && npm install
	@cp -n .env.example .env 2>/dev/null && echo "Created .env — add your GROQ_API_KEY" || echo ".env already exists, skipping"

# ── Smoke test ─────────────────────────────────────────────────────────────────
smoke:
	$(PYTHON) evaluate.py --precompute --split dev --version v2 --limit 20
