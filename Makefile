.DEFAULT_GOAL := help
SHELL         := /bin/bash

COMPOSE_FILE  := container/docker-compose.yaml
COMPOSE       := docker compose -f $(COMPOSE_FILE)
VENV          := .venv
UV            := uv
PYTHON        := $(VENV)/bin/python

# Local host endpoints for helper scripts run outside containers.
LOCAL_CONNECT_URL         := http://localhost:8083
LOCAL_SCHEMA_REGISTRY_URL := http://localhost:8081
LOCAL_KAFKA_BROKERS       := localhost:9092,localhost:9093,localhost:9094
LOCAL_MYSQL_URL           := jdbc:mysql://mysql:3306/retail_ops?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&characterEncoding=UTF-8&sessionVariables=sql_mode=''
DDL_DIR                   := data_platform/ddl

# Core local development services (fast startup, excludes heavy optional stacks).
CORE_SERVICES := app redis mysql neo4j broker1 broker2 broker3 schema-registry kafka-connect

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD  := \033[1m
RESET := \033[0m
GREEN := \033[32m
CYAN  := \033[36m

# ── Help ──────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@printf "$(BOLD)Agentic Operational Intelligence Platform (local development)$(RESET)\n\n"
	@printf "$(CYAN)Platform Setup$(RESET)\n"
	@printf "  %-28s %s\n" "make install"           "Create .venv and install all dependency groups"
	@printf "  %-28s %s\n" "make install-streaming" "Install streaming extras (confluent-kafka, fastavro …)"
	@printf "  %-28s %s\n" "make env"               "Copy .env.example → .env (edit afterwards)"
	@printf "\n$(CYAN)Container Stack$(RESET)\n"
	@printf "  %-28s %s\n" "make up"                "Start core local services only (app + kafka + mysql + redis)"
	@printf "  %-28s %s\n" "make up-full"           "Start full stack (includes Airflow/Flink/lakehouse/analytics)"
	@printf "  %-28s %s\n" "make down"              "Stop and remove all containers"
	@printf "  %-28s %s\n" "make restart"           "Stop then start the core local stack"
	@printf "  %-28s %s\n" "make restart-full"      "Stop then start the full local stack"
	@printf "  %-28s %s\n" "make rebuild"           "Force-rebuild images and restart"
	@printf "  %-28s %s\n" "make ps"                "Show container status"
	@printf "  %-28s %s\n" "make logs"              "Tail logs for all services (Ctrl-C to exit)"
	@printf "\n$(CYAN)AI Systems (Gateway)$(RESET)\n"
	@printf "  %-28s %s\n" "make dev"               "Run the FastAPI app locally with hot-reload"
	@printf "  %-28s %s\n" "make mcp"               "Run the MCP server locally"
	@printf "  %-28s %s\n" "make webui-up"          "Start Streamlit WebUI (Docker)"
	@printf "  %-28s %s\n" "make webui-down"        "Stop Streamlit WebUI"
	@printf "  %-28s %s\n" "make webui-open"        "Print Streamlit WebUI URL"
	@printf "\n$(CYAN)Data Platform (Kafka + DDL + Producer)$(RESET)\n"
	@printf "  %-28s %s\n" "make register-schemas"  "Register all Avro schemas into Schema Registry"
	@printf "  %-28s %s\n" "make register-connectors" "Register JDBC Sink connectors for PDM tables"
	@printf "  %-28s %s\n" "make register-cdc"      "Register the CDC (Debezium) connector"
	@printf "  %-28s %s\n" "make ddl-apply"         "Apply all SQL files under data_platform/ddl to MySQL"
	@printf "  %-28s %s\n" "make ddl-status"        "Show table count in retail_ops"
	@printf "  %-28s %s\n" "make produce"           "Start the synthetic producer service (all topics, 0.5 s interval)"
	@printf "  %-28s %s\n" "make produce-stop"      "Stop the producer service"
	@printf "  %-28s %s\n" "make logs-producer"     "Tail producer logs"
	@printf "  %-28s %s\n" "make topics"            "List all Kafka topics"
	@printf "\n$(CYAN)Data Platform (Flink Streaming)$(RESET)\n"
	@printf "  %-28s %s\n" "make flink-jar"         "Build connector fat JAR with Maven (required before flink-up)"
	@printf "  %-28s %s\n" "make flink-up"          "Build and start JobManager + TaskManager"
	@printf "  %-28s %s\n" "make flink-refresh"     "Force-recreate Flink services to pick up compose/env changes"
	@printf "  %-28s %s\n" "make flink-run JOB=<name>" "Submit a single pipeline to the cluster"
	@printf "  %-28s %s\n" "make flink-submit"      "Submit all 14 pipelines to the cluster"
	@printf "  %-28s %s\n" "make flink-cancel JOB_ID=<id>" "Cancel a running job by Flink job ID"
	@printf "  %-28s %s\n" "make flink-down"        "Stop Flink cluster"
	@printf "  %-28s %s\n" "make flink-jobs"        "List running Flink jobs via REST API"
	@printf "  %-28s %s\n" "make flink-pipelines"   "List available pipeline names"
	@printf "  %-28s %s\n" "make flink-open"        "Open Flink dashboard over HTTP (127.0.0.1)"
	@printf "  %-28s %s\n" "make flink-open-localhost" "Open localhost dashboard and warn on HTTPS upgrade"
	@printf "\n$(CYAN)Lakehouse (Spark + Iceberg + dbt)$(RESET)\n"
	@printf "  %-28s %s\n" "make lake-up"           "Start lakehouse services (MinIO + Iceberg + Spark)"
	@printf "  %-28s %s\n" "make lake-stream"       "Start Spark CDC streaming worker"
	@printf "  %-28s %s\n" "make lake-down"         "Stop lakehouse services"
	@printf "  %-28s %s\n" "make dbt-deps"          "Install dbt packages in the dbt runner"
	@printf "  %-28s %s\n" "make dbt-run [LAYER=...]" "Run dbt models (optionally select layer)"
	@printf "  %-28s %s\n" "make dbt-test"          "Run dbt tests"
	@printf "  %-28s %s\n" "make minio-ui"          "Print MinIO UI endpoint and credentials"
	@printf "\n$(CYAN)Orchestration (Airflow)$(RESET)\n"
	@printf "  %-28s %s\n" "make airflow-up"        "Start Airflow and initialize metadata DB"
	@printf "  %-28s %s\n" "make airflow-down"      "Stop Airflow services"
	@printf "  %-28s %s\n" "make airflow-open"      "Open Airflow login over HTTP (avoids HTTPS-first browser upgrades)"
	@printf "  %-28s %s\n" "make airflow-open-localhost" "Open localhost URL and warn if browser upgrades to HTTPS"
	@printf "  %-28s %s\n" "make airflow-trigger"   "Trigger dbt_lakehouse_pipeline DAG"
	@printf "\n$(CYAN)Analytics (Feature + Vector)$(RESET)\n"
	@printf "  %-28s %s\n" "make analytics-up"      "Start Qdrant and Feast services"
	@printf "  %-28s %s\n" "make analytics-materialize" "Run Feast apply + materialization"
	@printf "  %-28s %s\n" "make analytics-index"   "Build/start vector indexer"
	@printf "  %-28s %s\n" "make analytics-index-dry" "Run vector indexing in dry-run mode"
	@printf "  %-28s %s\n" "make analytics-down"    "Stop analytics services"
	@printf "\n$(CYAN)Graph (Neo4j Relationships)$(RESET)\n"
	@printf "  %-28s %s\n" "make graph-up"          "Start Neo4j graph database"
	@printf "  %-28s %s\n" "make graph-sync"        "Sync ODS relationships + gold KPI snapshots to Neo4j"
	@printf "  %-28s %s\n" "make graph-check"       "Show Neo4j relationship counts by type"
	@printf "  %-28s %s\n" "make graph-down"        "Stop Neo4j graph database"
	@printf "\n$(CYAN)Observability / Logs$(RESET)\n"
	@printf "  %-28s %s\n" "make logs-app"          "Tail app service logs"
	@printf "  %-28s %s\n" "make logs-flink-jm"     "Tail JobManager logs"
	@printf "  %-28s %s\n" "make logs-flink-tm"     "Tail TaskManager logs"
	@printf "  %-28s %s\n" "make logs-airflow"      "Tail Airflow scheduler and webserver logs"
	@printf "  %-28s %s\n" "make logs-conduktor"    "Tail Conduktor console logs"
	@printf "  %-28s %s\n" "make conduktor-health"  "Check Conduktor health endpoint"
	@printf "  %-28s %s\n" "make conduktor-restart" "Restart Conduktor console container"
	@printf "\n$(CYAN)Quality$(RESET)\n"
	@printf "  %-28s %s\n" "make test"              "Run the test suite"
	@printf "  %-28s %s\n" "make test-cov"          "Run tests with coverage report"
	@printf "  %-28s %s\n" "make lint"              "Ruff lint check"
	@printf "  %-28s %s\n" "make fmt"               "Ruff auto-format"
	@printf "  %-28s %s\n" "make typecheck"         "Pyright type check"
	@printf "  %-28s %s\n" "make clean-producer"    "Remove producer __pycache__/pyc artifacts"
	@printf "\n$(CYAN)Note$(RESET)\n"
	@printf "  %-28s %s\n" "make help-full"         "Show all available targets"

.PHONY: help-full
help-full:
	@$(MAKE) -prRn : 2>/dev/null | awk -F':' '/^[a-zA-Z0-9_.-]+:$$/ {print $$1}' | sort -u

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
.PHONY: _ensure-flink-jar
_ensure-flink-jar:
	@if ! ls container/flink/target/kda-dependencies-*.jar >/dev/null 2>&1; then \
		echo "Flink connector JAR not found; building it now..."; \
		$(MAKE) flink-jar; \
	fi

.PHONY: up
up: _require-env
	$(COMPOSE) up -d $(CORE_SERVICES)

.PHONY: up-full
up-full: _require-env _ensure-flink-jar
	@echo "[1/6] Starting core services..."
	@$(MAKE) up
	@echo "[2/6] Bootstrapping Kafka/Schema/Conduktor helpers..."
	$(COMPOSE) up -d kafka-init schema-registry-init connect-init cdc-init autoheal conduktor-console
	@echo "[3/6] Starting Flink cluster..."
	@$(MAKE) flink-up
	@echo "[4/6] Starting lakehouse services..."
	@$(MAKE) lake-up
	@echo "[5/6] Starting Airflow services..."
	@$(MAKE) airflow-up
	@echo "[6/6] Starting analytics services..."
	@$(MAKE) analytics-up
	@echo "Full local stack started."

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: restart
restart: down up

.PHONY: restart-full
restart-full: down up-full

.PHONY: rebuild
rebuild: _require-env _ensure-flink-jar
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

# ── Data Platform (Kafka / Schemas / DDL / Producer) ─────────────────────────
.PHONY: register-schemas
register-schemas:
	SCHEMA_REGISTRY_URL="$(LOCAL_SCHEMA_REGISTRY_URL)" \
	SCHEMAS_DIR="data_platform/schema" \
	$(PYTHON) container/scripts/register_schemas.py

.PHONY: register-connectors
register-connectors:
	CONNECT_URL="$(LOCAL_CONNECT_URL)" \
	SCHEMA_REGISTRY_URL="$(LOCAL_SCHEMA_REGISTRY_URL)" \
	MYSQL_URL="$(LOCAL_MYSQL_URL)" \
	$(PYTHON) container/scripts/register_connectors.py

.PHONY: register-cdc
register-cdc:
	CONNECT_URL="$(LOCAL_CONNECT_URL)" \
	MYSQL_HOST=localhost \
	KAFKA_BOOTSTRAP_SERVERS="$(LOCAL_KAFKA_BROKERS)" \
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

.PHONY: ddl-apply
ddl-apply:
	@echo "Applying DDL files from $(DDL_DIR) to MySQL..."
	@$(COMPOSE) up -d mysql >/dev/null
	@echo "Waiting for MySQL readiness..."
	@for i in $$(seq 1 30); do \
		if $(COMPOSE) exec -T mysql mysqladmin ping -h localhost -uconnect_user -pconnect_pass --silent >/dev/null 2>&1; then \
			break; \
		fi; \
		sleep 2; \
		if [ $$i -eq 30 ]; then \
			echo "MySQL did not become ready in time."; \
			exit 1; \
		fi; \
	done
	@for ddl in $$(ls $(DDL_DIR)/*.sql | sort); do \
		echo "  --> $$ddl"; \
		$(COMPOSE) exec -T mysql mysql -uroot -proot_pass < "$$ddl"; \
	done
	@echo "DDL apply complete."

.PHONY: ddl-status
ddl-status:
	@$(COMPOSE) up -d mysql >/dev/null
	@for i in $$(seq 1 30); do \
		if $(COMPOSE) exec -T mysql mysqladmin ping -h localhost -uconnect_user -pconnect_pass --silent >/dev/null 2>&1; then \
			break; \
		fi; \
		sleep 2; \
		if [ $$i -eq 30 ]; then \
			echo "MySQL did not become ready in time."; \
			exit 1; \
		fi; \
	done
	@echo "Current table count in retail_ops:"
	@$(COMPOSE) exec -T mysql mysql -uroot -proot_pass -e "SELECT table_schema, COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema = 'retail_ops' GROUP BY table_schema;"

# ── AI Systems (Gateway) ──────────────────────────────────────────────────────
.PHONY: dev
dev:
	$(PYTHON) -m uvicorn ai_systems.gateway.api.app:app --reload --host 0.0.0.0 --port 8000

.PHONY: mcp
mcp:
	$(PYTHON) ai_systems/gateway/mcp/server.py

.PHONY: webui-up
webui-up:
	$(COMPOSE) up -d webui

.PHONY: webui-down
webui-down:
	$(COMPOSE) stop webui

.PHONY: webui-open
webui-open:
	@echo "Streamlit WebUI: http://localhost:8501"

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

.PHONY: clean-producer
clean-producer:
	find data_platform/producer -type d -name '__pycache__' -prune -exec rm -rf {} +
	find data_platform/producer -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

# ── Data Platform (Flink Streaming) ───────────────────────────────────────────
FLINK_PIPELINES := appointment article crewtime customer employee \
                   inventory kronos_hours sales_order sales_order_receipt \
                   site vehicle vehicle_inspection voucher work_order

.PHONY: _flink-up-services
_flink-up-services:
	@$(COMPOSE) up -d flink-jobmanager flink-taskmanager

.PHONY: _flink-wait-jobmanager
_flink-wait-jobmanager:
	@echo "Waiting for Flink JobManager and TaskManager slots to become ready..."
	@for i in $$(seq 1 45); do \
		if curl -sf --noproxy '*' http://localhost:8082/overview | python3 -c 'import json,sys; o=json.load(sys.stdin); ok=(o.get("taskmanagers",0) >= 1 and o.get("slots-total",0) >= 1 and o.get("slots-available",0) >= 1); raise SystemExit(0 if ok else 1)' >/dev/null 2>&1; then \
			echo "Flink cluster is ready (taskmanagers and slots available)."; \
			exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "Flink cluster did not become ready in time."; \
	exit 1

.PHONY: _flink-submit-job
_flink-submit-job:
	@if [ -z "$(JOB)" ]; then \
		echo "$(BOLD)Usage$(RESET): make _flink-submit-job JOB=<pipeline>"; \
		exit 1; \
	fi
	@$(COMPOSE) exec -T -e JOB_NAME=$(JOB) flink-jobmanager bash -lc '\
		set -e; \
		JOB_SCRIPT="/opt/flink/usrlib/flink_job/$$JOB_NAME/main.py"; \
		if [ ! -f "$$JOB_SCRIPT" ]; then \
			echo "ERROR: Pipeline script not found: $$JOB_SCRIPT"; \
			exit 1; \
		fi; \
		echo "==> Submitting pipeline: $$JOB_NAME"; \
		flink run -d -py "$$JOB_SCRIPT" -pyfs /opt/flink/usrlib -pyexec python3 \
	'

.PHONY: flink-jar
flink-jar:
	mvn package -f container/flink/pom.xml -q
	@echo "JAR built: $$(ls container/flink/target/kda-dependencies-*.jar)"

.PHONY: flink-up
flink-up: flink-jar _require-env
	@$(MAKE) --no-print-directory _flink-up-services
	@$(MAKE) --no-print-directory _flink-wait-jobmanager

.PHONY: flink-refresh
flink-refresh: _require-env
	$(COMPOSE) up -d --force-recreate flink-jobmanager flink-taskmanager
	@$(MAKE) --no-print-directory _flink-wait-jobmanager

.PHONY: flink-run
flink-run: _require-env _flink-up-services _flink-wait-jobmanager
	@if [ -z "$(JOB)" ]; then \
		echo "$(BOLD)Usage$(RESET): make flink-run JOB=<pipeline>"; \
		echo "Available: $(FLINK_PIPELINES)"; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory _flink-submit-job JOB=$(JOB)

.PHONY: flink-submit
flink-submit: _require-env _flink-up-services _flink-wait-jobmanager
	@echo "Submitting all $(words $(FLINK_PIPELINES)) pipelines..."
	@for job in $(FLINK_PIPELINES); do \
		echo "  --> $$job"; \
		$(MAKE) --no-print-directory _flink-submit-job JOB=$$job || echo "  [WARN] $$job submission failed"; \
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

.PHONY: flink-open
flink-open:
	@echo "Opening Flink Dashboard: http://127.0.0.1:8082/"
	@open "http://127.0.0.1:8082/"

.PHONY: flink-open-localhost
flink-open-localhost:
	@if ! curl -k -sf --max-time 3 https://localhost:8082/ >/dev/null 2>&1; then \
		echo "Warning: https://localhost:8082 is not served by Flink (HTTP only)."; \
		echo "If your browser upgrades localhost to HTTPS, disable HTTPS-first for localhost."; \
	fi
	@echo "Opening Flink Dashboard: http://localhost:8082/"
	@open "http://localhost:8082/"

.PHONY: logs-flink-jm
logs-flink-jm:
	$(COMPOSE) logs -f flink-jobmanager

.PHONY: logs-flink-tm
logs-flink-tm:
	$(COMPOSE) logs -f flink-taskmanager

# ── Observability (Conduktor helpers) ─────────────────────────────────────────
.PHONY: conduktor-restart
conduktor-restart:
	docker restart $$(docker ps -qf name=conduktor-console)

.PHONY: conduktor-health
conduktor-health:
	curl -sf --max-time 5 --noproxy '*' http://localhost:8086/api/health \
		&& echo "$(GREEN)healthy$(RESET)" || echo "unhealthy"

# ── Data Platform (Lakehouse: Spark + Iceberg + dbt) ─────────────────────────
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
		$(COMPOSE) run --rm dbt-runner run \
			--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt; \
	else \
		$(COMPOSE) run --rm dbt-runner run \
			--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt \
			--select $(LAYER); \
	fi

.PHONY: dbt-test
dbt-test: _require-env
	$(COMPOSE) run --rm dbt-runner test \
		--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt

.PHONY: dbt-deps
dbt-deps: _require-env
	$(COMPOSE) run --rm dbt-runner deps \
		--profiles-dir /usr/app/dbt --project-dir /usr/app/dbt

.PHONY: minio-ui
minio-ui:
	@echo "MinIO console: http://localhost:9001  (user: minioadmin / minioadmin)"

# ── Orchestration (Airflow) ───────────────────────────────────────────────────
.PHONY: airflow-up
airflow-up: _require-env
	$(COMPOSE) up -d airflow-postgres
	$(COMPOSE) run --rm airflow-init
	$(COMPOSE) up -d airflow-webserver airflow-scheduler
	@echo "Airflow UI: http://localhost:8085  (admin / admin)"

.PHONY: airflow-down
airflow-down:
	$(COMPOSE) stop airflow-webserver airflow-scheduler airflow-postgres 2>/dev/null || true

.PHONY: airflow-open
airflow-open:
	@echo "Opening Airflow UI: http://127.0.0.1:8085/login/"
	@open "http://127.0.0.1:8085/login/"

.PHONY: airflow-open-localhost
airflow-open-localhost:
	@if ! curl -k -sf --max-time 3 https://localhost:8085/ >/dev/null 2>&1; then \
		echo "Warning: https://localhost:8085 is not served by Airflow (HTTP only)."; \
		echo "If your browser upgrades localhost to HTTPS, disable HTTPS-first for localhost."; \
	fi
	@echo "Opening Airflow UI: http://localhost:8085/login/"
	@open "http://localhost:8085/login/"

.PHONY: airflow-trigger
airflow-trigger:
	$(COMPOSE) exec airflow-scheduler \
		airflow dags trigger dbt_lakehouse_pipeline

.PHONY: logs-airflow
logs-airflow:
	$(COMPOSE) logs -f airflow-scheduler airflow-webserver

# ── Analytics layer (Feature Store + Semantic Layer + Vector Index) ──────────
.PHONY: analytics-up
analytics-up: _require-env
	$(COMPOSE) up -d qdrant feast-server
	@echo "Qdrant dashboard : http://localhost:6333/dashboard"
	@echo "Feast server     : http://localhost:6566/get-online-features"

.PHONY: analytics-materialize
analytics-materialize: _require-env
	$(COMPOSE) run --rm \
		-e AWS_ACCESS_KEY_ID=minioadmin \
		-e AWS_SECRET_ACCESS_KEY=minioadmin \
		-e AWS_REGION=us-east-1 \
		-e AWS_DEFAULT_REGION=us-east-1 \
		-e AWS_ENDPOINT_URL=http://minio:9000 \
		-e AWS_ENDPOINT_URL_S3=http://minio:9000 \
		-e AWS_S3_ADDRESSING_STYLE=path \
		-v $(PWD)/data_platform/feature_store:/feature_store \
		feast-server bash -c \
		"cd /feature_store && feast apply --skip-source-validation && python materialize.py"

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

.PHONY: graph-up
graph-up:
	$(COMPOSE) up -d neo4j

.PHONY: graph-sync
graph-sync:
	$(COMPOSE) run --build --rm app /bin/bash -lc \
		"/app/.venv/bin/python data_platform/graph/sync_relationships.py && /app/.venv/bin/python data_platform/graph/sync_gold_kpis.py"

.PHONY: graph-check
graph-check:
	$(COMPOSE) up -d neo4j
	$(COMPOSE) exec neo4j cypher-shell -u neo4j -p neo4j \
		"MATCH ()-[r]->() \
		 WHERE type(r) IN ['AVAILABLE_AT','WORKS_AT','VISITS','HAS_KPI_SNAPSHOT'] \
		 RETURN type(r) AS relationship_type, count(r) AS relationship_count \
		 ORDER BY relationship_type"

.PHONY: graph-down
graph-down:
	$(COMPOSE) stop neo4j 2>/dev/null || true

# ── Internal guards ───────────────────────────────────────────────────────────
.PHONY: _require-env
_require-env:
	@if [ ! -f .env ]; then \
		echo "$(BOLD)ERROR$(RESET): .env not found. Run 'make env' and fill in ANTHROPIC_API_KEY."; \
		exit 1; \
	fi
