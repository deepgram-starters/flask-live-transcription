.PHONY: help init dev build start update clean status

help:
	@echo "Available commands:"
	@echo "  make init     - Initialize submodules and install dependencies"
	@echo "  make dev      - Start development servers (Flask + Vite HMR)"
	@echo "  make build    - Build frontend for production"
	@echo "  make start    - Start production server"
	@echo "  make update   - Update submodules to latest"
	@echo "  make clean    - Remove venv, node_modules and build artifacts"
	@echo "  make status   - Show git and submodule status"

init:
	@echo "Initializing submodules..."
	git submodule update --init --recursive
	@echo "Creating Python virtual environment..."
	python3 -m venv venv
	@echo "Installing Python dependencies..."
	./venv/bin/pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pnpm install
	@echo "Setup complete! Run 'make dev' to start development."

dev:
	@echo "Starting development server..."
	@export NODE_ENV=development && ./venv/bin/python app.py

build:
	@echo "Building frontend for production..."
	cd frontend && pnpm build
	@echo "Build complete!"

start:
	@echo "Starting production server..."
	@export NODE_ENV=production && ./venv/bin/python app.py

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
