# HoloMed Backend API

FastAPI backend server for HoloMed - Holographic Medical Visualization Platform.

## Features

- User authentication and authorization (JWT)
- 3D model upload and management
- Session tracking
- RESTful API endpoints

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional):
```bash
export DATABASE_URL="sqlite:///./holomed.db"  # Default SQLite
# For PostgreSQL: export DATABASE_URL="postgresql://user:pass@localhost/holomed"
export SECRET_KEY="your-secret-key-here"
```

3. Run the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get access token
- `GET /api/auth/me` - Get current user info

### Models
- `POST /api/models/upload` - Upload 3D model
- `GET /api/models` - List user's models
- `GET /api/models/{model_id}` - Get model details
- `DELETE /api/models/{model_id}` - Delete model

### Sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions` - List user's sessions
- `PATCH /api/sessions/{session_id}/end` - End session

## Development

### Using Docker

```bash
docker build -t holomed-backend .
docker run -p 8000:8000 holomed-backend
```

## Production Deployment

1. Set proper `SECRET_KEY` environment variable
2. Use PostgreSQL instead of SQLite
3. Configure CORS origins properly
4. Set up file storage (S3, GCS, etc.)
5. Use a production ASGI server like Gunicorn with Uvicorn workers
