VENV := $(CURDIR)/venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
NPM := $(VENV)/bin/npm
NPX := $(VENV)/bin/npx
NODE_VERSION := 20.18.0
NODE_ENV_VARS := PATH=$(VENV)/bin:$$PATH npm_config_cache=$(VENV)/.npm-cache

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
	cd frontend && rm -rf node_modules && $(NODE_ENV_VARS) $(NPM) install --no-fund --no-audit
	@echo "Installing docs dependencies..."
	cd docs && rm -rf node_modules && $(NODE_ENV_VARS) $(NPM) install --no-fund --no-audit
	@cp -n .env.example .env 2>/dev/null && echo "Created .env — add your GROQ_API_KEY" || echo ".env already exists, skipping"
	@echo ""
	@echo "  ✓ Installation complete. Run: make start"
	@echo ""

# ── Start ──────────────────────────────────────────────────────────────────────
start:
	@if [ ! -f $(PYTHON) ]; then echo "Error: venv not found. Run 'make install' first." && exit 1; fi
	@$(PYTHON) start.py

# ── Stop ───────────────────────────────────────────────────────────────────────
stop:
	@$(PYTHON) -c "import start; start.stop()" 2>/dev/null || true
	@pkill -f "uvicorn api:app" 2>/dev/null || true
	@sleep 1

# ── Restart ────────────────────────────────────────────────────────────────────
restart: stop start

# ── Status ─────────────────────────────────────────────────────────────────────
status:
	@if [ -f /tmp/aflhr_pids.txt ]; then \
		echo "--- Running PIDs ---"; \
		cat /tmp/aflhr_pids.txt; \
		echo "--- Processes ---"; \
		while read pid; do ps -p $$pid -o pid,command 2>/dev/null | tail -1; done < /tmp/aflhr_pids.txt; \
	else \
		echo "  Nothing running (no PID file found)"; \
	fi

# ── Smoke test ─────────────────────────────────────────────────────────────────
smoke:
	$(PYTHON) evaluate.py --precompute --split dev --version v2 --limit 20

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	$(PYTHON) -m pytest tests/ -v

test-all:
	$(PYTHON) -m pytest tests/ -v --run-slow
