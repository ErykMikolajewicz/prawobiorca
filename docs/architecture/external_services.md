# External Services

---

## Relational Database

### Technology Choice and Justification
PostgreSQL was chosen as the relational database. The decision was driven by the need for a scalable and durable solution for storing information. Postgres stands out with its rich set of data types (e.g., JSON support), high performance, and broad support within the Python ecosystem — efficient drivers are available, implemented in Cython/C, including asynchronous versions.

### Scope of Use
Postgres serves as the default data storage location in the application. Other forms of storage are used only when required for performance reasons or due to the absence of certain functionality in the relational database.

### Abstraction Layer and Integration
The application uses the SQLAlchemy ORM for database communication. There is a repository pattern used to gather all data access code in one place and decouple app layer for orm related concerns.

### Capabilities and Plans
Replacing Postgres is considered unlikely but possible.

---

## TextTransformator

Api with an option to embed document and split PDF files for elements.

---

## Embedding Service

### Technology Choice and Justification
**OpenVINO Model Server (OVMS)** serves the embedding model directly — no custom application code — replacing an earlier FastAPI + ONNX Runtime app with EmbeddingGemma-300m. The model is `sdadas/mmlw-retrieval-roberta-large-v2` (Polish RoBERTa, 1024-dimensional vectors, 512-token context), chosen for its strong Polish retrieval results on PL-MTEB relative to its size. It is quantized to int8 weights and runs on CPU in every environment.

### Scope of Use
`core-service` calls the OpenAI-compatible `/v3/embeddings` endpoint (model name `mmlw-retrieval-roberta-large-v2`) to embed regulation chunks in the worker and search queries in the API. Queries are prefixed with `[query]: `, chunks are sent as `{title}\n{text}` without a prefix. OVMS applies CLS pooling and L2 normalization.

### Abstraction Layer and Integration
There is no pre-converted OpenVINO build of the model on Hugging Face and current OVMS images do not include `optimum-cli`, so the `embedding-service` image is built in two stages: a `python:3.12-slim` stage exports the model with `optimum-cli export openvino --weight-format int8` and `convert_tokenizer`, and the final stage is the OVMS image with that model baked in. Nothing is downloaded or converted at startup, and no volume is needed. OVMS serves it with `--task=embeddings --pooling=CLS`. `core-service` counts tokens locally with the same `tokenizer.json` to fit chunks within the limit.

### Capabilities and Future Plans
Changing the model requires re-embedding all regulations — the vector column length is fixed in the database schema.

---

## LLM Service

### Technology Choice and Justification
**OpenVINO Model Server (OVMS)** serves the conversational LLM directly — no custom application code — using a pre-quantized int4 OpenVINO IR build of Qwen2.5-7B-Instruct (`OpenVINO/Qwen2.5-7B-Instruct-int4-ov` on Hugging Face). It provides a maintained server with an OpenAI-compatible API, continuous batching and PagedAttention for CPU and Intel iGPU inference. This model is configured as the official, robust baseline (~4.5 GB RAM footprint) replacing earlier experiments with multimodal models (Gemma-4 VLM) and undersized models (Gemma-2B) to guarantee stability, native ChatML (`system` role) support, and high quality Polish language legal syntax. This keeps the service consistent with the rest of the stack's preference for Intel-hardware-friendly, CPU-first inference (as in `embedding-service`'s ONNX Runtime usage).

### Scope of Use
Standalone service exposing an OpenAI-compatible `/v1/chat/completions` endpoint (model name `qwen-2.5-7b-it`), consumed by `core-service` for automated application/letter drafting.

### Abstraction Layer and Integration
OVMS pulls the model repository from Hugging Face on first start (`--source_model`) into a mounted persistent volume, so restarts reuse the cached model instead of re-downloading it. No custom image build or model-baking step is needed.

### Capabilities and Future Plans
Planned follow-ups: streaming responses, and exploring multi-turn conversational agents.

---

## Object Storage

### Technology Choice and Justification
Files are kept in an S3-compatible object storage rather than the relational database — storing files in Postgres would hurt database performance, and serving them through the web application would put a heavy load on `core-service`. The application talks to storage exclusively through the S3 protocol, which lets the same client code run against different backends depending on the deployment mode: **RustFS** on-premise (run as a container via Podman) and **Google Cloud Storage** in the cloud, accessed through its S3 interoperability API. No environment-specific storage code is needed.

### Scope of Use
Object storage holds both public and private files:

- **Public files** (e.g., laws, court rulings) are accessible via a presigned/standard URL.
- **Private user files** are available only through presigned URLs with a limited validity period.

Files never transit through `core-service`. The browser writes a file directly to storage using a presigned POST target (URL + form fields) that `core-service` generates and hands back after registering the file's metadata; it then calls back a confirmation endpoint so `core-service` can schedule background processing. Reading works the same way in reverse: `core-service` returns a presigned GET URL, and the browser fetches the file directly from storage. The Taskiq worker is the one component that reads raw file bytes itself, for text extraction/chunking/embedding.

### Abstraction Layer and Integration
The storage port is a small `Protocol` in the application layer, backed by a single S3-protocol adapter (`aiobotocore`) in infrastructure — the same adapter class is used unchanged for both RustFS and GCS. Two clients are configured: the main client, used for internal calls, and a "presign" client pointed at a public endpoint URL (`OBJECT_STORAGE_PUBLIC_ENDPOINT_URL`), used only to generate presigned URLs so they stay reachable from the browser even when the internal endpoint (`OBJECT_STORAGE_ENDPOINT_URL`) is not (e.g. an internal cluster hostname in local/on-premise deployments).

### Capabilities and Future Plans
An alternative considered in the design phase was storing files in a file system and serving them via Nginx, but this was deemed less scalable and more difficult for access management. Because integration goes through the S3 protocol rather than a cloud-specific SDK, switching to another S3-compatible backend in the future would not require any application code changes.
