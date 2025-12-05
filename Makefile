.PHONY: install up demo test deploy-render clean

install:
	pip install -r requirements.txt

up:
	docker-compose up -d
	sleep 10  # Wait for DB
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

demo:
	python examples/adult_demo.py  # Runs detection + report

test:
	pytest tests/

deploy-render:
	# Assumes Render.com CLI installed; pushes to your free instance
	render deploy --service your-service-id  # Or manual via dashboard

clean:
	docker-compose down -v
	pip freeze | xargs pip uninstall -y