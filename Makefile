VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
NPM := $(VENV)/bin/npm
NPX := $(VENV)/bin/npx
NODE_VERSION := 20.18.0
PID_BACKEND := /tmp/aflhr_backend.pid
PID_FRONTEND := /tmp/aflhr_frontend.pid
PID_DOCS := /tmp/aflhr_docs.pid
BACKEND_PORT := 8000
FRONTEND_PORT := 5173
DOCS_PORT := 4000

.PHONY: start stop restart status install smoke test test-all help

# ── Default ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  make install    Install everything (Python venv + Node.js + all deps)"
	@echo "  make start      Start backend + frontend + docs"
	@echo "  make stop       Stop backend + frontend + docs"
	@echo "  make restart    Stop then start"
	@echo "  make status     Show what's running"
	@echo "  make test       Run fast unit tests (~4s)"
	@echo "  make test-all   Run all tests including slow integration (~60s)"
	@echo "  make smoke      Smoke test (precompute 20 samples)"
	@echo ""
	@echo "  Prerequisites: Python 3.10+ and make (Node.js is installed automatically)"
	@echo ""

# ── Install ────────────────────────────────────────────────────────────────────
install:
	@echo "Checking prerequisites..."
	@command -v python3 >/dev/null 2>&1 || (echo "Error: python3 not found. Install Python 3.10+ first." && exit 1)
	@echo "Creating Python virtual environment..."
	python3 -m venv $(VENV)
	@echo "Upgrading pip and fixing SSL certificates..."
	$(PIP) install --upgrade pip certifi
	@echo "Installing Node.js $(NODE_VERSION) into venv (via nodeenv)..."
	$(PIP) install nodeenv
	SSL_CERT_FILE=$$($(PYTHON) -c "import certifi; print(certifi.where())") \
		$(PYTHON) -m nodeenv --node=$(NODE_VERSION) --python-virtualenv --prebuilt $(VENV)
	@echo "Installing Python dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && rm -rf node_modules && $(NPM) install --no-fund --no-audit
	@echo "Installing docs dependencies..."
	cd docs && rm -rf node_modules && $(NPM) install --no-fund --no-audit
	@cp -n .env.example .env 2>/dev/null && echo "Created .env — add your GROQ_API_KEY" || echo ".env already exists, skipping"
	@echo ""
	@echo "  ✓ Installation complete. Run: make start"
	@echo ""

# ── Start ──────────────────────────────────────────────────────────────────────
start: stop
	@if [ ! -f $(PYTHON) ]; then echo "Error: venv not found. Run 'make install' first." && exit 1; fi
	@echo "Starting backend on port $(BACKEND_PORT)..."
	@$(PYTHON) -m uvicorn api:app --port $(BACKEND_PORT) --log-level warning > /tmp/aflhr_backend.log 2>&1 & echo $$! > $(PID_BACKEND)
	@echo "Waiting for backend (loading models, ~20s)..."
	@for i in $$(seq 1 30); do \
		sleep 2; \
		curl -sf http://localhost:$(BACKEND_PORT)/api/health > /dev/null 2>&1 && echo "  ✓ Backend ready" && break; \
		[ $$i -eq 30 ] && echo "  ✗ Backend failed — check: tail /tmp/aflhr_backend.log"; \
	done
	@echo "Starting frontend on port $(FRONTEND_PORT)..."
	@cd frontend && $(NPM) run dev -- --port $(FRONTEND_PORT) --strictPort > /tmp/aflhr_frontend.log 2>&1 & echo $$! > $(PID_FRONTEND)
	@sleep 4
	@grep -q "Local:" /tmp/aflhr_frontend.log \
		&& echo "  ✓ Frontend ready" \
		|| (echo "  ✗ Frontend failed — check: tail /tmp/aflhr_frontend.log" && cat /tmp/aflhr_frontend.log)
	@echo "Starting docs on port $(DOCS_PORT)..."
	@cd docs && $(NPX) docusaurus start --port $(DOCS_PORT) --no-open > /tmp/aflhr_docs.log 2>&1 & echo $$! > $(PID_DOCS)
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

# ── Smoke test ─────────────────────────────────────────────────────────────────
smoke:
	$(PYTHON) evaluate.py --precompute --split dev --version v2 --limit 20

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	$(PYTHON) -m pytest tests/ -v

test-all:
	$(PYTHON) -m pytest tests/ -v --run-slow
