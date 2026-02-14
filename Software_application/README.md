# HoloMed Desktop Application

A modern desktop application for holographic medical visualization with hand tracking control.

## Features

- 🔐 User authentication (login/register)
- 📦 3D model management (upload, list, delete)
- 🎮 Hand gesture controls (pinch to rotate, two-hand zoom)
- 🎨 Beautiful holographic visualization
- 🔄 Real-time camera feed integration
- 💾 Model storage and synchronization with backend

## Prerequisites

- Python 3.10 or higher
- Webcam/camera for hand tracking
- Backend API running (see `../backend/QUICK_START.md`)

## Installation

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # macOS/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API URL (optional):**
   Set environment variable if backend is not on localhost:8000:
   ```bash
   set HOLOMED_API_URL=http://your-api-url:8000  # Windows
   # or
   export HOLOMED_API_URL=http://your-api-url:8000  # macOS/Linux
   ```

## Running the Application

1. **Make sure the backend is running:**
   ```bash
   cd ../backend
   uvicorn main:app --reload
   ```

2. **Start the desktop application:**
   ```bash
   python main.py
   ```

## Usage

1. **Login/Register:** When you start the app, you'll be prompted to login or register
2. **Upload Models:** Click "Upload Model" to add 3D models (STL, OBJ, PLY, VTK, GLTF, GLB)
3. **View Models:** Select a model from the list and click "View Selected Model"
4. **Hand Controls:**
   - **Rotate:** Pinch thumb and index finger together and move your hand
   - **Zoom:** Use two hands - bring together to zoom in, apart to zoom out

## Troubleshooting

- **Camera not working:** Ensure your webcam is connected and not used by another app
- **API connection failed:** Make sure the backend is running on `http://localhost:8000`
- **Model upload fails:** Check file size (max 100MB) and format
- **Viewer window doesn't open:** Check console for errors, ensure PyVista is properly installed

## Building Executable (Optional)

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name HoloMed --icon=icon.ico main.py
```

The executable will be in the `dist` folder.

**Note:** For PyInstaller, you may need to create a spec file to include all dependencies properly.

## Project Structure

```
software_application/
├── main.py              # Application entry point
├── app.py               # Main window and application logic
├── auth_window.py       # Login/Register dialog
├── model_manager.py      # Model upload/list management
├── viewer_window.py     # 3D visualization with hand tracking
├── api_client.py        # Backend API client
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## API Integration

The desktop app connects to the FastAPI backend and uses the following endpoints:
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/models/upload` - Upload 3D model
- `GET /api/models` - List user's models
- `GET /api/models/{id}` - Get model details
- `DELETE /api/models/{id}` - Delete model
- `GET /uploads/{filename}` - Download model file

## License

© 2024 HoloMed
