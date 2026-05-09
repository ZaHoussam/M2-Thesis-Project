# Intelligent Laboratory Access Control System

Master's thesis project — deep learning-based facial recognition
for secure lab access management.

## Architecture
- **Server**: FastAPI + PostgreSQL — authentication, matching, logging
- **Client**: Python edge device — camera, face detection, embedding

## Quick Start

### 1. Database
```bash
psql -U mrlhou -c "CREATE DATABASE lab_access;"
psql -U mrlhou -d lab_access -f server/schema.sql
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
| Zone | Score      | Response      |
|------|------------|---------------|
| A    | > 0.85     | ALLOW         |
| C    | ≤ 0.60     | DENY          |

## Project Structure
See folder layout below.

├── lab-access/                    # Project root
│   ├── .env.example               # Template environment file
│   ├── Dockerfile                 # Docker configuration
│   ├── README.md                  # Project README
│   ├── docker-compose.yml         # Docker Compose for services
│   │
│   ├── server/                    # FastAPI backend
│   │   ├── main.py                # Application entry point
│   │   ├── config.py              # Settings management
│   │   ├── database.py            # Database connection
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── schemas/               # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   └── enrollment.py
│   │   ├── routers/               # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── enrollment.py
│   │   │   └── verify.py
│   │   ├── services/              # Business logic
│   │   │   ├── arcface.py
│   │   │   ├── matcher.py
│   │   │   └── enrollment.py
│   │   ├── utils/                 # Utility functions
│   │   │   ├── face_crop.py
│   │   │   ├── image_utils.py
│   │   │   └── validation.py
│   │   └── requirements.txt
│   │
│   ├── client/                    # Edge device client
│   │   ├── main.py                # Main client application
│   │   ├── config.py              # Client settings
│   │   ├── capture.py             # Camera capture and face detection
│   │   ├── embedding.py           # ArcFace embedding generation
│   │   ├── matcher.py             # Client-side matching logic
│   │   ├── schemas/               # Pydantic models for client
│   │   │   └── verify.py
│   │   ├── utils/                 # Client utilities
│   │   │   ├── detector.py
│   │   │   ├── preprocess.py
│   │   │   └── websocket_client.py
│   │   ├── tests/                 # Client tests
│   │   └── requirements.txt
│   │
│   ├── data/                      # Optional data directory
│   ├── tests/                     # Project-wide tests
│   └── .env.example               # Template environment file

# Run server:
 cd server
 source venv/bin/activate
 uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run client:
 cd client
 source venv/bin/activate
 python main.py