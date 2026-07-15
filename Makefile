.DEFAULT_GOAL := help
SHELL         := /bin/bash

COMPOSE       := docker compose
VENV          := .venv
UV            := uv
PYTHON        := $(VENV)/bin/python

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD  := \033[1m
RESET := \033[0m
GREEN := \033[32m
CYAN  := \033[36m

# ── Help ──────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@printf "$(BOLD)Agentic Operational Intelligence Platform$(RESET)\n\n"
	@printf "$(CYAN)Setup$(RESET)\n"
	@printf "  %-28s %s\n" "make install"           "Create .venv and install all dependency groups"
	@printf "  %-28s %s\n" "make install-streaming" "Install streaming extras (confluent-kafka, fastavro …)"
	@printf "  %-28s %s\n" "make env"               "Copy .env.example → .env (edit afterwards)"
	@printf "\n$(CYAN)Docker stack$(RESET)\n"
	@printf "  %-28s %s\n" "make up"                "Start the full stack (build images first if needed)"
	@printf "  %-28s %s\n" "make down"              "Stop and remove all containers"
	@printf "  %-28s %s\n" "make restart"           "Stop then start the full stack"
	@printf "  %-28s %s\n" "make rebuild"           "Force-rebuild images and restart"
	@printf "  %-28s %s\n" "make ps"                "Show container status"
	@printf "  %-28s %s\n" "make logs"              "Tail logs for all services (Ctrl-C to exit)"
	@printf "  %-28s %s\n" "make logs-app"          "Tail app service logs"
	@printf "  %-28s %s\n" "make logs-conduktor"    "Tail Conduktor console logs"
	@printf "\n$(CYAN)Kafka / Schemas$(RESET)\n"
	@printf "  %-28s %s\n" "make register-schemas"  "Register all Avro schemas into Schema Registry"
	@printf "  %-28s %s\n" "make register-connectors" "Register JDBC Sink connectors for PDM tables"
	@printf "  %-28s %s\n" "make register-cdc"      "Register the CDC (Debezium) connector"
	@printf "  %-28s %s\n" "make produce"           "Start the synthetic producer service (all topics, 0.5 s interval)"
	@printf "  %-28s %s\n" "make produce-stop"      "Stop the producer service"
	@printf "  %-28s %s\n" "make logs-producer"     "Tail producer logs"
	@printf "  %-28s %s\n" "make topics"            "List all Kafka topics"
	@printf "\n$(CYAN)App$(RESET)\n"
	@printf "  %-28s %s\n" "make dev"               "Run the FastAPI app locally with hot-reload"
	@printf "  %-28s %s\n" "make mcp"               "Run the MCP server locally"
	@printf "\n$(CYAN)Quality$(RESET)\n"
	@printf "  %-28s %s\n" "make test"              "Run the test suite"
	@printf "  %-28s %s\n" "make test-cov"          "Run tests with coverage report"
	@printf "  %-28s %s\n" "make lint"              "Ruff lint check"
	@printf "  %-28s %s\n" "make fmt"               "Ruff auto-format"
	@printf "  %-28s %s\n" "make typecheck"         "Pyright type check"
	@printf "\n$(CYAN)Conduktor$(RESET)\n"
	@printf "  %-28s %s\n" "make conduktor-restart" "Restart the Conduktor console container"
	@printf "  %-28s %s\n" "make conduktor-health"  "Check Conduktor health endpoint"
	@printf "\n$(CYAN)Lakehouse (Spark + Iceberg + dbt)$(RESET)\n"
	@printf "  %-28s %s\n" "make lake-up"           "Start MinIO, Iceberg REST catalog, Spark cluster"
	@printf "  %-28s %s\n" "make lake-stream"       "Start Spark CDC streaming (landing layer)"
	@printf "  %-28s %s\n" "make lake-down"         "Stop the lakehouse stack"
	@printf "  %-28s %s\n" "make dbt-run"           "Run all dbt layers (bronze → silver → gold)"
	@printf "  %-28s %s\n" "make dbt-run LAYER=<l>" "Run a single dbt layer (bronze|silver|gold)"
	@printf "  %-28s %s\n" "make dbt-test"          "Run dbt tests"
	@printf "  %-28s %s\n" "make dbt-deps"          "Install dbt packages"
	@printf "  %-28s %s\n" "make minio-ui"          "Print MinIO console URL"
	@printf "\n$(CYAN)Airflow$(RESET)\n"
	@printf "  %-28s %s\n" "make airflow-up"        "Build and start Airflow (webserver + scheduler)"
	@printf "  %-28s %s\n" "make airflow-down"      "Stop Airflow services"
	@printf "  %-28s %s\n" "make airflow-trigger"   "Trigger the dbt pipeline DAG manually"
	@printf "  %-28s %s\n" "make logs-airflow"      "Tail Airflow scheduler logs"
	@printf "\n$(CYAN)Analytics (Feature Store + Semantic Layer + Vector Index)$(RESET)\n"
	@printf "  %-28s %s\n" "make analytics-up"      "Start Qdrant + Feast feature server"
	@printf "  %-28s %s\n" "make analytics-materialize" "Materialize features to Redis (Feast)"
	@printf "  %-28s %s\n" "make analytics-index"   "Build Qdrant vector indexes from gold layer"
	@printf "  %-28s %s\n" "make analytics-index-dry" "Dry-run: print index payloads without upserting"
	@printf "  %-28s %s\n" "make analytics-down"    "Stop Qdrant + Feast"
	@printf "\n$(CYAN)Flink$(RESET)\n"
	@printf "  %-28s %s\n" "make flink-jar"         "Build connector fat JAR with Maven (required before flink-up)"
	@printf "  %-28s %s\n" "make flink-up"          "Build and start JobManager + TaskManager"
	@printf "  %-28s %s\n" "make flink-run JOB=<name>" "Submit a single pipeline to the cluster"
	@printf "  %-28s %s\n" "make flink-submit"      "Submit all 14 pipelines to the cluster"
	@printf "  %-28s %s\n" "make flink-cancel JOB_ID=<id>" "Cancel a running job by Flink job ID"
	@printf "  %-28s %s\n" "make flink-down"        "Stop Flink cluster"
	@printf "  %-28s %s\n" "make flink-jobs"        "List running Flink jobs via REST API"
	@printf "  %-28s %s\n" "make flink-pipelines"   "List available pipeline names"
	@printf "  %-28s %s\n" "make logs-flink-jm"     "Tail JobManager logs"
	@printf "  %-28s %s\n" "make logs-flink-tm"     "Tail TaskManager logs"

# ── Setup ─────────────────────────────────────────────────────────────────────
.PHONY: install
install:
	$(UV) sync --all-groups

.PHONY: install-streaming
install-streaming:
	$(UV) sync --group streaming

.PHONY: env
env:
	@if [ -f .env ]; then \
		echo ".env already exists — skipping"; \
	else \
		cp config/source_connections.example.yaml .env.yaml 2>/dev/null || true; \
		printf "ANTHROPIC_API_KEY=\n\nAOIP_KPI_SOURCE=aurora_mysql\nAOIP_AURORA_MYSQL__HOST=mysql\nAOIP_AURORA_MYSQL__PORT=3306\nAOIP_AURORA_MYSQL__DATABASE=retail_ops\nAOIP_AURORA_MYSQL__USERNAME=connect_user\nAURORA_PASSWORD=connect_pass\nAOIP_REDIS__URL=redis://redis:6379/0\nKAFKA_BROKERS=broker1:29092,broker2:29092,broker3:29092\nSCHEMA_REGISTRY_URL=http://schema-registry:8081\n" > .env; \
		echo "Created .env — set ANTHROPIC_API_KEY before running make up"; \
	fi

# ── Docker stack ──────────────────────────────────────────────────────────────
.PHONY: up
up: _require-env
	$(COMPOSE) up -d

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: restart
restart: down up

.PHONY: rebuild
rebuild: _require-env
	$(COMPOSE) build --no-cache
	$(COMPOSE) --profile producer up -d

.PHONY: ps
ps:
	$(COMPOSE) ps

.PHONY: logs
logs:
	$(COMPOSE) logs -f

.PHONY: logs-app
logs-app:
	$(COMPOSE) logs -f app

.PHONY: logs-conduktor
logs-conduktor:
	$(COMPOSE) logs -f conduktor-console

# ── Kafka / Schemas ───────────────────────────────────────────────────────────
.PHONY: register-schemas
register-schemas:
	$(PYTHON) container/scripts/register_schemas.py

.PHONY: register-connectors
register-connectors:
	$(PYTHON) container/scripts/register_connectors.py

.PHONY: register-cdc
register-cdc:
	$(PYTHON) container/scripts/register_cdc_connector.py

.PHONY: produce
produce: _require-env
	$(COMPOSE) --profile producer up -d producer

.PHONY: produce-stop
produce-stop:
	$(COMPOSE) --profile producer stop producer

.PHONY: logs-producer
logs-producer:
	$(COMPOSE) --profile producer logs -f producer

.PHONY: topics
topics:
	docker exec $$(docker ps -qf name=broker1) \
		kafka-topics --bootstrap-server localhost:9092 --list \
		| grep -v '^__'

# ── App ───────────────────────────────────────────────────────────────────────
.PHONY: dev
dev:
	$(PYTHON) -m uvicorn ai_system.gateway.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: mcp
mcp:
	$(PYTHON) services/mcp_server.py

# ── Quality ───────────────────────────────────────────────────────────────────
.PHONY: test
test:
	$(VENV)/bin/pytest

.PHONY: test-cov
test-cov:
	$(VENV)/bin/pytest --cov --cov-report=term-missing

.PHONY: lint
lint:
	$(VENV)/bin/ruff check .

.PHONY: fmt
fmt:
	$(VENV)/bin/ruff format .

.PHONY: typecheck
typecheck:
	$(VENV)/bin/pyright

# ── Flink cluster ─────────────────────────────────────────────────────────────
FLINK_PIPELINES := appointment article crewtime customer employee \
                   inventory kronos_hours sales_order sales_order_receipt \
                   site vehicle vehicle_inspection voucher work_order

.PHONY: flink-jar
flink-jar:
	mvn package -f container/flink/pom.xml -q
	@echo "JAR built: $$(ls container/flink/target/kda-dependencies-*.jar)"

.PHONY: flink-up
flink-up: flink-jar _require-env
	$(COMPOSE) up -d flink-jobmanager flink-taskmanager

.PHONY: flink-run
flink-run: _require-env
	@if [ -z "$(JOB)" ]; then \
		echo "$(BOLD)Usage$(RESET): make flink-run JOB=<pipeline>"; \
		echo "Available: $(FLINK_PIPELINES)"; \
		exit 1; \
	fi
	$(COMPOSE) run --rm -e JOB_NAME=$(JOB) flink-runner

.PHONY: flink-submit
flink-submit: _require-env
	@echo "Submitting all $(words $(FLINK_PIPELINES)) pipelines..."
	@for job in $(FLINK_PIPELINES); do \
		echo "  --> $$job"; \
		$(COMPOSE) run --rm -e JOB_NAME=$$job flink-runner || echo "  [WARN] $$job submission failed"; \
	done
	@echo "All pipelines submitted. Check http://localhost:8082 for status."

.PHONY: flink-cancel
flink-cancel:
	@if [ -z "$(JOB_ID)" ]; then \
		echo "$(BOLD)Usage$(RESET): make flink-cancel JOB_ID=<flink-job-id>"; \
		echo "Find job IDs with: make flink-jobs"; \
		exit 1; \
	fi
	curl -sf --noproxy '*' -X PATCH \
		"http://localhost:8082/jobs/$(JOB_ID)?mode=cancel" | python3 -m json.tool

.PHONY: flink-down
flink-down:
	$(COMPOSE) stop flink-jobmanager flink-taskmanager 2>/dev/null || true

.PHONY: flink-jobs
flink-jobs:
	curl -sf --noproxy '*' http://localhost:8082/jobs 2>&1 | python3 -m json.tool

.PHONY: flink-pipelines
flink-pipelines:
	@echo "Available pipelines:"
	@for job in $(FLINK_PIPELINES); do echo "  $$job"; done

.PHONY: logs-flink-jm
logs-flink-jm:
	$(COMPOSE) logs -f flink-jobmanager

.PHONY: logs-flink-tm
logs-flink-tm:
	$(COMPOSE) logs -f flink-taskmanager

# ── Conduktor helpers ─────────────────────────────────────────────────────────
.PHONY: conduktor-restart
conduktor-restart:
	docker restart $$(docker ps -qf name=conduktor-console)

.PHONY: conduktor-health
conduktor-health:
	curl -sf --max-time 5 --noproxy '*' http://localhost:8080/api/health \
		&& echo "$(GREEN)healthy$(RESET)" || echo "unhealthy"

# ── Lakehouse (Spark + Iceberg + dbt) ────────────────────────────────────────
.PHONY: lake-up
lake-up: _require-env
	$(COMPOSE) up -d minio minio-init iceberg-rest spark-master spark-worker spark-thriftserver
	@echo "MinIO console : http://localhost:9001  (minioadmin / minioadmin)"
	@echo "Iceberg REST  : http://localhost:8181"
	@echo "Spark Master  : http://localhost:4040"
	@echo "Thrift JDBC   : jdbc:hive2://localhost:10000"

.PHONY: lake-stream
lake-stream: _require-env
	$(COMPOSE) up -d spark-cdc-streaming

.PHONY: lake-down
lake-down:
	$(COMPOSE) stop spark-cdc-streaming spark-thriftserver spark-worker spark-master iceberg-rest minio 2>/dev/null || true

.PHONY: dbt-run
dbt-run: _require-env
	@if [ -z "$(LAYER)" ]; then \
		$(COMPOSE) run --rm dbt-runner dbt run \
			--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt; \
	else \
		$(COMPOSE) run --rm dbt-runner dbt run \
			--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt \
			--select $(LAYER); \
	fi

.PHONY: dbt-test
dbt-test: _require-env
	$(COMPOSE) run --rm dbt-runner dbt test \
		--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt

.PHONY: dbt-deps
dbt-deps: _require-env
	$(COMPOSE) run --rm dbt-runner dbt deps \
		--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt

.PHONY: minio-ui
minio-ui:
	@echo "MinIO console: http://localhost:9001  (user: minioadmin / minioadmin)"

# ── Airflow ───────────────────────────────────────────────────────────────────
.PHONY: airflow-up
airflow-up: _require-env
	$(COMPOSE) up -d airflow-postgres
	$(COMPOSE) run --rm airflow-init
	$(COMPOSE) up -d airflow-webserver airflow-scheduler
	@echo "Airflow UI: http://localhost:8085  (admin / admin)"

.PHONY: airflow-down
airflow-down:
	$(COMPOSE) stop airflow-webserver airflow-scheduler airflow-postgres 2>/dev/null || true

.PHONY: airflow-trigger
airflow-trigger:
	$(COMPOSE) exec airflow-scheduler \
		airflow dags trigger dbt_lakehouse_pipeline

.PHONY: logs-airflow
logs-airflow:
	$(COMPOSE) logs -f airflow-scheduler airflow-webserver

# ── Analytics layer (Feature Store + Semantic Layer + Vector Index) ───────────
.PHONY: analytics-up
analytics-up: _require-env
	$(COMPOSE) up -d qdrant feast-server
	@echo "Qdrant dashboard : http://localhost:6333/dashboard"
	@echo "Feast server     : http://localhost:6566/get-online-features"

.PHONY: analytics-materialize
analytics-materialize: _require-env
	$(COMPOSE) run --rm -v $(PWD)/data_platform/feature_store:/feature_store \
		feast-server bash -c \
		"pip install -q feast[spark,redis]==0.40.0 && \
		 cd /feature_store && feast apply && \
		 python materialize.py"

.PHONY: analytics-index
analytics-index: _require-env
	$(COMPOSE) up --build -d vector-indexer
	@echo "Indexing started — tail logs with: $(COMPOSE) logs -f vector-indexer"

.PHONY: analytics-index-dry
analytics-index-dry:
	$(COMPOSE) run --rm vector-indexer bash -c \
		'pip install -q qdrant-client==1.9.0 sentence-transformers==2.7.0 pyhive[hive]==0.7.0 thrift==0.20.0 && \
		 python /app/indexer.py --dry-run'

.PHONY: analytics-down
analytics-down:
	$(COMPOSE) stop qdrant feast-server vector-indexer 2>/dev/null || true

# ── Internal guards ───────────────────────────────────────────────────────────
.PHONY: _require-env
_require-env:
	@if [ ! -f .env ]; then \
		echo "$(BOLD)ERROR$(RESET): .env not found. Run 'make env' and fill in ANTHROPIC_API_KEY."; \
		exit 1; \
	fi
