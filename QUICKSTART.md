# HoloMed - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- **Backend**: Python 3.10+, pip
- **Web App**: Node.js 18+, npm/yarn
- **Mobile App**: Node.js 18+, React Native CLI, Xcode (iOS) or Android Studio (Android)
- **Docker** (optional): For containerized deployment

---

## 📦 Option 1: Docker (Easiest)

### Start Everything
```bash
docker-compose up
```

### Access Services
- **Web App**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🛠️ Option 2: Manual Setup

### Step 1: Backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend will run on http://localhost:8000

**Test it:**
- Visit http://localhost:8000/docs for interactive API documentation
- Visit http://localhost:8000/health to check if it's running

### Step 2: Web Application

```bash
cd Webapp
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

Web app will run on http://localhost:3000

**First Steps:**
1. Open http://localhost:3000
2. Click "Login" to register a new account
3. Upload a 3D model (STL, OBJ, PLY, VTK, GLTF, GLB)
4. Click on a model to view it with hand tracking

### Step 3: Mobile Application

#### iOS Setup
```bash
cd Mobileapp
npm install
cd ios && pod install && cd ..
npm run ios
```

#### Android Setup
```bash
cd Mobileapp
npm install
npm run android
```

**Important:** Update API URL in mobile app files:
- `src/screens/HomeScreen.tsx`
- `src/screens/LoginScreen.tsx`
- `src/store/authStore.ts`

Change `const API_URL = 'http://localhost:8000';` to:
- **iOS Simulator**: `http://localhost:8000`
- **Android Emulator**: `http://10.0.2.2:8000`
- **Physical Device**: `http://YOUR_COMPUTER_IP:8000`

---

## 🎮 Usage

### Web App
1. **Register/Login**: Create an account or sign in
2. **Upload Model**: Click "Upload 3D Model" and select a file
3. **View Model**: Click on any model to open the 3D viewer
4. **Gestures**:
   - Pinch thumb + index finger and move = Rotate
   - Two hands: bring together/apart = Zoom

### Mobile App
1. **Login**: Sign in with your account
2. **Upload**: Tap "Upload 3D Model" to add a model
3. **View**: Tap on any model to open the viewer
4. **Gestures**: Same as web app

---

## 📁 Project Structure

```
holomed/
├── backend/              # FastAPI backend
│   ├── main.py          # API server
│   ├── models.py        # Database models
│   ├── auth.py          # Authentication
│   └── requirements.txt  # Python dependencies
│
├── Webapp/              # Next.js web app
│   ├── src/
│   │   ├── app/         # Next.js app router
│   │   ├── components/  # React components
│   │   └── store/       # State management
│   └── package.json     # Node dependencies
│
├── Mobileapp/           # React Native app
│   ├── src/
│   │   ├── screens/     # App screens
│   │   └── store/       # State management
│   └── package.json     # Node dependencies
│
└── docker-compose.yml   # Docker orchestration
```

---

## 🔧 Configuration

### Backend Environment Variables
Create `backend/.env`:
```
DATABASE_URL=sqlite:///./holomed.db
SECRET_KEY=your-secret-key-here
```

### Web App Environment Variables
Create `Webapp/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Mobile App
Update API_URL in:
- `src/screens/HomeScreen.tsx`
- `src/screens/LoginScreen.tsx`
- `src/store/authStore.ts`

---

## 🐛 Troubleshooting

### Backend Issues
- **Port 8000 already in use**: Change port in `uvicorn main:app --port 8001`
- **Database errors**: Delete `holomed.db` and restart
- **Import errors**: Make sure you're in the `backend/` directory

### Web App Issues
- **Cannot connect to API**: Check `NEXT_PUBLIC_API_URL` in `.env.local`
- **Camera not working**: Grant camera permissions in browser
- **Models not loading**: Ensure backend is running

### Mobile App Issues
- **Cannot connect to API**: 
  - iOS Simulator: Use `localhost:8000`
  - Android Emulator: Use `10.0.2.2:8000`
  - Physical Device: Use your computer's IP address
- **Build errors**: Run `cd ios && pod install` for iOS
- **Camera permission**: Grant in device settings

---

## 📚 Next Steps

1. **Test the API**: Visit http://localhost:8000/docs
2. **Create an account**: Register via web app
3. **Upload a model**: Try with a sample STL/OBJ file
4. **Test gestures**: Use hand tracking in the viewer

---

## 🎯 Production Deployment

### Backend
- Use PostgreSQL instead of SQLite
- Set strong `SECRET_KEY`
- Configure CORS properly
- Use cloud storage (S3/GCS) for models

### Web App
- Build: `npm run build`
- Deploy to Vercel/Netlify
- Set production API URL

### Mobile App
- Configure bundle IDs in `app.json`
- Build and submit to App Store/Play Store

---

## 📞 Support

For issues, check:
- Backend logs: Terminal output
- Web app: Browser console
- Mobile app: React Native debugger

---

**Happy coding! 🚀**
