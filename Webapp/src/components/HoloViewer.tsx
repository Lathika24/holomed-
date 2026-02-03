import { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';

// Configuration matching Python reference exactly
const Config = {
  PINCH_THRESHOLD: 0.05,
  ROTATION_SENSITIVITY: 120,
  SCALE_SENSITIVITY: 1.5,
  TARGET_FPS: 30,
  HOLO_COLOR: '#00ffff', // cyan
  HOLO_EDGE_COLOR: '#ffffff', // white
  BG_DISTANCE: 20.0, // How far back the camera plane sits
  MESH_SCALE_BASE: 1.0,
};

// Dynamic imports for Three.js loaders
type LoaderType = any;

// Inner "Ghost" volume component (matching Python actor_inner)
function InnerMesh({ 
  model, 
  currentRotation,
  currentScale 
}: { 
  model: THREE.Group; 
  currentRotation: React.MutableRefObject<[number, number, number]>;
  currentScale: React.MutableRefObject<number>;
}) {
  const innerRef = useRef<THREE.Group>(null);
  const meshRefs = useRef<THREE.Mesh[]>([]);

  useEffect(() => {
    if (!innerRef.current || !model) return;
    
    // Clear previous meshes
    while (innerRef.current.children.length > 0) {
      innerRef.current.remove(innerRef.current.children[0]);
    }
    meshRefs.current = [];
    
    // Clone model for inner mesh
    const clonedModel = model.clone();
    
    // Apply hologram material to all meshes (matching Python: color=cyan, opacity=0.15, lighting=False)
    clonedModel.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const innerMaterial = new THREE.MeshBasicMaterial({
          color: Config.HOLO_COLOR,
          transparent: true,
          opacity: 0.15,
          // No lighting (MeshBasicMaterial doesn't respond to lights)
        });
        child.material = innerMaterial;
        meshRefs.current.push(child);
      }
    });
    
    innerRef.current.add(clonedModel);
  }, [model]);

  useFrame(() => {
    if (!innerRef.current) return;
    
    // Update rotation (matching Python: actor.orientation = self.current_rot)
    // Python uses degrees, Three.js uses radians
    innerRef.current.rotation.x = THREE.MathUtils.degToRad(currentRotation.current[0]);
    innerRef.current.rotation.y = THREE.MathUtils.degToRad(currentRotation.current[1]);
    innerRef.current.rotation.z = THREE.MathUtils.degToRad(currentRotation.current[2]);
    
    // Update scale (matching Python: actor.scale = [self.current_scale] * 3)
    innerRef.current.scale.setScalar(currentScale.current);
  });

  return <group ref={innerRef} />;
}

// Outer "Wireframe" structure component (matching Python actor_outer)
function OuterMesh({ 
  model, 
  currentRotation,
  currentScale 
}: { 
  model: THREE.Group;
  currentRotation: React.MutableRefObject<[number, number, number]>;
  currentScale: React.MutableRefObject<number>;
}) {
  const outerRef = useRef<THREE.Group>(null);
  const meshRefs = useRef<THREE.Mesh[]>([]);

  useEffect(() => {
    if (!outerRef.current || !model) return;
    
    // Clear previous meshes
    while (outerRef.current.children.length > 0) {
      outerRef.current.remove(outerRef.current.children[0]);
    }
    meshRefs.current = [];
    
    // Clone model for outer wireframe
    const clonedModel = model.clone();
    
    // Apply wireframe material (matching Python: color=white, opacity=0.8, style='wireframe', lighting=False)
    clonedModel.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const outerMaterial = new THREE.MeshBasicMaterial({
          color: Config.HOLO_EDGE_COLOR,
          wireframe: true,
          transparent: true,
          opacity: 0.8,
          // No lighting (MeshBasicMaterial doesn't respond to lights)
        });
        child.material = outerMaterial;
        meshRefs.current.push(child);
      }
    });
    
    outerRef.current.add(clonedModel);
  }, [model]);

  useFrame(() => {
    if (!outerRef.current) return;
    
    // Update rotation (matching Python: actor.orientation = self.current_rot)
    outerRef.current.rotation.x = THREE.MathUtils.degToRad(currentRotation.current[0]);
    outerRef.current.rotation.y = THREE.MathUtils.degToRad(currentRotation.current[1]);
    outerRef.current.rotation.z = THREE.MathUtils.degToRad(currentRotation.current[2]);
    
    // Update scale (matching Python: actor.scale = [self.current_scale] * 3)
    outerRef.current.scale.setScalar(currentScale.current);
  });

  return <group ref={outerRef} />;
}

// AR Background Plane with video texture (matching Python bg_plane)
function BackgroundPlane({ videoRef }: { videoRef: React.RefObject<HTMLVideoElement> }) {
  const planeRef = useRef<THREE.Mesh>(null);
  const textureRef = useRef<THREE.VideoTexture | null>(null);

  useEffect(() => {
    if (!videoRef.current || !planeRef.current) return;

    const texture = new THREE.VideoTexture(videoRef.current);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    textureRef.current = texture;

    // Matching Python: lighting=False
    const material = new THREE.MeshBasicMaterial({
      map: texture,
      side: THREE.DoubleSide,
    });
    
    if (planeRef.current) {
      planeRef.current.material = material;
    }

    return () => {
      texture.dispose();
    };
  }, [videoRef]);

  // Create plane geometry (32x18 units matching Python: i_size=32, j_size=18)
  const planeGeometry = new THREE.PlaneGeometry(32, 18);
  
  return (
    <mesh
      ref={planeRef}
      geometry={planeGeometry}
      position={[0, 0, -Config.BG_DISTANCE]} // Matching Python: center=(0, 0, -Config.BG_DISTANCE)
      rotation={[0, 0, 0]}
    />
  );
}

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
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // Interaction memory (matching Python SharedState)
  const lastPinchPos = useRef<{ x: number; y: number } | null>(null);
  const lastHandDist = useRef<number | null>(null);
  
  // Current state (matching Python: self.current_rot, self.current_scale)
  const currentRotation = useRef<[number, number, number]>([0, 0, 0]);
  const currentScale = useRef<number>(1.0);

  // Load and normalize 3D model (matching Python load_and_normalize_mesh exactly)
  useEffect(() => {
    if (!modelUrl) return;

    setLoading(true);
    setError(null);

    const loadModel = async () => {
      try {
        const loader = await getLoader(modelUrl); 
        const loadedModel = await new Promise<THREE.Group>((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Model loading timeout'));
          }, 30000);

          loader.load(
            modelUrl,
            (object: any) => {
              clearTimeout(timeout);
              
              // Handle different loader return types
              let modelObject: THREE.Object3D;
              if (object.scene) {
                // GLTFLoader returns { scene, animations, etc }
                modelObject = object.scene;
              } else if (object instanceof THREE.Object3D) {
                modelObject = object;
              } else {
                modelObject = object as THREE.Object3D;
              }
              
              // Normalization Routine (matching Python exactly)
              // 1. Center at origin
              const box = new THREE.Box3().setFromObject(modelObject);
              const center = box.getCenter(new THREE.Vector3());
              modelObject.position.sub(center);

              // 2. Rotate 90 degrees if it's an OBJ (often they come in lying down)
              if (modelUrl.toLowerCase().endsWith('.obj')) {
                modelObject.rotateX(THREE.MathUtils.degToRad(-90));
              }

              // 3. Scale to fit screen (target size ~5 units, matching Python)
              const size = box.getSize(new THREE.Vector3());
              const maxDim = Math.max(size.x, size.y, size.z);
              
              if (maxDim > 0) {
                const scaleFactor = 5.0 / maxDim;
                modelObject.scale.multiplyScalar(scaleFactor);
              }

              resolve(modelObject as THREE.Group);
            },
            (progress: any) => {
              if (progress && progress.total) {
                const percent = (progress.loaded / progress.total) * 100;
                console.log(`Loading progress: ${percent.toFixed(1)}%`);
              }
            },
            (error: any) => {
              clearTimeout(timeout);
              console.error('Loader error:', error);
              reject(error);
            }
          );
        });

        setModel(loadedModel);
        setLoading(false);
      } catch (err: any) {
        console.error('Error loading model:', err);
        setError(err.message || 'Failed to load 3D model');
        setLoading(false);
      }
    };

    loadModel();
  }, [modelUrl]);

  // Initialize hand tracking (matching Python HandTracker exactly)
  useEffect(() => {
    if (!videoRef.current) return;

    let detector: any = null;
    let animationFrameId: number | null = null;
    let lastFrameTime = 0;
    const frameInterval = 1000 / Config.TARGET_FPS; // 30 FPS

    const initHandTracking = async () => {
      try {
        // Dynamically import TensorFlow.js
        const tf = await import('@tensorflow/tfjs');
        const handPoseDetection = await import('@tensorflow-models/hand-pose-detection');
        
        await tf.ready();

        // Initialize detector (matching Python: max_num_hands=2, model_complexity=0)
        const model = (handPoseDetection.SupportedModels as any).MediaPipe;
        detector = await handPoseDetection.createDetector(model, {
          runtime: 'mediapipe' as any,
          modelType: 'lite' as any,
          maxHands: 2,
        });

        handsRef.current = detector;

        // Start video stream (1280x720 matching Python)
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 }
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          // Flip for mirror effect (matching Python: cv2.flip(frame, 1))
          videoRef.current.style.transform = 'scaleX(-1)';
          await videoRef.current.play();
        }

        // Process frames (matching Python HandTracker.run() exactly)
        const processFrame = async (currentTime: number) => {
          // Throttle to target FPS
          if (currentTime - lastFrameTime < frameInterval) {
            animationFrameId = requestAnimationFrame(processFrame);
            return;
          }
          lastFrameTime = currentTime;

          if (!videoRef.current || !detector || videoRef.current.readyState !== videoRef.current.HAVE_ENOUGH_DATA) {
            animationFrameId = requestAnimationFrame(processFrame);
            return;
          }

          try {
            const hands = await detector.estimateHands(videoRef.current, { flipHorizontal: false });
            
            // Initialize gesture variables (matching Python exactly)
            let rotDelta: [number, number, number] = [0, 0, 0];
            let scaleMult = 1.0;
            let tracking = false;

            if (hands && hands.length > 0) {
              tracking = true;
              const hand1 = hands[0];
              const keypoints = hand1.keypoints;
              
              // Find index tip (8) and thumb tip (4) - matching Python landmark indices
              const indexTip = keypoints.find((kp: any) => kp.name === 'index_finger_tip' || kp.name === 8);
              const thumbTip = keypoints.find((kp: any) => kp.name === 'thumb_tip' || kp.name === 4);
              
              if (indexTip && thumbTip) {
                // Calculate pinch distance (normalized, matching Python)
                const p1 = [indexTip.x, indexTip.y];
                const p2 = [thumbTip.x, thumbTip.y];
                const pinchDist = Math.sqrt(
                  Math.pow(p1[0] - p2[0], 2) + 
                  Math.pow(p1[1] - p2[1], 2)
                );

                // Gesture 1: One-handed Pinch to Rotate (matching Python exactly)
                if (pinchDist < Config.PINCH_THRESHOLD) {
                  const center = [
                    (p1[0] + p2[0]) / 2,
                    (p1[1] + p2[1]) / 2
                  ];
                  
                  if (lastPinchPos.current) {
                    // Calculate movement delta (matching Python: dx, dy * ROTATION_SENSITIVITY)
                    const dx = (center[0] - lastPinchPos.current.x) * Config.ROTATION_SENSITIVITY;
                    const dy = (center[1] - lastPinchPos.current.y) * Config.ROTATION_SENSITIVITY;
                    rotDelta = [dy, dx, 0]; // Pitch, Yaw (matching Python: (dy, dx, 0))
                  }
                  lastPinchPos.current = { x: center[0], y: center[1] };
                } else {
                  lastPinchPos.current = null;
                }

                // Gesture 2: Two-handed Zoom (matching Python)
                if (hands.length === 2) {
                  const hand2 = hands[1];
                  const h2Keypoints = hand2.keypoints;
                  const h1Index = keypoints.find((kp: any) => kp.name === 'index_finger_tip' || kp.name === 8);
                  const h2Index = h2Keypoints.find((kp: any) => kp.name === 'index_finger_tip' || kp.name === 8);
                  
                  if (h1Index && h2Index) {
                    // Distance between index fingers of both hands (matching Python)
                    const h1Pos = [h1Index.x, h1Index.y];
                    const h2Pos = [h2Index.x, h2Index.y];
                    const handDist = Math.sqrt(
                      Math.pow(h1Pos[0] - h2Pos[0], 2) + 
                      Math.pow(h1Pos[1] - h2Pos[1], 2)
                    );

                    if (lastHandDist.current !== null && lastHandDist.current > 0.01) {
                      // Ratio change (matching Python)
                      scaleMult = handDist / lastHandDist.current;
                    }
                    lastHandDist.current = handDist;
                  }
                } else {
                  lastHandDist.current = null;
                }
              }
            } else {
              // No hands detected - reset tracking (matching Python)
              lastPinchPos.current = null;
              lastHandDist.current = null;
            }

            // Update rotation and scale (matching Python update_loop exactly)
            if (rotDelta[0] !== 0 || rotDelta[1] !== 0 || rotDelta[2] !== 0) {
              currentRotation.current[0] += rotDelta[0];
              currentRotation.current[1] += rotDelta[1];
              currentRotation.current[2] += rotDelta[2];
            }

            if (scaleMult !== 1.0) {
              currentScale.current *= scaleMult;
              currentScale.current = Math.max(0.2, Math.min(5.0, currentScale.current));
            }

            // Callback for analytics
            if (tracking && onGestureUpdate) {
              onGestureUpdate([...currentRotation.current], currentScale.current);
            }
          } catch (error) {
            console.error('Hand detection error:', error);
          }
          
          animationFrameId = requestAnimationFrame(processFrame);
        };

        // Wait for video to be ready
        if (videoRef.current) {
          videoRef.current.addEventListener('loadedmetadata', () => {
            processFrame(performance.now());
          });
        }
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


  const getLoader = async (url: string): Promise<LoaderType> => {
    const ext = url.split('.').pop()?.toLowerCase();
    
    try {
      switch (ext) {
        case 'gltf':
        case 'glb': {
          const loaderModule = await import('three/examples/jsm/loaders/GLTFLoader.js');
          return new loaderModule.GLTFLoader();
        }
        case 'obj': {
          const loaderModule = await import('three/examples/jsm/loaders/OBJLoader.js');
          return new loaderModule.OBJLoader();
        }
        case 'stl': {
          const loaderModule = await import('three/examples/jsm/loaders/STLLoader.js');
          return new loaderModule.STLLoader();
        }
        case 'ply': {
          const loaderModule = await import('three/examples/jsm/loaders/PLYLoader.js');
          return new loaderModule.PLYLoader();
        }
        default: {
          const loaderModule = await import('three/examples/jsm/loaders/GLTFLoader.js');
          return new loaderModule.GLTFLoader();
        }
      }
    } catch (error) {
      console.error('Error loading Three.js loader:', error);
      const loaderModule = await import('three/examples/jsm/loaders/GLTFLoader.js');
      return new loaderModule.GLTFLoader();
    }
  };

  return (
    <div className="relative w-full h-screen bg-black">
      {/* Hidden video element for hand tracking and texture */}
      <video
        ref={videoRef}
        className="hidden"
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

      {/* 3D Canvas - matching Python plotter setup exactly */}
      <Canvas className="absolute top-0 left-0 w-full h-full">
        {/* Camera setup (matching Python: position=(0,0,10), focal_point=(0,0,0), up=(0,1,0)) */}
        <PerspectiveCamera 
          makeDefault 
          position={[0, 0, 10]} 
          fov={50}
        />
        
        {/* No ambient/point lights (matching Python: lighting=False) */}
        
        {/* AR Background Plane with video texture */}
        {videoRef.current && <BackgroundPlane videoRef={videoRef} />}
        
        {/* Dual mesh rendering: Inner ghost + Outer wireframe (matching Python exactly) */}
        {model && (
          <>
            <InnerMesh 
              model={model} 
              currentRotation={currentRotation}
              currentScale={currentScale}
            />
            <OuterMesh 
              model={model}
              currentRotation={currentRotation}
              currentScale={currentScale}
            />
          </>
        )}
      </Canvas>

      {/* Instructions overlay */}
      <div className="absolute bottom-4 left-4 z-50 bg-black bg-opacity-70 p-4 rounded-lg text-sm">
        <div className="text-cyan-400 mb-2">Jarvis Gesture Controls:</div>
        <div>• Pinch thumb & index finger + move = Rotate</div>
        <div>• Two hands: bring together/apart = Zoom</div>
      </div>
    </div>
  );
}
