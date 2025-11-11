# Version Control & Docker Compose Organization Guide

## Version Control Strategy

### Recommended Approach: Keep as Regular Directory ✅

Since you plan to **customize LightRAG internally**, keeping it as a regular directory is the best approach:

**Why Keep as Directory?**
- ✅ Full control over modifications
- ✅ No submodule complexity
- ✅ Easy to make internal changes
- ✅ All code in one repository
- ✅ Simpler git workflow

**Setup:**

1. **Ensure LightRAG is tracked in your repo**:
```bash
# If LightRAG has its own .git, remove it
rm -rf LightRAG/.git

# Add LightRAG to your repo
git add LightRAG/
git commit -m "feat: Add LightRAG with customizations"
```

2. **Configure .gitignore** (exclude data, not source):
```gitignore
# LightRAG data directories (don't commit)
LightRAG/data/
LightRAG/rag_storage/
LightRAG/*.log
LightRAG/__pycache__/
LightRAG/**/__pycache__/
LightRAG/.env
LightRAG/config.ini

# But keep source code
!LightRAG/lightrag/
!LightRAG/pyproject.toml
!LightRAG/README.md
!LightRAG/Dockerfile
```

3. **Track your customizations**:
   - Make changes directly in `LightRAG/` directory
   - Commit changes as part of your main repo
   - Use clear commit messages: `feat(lightrag): Add URL endpoint`

**Updating from Upstream (Optional):**
If you want to pull updates from upstream LightRAG:
```bash
# Add upstream as remote (one-time)
cd LightRAG
git remote add upstream https://github.com/Distillative-AI/LightRAG.git

# Fetch updates
git fetch upstream

# Merge specific updates (be careful with conflicts)
git merge upstream/main

# Or cherry-pick specific commits
git cherry-pick <commit-hash>
```

**Note**: Since you're customizing internally, you may not need upstream updates. Your fork becomes the source of truth.

### Recommended Structure

```
your-repo/
├── docker-compose.yml        # Main app orchestration with profiles
├── fastapi_backend/
├── nextjs-frontend/
├── LightRAG/                 # Regular directory (customized)
│   ├── lightrag/
│   │   └── api/
│   │       └── routers/
│   │           └── document_routes.py  # Your URL endpoint modifications
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── ...
├── .gitignore               # Excludes LightRAG data directories
└── README.md
```

---

## Docker Compose Organization

### Option 1: Single File with Profiles (Recommended) ✅

**Best for**: Development, simplicity, shared services

**Structure:**
```yaml
# docker-compose.yml
services:
  # Shared infrastructure
  db:
    # ... PostgreSQL config
  qdrant:
    # ... Qdrant config (shared by both)
  
  # Main app services
  backend:
    profiles: ["app"]  # Only start with --profile app
    # ...
  frontend:
    profiles: ["app"]
    # ...
  
  # LightRAG service
  lightrag:
    profiles: ["lightrag"]  # Only start with --profile lightrag
    # ...
```

**Usage:**
```bash
# Start everything
docker compose --profile app --profile lightrag up -d

# Start only app services
docker compose --profile app up -d

# Start only LightRAG (for testing)
docker compose --profile lightrag up -d

# Start shared services + app
docker compose up -d db qdrant && docker compose --profile app up -d
```

**Pros:**
- ✅ Single file to manage
- ✅ Shared services (db, qdrant) always available
- ✅ Easy to start/stop different components
- ✅ Clear separation via profiles

**Cons:**
- ⚠️ Slightly more complex commands

### Option 2: Separate Compose Files (Alternative)

**Best for**: Complete separation, different environments

**Structure:**
```
docker-compose.yml          # Main app services
docker-compose.lightrag.yml # LightRAG service
docker-compose.shared.yml   # Shared services (db, qdrant)
```

**docker-compose.yml** (Main app):
```yaml
services:
  backend:
    # ...
  frontend:
    # ...
  # Reference shared services
  db:
    extends:
      file: docker-compose.shared.yml
      service: db
  qdrant:
    extends:
      file: docker-compose.shared.yml
      service: qdrant
```

**docker-compose.lightrag.yml** (LightRAG):
```yaml
services:
  lightrag:
    # ...
  # Reference shared services
  qdrant:
    extends:
      file: docker-compose.shared.yml
      service: qdrant
```

**Usage:**
```bash
# Start shared services
docker compose -f docker-compose.shared.yml up -d

# Start main app
docker compose up -d

# Start LightRAG
docker compose -f docker-compose.lightrag.yml up -d

# Start everything
docker compose -f docker-compose.shared.yml up -d
docker compose up -d
docker compose -f docker-compose.lightrag.yml up -d
```

**Pros:**
- ✅ Complete separation
- ✅ Can deploy independently
- ✅ Clear file organization

**Cons:**
- ⚠️ More files to manage
- ⚠️ More complex commands
- ⚠️ Need to coordinate shared services

### Option 3: Single Unified File (Simplest)

**Best for**: Small projects, everything always runs together

**Structure:**
```yaml
# docker-compose.yml - everything in one file
services:
  db:
    # ...
  qdrant:
    # ...
  backend:
    # ...
  frontend:
    # ...
  lightrag:
    # ...
```

**Usage:**
```bash
# Start everything
docker compose up -d

# Start specific services
docker compose up -d db qdrant backend
```

**Pros:**
- ✅ Simplest approach
- ✅ One command to rule them all

**Cons:**
- ⚠️ Can't easily separate concerns
- ⚠️ Harder to deploy independently

---

## Recommended Setup: Profiles Approach

### Implementation

**docker-compose.yml:**
```yaml
services:
  # ============================================
  # Shared Infrastructure (No Profile)
  # ============================================
  db:
    image: postgres:17
    # ... existing config
    # No profile - always available

  qdrant:
    image: qdrant/qdrant:latest
    # ... existing config
    # No profile - always available (shared by app and LightRAG)

  # ============================================
  # Main Application Services (Profile: app)
  # ============================================
  prestart:
    profiles: ["app"]
    # ... existing config

  backend:
    profiles: ["app"]
    depends_on:
      - db
      - qdrant
    # ... existing config

  frontend:
    profiles: ["app"]
    # ... existing config

  agent:
    profiles: ["app"]
    # ... existing config

  indexing-worker:
    profiles: ["app"]  # Will be removed after migration
    # ... existing config

  kafka:
    profiles: ["app"]  # Will be removed after migration
    # ... existing config

  kafka-ui:
    profiles: ["app"]  # Will be removed after migration
    # ... existing config

  minio:
    profiles: ["app"]
    # ... existing config

  mailhog:
    profiles: ["app"]
    # ... existing config

  # ============================================
  # LightRAG Service (Profile: lightrag)
  # ============================================
  lightrag:
    profiles: ["lightrag"]
    build:
      context: ./LightRAG
      dockerfile: Dockerfile
    ports:
      - "${LIGHTRAG_PORT:-8001}:9621"
    environment:
      - HOST=0.0.0.0
      - PORT=9621
      - LIGHTRAG_WORKING_DIR=/app/data/rag_storage
      - LIGHTRAG_INPUT_DIR=/app/data/inputs
      - QDRANT_URL=http://qdrant:6333
      - QDRANT_API_KEY=${QDRANT_API_KEY:-}
      - LIGHTRAG_VECTOR_STORAGE=QdrantVectorDBStorage
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLM_BINDING=openai
      - LLM_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
      - EMBEDDING_BINDING=openai
      - EMBEDDING_MODEL=${OPENAI_MODEL:-text-embedding-3-small}
      - EMBEDDING_DIM=${OPENAI_EMBEDDING_DIMENSION:-1536}
      # Add other LightRAG configs...
    volumes:
      - lightrag_working:/app/data/rag_storage
      - lightrag_input:/app/data/inputs
      - ./LightRAG/config.ini:/app/config.ini:ro
      - ./LightRAG/.env:/app/.env:ro
    networks:
      - my_network
    depends_on:
      qdrant:
        condition: service_healthy
    restart: unless-stopped

volumes:
  # ... existing volumes
  lightrag_working:
  lightrag_input:

networks:
  my_network:
    driver: bridge
```

### Usage Examples

```bash
# Development: Start everything
docker compose --profile app --profile lightrag up -d

# Production: Start only app (LightRAG on separate server)
docker compose --profile app up -d

# Testing: Start only LightRAG + shared services
docker compose up -d db qdrant
docker compose --profile lightrag up -d

# Stop specific profiles
docker compose --profile app down
docker compose --profile lightrag down

# View logs
docker compose --profile app logs -f
docker compose --profile lightrag logs -f
```

### Makefile Integration

Add to your `Makefile`:
```makefile
.PHONY: up up-app up-lightrag up-all down

# Start everything
up-all:
	docker compose --profile app --profile lightrag up -d

# Start only app services
up-app:
	docker compose --profile app up -d

# Start only LightRAG
up-lightrag:
	docker compose up -d db qdrant
	docker compose --profile lightrag up -d

# Start shared services
up-shared:
	docker compose up -d db qdrant

# Stop everything
down:
	docker compose --profile app --profile lightrag down

# Stop app only
down-app:
	docker compose --profile app down

# Stop LightRAG only
down-lightrag:
	docker compose --profile lightrag down
```

---

## Git Workflow for LightRAG Modifications

### Simple Workflow (Regular Directory):

```bash
# 1. Make changes in LightRAG directory
cd LightRAG/lightrag/api/routers
# ... edit document_routes.py to add URL endpoint ...

# 2. Commit changes as part of main repo
cd ../../../../  # Back to repo root
git add LightRAG/
git commit -m "feat(lightrag): Add URL endpoint to document routes"
git push

# That's it! Simple and straightforward.
```

### Best Practices:

1. **Use conventional commits** for LightRAG changes:
   - `feat(lightrag): Add URL endpoint`
   - `fix(lightrag): Fix URL extraction timeout`
   - `refactor(lightrag): Improve document processing`

2. **Document customizations** in `LightRAG/CUSTOMIZATIONS.md`:
   ```markdown
   # LightRAG Customizations
   
   ## Modified Files
   - `lightrag/api/routers/document_routes.py` - Added `/documents/url` endpoint
   
   ## Custom Features
   - URL content extraction using markitdown
   - Background processing for async URL fetching
   ```

3. **Keep upstream reference** (optional, for reference only):
   ```bash
   # Add upstream remote for reference (don't push to it)
   cd LightRAG
   git remote add upstream https://github.com/Distillative-AI/LightRAG.git
   git remote set-url --push upstream DISABLED  # Prevent accidental pushes
   ```

---

## .gitignore Recommendations

Add to `.gitignore`:
```gitignore
# LightRAG data directories (don't commit runtime data)
LightRAG/data/
LightRAG/rag_storage/
LightRAG/*.log
LightRAG/__pycache__/
LightRAG/**/__pycache__/
LightRAG/.env
LightRAG/config.ini
LightRAG/*.pyc
LightRAG/**/*.pyc

# But keep LightRAG source code
!LightRAG/lightrag/
!LightRAG/pyproject.toml
!LightRAG/README.md
!LightRAG/Dockerfile
!LightRAG/setup.py
!LightRAG/MANIFEST.in
```

---

## Summary & Recommendation

### Version Control: ✅ Regular Directory (Customized)
- Keep LightRAG as regular directory in your repo
- Track all customizations directly
- Simple git workflow - just commit changes
- No submodule complexity
- Full control over modifications

### Docker Compose: ✅ Single File with Profiles
- Use `docker-compose.yml` with profiles
- Shared services (db, qdrant) have no profile (always available)
- App services use `profile: ["app"]`
- LightRAG uses `profile: ["lightrag"]`
- Easy to start/stop independently
- Simple commands with Makefile helpers

This approach gives you:
- ✅ Clean separation of concerns
- ✅ Easy deployment flexibility
- ✅ Shared infrastructure (Qdrant)
- ✅ Simple commands
- ✅ Version control clarity

