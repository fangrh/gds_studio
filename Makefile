.PHONY: dev dev-backend dev-frontend test install build deploy-staging deploy-prod

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

deploy-staging:
	helm upgrade --install gds-collab-staging ./helm/gds-collab \
		-f ./helm/gds-collab/values.yaml \
		-f ./helm/gds-collab/values-staging.yaml \
		--namespace staging --create-namespace

deploy-prod:
	helm upgrade --install gds-collab-prod ./helm/gds-collab \
		-f ./helm/gds-collab/values.yaml \
		-f ./helm/gds-collab/values-production.yaml \
		--namespace production --create-namespace
