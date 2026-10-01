# Library Overview

This document contains information about selected libraries along with the reasoning behind their use. It also compares alternative solutions — both other services and different implementation approaches.  
This means the section explains, for example, why a specific Postgres driver was chosen but does not explain why Postgres was selected over MySQL.  
Justifications for choosing components that work with the application can be found in [external services](external_services.md).

If a library is used with a major version lower than the latest, a justification for this should also be provided.

Information about the currently used library versions can be found in the `pyproject.toml` file.

---

## Required dependencies

Below are the dependencies essential for the application to run, which should be included in the production release.

### Alembic
A tool for performing database migrations. Works in tandem with [SQLAlchemy](#sqlalchemyasyncio) and is essentially irreplaceable when using this ORM.
Shipped in the application image, so migrations run from the same image as the application, only with the `alembic upgrade head` command. Also used in tests to initialize tables and schemas in the database.

---

### asyncpg

Chosen as an asynchronous Postgres client, consistent with the philosophy of the [FastAPI](#fastapi) framework, which encourages asynchronous code.  
The downside is connection sharing issues during tests — see the [integration tests](../tests/integration_fixtures.md) section for more details.

`asyncpg` was selected due to its top performance in benchmarks. `psycopg3` was also considered, as its support for both synchronous and asynchronous APIs could simplify certain operations (e.g., `alembic` migrations). However, performance was deemed more critical due to frequent database reads.

Switching the driver later should be relatively easy thanks to the use of the [SQLAlchemy](#sqlalchemyasyncio) ORM.

---

### bcrypt

Password hashing library chosen for security reasons.  
`bcrypt` provides strong resistance to brute-force attacks and is easy to use.

Alternatives:  
- **`hashlib`** (Python standard library) — lacks salt support, which would increase implementation complexity or expose hashes to rainbow table attacks.  
- **`passlib`** — supports `argon2`, which is more secure than `bcrypt`. However, it was considered unnecessary, and its longer hashing time could negatively impact the user experience during login.

---

### email-validator

An optional Pydantic dependency is used to validate email addresses in the application.

---

### fastapi

The main framework used in the project. Selected for:  
- high performance due to asynchronous programming support,  
- data validation via Pydantic,  
- automatic documentation generation (Swagger),  
- easier testing through dependency injection.

Alternatives:  
- **Flask** — weaker asynchronous support and requires installing many plugins for basic functionality.  
- **Django** — overly complex for the project’s needs (e.g., HTML file hosting, rigid ORM structure). The application is intended to operate as a set of SOA services communicating via REST API, where FastAPI is a lighter, more flexible option.

---

### granian

An HTTP server written in Rust, supporting HTTP/2.  
Pros: high performance.  
Cons: harder debugging compared to Python-based servers (e.g., hypercorn).

---

### httpx2

New popular http Python client. Used for its async support.
Used to communicate with embedding service.

---

### pgvector

Plugin for vector capabilities in Postgres.

---

### pydantic-settings

A library for managing application configuration.  
Pros:  
- type and value validation,  
- centralized configuration,  
- minimal impact on application size (Pydantic is already in use).  

Alternatives were not extensively researched.

---

### pyjwt

Library used to issue and verify the signed JSON Web Tokens that carry the user session (access tokens).
Chosen because it is the reference Python JWT implementation, has no transitive dependencies, and exposes exactly
the primitives needed here — `encode`/`decode` with an explicit algorithm allow-list.

Alternatives:
- **`python-jose`** — covers the whole JOSE suite (JWE, JWK, JWS), far more than a symmetric HS256 token needs,
  and is maintained less actively.
- **`authlib`** — a full OAuth2/OIDC framework; the application only issues its own first-party tokens,
  so the extra surface would be unused.
- **hand-written HMAC signing** on top of `hmac`/`hashlib` — avoids a dependency but means maintaining custom
  cryptographic code, including claim validation and constant-time comparison. Not worth the risk.

---

### python-multipart

A library for handling file uploads in applications based on [FastAPI](#fastapi).

---

### sqlalchemy\[asyncio\]

The most popular ORM in Python.  
Pros:  
- rich functionality and documentation,  
- production maturity,  
- built-in connection pooling.  

Cons:  
- steep learning curve,  
- documentation covers both legacy (1.4) and modern (2.x) versions, which can be confusing.  

Alternative: **[Tortoise ORM](https://tortoise.github.io/){target=_blank}** — natively asynchronous and simpler to use, though less popular.

---

### taskiq

Distributed task queue used to run heavy, long-running document preparation (extraction + chunking + embedding) in a background worker instead of blocking the request-response cycle. Chosen for its native async-first design and straightforward FastAPI-style dependency injection, which fits the existing codebase.

Alternative: **Celery** — the most established Python task queue, but it is not async-native and requires more configuration to work well with an asyncio-based codebase.

The broker is not a library: it is a small PostgreSQL broker in `core-service/src/infrastructure/tasks/broker.py`, so the queue lives in the existing database and no separate service is needed (see [Architecture](architecture.md#32-asynchronous-job-processing-with-taskiq)). The ready-made PostgreSQL brokers (`taskiq-pg`, `taskiq-postgres`) were rejected because they pick messages up only on `NOTIFY`: a message sent while no worker is listening, or one claimed by a worker that crashed, is never delivered again. Redis (`taskiq-redis`) was used before, but it added a separate stateful service, and its list-based broker lost the task being processed when the worker crashed.

## Storage Dependencies

### aiobotocore

Native-async S3-compatible client, used as the single adapter for object storage in both deployment modes: **RustFS** on-premise and **Google Cloud Storage** in the cloud via its S3 interoperability API. Chosen over `google-cloud-storage` because it is asynchronous natively (no sync-wrapper needed) and because one S3-protocol client covers both backends, avoiding a second, environment-specific adapter.

Pulls in `botocore` transitively for the underlying S3 request signing (including presigned URL generation).



## Dev/Test Dependencies

Dependencies are required during the development process, writing tests, or debugging. Unlike the main dependencies section, they are not required to run the application in a production environment.

---

### granian\[reload\]
An extension of [Granian](#granian) that enables automatic reload when code changes. Used during debugging when running the application via a bash script.

---

### zensical
A documentation generator that outputs a website. You are most likely reading documentation generated with it right now.

---

### mkdocstrings\[python\]
A plugin that integrates Python docstrings into documentation generated with [zensical](#zensical).

---

### pytest
The most popular testing framework in Python. Significantly extends the capabilities of the built-in `unittest` module. Alternative testing frameworks were not considered.

---

### pytest-asyncio
A [Pytest](#pytest) plugin that enables testing asynchronous code. It has some limitations—tests are executed in a simulated asynchronous manner (each in a separate thread), which makes sharing the event loop with the application difficult and prevents speeding up tests by skipping the wait for asynchronous operations to complete.

---

### ruff
Popular python linter. Used to ensure similar formatting across various devs. Also, can catch some bad smelling code, like unused imports

---

### testcontainers\[postgres\]
A library for easily creating containers during integration tests. Officially works only with Docker, but Podman can be configured to cooperate with it by emulating Docker.
