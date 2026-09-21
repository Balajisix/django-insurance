# Insurance Claims Platform

A Django REST API for managing insurance claims end to end: customers, policies, claim submission, supporting documents, an AI-assisted review pipeline (OCR, embeddings, RAG, summaries, inconsistency detection), and a Snowflake-backed analytics layer.

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the project](#running-the-project)
- [Snowflake analytics](#snowflake-analytics)
- [API reference](#api-reference)
- [Claim workflow](#claim-workflow)
- [Roles and permissions](#roles-and-permissions)
- [Troubleshooting](#troubleshooting)

## Features

- **Users and roles**: token authentication with four roles (Customer, Claims Officer, Manager, Admin).
- **Customers and policies**: customer profiles, policies and policy coverages.
- **Claims**: submission, a validated status workflow, an event history, requirements and settlements.
- **Documents**: claim documents stored in AWS S3, with file validation.
- **AI document processing**:
  - Text extraction from PDFs and images (pypdf, Tesseract OCR)
  - Text chunking and Hugging Face embeddings stored in a FAISS index
  - Semantic search and RAG question answering over claim documents
  - Vision analysis of document images
- **AI claim intelligence**: claim summaries, missing-document detection, inconsistency analysis, and a single "complete AI workflow" endpoint.
- **Analytics**: PostgreSQL data is loaded into a Snowflake star schema (full load, incremental load, or an automatic worker) and served through analytics endpoints.

## Tech stack

| Area | Technology |
|---|---|
| Backend | Python, Django 6, Django REST Framework |
| Database | PostgreSQL (psycopg 3) |
| File storage | AWS S3 (django-storages, boto3) |
| OCR / PDF | Tesseract (pytesseract), pypdf, Pillow |
| Embeddings / LLM / vision | Hugging Face (sentence-transformers, HF Inference API) |
| Vector store | FAISS (faiss-cpu), saved on local disk |
| Analytics warehouse | Snowflake (snowflake-connector-python), pandas |
| Config | django-environ (`.env`) |

## Architecture

```
                 ┌────────────────────────────┐
   Client ─────► │  Django REST API (/api/v1) │
 (token auth)    └──────┬───────────┬─────────┘
                        │           │
        ┌───────────────┘           └────────────────┐
        ▼                                            ▼
  PostgreSQL (source of truth)                 AWS S3 (documents)
  customers, policies, claims,                        │
  documents, AI results                               ▼
        │                                  Text extraction + OCR
        │                                            │
        │                             chunks ─► embeddings ─► FAISS index
        │                                            │      (storage/faiss)
        │                                            ▼
        │                              RAG, summaries, inconsistencies
        │
        │  triggers → NOTIFY
        ▼
  Snowflake worker ──► incremental ETL (watermarks + MERGE) ──► Snowflake DW
                                                                   │
                                            Analytics API ◄────────┘
```

## Project structure

```
config/                 Project settings and root URL routing
  api_urls.py           All /api/v1/ routes
apps/
  users/                Custom user model, roles, auth endpoints
  customers/            Customer profiles
  policies/             Policies and coverages
  claims/               Claims, workflow, events, settlements, AI result models
  documents/            Claim document upload and S3 storage
  ai/                   Extraction, chunking, embeddings, FAISS, RAG, LLM, vision
  analytics/            Snowflake client, ETL pipelines, analytics API
    etl/                extract, transform, load, pipeline, incremental_pipeline, watermark
    management/commands/  load_snowflake, load_snowflake_incremental, run_snowflake_worker
  common/               Shared exceptions and identifier helpers
  sql/                  Snowflake SQL (analytics views)
storage/faiss/          FAISS index files (created at runtime, git-ignored)
```

## Setup

### Prerequisites

- Python 3.12 or newer
- PostgreSQL 14 or newer, with an empty database created
- An AWS account with an S3 bucket
- A Hugging Face access token
- A Snowflake account with a database, schema, warehouse and role
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed (needed for images and scanned PDFs)

### 1. Get the code

```bash
git clone <your-repository-url>
cd insurance-usecase
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Windows (Git Bash) / macOS / Linux
source venv/Scripts/activate      # Git Bash on Windows
source venv/bin/activate          # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

`torch` and `sentence-transformers` are large, so the first install can take a while.

### 4. Create the PostgreSQL database

```sql
CREATE DATABASE insurance;
```

Use any name you like, and put it in `POSTGRES_DB`.

### 5. Configure the environment

```bash
cp .env.example .env
```

Then edit `.env` with your own values. See [Configuration](#configuration).

### 6. Apply migrations

```bash
python manage.py migrate
```

This also installs the PostgreSQL triggers used by the [Snowflake worker](#option-c-automatic-worker-recommended).

### 7. Create an admin user

```bash
python manage.py createsuperuser
```

Users log in with their **email**. New accounts can also be created through `POST /api/v1/auth/register/`.

### 8. Start the server

```bash
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/v1/` and the Django admin at `http://127.0.0.1:8000/admin/`.

## Configuration

All settings are read from `.env` (see [.env.example](.env.example)). The variables marked **required** have no default, and Django will not start without them.

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | yes | Django secret key |
| `DEBUG` | no | `True` for development (default `False`) |
| `ALLOWED_HOSTS` | no | Comma-separated hostnames |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | yes | PostgreSQL credentials |
| `POSTGRES_HOST` / `POSTGRES_PORT` | yes | PostgreSQL location (for example `127.0.0.1` and `5432`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | yes | Credentials with access to the bucket |
| `AWS_STORAGE_BUCKET_NAME` / `AWS_S3_REGION_NAME` | yes | Bucket for claim documents and its region |
| `TESSERACT_CMD` | no | Full path to the Tesseract executable, if it is not on `PATH` (for example `C:\Program Files\Tesseract-OCR\tesseract.exe`) |
| `HF_API_TOKEN` | yes | Hugging Face token |
| `HF_EMBEDDING_MODEL` | no | Default `sentence-transformers/all-MiniLM-L6-v2` |
| `HF_LLM_MODEL` | no | Default `openai/gpt-oss-120b:fastest` |
| `HF_VISION_MODEL` | no | Default `deepseek-ai/DeepSeek-V4-Flash-Vision-Exp` |
| `SNOWFLAKE_ACCOUNT` / `SNOWFLAKE_USER` / `SNOWFLAKE_PASSWORD` | yes | Snowflake login |
| `SNOWFLAKE_WAREHOUSE` / `SNOWFLAKE_DATABASE` / `SNOWFLAKE_SCHEMA` / `SNOWFLAKE_ROLE` | yes | Snowflake target |

Never commit `.env`. It is already in `.gitignore`.

## Running the project

| Task | Command |
|---|---|
| Run the API | `python manage.py runserver` |
| Apply migrations | `python manage.py migrate` |
| Full Snowflake load | `python manage.py load_snowflake` |
| Incremental Snowflake load (once) | `python manage.py load_snowflake_incremental` |
| Automatic Snowflake worker | `python manage.py run_snowflake_worker` |

### Typical API flow

1. Register and log in: `POST /api/v1/auth/register/`, then `POST /api/v1/auth/login/`. The response contains a token.
2. Send the token on every request: `Authorization: Token <token>`.
3. Create a customer, then a policy, then a claim.
4. Upload documents to the claim: `POST /api/v1/claims/<claim_id>/documents/`.
5. Process a document: `POST /api/v1/ai/documents/<document_id>/process/` (extract, chunk, embed).
6. Run the AI workflow for the claim: `POST /api/v1/ai/claims/<claim_id>/process/`.
7. Move the claim through review, approval, settlement and closure with the workflow endpoints.

## Snowflake analytics

The analytics layer copies data from PostgreSQL into a star schema in Snowflake:

- Dimensions: `DIM_CUSTOMER`, `DIM_POLICY`, `DIM_CLAIM_TYPE` (and a date dimension)
- Fact: `FACT_CLAIM`
- Metadata: a watermark table, created automatically, that records how far each source has been loaded
- View: [apps/sql/claims_analytics.sql](apps/sql/claims_analytics.sql) defines `VW_CLAIM_ANALYTICS_BASE`, which the analytics endpoints query

> **Prerequisite:** the dimension and fact tables and the analytics view must exist in your Snowflake schema before the first load. Only the watermark table is created by the code. Run the SQL in `apps/sql/` and create the `DIM_*` and `FACT_CLAIM` tables in your target database first.

Check the connection with `GET /api/v1/analytics/snowflake/health/`.

### Option A: full load

```bash
python manage.py load_snowflake
```

Reads everything from PostgreSQL and loads it. Use it for the first load.

### Option B: incremental load (manual)

```bash
python manage.py load_snowflake_incremental
```

Loads only rows whose `updated_at` is newer than the stored watermark, uses `MERGE` so reruns do not create duplicates, and moves the watermark only after a successful commit.

### Option C: automatic worker (recommended)

```bash
python manage.py run_snowflake_worker
```

A long-running process that keeps Snowflake up to date without you running anything:

1. Database triggers (installed by `migrate`) send a PostgreSQL `NOTIFY` whenever customers, policies, claims, settlements or AI analyses change.
2. The worker listens, waits for a burst of changes to settle, then runs the incremental ETL once.
3. It also syncs at startup, and at least every 5 minutes as a safety net.

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--debounce` | 5 | Seconds of quiet after a change before syncing |
| `--max-wait` | 30 | Longest a burst of changes can delay a sync |
| `--fallback-interval` | 300 | Longest gap between syncs when nothing changes |
| `--retry-delay` | 30 | Wait after a failed sync before retrying |

Run it as a separate process next to the web server, and in production under a process manager (systemd, Supervisor, or a Docker service). Run one instance only.

Known limits: deleted rows are not removed from Snowflake, and a change to a user's name alone does not update the customer dimension.

## API reference

All routes are under `/api/v1/` and require `Authorization: Token <token>` unless noted.

### Auth (`/auth/`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register/` | Create an account (no token needed) |
| POST | `/auth/login/` | Get a token (no token needed) |
| POST | `/auth/logout/` | Invalidate the token |
| GET | `/auth/me/` | Current user |

### Customers and policies

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/customers/` | List or create customers |
| GET | `/customers/<id>/` | Customer detail |
| GET, POST | `/policies/` | List or create policies |
| GET | `/policies/<id>/` | Policy detail |
| POST | `/policies/<id>/coverages/` | Add a coverage to a policy |

### Claims (`/claims/`)

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/claims/` | List or submit claims |
| GET | `/claims/<id>/` | Claim detail |
| POST | `/claims/<id>/start-processing/` | Submitted, then Document Processing |
| POST | `/claims/<id>/start-review/` | Start review |
| POST | `/claims/<id>/request-information/` | Ask the customer for more information |
| POST | `/claims/<id>/resume-review/` | Resume after information is received |
| POST | `/claims/<id>/approve/` | Approve |
| POST | `/claims/<id>/reject/` | Reject |
| POST | `/claims/<id>/start-settlement/` | Start settlement |
| POST | `/claims/<id>/settle/` | Record the settlement |
| POST | `/claims/<id>/close/` | Close the claim |
| GET | `/claims/<id>/events/` | Audit trail |
| GET | `/claims/<id>/requirements/` | Document requirements |
| GET | `/claims/<id>/settlement/` | Settlement detail |

### Documents

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/claims/<claim_id>/documents/` | List or upload claim documents |
| GET, DELETE | `/documents/<id>/` | Document detail |

### AI (`/ai/`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/ai/documents/<id>/process/` | Extract text, chunk and embed a document |
| GET | `/ai/documents/<id>/processing-jobs/` | Processing job history |
| GET | `/ai/documents/<id>/extraction/` | Extracted text |
| POST | `/ai/documents/<id>/chunks/` | Create chunks |
| GET | `/ai/documents/<id>/chunks/list/` | List chunks |
| POST | `/ai/documents/<id>/embeddings/` | Create embeddings |
| GET | `/ai/documents/<id>/visual-analysis/` | Vision analysis |
| POST | `/ai/search/` | Semantic search |
| POST | `/ai/rag/query/` | Question answering over documents |
| POST | `/ai/claims/<id>/summary/` | Generate the claim AI summary |
| GET | `/ai/claims/<id>/summary/detail/` | Read the saved summary |
| GET | `/ai/claims/<id>/missing-documents/` | Missing-document analysis |
| POST | `/ai/claims/<id>/inconsistencies/analyze/` | Run inconsistency analysis |
| GET | `/ai/claims/<id>/inconsistencies/` | Read inconsistencies |
| GET | `/ai/claims/<id>/intelligence/` | Combined AI view of a claim |
| POST | `/ai/claims/<id>/process/` | Run the complete AI workflow |

### Analytics (`/analytics/`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/analytics/snowflake/health/` | Snowflake connection check |
| GET | `/analytics/dashboard/` | Dashboard summary |
| GET | `/analytics/claims/overview/` | Overall claim metrics |
| GET | `/analytics/claims/by-type/` | Claims by type |
| GET | `/analytics/claims/by-status/` | Claims by status |
| GET | `/analytics/claims/monthly-trend/` | Monthly trend |
| GET | `/analytics/claims/by-policy-type/` | Claims by policy type |
| GET | `/analytics/claims/processing/` | Processing time metrics |
| GET | `/analytics/claims/settlement/` | Settlement metrics |
| GET | `/analytics/claims/ai/` | AI review metrics |
| GET | `/analytics/customers/claims/` | Claims per customer |

Errors are returned as JSON with a `detail` message.

## Claim workflow

Status changes are checked in [apps/claims/workflow.py](apps/claims/workflow.py). Any other transition is rejected.

```
SUBMITTED
   └─► DOCUMENT_PROCESSING
          └─► UNDER_REVIEW ◄──────────────┐
                 ├─► ADDITIONAL_INFO_REQUIRED ─┘
                 ├─► REJECTED  (final)
                 └─► APPROVED
                        └─► SETTLEMENT_IN_PROGRESS
                               └─► SETTLED
                                      └─► CLOSED  (final)
```

Each transition is recorded as a claim event.

## Roles and permissions

Roles: `CUSTOMER`, `CLAIMS_OFFICER`, `MANAGER`, `ADMIN` (defined in [apps/users/models.py](apps/users/models.py)). Permission classes such as `IsCustomer`, `IsClaimsOfficer`, `IsManager` and `IsAdmin` are in [apps/users/permissions.py](apps/users/permissions.py). The default for every endpoint is "authenticated user".

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `ImproperlyConfigured: Set the X environment variable` | A required variable is missing from `.env` |
| Cannot connect to PostgreSQL | Check the `POSTGRES_*` values and that the server is running |
| `TesseractNotFoundError` | Install Tesseract and set `TESSERACT_CMD` |
| S3 errors when uploading | Check the AWS keys, bucket name and region, and the bucket permissions |
| Snowflake load fails on a missing table | Create the `DIM_*` and `FACT_CLAIM` tables first (see [Snowflake analytics](#snowflake-analytics)) |
| `Unable to resolve CUSTOMER_KEY` during the incremental load | The related customer or policy has not reached Snowflake yet. Run `load_snowflake` once, or rerun the incremental load |
| Search returns nothing | The document has not been chunked and embedded yet. Run the document `process/` endpoint first |
| FAISS index seems stale or corrupt | Stop the app, delete `storage/faiss/claims.index`, and re-embed the documents |
