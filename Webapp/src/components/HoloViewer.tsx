'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera, OrbitControls, Environment, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

interface HoloViewerProps {
  modelUrl: string;
  onBack?: () => void;
  onGestureUpdate?: (rotation: [number, number, number], scale: number) => void;
}

export default function HoloViewer({ modelUrl, onBack, onGestureUpdate }: HoloViewerProps) {
  const [model, setModel] = useState<THREE.Group | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const handsRef = useRef<any>(null);
  const cameraRef = useRef<any>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastPinchPos = useRef<{ x: number; y: number } | null>(null);
  const lastHandDist = useRef<number | null>(null);
  const currentRotation = useRef<[number, number, number]>([0, 0, 0]);
  const currentScale = useRef<number>(1.0);
  const meshRef = useRef<THREE.Group>(null);

  // Load 3D model
  useEffect(() => {
    if (!modelUrl) return;

    setLoading(true);
    setError(null);

    const loadModel = async () => {
      try {
        const loader = await getLoader(modelUrl);
        const loadedModel = await new Promise<THREE.Group>((resolve, reject) => {
          loader.load(
            modelUrl,
            (object) => {
              // Center and normalize the model
              const box = new THREE.Box3().setFromObject(object);
              const center = box.getCenter(new THREE.Vector3());
              const size = box.getSize(new THREE.Vector3());
              const maxDim = Math.max(size.x, size.y, size.z);
              const scale = 5.0 / maxDim;

              object.position.sub(center);
              object.scale.multiplyScalar(scale);

              resolve(object);
            },
            undefined,
            reject
          );
        });

        setModel(loadedModel);
        setLoading(false);
      } catch (err) {
        console.error('Error loading model:', err);
        setError('Failed to load 3D model');
        setLoading(false);
      }
    };

    loadModel();
  }, [modelUrl]);

  // Initialize hand tracking with TensorFlow.js
  useEffect(() => {
    if (!videoRef.current) return;

    let detector: any = null;
    let animationFrameId: number | null = null;

    const initHandTracking = async () => {
      try {
        // Dynamically import TensorFlow.js
        const tf = await import('@tensorflow/tfjs');
        const handPoseDetection = await import('@tensorflow-models/hand-pose-detection');
        
        await tf.ready();

        // Initialize detector
        const model = handPoseDetection.SupportedModels.MediaPipe;
        detector = await handPoseDetection.createDetector(model, {
          runtime: 'mediapipe',
          modelType: 'lite',
          maxHands: 2,
        });

        handsRef.current = detector;

        // Start video stream
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 }
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        // Process frames
        const processFrame = async () => {
          if (!videoRef.current || !detector || videoRef.current.readyState !== videoRef.current.HAVE_ENOUGH_DATA) {
            animationFrameId = requestAnimationFrame(processFrame);
            return;
          }

          try {
            const hands = await detector.estimateHands(videoRef.current, { flipHorizontal: false });
            
            if (hands && hands.length > 0) {
              const hand1 = hands[0];
              const keypoints = hand1.keypoints;
              
              // Find index tip and thumb tip by name
              const indexTip = keypoints.find((kp: any) => kp.name === 'index_finger_tip' || kp.name === 8);
              const thumbTip = keypoints.find((kp: any) => kp.name === 'thumb_tip' || kp.name === 4);
              
              if (indexTip && thumbTip) {
                const videoWidth = videoRef.current.videoWidth || 1280;
                const videoHeight = videoRef.current.videoHeight || 720;
                const maxDim = Math.max(videoWidth, videoHeight);
                
                const pinchDist = Math.sqrt(
                  Math.pow(indexTip.x - thumbTip.x, 2) + 
                  Math.pow(indexTip.y - thumbTip.y, 2)
                ) / maxDim;

                // Rotation gesture (pinch + move)
                if (pinchDist < 0.05) {
                  const centerX = (indexTip.x + thumbTip.x) / 2 / videoWidth;
                  const centerY = (indexTip.y + thumbTip.y) / 2 / videoHeight;
                  
                  if (lastPinchPos.current) {
                    const dx = (centerX - lastPinchPos.current.x) * 120;
                    const dy = (centerY - lastPinchPos.current.y) * 120;
                    currentRotation.current[0] += dy;
                    currentRotation.current[1] += dx;
                    
                    if (meshRef.current) {
                      meshRef.current.rotation.x = THREE.MathUtils.degToRad(currentRotation.current[0]);
                      meshRef.current.rotation.y = THREE.MathUtils.degToRad(currentRotation.current[1]);
                    }
                    
                    onGestureUpdate?.([...currentRotation.current], currentScale.current);
                  }
                  lastPinchPos.current = { x: centerX, y: centerY };
                } else {
                  lastPinchPos.current = null;
                }

                // Zoom gesture (two hands)
                if (hands.length === 2) {
                  const hand2 = hands[1];
                  const h2Keypoints = hand2.keypoints;
                  const h1Index = keypoints.find((kp: any) => kp.name === 'index_finger_tip' || kp.name === 8);
                  const h2Index = h2Keypoints.find((kp: any) => kp.name === 'index_finger_tip' || kp.name === 8);
                  
                  if (h1Index && h2Index) {
                    const handDist = Math.sqrt(
                      Math.pow(h1Index.x - h2Index.x, 2) + 
                      Math.pow(h1Index.y - h2Index.y, 2)
                    ) / maxDim;

                    if (lastHandDist.current !== null && lastHandDist.current > 0.01) {
                      const scaleMult = handDist / lastHandDist.current;
                      currentScale.current = Math.max(0.2, Math.min(5.0, currentScale.current * scaleMult));
                      
                      if (meshRef.current) {
                        meshRef.current.scale.setScalar(currentScale.current);
                      }
                      
                      onGestureUpdate?.([...currentRotation.current], currentScale.current);
                    }
                    lastHandDist.current = handDist;
                  }
                } else {
                  lastHandDist.current = null;
                }
              }
            }
          } catch (error) {
            console.error('Hand detection error:', error);
          }
          
          animationFrameId = requestAnimationFrame(processFrame);
        };

        // Wait for video to be ready
        videoRef.current.addEventListener('loadedmetadata', () => {
          processFrame();
        });
      } catch (error) {
        console.warn('Hand tracking initialization failed:', error);
      }
    };

    initHandTracking();

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (videoRef.current?.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
      if (detector) {
        detector.dispose();
      }
    };
  }, [onGestureUpdate]);

  const getLoader = async (url: string) => {
    const ext = url.split('.').pop()?.toLowerCase();
    
    // Helper to try loading from different paths
    const loadLoader = async (loaderName: string) => {
      const paths = [
        `three/addons/loaders/${loaderName}.js`,
        `three/examples/jsm/loaders/${loaderName}.js`,
      ];
      
      for (const path of paths) {
        try {
          const module = await import(path);
          return module[loaderName];
        } catch (e) {
          // Try next path
          continue;
        }
      }
      throw new Error(`Could not load ${loaderName} from any path`);
    };
    
    switch (ext) {
      case 'gltf':
      case 'glb': {
        const GLTFLoader = await loadLoader('GLTFLoader');
        return new GLTFLoader();
      }
      case 'obj': {
        const OBJLoader = await loadLoader('OBJLoader');
        return new OBJLoader();
      }
      case 'stl': {
        const STLLoader = await loadLoader('STLLoader');
        return new STLLoader();
      }
      case 'ply': {
        const PLYLoader = await loadLoader('PLYLoader');
        return new PLYLoader();
      }
      default: {
        const GLTFLoader = await loadLoader('GLTFLoader');
        return new GLTFLoader();
      }
    }
  };

  return (
    <div className="relative w-full h-screen">
      {/* Video background */}
      <video
        ref={videoRef}
        className="absolute top-0 left-0 w-full h-full object-cover opacity-30"
        autoPlay
        playsInline
        muted
      />

      {/* Back button */}
      {onBack && (
        <button
          onClick={onBack}
          className="absolute top-4 left-4 z-50 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          ← Back
        </button>
      )}

      {/* Loading/Error overlay */}
      {(loading || error) && (
        <div className="absolute inset-0 flex items-center justify-center z-40 bg-black bg-opacity-75">
          {loading && <div className="text-cyan-400 text-xl">Loading 3D model...</div>}
          {error && <div className="text-red-400 text-xl">{error}</div>}
        </div>
      )}

      {/* 3D Canvas */}
      <Canvas className="absolute top-0 left-0 w-full h-full">
        <PerspectiveCamera makeDefault position={[0, 0, 10]} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <pointLight position={[-10, -10, -10]} />
        
        {model && (
          <group ref={meshRef}>
            {/* Inner hologram effect */}
            <primitive
              object={model.clone()}
              scale={currentScale.current}
            >
              <meshStandardMaterial
                color="#00ffff"
                transparent
                opacity={0.15}
                emissive="#00ffff"
                emissiveIntensity={0.2}
              />
            </primitive>
            
            {/* Outer wireframe */}
            <primitive
              object={model.clone()}
              scale={currentScale.current}
            >
              <meshBasicMaterial
                color="#ffffff"
                wireframe
                transparent
                opacity={0.8}
              />
            </primitive>
          </group>
        )}
        
        {/* Background plane with video texture */}
        {videoRef.current && (
          <mesh position={[0, 0, -20]}>
            <planeGeometry args={[32, 18]} />
            <meshBasicMaterial>
              <videoTexture attach="map" args={[videoRef.current]} />
            </meshBasicMaterial>
          </mesh>
        )}
      </Canvas>

      {/* Instructions overlay */}
      <div className="absolute bottom-4 left-4 z-50 bg-black bg-opacity-70 p-4 rounded-lg text-sm">
        <div className="text-cyan-400 mb-2">Gesture Controls:</div>
        <div>• Pinch thumb & index finger + move = Rotate</div>
        <div>• Two hands: bring together/apart = Zoom</div>
      </div>
    </div>
  );
}
