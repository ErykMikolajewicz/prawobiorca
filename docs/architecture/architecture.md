# Application Architecture

## 1. Introduction and System Overview

**Prawobiorca** is a modern web application providing intelligent legal search and document management capabilities. The system supports AI-assisted (semantic vector search) retrieval of legal acts, as well as case management and document drafting for authenticated users.

The whole application lives in a single repository: the Python backend services described below, and the Vue frontend (`prawobiorca-frontend`) documented in [Frontend](frontend.md).

The system is designed to run in two primary environments:
- **Cloud (GCP / Google Cloud Platform)**: Utilizing containerized workloads with scale-to-zero capabilities for resource-heavy operations to optimize cost and resource allocation.
- **On-Premise**: Running containerized services using **Podman** / Docker.

---

## 2. System Architecture & Components

The architecture follows a **Monolith** pattern for core business logic, paired with **specialized microservices** for compute-heavy tasks:

```mermaid
flowchart TD
    Browser["Browser"]
    Ingress["nginx / Ingress"]
    Frontend["prawobiorca-frontend<br/>(Vue SPA served by nginx)"]
    Core["core-service<br/>(Auth, Cases, Files, Search Engine)"]
    Worker["Taskiq Worker<br/>(File Preparator / Chunking / Indexing)"]
    Embeddings["embeddings-service<br/>(OpenVINO Model Server)"]
    Extraction["extraction-service"]
    DB[("PostgreSQL + pgvector<br/>(Metadata, Chunks, Task Queue)")]
    Storage[("Object Storage<br/>RustFS (on-premise) / GCS (cloud)")]

    Browser --> Ingress
    Ingress -->|"/"| Frontend
    Ingress -->|"/api"| Core
    Core -->|Dispatches Task| DB
    Core -->|Generates Query Embed| Embeddings
    Core -->|Vector & Relational DB| DB
    Core -->|"Generates presigned upload/download URL"| Storage
    Browser -->|"Uploads/downloads file directly<br/>(presigned URL, bypasses Core)"| Storage
    DB -->|Consumes Task| Worker
    Worker -->|Batch Embed| Embeddings
    Worker -->|extract text| Extraction
    Worker -->|Reads file bytes| Storage
```

### 2.1. `core-service` (Main API & Taskiq Worker)
Hosts the core domain logic, user-facing endpoints, and background document indexing within a single modular codebase:
* **Core API (FastAPI)**:
  * User authentication, authorization, and profile management.
  * Case (*Sprawy*) management and document metadata handling (filenames, upload status, permissions).
  * Storage orchestration: generates presigned upload/download URLs (S3 presigned POST/GET) so the browser transfers file bytes directly with object storage — `core-service` never proxies the bytes itself. The Taskiq worker separately reads the raw bytes back from storage for processing.
  * Fast synchronous search execution: requests single query embeddings from `embeddings-service` and performs vector similarity search against PostgreSQL (`pgvector`).
  * Dispatches asynchronous file processing tasks using **Taskiq**, automatically upon upload confirmation — no separate request is needed to start indexing. The task is written to PostgreSQL in the same transaction that marks the document as in progress.
* **File Preparator (Taskiq Worker)**:
  * Consumes document preparation jobs from the PostgreSQL task queue.
  * Coordinates document processing pipeline: sends file to `extraction-service`, chunks structured text, requests batch embeddings from `embeddings-service`, and persists vector embeddings into PostgreSQL.
  * Chunking follows the editorial structure of the act (article / paragraph, with its chapter breadcrumb) recovered from the text itself, not the layout labels returned by `extraction-service` — see [Legal documents parsing](legal_documents_parsing.md).
  * Updates document processing status in PostgreSQL directly without inter-service RPC overhead.
  * Retries a document up to 3 times when `extraction-service` or `embeddings-service` is unavailable; after the last attempt the document is marked as failed and can be retried on demand. A document whose processing crashed the worker 3 times is marked as failed as well.

### 2.2. `embeddings-service`
* **Responsibilities**:
  * Dedicated, stateless service generating dense vector embeddings for text chunks and search queries with the Polish retrieval model `sdadas/mmlw-retrieval-roberta-large-v2` (int8), served directly by **OpenVINO Model Server (OVMS)** — no custom application code — via the OpenAI-compatible `/v3/embeddings` endpoint.
* **Characteristics**:
  * **Isolated Compute**: Heavy tensor computation and embedding model memory footprints are completely decoupled from the main API, preventing thread blockage and memory spikes.
  * **Independent Scaling**: Can be scaled independently (e.g., on GPU or high-CPU compute instances) based on search traffic and document ingestion volume.
  * **Fast cold start**: the OpenVINO int8 export of the model is baked into the image at build time, so no model download or conversion happens at startup and no volume is needed; it runs on CPU in every environment.
  * A single endpoint accepts both single texts and batches.
  * **Scale-to-0 on GCP**: search queries from `core-service` are embedded by `embedding-service` on **Cloud Run** (2 CPU, 2 inference threads), deployed by `scripts/cloud/deploy_embedding_service.sh` with `--ingress=internal`. It scales to zero, so the first search after a period of inactivity waits roughly 10–20 s for the cold start.
  * **Separate batch instance on GCP**: the Taskiq worker embeds document chunks through `embedding-batch-service`, a second instance of the same image on **Cloud Run** (8 CPU, 8 inference threads), so batch ingestion never competes with user queries. It scales to zero and is billed only while a request is being handled; the only caller is the worker, so the cold start is absorbed by a background job. Deployed by `scripts/cloud/deploy_embedding_batch_service.sh` with `--ingress=internal`; the worker overrides `EMBEDDING_SERVICE_URL` (and `EMBEDDING_SERVICE_BATCH_SIZE`) in its own deployment.

### 2.3. `extraction-service`
* **Responsibilities**:
  * Document layout analysis, and text extraction (PDFs) into structured JSON format, using Docling.
* **Characteristics**:
  * Completely stateless service.
  * **Scale-to-0 on GCP**: runs on **Cloud Run** rather than in the GKE cluster, so it scales to zero natively and is billed only while a request is being handled. Deployed by `scripts/cloud/deploy_extraction_service.sh` with `--ingress=internal`, which limits callers to the VPC; the Taskiq worker reaches it over HTTPS at the service URL in `EXTRACTION_SERVICE_URL`. The only caller is the worker, so the cold start is absorbed by a background job rather than by a user request.
  * **Fast cold start**: the image uses CPU-only PyTorch and has the Docling models (layout, TableFormer, RapidOCR) baked in, so no model download happens at startup; models are loaded eagerly before the service reports healthy. On Cloud Run a cold start costs roughly 30 s on top of the request.
  * Runs as a dedicated container in On-Premise deployments (single replica, no scale-to-0).

### 2.4. `llm-service`
* **Responsibilities**:
  * LLM inference (Qwen2.5-7B-Instruct, int4-quantized), served directly by **OpenVINO Model Server (OVMS)** — no custom application code — exposing an OpenAI-compatible `/v1/chat/completions` HTTP endpoint.
* **Characteristics**:
  * Used by `core-service` to draft student applications (*wnioski*) rendered to PDF — see [AI module](../ai.md).
  * OVMS pulls the model from Hugging Face straight into a persistent volume on first start (cached across restarts after that), so no image build/model-baking step is needed for this service.
  * On-Premise uses `--target_device=AUTO` with `/dev/dri` passed through, so it runs on the Intel iGPU when the host exposes one and transparently falls back to CPU otherwise. GCP stays on CPU (GKE Autopilot only supports NVIDIA GPU passthrough).
  * **No scale-to-0 yet**: runs as a single always-on replica on GKE. The service is not deployed by `scripts/cloud/deploy_app.sh`, so it costs nothing today; the scaling model has to be settled together with the `core-service` integration, since the model's RAM footprint is too large to keep idle once it is actually serving traffic.

### 2.5. `prawobiorca-frontend`
* **Responsibilities**:
  * Single-page application (Vue 3 + TypeScript) delivering the whole user interface: search, authentication, case and document management.
* **Characteristics**:
  * Built with Vite into static assets and served by **nginx** from its own container; no server-side rendering and no application server.
  * Communicates only with `core-service` over the HTTP REST API, under the `/api` prefix of the shared ingress — it never reaches the database or the compute services directly.
  * Stateless from the deployment point of view: the session lives in cookies issued by `core-service`.
  * See [Frontend](frontend.md) for the stack, project structure and development commands.

---

## 3. Key Architectural Decisions & Patterns

### 3.1. Monolith for Core Business (`core-service`)
* **Simplicity & Velocity**: Simple monolith, but with clean architecture, possibly to modularize, if team growth.
* **Architecture**: Use cases and domain entities for documents, cases, with separate layers for framework, and infrastructure (e.g. db connection).

### 3.2. Asynchronous Job Processing with Taskiq
* **Modern Async-First Design**: Native integration with FastAPI and asynchronous Python runtimes.
* **PostgreSQL Broker**: Tasks are stored in the `task_messages` table of the main database by a custom broker (`infrastructure/tasks/broker.py`), so no separate broker service is needed. A task is kept in the table until it is executed:
  * **Transactional dispatch**: the task is inserted in the same transaction as the related status change, so it exists only if that change is committed.
  * **Claiming**: a worker takes a task with `SELECT ... FOR UPDATE SKIP LOCKED` and locks it for a lease (`TASK_LEASE_SECONDS`), so concurrent workers never take the same task.
  * **Wake-up**: `NOTIFY` wakes the worker immediately, and polling every `TASK_POLL_INTERVAL_SECONDS` picks up tasks sent while no worker was listening.
  * **Heartbeat**: while a task runs, the worker extends its lease every `TASK_HEARTBEAT_SECONDS`. If the worker crashes, the lease expires and the task is delivered again.
  * **Acknowledgement**: the row is deleted only after the task has been executed.
  * **Poison messages**: each delivery is counted and passed to the task in the `delivery_attempt` label; above the limit, the task marks the document as failed instead of processing it.
* **Resilience**: Provides built-in retry mechanisms, failure handling, and transparent task parameter serialization.

### 3.3. Compute Decoupling (Embeddings & Extraction)
* **Resource Isolation**: CPU/GPU-intensive tasks (OCR extraction and vector embedding generation) reside in specialized microservices.
* **Guaranteed Latency**: The primary web API stays lightweight, responsive, and fast under heavy indexing workloads.

---

## 4. More about core-service architecture

Each Python service in the repository follows **Clean Architecture** principles, enforcing strict inward-pointing dependency rules. The frontend is not bound by these rules — its structure is described in [Frontend](frontend.md).

```mermaid
flowchart TB
    subgraph Framework["Framework (FastAPI, Taskiq Workers)"]
        subgraph Infrastructure["Infrastructure (DB Repos, HTTP Clients, Storage)"]
            subgraph Application["Application (Use Cases, DTOs, Ports)"]
                Domain["Domain (Entities, Value Objects)"]
            end
        end
    end
```

### 4.1. Layers

#### `../../core-service/src/domain`
The innermost core of the service containing **Enterprise Business Rules**. It has zero dependencies on outer layers or external frameworks.
- **Entities**: Business models encapsulating identity and business state (e.g., `User`, `Case`, `Document`, `Chunk`).
- **Value Objects**: Immutable data structures representing concepts without identity.
- **Services**: Pure business algorithms and domain rules.
- **Exceptions**: Domain-specific error definitions.

#### `../../core-service/src/app` (or `../../core-service/src/app`)
Contains **Application Business Rules** and use case orchestrations.
- **Use Cases**: Individual business workflows (e.g., `RegisterUser`, `ProcessUploadedDocument`, `SearchDocuments`).
- **DTOs**: Data Transfer Objects defining input/output contracts.
- **Ports & Interfaces**: Abstract contracts for repositories, vector embedders, and external APIs implemented by the Infrastructure layer.

#### `../../core-service/src/infrastructure`
Acts as adapters for external systems and technical tools, implementing ports defined in domain/application.
- **Relational DB**: SQLAlchemy repositories, connection pools, and database schemas.
- **External Clients**: HTTP/gRPC clients communicating with external services (`embeddings-service`, `extraction-service`).
- **Object Storage**: a single S3-protocol adapter (`aiobotocore`), reused unchanged against RustFS on-premise and against Google Cloud Storage's S3-interoperability endpoint in the cloud. A separate "presign" client, pointed at a public endpoint URL, keeps presigned URLs handed to the browser reachable even when the internal endpoint isn't.

#### `../../core-service/src/framework`
The outermost delivery mechanism and dependency injection root.
- **API**: FastAPI routes, middleware, and request/response serialization.
- **Workers**: Taskiq worker definitions and task registrations.
- **Dependencies**: Dependency injection wiring combining infrastructure implementations with application use cases.

#### `../../core-service/src/shared`
Cross-cutting concerns across layers (configuration settings, logging utilities, common base exceptions).

---

## 5. Import Rules

To preserve architectural boundaries:
- **`domain`** must NOT import from `app`, `infrastructure`, or `framework`.
- **`app`** can import from `domain`, but must NOT import from `infrastructure` or `framework`.
- **`infrastructure`** can import from `app` (interfaces, DTOs) and `domain`. It must NOT import from `framework`.
- **`framework`** is the assembly root and can import from `app`, `domain`, and `infrastructure` to wire dependencies.
- **`shared`** can be imported by any layer, but should not depend on domain or infrastructure specifics.
