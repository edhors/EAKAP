# SpiceDB + PostgreSQL one-shot setup (Docker)

This guide sets up SpiceDB with a Postgres datastore on a single host (e.g. a cloud VM) so that migrations run automatically and the server is ready to use.

## Prerequisites

- Docker
- If clients connect from another machine: open **TCP port 50051** (gRPC) in the host firewall / cloud security group (e.g. Oracle Cloud ingress rule: protocol TCP, destination port 50051, source as needed).

---

## Option A: Sequential commands (copy-paste one-shot)

Run these in order. The `until` loop waits for Postgres to be ready before running migrations.

```bash
# 1. Create network
docker network create spicedb-net

# 2. Start Postgres
docker run -d \
  --name spicedb-postgres \
  --network spicedb-net \
  -e POSTGRES_DB=spicedb \
  -e POSTGRES_USER=spicedb \
  -e POSTGRES_PASSWORD=spicedb \
  -v spicedb_pgdata:/var/lib/postgresql/data \
  --memory="512m" \
  --restart unless-stopped \
  postgres:15

# 3. Wait for Postgres to accept connections (required before migrate)
until docker exec spicedb-postgres pg_isready -U spicedb; do
  echo "Waiting for Postgres..."
  sleep 2
done

# 4. Run datastore migrations (creates tables; required before SpiceDB can serve)
docker run --rm \
  --network spicedb-net \
  authzed/spicedb datastore migrate head \
  --datastore-engine postgres \
  --datastore-conn-uri "postgres://spicedb:spicedb@spicedb-postgres:5432/spicedb?sslmode=disable"

# 5. Start SpiceDB
docker run -d \
  --name spicedb \
  --network spicedb-net \
  -p 50051:50051 \
  -p 8443:8443 \
  --memory="512m" \
  --restart unless-stopped \
  authzed/spicedb serve \
  --http-enabled \
  --grpc-preshared-key "test" \
  --datastore-engine postgres \
  --datastore-conn-uri "postgres://spicedb:spicedb@spicedb-postgres:5432/spicedb?sslmode=disable"
```

After step 5, SpiceDB is listening on:

- **gRPC:** `localhost:50051` (or `YOUR_VM_IP:50051` from another machine if the firewall allows it)
- **HTTP:** `localhost:8443`

Use preshared key `test` in your client (e.g. `InsecureClient("host:50051", "test")`).

---

## Option B: Docker Compose (recommended for repeatable setup)

Compose can start Postgres, wait for it to be healthy, then start SpiceDB. Migrations still need to be run once; the `migrate` service runs once and exits, and `spicedb` starts only after Postgres is healthy.

Save as `docker-compose.yml`:

```yaml
services:
  spicedb-postgres:
    image: postgres:15
    container_name: spicedb-postgres
    environment:
      POSTGRES_DB: spicedb
      POSTGRES_USER: spicedb
      POSTGRES_PASSWORD: spicedb
    volumes:
      - spicedb_pgdata:/var/lib/postgresql/data
    networks:
      - spicedb-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U spicedb"]
      interval: 2s
      timeout: 5s
      retries: 10
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

  spicedb-migrate:
    image: authzed/spicedb
    container_name: spicedb-migrate
    command: datastore migrate head
    networks:
      - spicedb-net
    environment:
      SPICEDB_DATASTORE_ENGINE: postgres
      SPICEDB_DATASTORE_CONN_URI: "postgres://spicedb:spicedb@spicedb-postgres:5432/spicedb?sslmode=disable"
    depends_on:
      spicedb-postgres:
        condition: service_healthy
    restart: "no"

  spicedb:
    image: authzed/spicedb
    container_name: spicedb
    command:
      - serve
      - --http-enabled
      - --grpc-preshared-key
      - "test"
      - --datastore-engine
      - postgres
      - --datastore-conn-uri
      - "postgres://spicedb:spicedb@spicedb-postgres:5432/spicedb?sslmode=disable"
    ports:
      - "50051:50051"
      - "8443:8443"
    networks:
      - spicedb-net
    depends_on:
      spicedb-migrate:
        condition: service_completed_successfully
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M

networks:
  spicedb-net:
    driver: bridge

volumes:
  spicedb_pgdata:
```

One-shot:

```bash
docker compose up -d
```

Compose will start Postgres, wait until it’s healthy, run the migrate container once, then start SpiceDB. For a fresh install you only need `docker compose up -d`; no manual migrate step.

---

## What each step does

| Step | Purpose |
|------|--------|
| **Network** | Lets SpiceDB and Postgres containers resolve each other by name (`spicedb-postgres`, etc.). |
| **Postgres** | Persistent datastore for SpiceDB (relationships, schema, etc.). |
| **Wait for Postgres** | Migrations must run against a running DB; otherwise they fail or SpiceDB starts with an empty schema. |
| **`datastore migrate head`** | Creates all required tables in Postgres (`relation_tuple_transaction`, `alembic_version`, `metadata`, etc.). Without this, SpiceDB reports "relation does not exist" and won’t serve. |
| **SpiceDB serve** | gRPC (50051) and HTTP (8443) server that uses the migrated Postgres. |

## Cloud firewall (Oracle Cloud example)

If your app runs off the VM, add an **ingress** rule in the VCN security list:

- **Source CIDR:** your client IP or `0.0.0.0/0` (for testing only)
- **IP Protocol:** TCP
- **Source Port Range:** All
- **Destination Port Range:** 50051

## Resetting and starting over

To wipe data and repeat the one-shot setup:

```bash
# Stop and remove containers (and migrate container if used)
docker stop spicedb spicedb-postgres 2>/dev/null
docker rm spicedb spicedb-postgres 2>/dev/null

# Remove the volume (deletes all SpiceDB data)
docker volume rm spicedb_pgdata 2>/dev/null

# Then run Option A or Option B again
```

With Compose: `docker compose down -v` then `docker compose up -d`.
