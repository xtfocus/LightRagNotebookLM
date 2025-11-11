
<p align="center">
    <em>Next.js FastAPI Template: Python + Modern TypeScript stack with Zod validation.</em>
</p>

---

# Next.js FastAPI Template

> **IMPORTANT: This project is designed to be developed and tested exclusively using Docker and Docker Compose. Running backend, frontend, or tests directly on your host machine is not supported. All commands and development should be performed inside Docker containers via Docker Compose or the provided Makefile targets.**


## Table of Contents
* [About](#about)
* [Production-Ready Authentication & Dashboard](#production-ready-authentication-and-dashboard)
* [Getting Started with This Template](#getting-started-with-this-template)
* [Setup](#docker-setup)
  * [Installing Required Tools](#installing-required-tools)
    * [1. Docker](#1-docker)
    * [2. Docker Compose](#2-docker-compose)
  * [Setting Up Environment Variables](#setting-up-environment-variables)
* [Running the Application](#running-the-application)
* [Hot Reload on development](#hot-reload-on-development)
* [Testing](#testing)
* [Email Localhost Setup](#email-localhost-setup)
* [Pre-Commit Setup](#pre-commit-setup)
* [Alembic Database Migrations](#alembic-database-migrations)
* [GitHub Actions](#github-actions)
* [Production Deployment](#production-deployment)
* [CI (GitHub Actions) Setup for Production Deployment](#ci-github-actions-setup-for-production-deployment)
* [Post-Deployment Configuration](#post-deployment-configuration)
* [Makefile](#makefile)
* [Important Considerations](#important-considerations)
* [Contributing](#contributing)
* [Share your project!](#share-your-project)
* [Commercial Support](#commercial-support)
* [Tech Stack Overview](#tech-stack-overview)
* [Service Access & URLs](#service-access-and-urls)
* [Development Workflow with Docker Compose Watch](#development-workflow-with-docker-compose-watch)

## About
This template streamlines building APIs with [FastAPI](https://fastapi.tiangolo.com/) and dynamic frontends with [Next.js](https://nextjs.org/). It integrates the backend and frontend using [@hey-api/openapi-ts](https://github.com/hey-api/openapi-ts) to generate a type-safe client, with automated watchers to keep the OpenAPI schema and client updated, ensuring a smooth and synchronized development workflow.  

- [Next.js](https://nextjs.org/): Fast, SEO-friendly frontend framework  
- [FastAPI](https://fastapi.tiangolo.com/): High-performance Python backend  
- [SQLAlchemy](https://www.sqlalchemy.org/): Powerful Python SQL toolkit and ORM
- [PostgreSQL](https://www.postgresql.org/): Advanced open-source relational database
- [Pydantic](https://docs.pydantic.dev/): Data validation and settings management using Python type annotations
- [Zod](https://zod.dev/) + [TypeScript](https://www.typescriptlang.org/): End-to-end type safety and schema validation  
- [fastapi-users](https://fastapi-users.github.io/fastapi-users/): Complete authentication system with:
  - Secure password hashing by default
  - JWT (JSON Web Token) authentication
  - Email-based password recovery
- [Shadcn/ui](https://ui.shadcn.com/): Beautiful and customizable React components
- [OpenAPI-fetch](https://github.com/Hey-AI/openapi-fetch): Fully typed client generation from OpenAPI schema  
- [fastapi-mail](https://sabuhish.github.io/fastapi-mail/): Efficient email handling for FastAPI applications
- [uv](https://docs.astral.sh/uv/): An extremely fast Python package and project manager
- [Pytest](https://docs.pytest.org/): Powerful Python testing framework
- Code Quality Tools:
  - [Ruff](https://github.com/astral-sh/ruff): Fast Python linter
  - [ESLint](https://eslint.org/): JavaScript/TypeScript code quality
- Hot reload watchers:  
  - Backend: No file watcher is currently used
  - Frontend: [Chokidar](https://github.com/paulmillr/chokidar) for live updates  
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/): Consistent environments for development and production
- [MailHog](https://github.com/mailhog/MailHog): Email server for development
- [Pre-commit hooks](https://pre-commit.com/): Enforce code quality with automated checks  
- [OpenAPI JSON schema](https://swagger.io/specification/): Centralized API documentation and client generation  

With this setup, you'll save time and maintain a seamless connection between your backend and frontend, boosting productivity and reliability.

## Setup (Docker Only)

### Installing Required Tools

#### 1. Docker
Docker is required to run the project. Follow the appropriate installation guide:
- [Install Docker for Mac](https://docs.docker.com/docker-for-mac/install/)
- [Install Docker for Windows](https://docs.docker.com/docker-for-windows/install/)
- [Get Docker CE for Linux](https://docs.docker.com/install/linux/docker-ce/)

#### 2. Docker Compose
Ensure `docker-compose` is installed. Refer to the [Docker Compose installation guide](https://docs.docker.com/compose/install/).

### Setting Up Environment Variables

**Backend (`fastapi_backend/.env`):**
Copy the `.env.example` file to `.env` and update the variables with your own values.
   ```bash
   cd fastapi_backend && cp .env.example .env
   ```
1. Update the secret keys as needed. Generate a new secret key with:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
2. The DATABASE, MAIL, OPENAPI, CORS, and FRONTEND_URL settings are ready to use locally with Docker Compose.
3. The DATABASE and MAIL settings are already configured in Docker Compose.
4. The OPENAPI_URL setting is commented out. Uncommenting it will hide the /docs and openapi.json URLs, which is ideal for production.
5. See `.env.example` for more information about the variables.

**Frontend (`nextjs-frontend/.env.local`):**
Copy the `.env.example` file to `.env`. These values are unlikely to change, so you can leave them as they are.
   ```bash
   cd nextjs-frontend && cp .env.example .env
   ```

### Environment Configuration

This project now supports comprehensive environment variable configuration for all services. Copy the root-level `env.example` file to `.env` in the project root:

```bash
cp env.example .env
```

**Key Configuration Areas:**

1. **Service Ports**: All service ports are now configurable via environment variables:
   - `BACKEND_PORT`, `FRONTEND_PORT`, `AGENT_PORT`
   - `MINIO_API_PORT`, `MINIO_WEB_PORT`
   - `MAILHOG_SMTP_PORT`, `MAILHOG_WEB_PORT`
   - `POSTGRES_PORT`, `LANGGRAPHDB_PORT`

2. **Security**: MinIO credentials are now configurable:
   - `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
   - Default values should be changed in production

3. **API Configuration**: API prefixes and URLs are configurable:
   - `BACKEND_API_PREFIX`, `AGENT_API_PREFIX`
   - `NEXT_PUBLIC_API_URL`, `AGENT_URL`

4. **Database Configuration**: All database settings are environment-driven:
   - `POSTGRES_*` variables for main database
   - `LANGGRAPHDB_*` variables for agent database

**Security Notes:**
- Change default credentials in production environments
- Use strong passwords for database and MinIO access
- Consider using secrets management for sensitive values

## Running the Application

Start the core stack (ELK excluded by default via profiles):
```bash
docker compose up --build
```
Or use the Makefile for common tasks:
    ```bash
make docker-up
    ```

- **Backend**: Access the API at `http://localhost:${BACKEND_PORT:-8000}`.
- **Frontend**: Access the web application at `http://localhost:${FRONTEND_PORT:-3000}`.

### Optional: Start ELK (Logging & Monitoring)

- One-time setup (creates users/roles, starts ELK, verifies):
```bash
./scripts/setup_elk_stack.sh
```

- Daily with ELK enabled:
```bash
docker compose --profile elk up -d
```

- Verify health:
```bash
./scripts/verify_elk_stack.sh
```

## Development Workflow & API Configuration

This project uses a containerized development environment with shared volumes and environment variables. Understanding this workflow is crucial for effective development.

### Containerized Development Environment

**Key Principle:** Always work within containers for API-related tasks and environment-dependent operations.

**Why Containers?**
- Environment variables are properly configured in containers
- Volume mounts provide shared access to files (like OpenAPI schemas)
- Consistent development environment across team members
- Isolated dependencies and configurations

### Volume Mappings

The project uses several volume mappings for shared data:

```yaml
# Frontend container
volumes:
  - ./nextjs-frontend:/app                    # Source code
  - ./local-shared-data:/app/shared-data     # OpenAPI schema
  - nextjs-node-modules:/app/node_modules    # Dependencies

# Backend container  
volumes:
  - ./local-shared-data:/app/shared-data     # OpenAPI schema
  - fastapi-venv:/app/.venv                  # Python dependencies
```

### API Configuration System

The project uses a centralized API configuration system:

**Backend (`fastapi_backend`):**
- Uses `BACKEND_API_PREFIX` environment variable (default: `/api/v1`)
- All API routes are prefixed with this value
- Test files use `settings.BACKEND_API_PREFIX` for dynamic URLs

**Frontend (`nextjs-frontend`):**
- Uses `lib/apiConfig.ts` for centralized configuration
- Environment variables: `NEXT_PUBLIC_BACKEND_API_PREFIX`, `NEXT_PUBLIC_AGENT_API_PREFIX`
- Helper functions: `buildBackendUrl()`, `buildAgentUrl()`

### Backend-Frontend Synchronization

**Automated Process (Recommended):**

When making API changes, use the automated Makefile targets:

```bash
# For normal API changes
make sync-api-client

# For major backend changes (restarts backend)
make sync-api-client-force

# Generate client and clean up containers afterward
make sync-api-client-clean
```

**Manual Process (if needed):**

1. **Update Backend:**
   ```bash
   # Make your backend changes
   # Restart backend to apply changes
   docker compose up backend -d
   ```

2. **Verify Backend Health:**
   ```bash
   # Check if backend is responding
   curl http://localhost:8000/api/v1/utils/health-check/
   ```

3. **Regenerate OpenAPI Schema:**
   ```bash
   # Download fresh schema from backend
   curl -s http://localhost:8000/api/v1/openapi.json > local-shared-data/openapi.json
   ```

4. **Regenerate Frontend Client:**
   ```bash
   # Generate client from within frontend container
   docker compose exec frontend pnpm generate-client
   ```

5. **Update Frontend Code:**
   ```typescript
   // Use helper functions instead of hardcoded paths
   import { buildBackendUrl } from "@/lib/apiConfig";
   const url = buildBackendUrl("users/me");
   ```

### Common Development Issues & Solutions

**Problem:** OpenAPI client generation fails locally
```bash
# ❌ Don't do this
pnpm generate-client

# ✅ Do this instead
docker compose exec frontend pnpm generate-client
```

**Problem:** Environment variables not working
```bash
# Check if variables are set in docker-compose.yml
# Restart containers after changing environment variables
docker compose down && docker compose up -d
```

**Problem:** Volume mounts not working
```bash
# Check volume mappings in docker-compose.yml
# Ensure shared directories exist
ls -la local-shared-data/
```

**Problem:** Backend changes not reflected in frontend
```bash
# Follow the synchronization process above
# Always regenerate client after backend changes
```

**Problem:** Containers left running after development
```bash
# Use make targets for cleanup
make docker-clean          # Stop and remove containers
make docker-clean-all      # Complete cleanup (including images)
make sync-api-client-clean # Generate client and clean up automatically
```

### Environment Variables Management

**Backend Environment Variables:**
- Set in `docker-compose.yml` under backend service
- Include `BACKEND_API_PREFIX` for API prefix configuration
- Use `.env` file for sensitive data

**Frontend Environment Variables:**
- Set in `docker-compose.yml` under frontend service
- Use `NEXT_PUBLIC_*` prefix for client-side variables
- Include API prefix variables for configuration

### Best Practices

1. **Always use containers** for API-related tasks
2. **Use helper functions** instead of hardcoded paths
3. **Regenerate client** after any backend API changes
4. **Test incrementally** after each synchronization step
5. **Check environment variables** in docker-compose.yml first
6. **Use volume mounts** for shared data between services
7. **Follow the synchronization process** for API changes

### Hot Reload on Development

Hot reload is enabled by default in the Docker containers for both backend and frontend. Any code changes will automatically trigger reloads.

## Testing

All tests must be run inside Docker containers. Do not run tests directly on your host machine.

To run the test database container:
   ```bash
   make docker-up-test-db
   ```

Then run the tests:
   ```bash
   make docker-test-backend
   make docker-test-frontend
   ```

## Pre-Commit Setup

Pre-commit checks must be run inside Docker containers. Use the provided Makefile targets or run pre-commit inside the appropriate container.

To manually run the pre-commit checks on all files, use:
```bash
make docker-pre-commit
```

## Alembic Database Migrations
If you need to create a new Database Migration:
   ```bash
   make docker-db-schema migration_name="add users"
   ```
then apply the migration to the database:
   ```bash
   make docker-migrate-db
   ```

## GitHub Actions
This project has a pre-configured GitHub Actions setup to enable CI/CD. The workflow configuration files are inside the .github/workflows directory. You can customize these workflows to suit your project's needs better.

### Secrets Configuration
For the workflows to function correctly, add the secret keys to your GitHub repository's settings. Navigate to Settings > Secrets and variables > Actions and add the following keys:
```
DATABASE_URL: The connection string for your primary database.
TEST_DATABASE_URL: The connection string for your test database.
ACCESS_SECRET_KEY: The secret key for access token generation.
RESET_PASSWORD_SECRET_KEY: The secret key for reset password functionality.
VERIFICATION_SECRET_KEY: The secret key for email or user verification.
```

## Production Deployment

### Overview

 Deploying to **Vercel** is supported, with dedicated buttons for the **Frontend** and **Backend** applications. Both require specific configurations during and after deployment to ensure proper functionality.

---

### Frontend Deployment

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvintasoftware%2Fnextjs-fastapi-template%2Ftree%2Fmain%2Fnextjs-frontend&env=API_BASE_URL&envDescription=The%20API_BASE_URL%20is%20the%20backend%20URL%20where%20the%20frontend%20sends%20requests.)

1. **Deploying the Frontend**  
   - Click the **Frontend** button above to start the deployment process.  
   - During deployment, you will be prompted to set the `API_BASE_URL`. Use a placeholder value (e.g., `https://`) for now, as this will be updated with the backend URL later.  
   - Complete the deployment process [here](#post-deployment-configuration).

### Backend Deployment

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvintasoftware%2Fnextjs-fastapi-template%2Ftree%2Fmain%2Ffastapi_backend&env=CORS_ORIGINS,ACCESS_SECRET_KEY,RESET_PASSWORD_SECRET_KEY,VERIFICATION_SECRET_KEY&stores=%5B%7B%22type%22%3A%22postgres%22%7D%5D)

1. **Deploying the Backend**  
   - Click the **Backend** button above to begin deployment.
   - First, set up the database. The connection is automatically configured, so follow the steps, and it should work by default.
   - During the deployment process, you will be prompted to configure the following environment variables:

     - **CORS_ORIGINS**  
       - Set this to `["*"]` initially to allow all origins. Later, you can update this with the frontend URL.

     - **ACCESS_SECRET_KEY**, **RESET_PASSWORD_SECRET_KEY**, **VERIFICATION_SECRET_KEY**  
       - During deployment, you can temporarily set these secret keys as plain strings (e.g., `examplekey`). However, you should generate secure keys and update them after the deployment in the **Post-Deployment Configuration** section.

   - Complete the deployment process [here](#post-deployment-configuration).


## CI (GitHub Actions) Setup for Production Deployment

We provide the **prod-backend-deploy.yml** and **prod-frontend-deploy.yml** files to enable continuous integration through Github Actions. To connect them to GitHub, simply move them to the .github/workflows/ directory.

You can do it with the following commands:
   ```bash
    mv prod-backend-deploy.yml .github/workflows/prod-backend-deploy.yml
    mv prod-frontend-deploy.yml .github/workflows/prod-frontend-deploy.yml
   ```

### Prerequisites
1. **Create a Vercel Token**:  
   - Generate your [Vercel Access Token](https://vercel.com/account/tokens).  
   - Save the token as `VERCEL_TOKEN` in your GitHub secrets.

2. **Install Vercel CLI**:  
   ```bash
   pnpm i -g vercel@latest
   ```
3. Authenticate your account.
    ```bash
   vercel login
   ```
### Database Creation (Required)

   1. **Choosing a Database**
      - You can use your database hosted on a different service or opt for the [Neon](https://neon.tech/docs/introduction) database, which integrates seamlessly with Vercel.

   2. **Setting Up a Neon Database via Vercel**
      - In the **Projects dashboard** page on Vercel, navigate to the **Storage** section.  
      - Select the option to **Create a Database** to provision a Neon database.

   3. **Configuring the Database URL**
      - After creating the database, retrieve the **Database URL** provided by Neon.  
      - Include this URL in your **Environment Variables** under `DATABASE_URL`.  

   4. **Migrating the Database**
      - The database migration will happen automatically during the GitHub action deployment, setting up the necessary tables and schema.
### Frontend Setup

1. Link the nextjs-frontend Project

2. Navigate to the nextjs-frontend directory and run:
   ```bash
   cd nextjs-frontend
   vercel link
   ```
3. Follow the prompts:
   - Link to existing project? No
   - Modify settings? No

4. Save Project IDs and Add GitHub Secrets:
  - Open `nextjs-frontend/.vercel/project.json` and add the following to your GitHub repository secrets:
    - `projectId` → `VERCEL_PROJECT_ID_FRONTEND`
    - `orgId` → `VERCEL_ORG_ID`

### Backend Setup

1. Link the fastapi_backend Project

2. Navigate to the fastapi_backend directory and run:
   ```bash
   cd fastapi_backend
   vercel link --local-config=vercel.prod.json
   ```
   - We use a specific configuration file to set the --local-config value.
3. Follow the prompts:
   - Link to existing project? No
   - Modify settings? No

4. Save Project IDs and Add GitHub Secrets:
  - Open `fastapi_backend/.vercel/project.json` and add the following to your GitHub repository secrets:
    - `projectId` → `VERCEL_PROJECT_ID_BACKEND`
    - `orgId` → `VERCEL_ORG_ID` (Only in case you haven't added that before)

### Notes
- Once everything is set up, run `git push`, and the deployment will automatically occur.
- Please ensure you complete the setup for both the frontend and backend separately.
- Refer to the [Vercel CLI Documentation](https://vercel.com/docs/cli) for more details.
- You can find the project_id in the vercel web project settings.
- You can find the organization_id in the vercel web organization settings.

## **Post-Deployment Configuration**

### Frontend
   - Navigate to the **Settings** page of the deployed frontend project.  
   - Access the **Environment Variables** section.  
   - Update the `API_BASE_URL` variable with the backend URL once the backend deployment is complete.

### Backend
   - Access the **Settings** page of the deployed backend project.  
   - Navigate to the **Environment Variables** section and update the following variables with secure values:

     - **CORS_ORIGINS**  
       - Once the frontend is deployed, replace `["*"]` with the actual frontend URL.

     - **ACCESS_SECRET_KEY**  
       - Generate a secure key for API access and set it here.  

     - **RESET_PASSWORD_SECRET_KEY**
       - Generate a secure key for password reset functionality and set it.

     - **VERIFICATION_SECRET_KEY**  
       - Generate a secure key for user verification and configure it.

   - For detailed instructions on setting these secret keys, please look at the section on [Setting up Environment Variables](#setting-up-environment-variables).

### Fluid Serverless Activation
[Fluid](https://vercel.com/docs/functions/fluid-compute) is Vercel's new concurrency model for serverless functions, allowing them to handle multiple 
requests per execution instead of spinning up a new instance for each request. This improves performance, 
reduces cold starts, and optimizes resource usage, making serverless workloads more efficient.

Follow this [guide](https://vercel.com/docs/functions/fluid-compute#how-to-enable-fluid-compute) to activate Fluid.

## Makefile

This project includes a `Makefile` that provides a set of commands to simplify everyday tasks such as starting the backend and frontend servers, running tests, building Docker containers, and more.

### Available Commands

You can see all available commands and their descriptions by running the following command in your terminal:

```bash
make help
```

## Important Considerations
- **Docker-Only Development**: All development, testing, and code quality checks must be performed using Docker and Docker Compose. Running backend, frontend, or tests directly on your host machine is not supported.
- **Environment Variables**: Ensure your `.env` files are up-to-date.
- **Database Setup**: The database runs in Docker. Do not attempt to run a local database on your host for this project.
- **Consistency**: Do not switch between Docker and local host development. Use Docker exclusively to avoid permission issues or unexpected problems.

## Tech Stack Overview

- **Frontend:** Next.js (React, TypeScript, Tailwind CSS)
- **Backend:** FastAPI (Python 3.10+), async/await, SQLModel (async), Alembic
- **Database:** PostgreSQL (Dockerized)
- **ORM:** SQLModel (async, built on SQLAlchemy)
- **Authentication:** OAuth2/JWT, password hashing, registration, login, password reset
- **Object Storage:** MinIO (S3-compatible, Dockerized)
- **Email Testing:** MailHog (Dockerized)
- **API Client:** Auto-generated OpenAPI client for frontend
- **Dev Environment:** Docker Compose, Makefile, .env config
- **Testing:** Pytest, async test support
- **Code Quality:** Ruff, ESLint, Pre-commit hooks

## Service Access & URLs

| Service    | URL/Port                | Description                        |
|------------|-------------------------|------------------------------------|
| Frontend   | http://localhost:${FRONTEND_PORT:-3000}   | Next.js web app                    |
| Backend    | http://localhost:${BACKEND_PORT:-8000}   | FastAPI API                        |
| MinIO      | http://localhost:${MINIO_WEB_PORT:-9001}   | MinIO Web UI (configurable credentials)      |
| MinIO API  | http://localhost:${MINIO_API_PORT:-9000}   | S3-compatible API endpoint         |
| MailHog    | http://localhost:${MAILHOG_WEB_PORT:-8025}   | Email testing web UI               |
| MailHog SMTP | localhost:${MAILHOG_SMTP_PORT:-1025}        | SMTP server for backend email      |
| Agent API  | http://localhost:${AGENT_PORT:-8200}   | LLM/AI agent FastAPI service       |
| Postgres   | localhost:${POSTGRES_PORT:-5432}          | Main DB (backend)                  |
| LangGraph DB | localhost:${LANGGRAPHDB_PORT:-5433}        | Agent DB (LLM workflows)           |

### MinIO Usage
- MinIO is an S3-compatible object storage service running in Docker.
- Access the MinIO web UI at [http://localhost:${MINIO_WEB_PORT:-9001}](http://localhost:${MINIO_WEB_PORT:-9001}) (credentials configurable via environment variables).
- Use the web UI to browse, upload, or manage files/buckets.
- The backend is pre-configured to use MinIO for document storage.
- **Security Note**: Default credentials should be changed in production. Set `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` environment variables.

## Development Workflow with Docker Compose Watch

This project uses Docker Compose's [watch feature](https://docs.docker.com/compose/watch/) for a seamless development experience.

- When you run `docker compose up`, your local code changes in `nextjs-frontend` are automatically synced into the running container.
- The Next.js dev server (`pnpm dev`) inside the container detects these changes and hot reloads the app in your browser.
- No need to manually rebuild or restart the container for most code changes.

**Production:**
In production, the watch feature and volume mounts are disabled. The container runs the production build (`next start`) for maximum performance and reliability.



## Summary of Fixes Applied to Resolve the Original 404 Registration Error

### **Original Problem**
The user encountered a `404 Not Found` error when trying to register a user via Docker Compose. The frontend was making a POST request to `/register`, but the backend was returning a 404 for `/auth/register`.

### **Root Cause Analysis**
1. **Backend Endpoint Mismatch**: The backend's actual registration endpoint was `/api/v1/users/signup`, but the frontend's auto-generated OpenAPI client was hardcoded to use `/auth/register`.

2. **OpenAPI Client Generation Issue**: The frontend was using an outdated auto-generated TypeScript client that didn't match the current backend API specification.

### **Solution Steps**

#### **1. Identified the Correct Backend Endpoint**
- Examined `fastapi_backend/app/api/routes/users.py` and confirmed the registration endpoint is `/api/v1/users/signup`

#### **2. Regenerated the OpenAPI Client**
- Located the OpenAPI specification file at `local-shared-data/openapi.json`
- Regenerated the frontend client using the correct path: `pnpm openapi-ts`
- This updated the client to use the correct function names and endpoint URLs

#### **3. Updated Frontend Code to Match New Client**
The regenerated client introduced new function names and data structures, requiring updates to:

**Actions:**
- `register-action.ts`: Changed from `registerRegister` to `usersRegisterUser`
- `login-action.ts`: Changed from `authJwtLogin` to `loginLoginAccessToken`
- `items-action.ts`: Updated to use `itemsReadItems`, `itemsDeleteItem`, `itemsCreateItem` and changed data structure from `name`/`quantity` to `title`/`description`
- `password-reset-action.ts`: Changed from `resetForgotPassword`/`resetResetPassword` to `loginRecoverPassword`/`loginResetPassword` and updated parameter structures
- `logout-action.ts`: Removed API call since no logout endpoint exists in the API

**Data Structures:**
- `lib/definitions.ts`: Updated `itemSchema` to use `title` instead of `name` and removed `quantity`
- `lib/utils.ts`: Updated error type imports to match new client

**Pages:**
- `app/items/page.tsx`: Updated to handle `ItemsReadItemsResponse` structure and display `item.title` instead of `item.name`

**Middleware:**
- `middleware.ts`: Changed from `usersCurrentUser` to `usersReadUserMe`

**Tests:**
- `__tests__/register.test.ts`: Updated all references from `registerRegister` to `usersRegisterUser`
- `__tests__/login.test.tsx`: Updated all references from `authJwtLogin` to `loginLoginAccessToken`
- `__tests__/passwordReset.test.tsx`: Updated all references from `resetForgotPassword` to `loginRecoverPassword` and corrected parameter structure
- `__tests__/passwordResetConfirm.test.tsx`: Updated all references from `resetResetPassword` to `loginResetPassword` and corrected parameter structure

### **Key Technical Changes**

1. **Function Name Updates:**
   - `registerRegister` → `usersRegisterUser`
   - `authJwtLogin` → `loginLoginAccessToken`
   - `readItem` → `itemsReadItems`
   - `createItem` → `itemsCreateItem`
   - `deleteItem` → `itemsDeleteItem`
   - `resetForgotPassword` → `loginRecoverPassword`
   - `resetResetPassword` → `loginResetPassword`
   - `usersCurrentUser` → `usersReadUserMe`

2. **Data Structure Updates:**
   - Item creation: `name` → `title`, removed `quantity`
   - Password reset: `password` → `new_password`
   - API responses: Updated to handle new response structures

3. **Parameter Structure Updates:**
   - Password recovery: `body` → `path` for email parameter
   - Item deletion: `item_id` → `id` in path parameters

### **Result**
The registration functionality now works correctly:
- Frontend calls the correct endpoint (`/api/v1/users/signup`)
- All related functionality (login, items management, password reset) has been updated to use the correct API endpoints and data structures
- Test files have been updated to match the new client interface
- The Docker Compose setup is now fully functional

The original 404 error has been completely resolved, and the entire application stack is now properly synchronized between frontend and backend.

