.PHONY: dev dev-backend dev-frontend test install build

dev:
	docker compose -f docker-compose.dev.yml up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest -v

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	cd agent-skill && pip install -e .

build:
	cd frontend && npm run build
