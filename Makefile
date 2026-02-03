.PHONY: help check-prereqs init install install-backend install-frontend start-backend start-frontend start update clean status

help:
	@echo "Available commands:"
	@echo "  make check-prereqs     - Check for required tools (git, python3, pip)"
	@echo "  make init              - Initialize submodules and install all dependencies"
	@echo "  make install-backend   - Install backend dependencies only"
	@echo "  make install-frontend  - Install frontend dependencies only"
	@echo "  make start             - Start application (backend + frontend)"
	@echo "  make start-backend     - Start backend only (port 8081)"
	@echo "  make start-frontend    - Start frontend only (port 8080)"
	@echo "  make update            - Update submodules to latest"
	@echo "  make clean             - Remove venv, node_modules and build artifacts"
	@echo "  make status            - Show git and submodule status"

check-prereqs:
	@echo "==> Checking prerequisites..."
	@command -v git >/dev/null 2>&1 || { echo "❌ git is required but not installed. Visit https://git-scm.com"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "❌ python3 is required but not installed. Visit https://python.org"; exit 1; }
	@command -v pip3 >/dev/null 2>&1 || { echo "❌ pip3 is required but not installed."; exit 1; }
	@echo "✓ All prerequisites installed"
	@echo ""

init: check-prereqs
	@echo "==> Initializing submodules..."
	git submodule update --init --recursive
	@echo ""
	@echo "==> Creating Python virtual environment..."
	python3 -m venv venv
	@echo ""
	@echo "==> Installing Python dependencies..."
	./venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "==> Installing frontend dependencies..."
	cd frontend && corepack pnpm install
	@echo ""
	@echo "✓ Project initialized successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy sample.env to .env and add your DEEPGRAM_API_KEY"
	@echo "  2. Run 'make start' to start the application"
	@echo ""

install: init

install-backend:
	@echo "==> Installing backend dependencies..."
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

install-frontend:
	@echo "==> Installing frontend dependencies..."
	@if [ ! -d "frontend" ] || [ -z "$$(ls -A frontend)" ]; then \
		echo "❌ Error: Frontend submodule not initialized. Run 'make init' first."; \
		exit 1; \
	fi
	cd frontend && corepack pnpm install

start-backend:
	@if [ ! -f ".env" ]; then \
		echo "❌ Error: .env file not found. Copy sample.env to .env and add your DEEPGRAM_API_KEY"; \
		exit 1; \
	fi
	@echo "==> Starting backend on http://localhost:8081"
	./venv/bin/python app.py

start-frontend:
	@if [ ! -d "frontend" ] || [ -z "$$(ls -A frontend)" ]; then \
		echo "❌ Error: Frontend submodule not initialized. Run 'make init' first."; \
		exit 1; \
	fi
	@echo "==> Starting frontend on http://localhost:8080"
	cd frontend && corepack pnpm run dev -- --port 8080 --no-open

start:
	@if [ ! -f ".env" ]; then \
		echo "❌ Error: .env file not found. Copy sample.env to .env and add your DEEPGRAM_API_KEY"; \
		exit 1; \
	fi
	@if [ ! -d "frontend" ] || [ -z "$$(ls -A frontend)" ]; then \
		echo "❌ Error: Frontend submodule not initialized. Run 'make init' first."; \
		exit 1; \
	fi
	@echo "==> Starting application..."
	@echo "    Backend:  http://localhost:8081"
	@echo "    Frontend: http://localhost:8080"
	@echo ""
	@$(MAKE) start-backend & $(MAKE) start-frontend & wait

update:
	@echo "Updating submodules..."
	git submodule update --remote --merge
	@echo "Submodules updated!"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf venv/
	rm -rf frontend/node_modules/
	rm -rf frontend/dist/
	rm -rf __pycache__/
	rm -rf *.pyc
	@echo "Clean complete!"

status:
	@echo "Git status:"
	@git status --short
	@echo "\nSubmodule status:"
	@git submodule status
