# Intelligent Laboratory Access Control System

**A comprehensive deep learning-based facial recognition system for secure laboratory access management and control.**

---

## 📋 Overview

The Intelligent Laboratory Access Control System is an advanced security solution that leverages cutting-edge facial recognition and anti-spoofing technologies to provide secure, efficient access control to laboratory facilities. This Master's thesis project combines edge computing with cloud-based verification to ensure real-time, reliable authentication while maintaining detailed audit logs for security compliance.

### Key Features

- **Real-time Facial Recognition**: Advanced face detection, embedding, and matching using state-of-the-art deep learning models
- **Anti-Spoofing Protection**: Multi-modal anti-spoofing detection to prevent fraudulent access attempts
- **Edge Processing**: Local face processing on edge devices for minimal latency and privacy
- **Multi-Factor Authentication**: Optional MFA integration for enhanced security
- **Comprehensive Logging**: Complete audit trail of all access attempts and system events
- **Web-Based Dashboard**: Real-time monitoring, user management, and analytics
- **Docker Deployment**: Containerized setup for easy deployment and scaling

---

## 🏗️ System Architecture

The system follows a three-tier architecture:

```
┌─────────────────┐
│   Web Frontend  │ (React + TypeScript)
│   (Dashboard)   │
└────────┬────────┘
         │
┌────────▼─────────────────┐
│   FastAPI Server        │
│ (Auth, Matching, Logs)  │
└────────┬─────────────────┘
         │
    ┌────▼────┐
    │PostgreSQL│
    │ Database │
    └──────────┘

┌─────────────────────┐
│  Python Edge Client │
│ (Camera Processing) │
└────────┬────────────┘
         │ (WebSocket/HTTP)
    (Connects to FastAPI Server)
```

### Components

| Component          | Technology                   | Purpose                                                |
| ------------------ | ---------------------------- | ------------------------------------------------------ |
| **Backend Server** | FastAPI + PostgreSQL         | REST API, authentication, face matching, audit logging |
| **Web Frontend**   | React 18 + TypeScript + Vite | Real-time dashboard, user management, analytics        |
| **Edge Client**    | Python                       | Camera capture, face detection, embedding generation   |
| **ML Models**      | PyTorch, ONNX                | Face recognition, anti-spoofing                        |
| **Infrastructure** | Docker + Docker Compose      | Containerized deployment                               |

---

## 🛠️ Technology Stack

### Backend

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migration**: Alembic
- **Authentication**: JWT-based with MFA support

### Frontend

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: CSS

### Client (Edge)

- **Language**: Python 3.10+
- **Libraries**: InsightFace, OpenCV, WebSocket
- **Models**:
  - Face Detection: RetinaFace
  - Face Embedding: ArcFace
  - Anti-Spoofing: MiniFASNet V2

---

## 📋 Prerequisites

- Python 3.10 or higher
- PostgreSQL 12+
- Node.js 16+ (for web frontend)
- Docker & Docker Compose (optional, for containerized deployment)
- Webcam/IP camera (for client access point)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd lab_access_system
```

### 2. Environment Configuration

Copy and configure environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup

Create the PostgreSQL database and apply schema:

```bash
createdb lab_access
psql -U <username> -d lab_access -f server/schema.sql
```

### 4. Backend Setup

```bash
cd server
python -m venv venv

# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 5. Frontend Setup

```bash
cd "Intelligent Lab Access Control System"
npm install
npm run dev
```

### 6. Client Setup

```bash
cd client
python -m venv venv

# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
# Install the InsightFace wheel (included in repository)
pip install insightface-0.7.3-cp310-cp310-win_amd64.whl
```

---

## ⚡ Quick Start

### Start the Backend Server

```bash
cd server
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`  
API Documentation: `http://localhost:8000/docs`

### Start the Web Dashboard

```bash
cd "Intelligent Lab Access Control System"
npm run dev
```

Access the dashboard at `http://localhost:5173`

### Start the Edge Client

```bash
cd client
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

### Using Docker Compose (All Services)

```bash
docker-compose up -d
```

---

## 🔐 Access Control Decision Logic

The system uses cosine similarity scoring for face matching decisions:

| Zone  | Similarity Score | Action    | Description                         |
| ----- | ---------------- | --------- | ----------------------------------- |
| **A** | > 0.60           | ✅ ALLOW  | High confidence match, grant access |
| **B** | 0.50 - 0.60      | ⚠️ REVIEW | Manual review recommended           |
| **C** | < 0.50           | ❌ DENY   | Low confidence, deny access         |

---

## 📁 Project Structure

```
lab_access_system/
├── server/                    # FastAPI backend
│   ├── main.py               # Application entry point
│   ├── config.py             # Configuration management
│   ├── requirements.txt       # Python dependencies
│   ├── schema.sql            # Database schema
│   ├── core/                 # Business logic
│   │   ├── alert_engine.py   # Alert processing
│   │   └── matcher.py        # Face matching engine
│   ├── db/                   # Database layer
│   │   ├── models.py         # SQLAlchemy models
│   │   └── session.py        # DB session management
│   ├── routers/              # API endpoints
│   │   ├── users.py          # User management
│   │   ├── enroll.py         # User enrollment
│   │   ├── verify.py         # Face verification
│   │   ├── alerts.py         # Alert management
│   │   └── mfa.py            # MFA endpoints
│   ├── schemas/              # Pydantic models
│   └── tests/                # Unit tests
│
├── client/                   # Python edge client
│   ├── main.py              # Client entry point
│   ├── config.py            # Configuration
│   ├── requirements.txt      # Python dependencies
│   ├── core/                # Core processing modules
│   │   ├── camera.py        # Camera interface
│   │   ├── detector.py      # Face detection
│   │   ├── embedder.py      # Face embedding
│   │   ├── antispoof.py     # Anti-spoofing check
│   │   ├── display.py       # Display rendering
│   │   ├── ws_client.py     # WebSocket communication
│   │   ├── camera_process.py# Processing pipeline
│   │   └── frame_aggregator.py # Frame buffering
│   └── calibration_data/    # Calibration files
│
├── Intelligent Lab Access Control System/  # React frontend
│   ├── index.html           # HTML entry point
│   ├── src/
│   │   ├── main.tsx         # React entry
│   │   ├── App.tsx          # Root component
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   ├── utils/           # Utility functions
│   │   └── types.ts         # TypeScript definitions
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
│
├── models/                  # Pre-trained ML models
│   ├── 2.7_80x80_MiniFASNetV2.pth    # Anti-spoofing model
│   └── silent_face.onnx                # Face detection model
│
├── docker-compose.yml       # Docker Compose configuration
└── README.md               # This file
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/lab_access

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Client
WEBSOCKET_URL=ws://localhost:8000/ws
API_URL=http://localhost:8000
```

---

## 📊 API Endpoints

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/token/refresh` - Refresh access token

### Enrollment

- `POST /enroll/start` - Initiate enrollment
- `POST /enroll/capture` - Capture face samples
- `POST /enroll/complete` - Complete enrollment

### Verification

- `POST /verify` - Verify user access

### Users

- `GET /users` - List all users
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Alerts & Logs

- `GET /alerts` - Get system alerts
- `GET /logs` - Get access logs

---

## 🧪 Testing

Run unit tests:

```bash
cd server
pytest tests/
```

---

## 📈 Performance Metrics

- **Face Detection Latency**: ~50-100ms per frame
- **Face Embedding Generation**: ~100-150ms
- **Database Query**: <50ms average
- **API Response Time**: <500ms
- **Throughput**: Up to 30 simultaneous connections

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit your changes: `git commit -am 'Add feature'`
3. Push to the branch: `git push origin feature/your-feature`
4. Submit a pull request

---

## 📝 License

This project is part of a Master's thesis and is provided as-is for educational and research purposes.

---

## 👤 Author

**Your Name** - Master's Thesis Project

For questions or support, please contact [your-email@example.com]

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [InsightFace Repository](https://github.com/deepinsight/insightface)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Last Updated**: June 2026  
**Version**: 1.0.0
