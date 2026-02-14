# HoloMed - Commercial Platform

Complete commercial platform for Holographic Medical Visualization with hand tracking control.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Web App    │     │ Mobile App  │     │ Desktop App │
│  (Next.js)  │     │ (React      │     │ (Python)    │
│             │     │  Native)    │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                  ┌────────▼────────┐
                  │   Backend API   │
                  │    (FastAPI)    │
                  └────────┬────────┘
                           │
                   ┌───────▼───────┐
                   │   Database    │
                   │   (SQLite)    │
                   └───────────────┘
```

## Project Structure

```
holomed/
├── backend/          # FastAPI backend server
├── Webapp/           # Next.js web application
├── Mobileapp/        # React Native mobile app
└── docker-compose.yml
```

## Quick Start

### Option 1: Using Docker (Recommended)

1. Start all services:
```bash
docker-compose up
```

2. Access:
   - Web App: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Web App

```bash
cd Webapp
npm install
npm run dev
```

#### Mobile App

```bash
cd Mobileapp
npm install
npm run ios  # or npm run android
```

## Features

### Backend API
- ✅ User authentication (JWT)
- ✅ 3D model upload and management
- ✅ Session tracking
- ✅ RESTful API endpoints
- ✅ File storage

### Web Application
- ✅ Modern React/Next.js interface
- ✅ Hand gesture tracking (MediaPipe.js)
- ✅ 3D visualization (Three.js)
- ✅ Model upload and management
- ✅ User authentication
- ✅ Responsive design

### Mobile Application
- ✅ Native iOS and Android support
- ✅ Camera integration
- ✅ 3D model viewing
- ✅ Model management
- ✅ User authentication

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Models
- `POST /api/models/upload` - Upload 3D model
- `GET /api/models` - List user's models
- `GET /api/models/{id}` - Get model details
- `DELETE /api/models/{id}` - Delete model

### Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions` - List sessions
- `PATCH /api/sessions/{id}/end` - End session

## Gesture Controls

- **Rotate**: Pinch thumb and index finger together and move your hand
- **Zoom**: Use two hands - bring together to zoom in, apart to zoom out

## Supported 3D Formats

- STL
- OBJ
- PLY
- VTK
- GLTF/GLB

## Development

### Environment Variables

**Backend** (`.env`):
```
DATABASE_URL=sqlite:///./holomed.db
SECRET_KEY=your-secret-key-here
```

**Web App** (`.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Mobile App**: Update API_URL in:
- `src/screens/HomeScreen.tsx`
- `src/screens/LoginScreen.tsx`
- `src/store/authStore.ts`

## Production Deployment

### Backend
1. Set proper `SECRET_KEY`
2. Use PostgreSQL instead of SQLite
3. Configure CORS origins
4. Set up cloud storage (S3, GCS)
5. Use production ASGI server

### Web App
1. Build: `npm run build`
2. Deploy to Vercel/Netlify
3. Set environment variables

### Mobile App
1. Configure app.json with proper bundle IDs
2. Build iOS: Xcode
3. Build Android: Android Studio
4. Submit to App Store/Play Store

## Commercial Features (Future)

- [ ] Subscription tiers (Free, Pro, Enterprise)
- [ ] Model marketplace
- [ ] Collaboration features
- [ ] Analytics dashboard
- [ ] Cloud sync
- [ ] AR mode (mobile)

## License

Proprietary - All rights reserved

## Support

For issues and questions, please contact support@holomed.com
