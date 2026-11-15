# Prawobiorca

Prawobiorca is an application developed within the WMS_DEV science club at the Wrocław University of Science and Technology.
Its goal is to help students defend and assert their rights.

The application is available at **[prawobiorca.pl](https://www.prawobiorca.pl)**.

The core part of the application is a regulations search engine. Users can find relevant legal acts by searching their descriptions, then search for provisions within a selected document. Both searches use the meaning of natural language queries.

Logged-in users can also:
- **Manage cases** - create cases and pin the regulations relevant to them.
- **Generate applications** - draft DOCX applications with AI, based on application templates and the data from a case.
- **Find application templates** - search published templates by name, with an optional AI search using their descriptions.
- **Search own regulations** - upload own files and search them the same way as public regulations.

Plans include:
- **Dean's Office Simulator** - practice in front of a computer to avoid stress at the counter.

## Repository Layout

The whole application lives in this repository:

- `apps/core/` - main API (FastAPI) and the Taskiq worker handling document processing.
- `apps/extraction/` - extracts structured text from PDFs.
- `apps/embedding/` - OpenVINO Model Server image with the embedding model baked in.
- `apps/web/` - Vue 3 frontend application.
- `deploy/` - Kubernetes manifests: a shared Kustomize base with overlays for GCP, the local kind cluster and E2E.
- `scripts/` - helper scripts for running the app locally and deploying it to the cloud.
- `docs/` - developer documentation.

## How to Contribute

1. **Clone the project and install dependencies**, preferably with [uv](https://docs.astral.sh/uv/):
    ```sh
    uv sync --all-groups
    ```
    - Install [just](https://just.systems) (version `1.38` or newer), which runs the project tasks.

2. **Install the frontend dependencies** (requires Node `^26.13.0` and pnpm `11.24.0`, easiest through `corepack enable`):
    ```sh
    cd apps/web
    pnpm install
    ```
    - See [apps/web/README.md](apps/web/README.md) for the frontend development commands.

3. **Set up the commit hook**:
    ```sh
    git config core.hooksPath .githooks
    ```

4. **Read the [developer documentation](https://erykmikolajewicz.github.io/prawobiorca/)**:
    - Read the section about **Workflow**, especially regarding the commit format.
    - Read about **Project Architecture**, especially the coding rules.
    - See [Working on documentation](docs/index.md#working-on-documentation) for local preview and build commands.

5. **Develop your code**:
    - Write your code on a feature branch.

6. **Submit**:
    - If everything works, push your code to the repository (remember to do it on a feature branch) and contact **Eryk Mikołajewicz** for a code review.

## Running the Application
To check how the application works, run it in a local [kind](https://kind.sigs.k8s.io) cluster. You need **Podman**, **kind** and **kubectl** installed.

```sh
just run-locally
```
This creates the `prawobiorca` cluster if it does not exist, builds the images of all services, loads the changed ones into the cluster and deploys the application together with the LLM running on CPU.

The first run takes a while: it loads about 4.5 GB of images, and the LLM downloads its model (about 20 GB) to `.llm-models` in the background. The model needs about 20 GB of RAM.

The database and the object storage use the Podman volumes `pg-data` and `rustfs-data`, the same as `just dev`, so both see the same data. Only one of them can run at a time, the scripts refuse to start while the other one is running.

Everything is served by the nginx gateway on [http://localhost:8080](http://localhost:8080):

- [http://localhost:8080/](http://localhost:8080/) - the frontend application
- [http://localhost:8080/api](http://localhost:8080/api) - the API
- [http://localhost:8080/docs](http://localhost:8080/docs) - the Swagger documentation
- [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json) - the OpenAPI schema
- [http://localhost:8080/storage/](http://localhost:8080/storage/) - the object storage

The object storage is also available directly on [http://localhost:9000](http://localhost:9000).

- `just run-locally-down` stops the cluster and keeps its data.
- `just run-locally-reset` deletes the cluster; the database, object storage and downloaded LLM models stay.

### Initialize databases
The database and the compute services are not exposed on the host, so forward their ports first:
```sh
kubectl --context kind-prawobiorca port-forward service/postgres 5432:5432 &
kubectl --context kind-prawobiorca port-forward service/embedding 8081:8080 &
kubectl --context kind-prawobiorca port-forward service/extraction 8082:8080 &
just init-db
kill %1 %2 %3
```
This command may take a while, it is making some hard extraction from PDFs. It reads the configuration from `apps/core/.env` (see `apps/core/.env.example`).

## Development Mode
For day-to-day development, run the backend and the frontend from the sources, with hot reload.

Build the images of the compute services once (or after changing them):
```sh
just build-embedding
just build-extraction
```

Start the backend:
```sh
just dev
```
This launches the Postgres, RustFS, embedding, extraction and LLM containers, runs the migrations, and starts the Taskiq worker and the API on [http://localhost:8000](http://localhost:8000), both reloading on code changes. The configuration is read from `apps/core/.env` (see `apps/core/.env.example`).

In a second terminal start the frontend:
```sh
cd apps/web
pnpm dev
```
The Vite dev server runs on [http://localhost:5173](http://localhost:5173) and proxies `/api` to the backend.
