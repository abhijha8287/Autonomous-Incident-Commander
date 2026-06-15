.PHONY: dev backend frontend install install-backend install-frontend seed

dev:
	@echo "Starting Autonomous Incident Commander..."
	@start cmd /k "cd backend && ..\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000"
	@cd frontend && npm run dev

backend:
	python -m uvicorn backend.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

install: install-backend install-frontend

install-backend:
	python -m venv venv
	venv\Scripts\pip install -r requirements.txt

install-frontend:
	cd frontend && npm install
