import { useState, useEffect, Suspense, lazy } from 'react';
import ModelSelector from '../components/ModelSelector';
import LoginModal from '../components/LoginModal';
import { useAuthStore } from '../store/authStore';

// Lazy load HoloViewer for code splitting
const HoloViewer = lazy(() => import('../components/HoloViewer'));

export default function Home() {
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const { isAuthenticated, user, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth().catch(console.error);
  }, [checkAuth]);

  const handleModelSelect = (modelUrl: string) => {
    setSelectedModel(modelUrl);
  };

  const handleBackToSelector = () => {
    setSelectedModel(null);
  };

  return (
    <main className="min-h-screen bg-black relative">
      {!isAuthenticated && (
        <div className="absolute top-4 right-4 z-50">
          <button
            onClick={() => setShowLogin(true)}
            className="px-4 py-2 bg-cyan-500 text-black rounded-lg hover:bg-cyan-400 transition-colors"
          >
            Login
          </button>
        </div>
      )}

      {isAuthenticated && user && (
        <div className="absolute top-4 right-4 z-50 text-sm">
          <span className="text-gray-400">Logged in as: </span>
          <span className="text-cyan-400">{user.email}</span>
        </div>
      )}

      {selectedModel ? (
        <Suspense fallback={
          <div className="flex items-center justify-center h-screen bg-black text-cyan-500">
            Initializing Holographic Engine...
          </div>
        }>
          <HoloViewer 
            modelUrl={selectedModel}
            onBack={handleBackToSelector}
            onGestureUpdate={(rotation, scale) => {
              // Send to backend for analytics
              console.log('Gesture:', rotation, scale);
            }}
          />
        </Suspense>
      ) : (
        <ModelSelector 
          onSelect={handleModelSelect}
          isAuthenticated={isAuthenticated}
        />
      )}

      {showLogin && (
        <LoginModal 
          onClose={() => setShowLogin(false)}
          onSuccess={() => {
            setShowLogin(false);
            checkAuth();
          }}
        />
      )}
    </main>
  );
}
