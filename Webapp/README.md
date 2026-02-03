# HoloMed Webapp

Holographic Medical Visualization with Hand Tracking - React Application

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Build tool and dev server
- **Three.js** - 3D graphics
- **React Three Fiber** - React renderer for Three.js
- **Zustand** - State management
- **TanStack Query** - Data fetching
- **Tailwind CSS** - Styling
- **TensorFlow.js** - Hand pose detection

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file in the root directory:
```env
VITE_API_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
Webapp/
├── src/
│   ├── components/      # React components
│   │   ├── HoloViewer.tsx
│   │   ├── LoginModal.tsx
│   │   └── ModelSelector.tsx
│   ├── pages/           # Page components
│   │   └── Home.tsx
│   ├── store/           # Zustand stores
│   │   └── authStore.ts
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
└── package.json
```

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## Features

- 3D model visualization with holographic effects
- Hand gesture controls (pinch to rotate, two hands to zoom)
- User authentication
- Model upload and management
- Support for multiple 3D formats (GLTF, OBJ, STL, PLY)

## Development Notes

- The app uses Vite for fast HMR (Hot Module Replacement)
- Three.js loaders are dynamically imported for better code splitting
- All components are client-side only (no SSR)
