# Intelligent Laboratory Access Control System

Master's thesis project — deep learning-based facial recognition
for secure lab access management.

## Architecture

- **Server**: FastAPI + PostgreSQL — authentication, matching, logging
- **Client**: Python edge device — camera, face detection, embedding

## Quick Start

### 1. Database

```bash
psql -U <user> -c "CREATE DATABASE lab_access;"
psql -U <user> -d lab_access -f server/schema.sql
```

### 2. Server

```bash
cd server
cp .env.example .env        # fill in your values
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Client

```bash
cd client
cp ../.env.example .env     # fill in your values
pip install -r requirements.txt
python main.py
```

## Decision Logic (Cosine Similarity)

| Zone | Score  | Response |
| ---- | ------ | -------- |
| A    | > 0.60 | ALLOW    |
| C    | < 0.60 | DENY     |

# Run server:

```bash
cd server
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

# Run client:

```bash
cd client
source venv/bin/activate
python main.py
```
