# Intelligent Laboratory Access Control System - Project Summary and Documentation

This document provides a comprehensive summary of the Laboratory Access Control System, detailing the project's evolution, architecture, and a complete breakdown of every file in the codebase.

## 1. Project Overview and Evolution
The system is designed to provide secure, real-time facial recognition access control for laboratory doors. It uses a client-server architecture where edge devices (clients with cameras) detect faces, generate embeddings, and send them to a central server for authentication.

### Key Milestones & Enhancements
Throughout the development journey, the following key tasks were accomplished:
- **Environment Configuration (`.env.example`)**: Created a template for secure configuration of database and application secrets.
- **Server Debugging (`/debug` route)**: Added a debug endpoint to easily check the server's threshold configurations.
- **Project Documentation**: Initiated automated documentation generation to track the system's state.
- **Threshold Adjustment**: Tuned the facial recognition sensitivity (ArcFace cosine similarity) to balance security and convenience (currently set at 0.50).
- **Client Startup & Camera Troubleshooting**: Fixed issues related to WebSocket disconnections (`ConnectionClosedError`) and integrated PC camera resource allocation conflicts.
- **Cleanup**: Removed obsolete features like MFA/PIN code to streamline the process to a fast, binary ALLOW/DENY workflow.
- **Performance Optimization**: Lowered the frame aggregation buffer from 7 to 3 to significantly reduce recognition latency, allowing for near-instant authentication while maintaining a highly responsive and striking UI.

## 2. System Architecture
- **Client**: A Python application using `OpenCV` for camera capture, `InsightFace` (RetinaFace + ArcFace) for face detection and 512-d embedding extraction, and `websockets` for real-time communication. It uses multiprocessing to keep the camera/AI processing separate from the UI rendering and network I/O.
- **Server**: A `FastAPI` application using `WebSockets` for live authentication and REST for enrollment. It uses `SQLAlchemy` (async) with `PostgreSQL` to store user data, embeddings, and access logs.

---

## 3. Comprehensive File-by-File Breakdown

### 3.1. Root Directory Files
- **`.env.example`**: The template for environment variables containing database credentials, server host details, and client configurations (like camera index and WebSocket URL).
- **`docker-compose.yml`**: Docker configuration for spinning up the PostgreSQL 16 database. It mounts `postgres_data` for persistence and executes `schema.sql` on initialization.
- **`README.md`**: The main project description and setup instructions.
- **`.gitignore`**: Excludes virtual environments (`venv/`), Python cache (`__pycache__`), local environment files (`.env`), downloaded ONNX models, and temporary files from version control.

### 3.2. Server Application (`server/`)
The backend is responsible for storing user data and making access decisions.

#### Root Server Files
- **`server/main.py`**: The FastAPI application entry point. It sets up CORS, includes the enrollment and verification routers, warms up the DB connection pool on startup, and provides `/health` and `/debug` endpoints.
- **`server/config.py`**: Uses `pydantic_settings` to load and validate environment variables (e.g., database URL, server port, threshold values).
- **`server/schema.sql`**: The PostgreSQL database schema definition. It creates the tables: `labs`, `users`, `face_embeddings` (with a constraint for 512-d arrays), and `access_logs`.
- **`server/requirements.txt`**: Server dependencies including `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic`, etc.

#### Database (`server/db/`)
- **`server/db/session.py`**: Configures the async SQLAlchemy engine and session factory (`AsyncSession`). It provides the `get_session()` context manager dependency for routes.
- **`server/db/models.py`**: SQLAlchemy ORM models defining the database schema in Python: `Lab`, `User`, `FaceEmbedding`, and `AccessLog`.

#### Core Logic (`server/core/`)
- **`server/core/matcher.py`**: Contains the core logic for authentication. It computes the cosine similarity between the incoming embedding and stored embeddings. It uses a weighted top-K approach and enforces a `MARGIN_THRESHOLD` (if the top 2 matches are too close, it denies access to prevent ambiguous false positives). Returns a `MatchResult` (ALLOW/DENY).

#### API Routers (`server/routers/`)
- **`server/routers/enroll.py`**: Provides the `POST /enroll` endpoint. It checks if the email is already registered, creates a new `User`, and stores their 512-d `FaceEmbedding`.
- **`server/routers/verify.py`**: Provides the `/ws/verify` WebSocket endpoint. It receives embeddings from the client, fetches active users from the DB, calls `find_best_match` to make a decision, logs the outcome to `AccessLog`, and sends the result (ALLOW/DENY) back to the client.

#### Schemas (`server/schemas/`)
- **`server/schemas/enroll.py`**: Pydantic models `EnrollRequest` and `EnrollResponse` for the enrollment endpoint.
- **`server/schemas/auth.py`**: Pydantic models `VerifyRequest` and `VerifyResponse` defining the WebSocket payload structures.

### 3.3. Client Application (`client/`)
The edge device application handling camera capture, AI inference, and display.

#### Root Client Files
- **`client/main.py`**: The main entry point. It manages the complex architecture using `multiprocessing` (spawning the camera/AI worker) and `asyncio` (for the display loop and WebSocket client). It bridges the processes using thread-safe queues.
- **`client/config.py`**: Loads client-specific settings (WebSocket URL, lab ID, camera index, min face size) using `pydantic_settings`.
- **`client/enroll.py`**: A standalone script for enrolling new users. It opens a camera feed, prompts the user to press SPACE to capture their face, asks for their details (name, email) via CLI, and sends the data to the server's REST endpoint.
- **`client/test_connection.py`**: A diagnostic script used to verify connectivity to the server (HTTP ping, health check, WebSocket connection test).
- **`client/requirements.txt`**: Client dependencies including `onnxruntime`, `opencv-python-headless`, `insightface`, `websockets`, etc.

#### Core Modules (`client/core/`)
- **`client/core/camera.py`**: A wrapper around `cv2.VideoCapture` to handle reading frames safely.
- **`client/core/camera_process.py`**: The `camera_worker` function that runs in a separate process. It reads frames, checks sharpness, runs the `FacePipeline`, pushes embeddings to the `FrameAggregator`, and sends data to the main process via queues.
- **`client/core/detector.py`**: Contains the `is_sharp` function using Laplacian variance to discard blurry frames before they reach the expensive AI pipeline.
- **`client/core/embedder.py`**: The `FacePipeline` class utilizing `InsightFace` to detect faces (RetinaFace) and extract 512-d embeddings (ArcFace). It only processes the largest face that meets the minimum size requirement.
- **`client/core/frame_aggregator.py`**: Buffers a set number of embeddings (currently 3) and computes their L2-normalized average. This creates a highly stable embedding representing natural face movement.
- **`client/core/display.py`**: The rendering engine. It draws the bounding boxes, status bars, real-time score indicators, and the striking full-screen "ALLOW/DENY" decision overlays using OpenCV drawing primitives.
- **`client/core/ws_client.py`**: The `AuthClient` class. It manages the persistent WebSocket connection to the server, sends the aggregated embeddings, and receives the server's authentication decisions, updating the application state for the display loop.

---

## 4. Conclusion
The Laboratory Access System is now a highly optimized, dual-process client/server application. By offloading heavy AI processing (InsightFace) to a dedicated background process and using an asynchronous WebSocket-driven UI loop, the system achieves fast, reliable, and visually engaging facial recognition access control. All deprecated features (MFA) have been cleanly removed, and the configuration has been tuned for optimal performance.
