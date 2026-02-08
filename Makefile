.PHONY: help check check-prereqs init install install-backend install-frontend start-backend start-frontend start test update clean status eject-frontend

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
	@echo "  make eject-frontend    - Eject frontend/contracts submodules for standalone dev"

check-prereqs:
	@echo "==> Checking prerequisites..."
	@command -v git >/dev/null 2>&1 || { echo "❌ git is required but not installed. Visit https://git-scm.com"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "❌ python3 is required but not installed. Visit https://python.org"; exit 1; }
	@command -v pip3 >/dev/null 2>&1 || { echo "❌ pip3 is required but not installed."; exit 1; }
	@echo "✓ All prerequisites installed"
	@echo ""
check: check-prereqs


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

test:
	@if [ ! -f ".env" ]; then \
		echo "❌ Error: .env file not found. Copy sample.env to .env and add your DEEPGRAM_API_KEY"; \
		exit 1; \
	fi
	@if [ ! -d "contracts" ] || [ -z "$$(ls -A contracts)" ]; then \
		echo "❌ Error: Contracts submodule not initialized. Run 'make init' first."; \
		exit 1; \
	fi
	@echo "==> Running contract conformance tests..."
	@bash contracts/tests/run-live-transcription-app.sh


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

eject-frontend:
	@echo ""
	@echo "⚠️  This will:"
	@echo "   1. Copy frontend submodule files into a regular 'frontend/' directory"
	@echo "   2. Remove the frontend git submodule configuration"
	@echo "   3. Remove the contracts git submodule"
	@echo "   4. Remove .gitmodules file"
	@echo ""
	@echo "   After ejecting, frontend changes can be committed directly"
	@echo "   with your backend changes. This cannot be undone."
	@echo ""
	@read -p "   Continue? [Y/n] " confirm; \
	if [ "$$confirm" != "Y" ] && [ "$$confirm" != "y" ] && [ -n "$$confirm" ]; then \
		echo "   Cancelled."; \
		exit 1; \
	fi
	@echo ""
	@echo "==> Ejecting frontend submodule..."
	@FRONTEND_TMP=$$(mktemp -d); \
	cp -r frontend/. "$$FRONTEND_TMP/"; \
	git submodule deinit -f frontend; \
	git rm -f frontend; \
	rm -rf .git/modules/frontend; \
	mkdir -p frontend; \
	cp -r "$$FRONTEND_TMP/." frontend/; \
	rm -rf "$$FRONTEND_TMP"; \
	rm -rf frontend/.git; \
	echo "   ✅ Frontend ejected to regular directory"
	@echo "==> Removing contracts submodule..."
	@if git config --file .gitmodules submodule.contracts.url > /dev/null 2>&1; then \
		git submodule deinit -f contracts; \
		git rm -f contracts; \
		rm -rf .git/modules/contracts; \
		echo "   ✅ Contracts submodule removed"; \
	else \
		echo "   ℹ️  No contracts submodule found"; \
	fi
	@if [ -f .gitmodules ] && [ ! -s .gitmodules ]; then \
		git rm -f .gitmodules; \
		echo "   ✅ Empty .gitmodules removed"; \
	fi
	@echo ""
	@echo "✅ Eject complete! Frontend files are now regular tracked files."
	@echo "   Run 'git add . && git commit' to save the changes."
