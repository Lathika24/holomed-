# HoloMed Web Application

Next.js web application for HoloMed - Holographic Medical Visualization Platform.

## Features

- 🎨 Modern React/Next.js interface
- 🤲 Hand gesture tracking using MediaPipe.js
- 🎭 3D model visualization with Three.js
- 📤 Upload and manage 3D models
- 🔐 User authentication
- 📱 Responsive design

## Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (see backend/README.md)

## Setup

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` and set:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Building for Production

```bash
npm run build
npm start
```

## Usage

1. **Login/Register**: Click the Login button to create an account or sign in
2. **Upload Models**: Upload 3D models in supported formats (STL, OBJ, PLY, VTK, GLTF, GLB)
3. **View Models**: Click on any model to open it in the 3D viewer
4. **Gesture Controls**:
   - **Rotate**: Pinch thumb and index finger together and move your hand
   - **Zoom**: Use two hands - bring them together to zoom in, apart to zoom out

## Supported 3D Formats

- STL
- OBJ
- PLY
- VTK
- GLTF/GLB

## Browser Requirements

- Modern browser with WebGL support
- Camera access permissions
- Chrome/Edge recommended for best MediaPipe performance

## Troubleshooting

- **Camera not working**: Ensure you've granted camera permissions in your browser
- **Models not loading**: Check that the backend API is running and accessible
- **Hand tracking not working**: Ensure good lighting and camera visibility
