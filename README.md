# Prawobiorca

Prawobiorca is an application developed within the WMS_DEV science club at the Wrocław University of Science and Technology.
Its goal is to help students defend and assert their rights.

The core part of the application is a regulations search engine. It allows collecting information in a simple and accessible way by entering queries, which are then processed based on their meaning rather than exact text matching.

Plans include:
- **Application Generator** - create elegant DOCX documents by simply describing what you want to achieve.
- **Court Judgments Search Engine** - check if other students have defended their cases in court and what the outcomes were.
- **Court Judgments Summarizer** - easily extract important facts from a sea of legal jargon!
- **Dean's Office Simulator** - practice in front of a computer to avoid stress at the counter.

## Repository Layout

The whole application lives in this repository:

- `core-service/` - main API (FastAPI) and the Taskiq worker handling document processing.
- `extraction-service/` - extracts structured text from PDFs.
- `embedding-service/` - OpenVINO Model Server image with the embedding model baked in.
- `prawobiorca-frontend/` - Vue 3 frontend application.
- `deploy/` - Kubernetes manifests for the local (Podman) and GCP environments.
- `scripts/` - helper scripts for running the app locally and deploying it to the cloud.
- `docs/` - developer documentation.

## How to Contribute

1. **Clone the project and install dependencies**, preferably with [uv](https://docs.astral.sh/uv/):
    ```sh
    uv sync --all-groups
    ```
    - Install [just](https://just.systems) (version `1.38` or newer), which runs the project tasks.

2. **Install the frontend dependencies** (requires Node `^24.15.0` and pnpm `11.24.0`, easiest through `corepack enable`):
    ```sh
    cd prawobiorca-frontend
    pnpm install
    ```
    - See [prawobiorca-frontend/README.md](prawobiorca-frontend/README.md) for the frontend development commands.

3. **Set up the commit hook**:
    ```sh
    git config core.hooksPath .githooks
    ```

4. **Open the documentation**:
    ```sh
    zensical serve
    ```
    - Read the section about **Workflow**, especially regarding the commit format.
    - Read about **Project Architecture**, especially the coding rules.

5. **Develop your code**:
    - Write your code on a feature branch.

6. **Submit**:
    - If everything works, push your code to the repository (remember to do it on a feature branch) and contact **Eryk Mikołajewicz** for a code review.

## Running the Application
To check how the application works, launch it using the script below. Note that you must have **Podman** installed for it to work!

Start with building images with:
```sh
just build-images
```
This builds the images of all services, including the frontend.

Then run:
```sh
just run-locally
```

## Initialize databases
```sh
just init-db
```
This command may take a while, it is making some hard extraction from PDFs.

Everything is served by the nginx ingress on [http://localhost:8080](http://localhost:8080):

- [http://localhost:8080/](http://localhost:8080/) - the frontend application
- [http://localhost:8080/api](http://localhost:8080/api) - the API
- [http://localhost:8080/docs](http://localhost:8080/docs) - the Swagger documentation
- [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json) - the OpenAPI schema
- [http://localhost:8080/storage/](http://localhost:8080/storage/) - the object storage

To stop the deployment run `just run-locally-down`.
