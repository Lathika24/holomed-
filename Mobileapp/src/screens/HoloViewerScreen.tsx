import React, { useRef, useEffect, useState } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Text,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Camera, useCameraDevice, useFrameProcessor } from 'react-native-vision-camera';
import { useNavigation, useRoute } from '@react-navigation/native';
import { runOnJS } from 'react-native-reanimated';

interface HoloViewerScreenProps {
  route: {
    params: {
      model: {
        id: number;
        name: string;
        file_path: string;
        file_format: string;
      };
    };
  };
}

export default function HoloViewerScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { model } = (route.params as any) || {};
  const device = useCameraDevice('back');
  const [hasPermission, setHasPermission] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkCameraPermission();
  }, []);

  const checkCameraPermission = async () => {
    const status = await Camera.requestCameraPermission();
    setHasPermission(status === 'granted');
    setLoading(false);
  };

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';
    // Process frame for hand tracking
    // MediaPipe integration would go here
    // For now, this is a placeholder
  }, []);

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#00ffff" />
      </View>
    );
  }

  if (!hasPermission) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Camera permission required</Text>
        <TouchableOpacity
          style={styles.button}
          onPress={checkCameraPermission}
        >
          <Text style={styles.buttonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!device) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>No camera device found</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Camera
        style={StyleSheet.absoluteFill}
        device={device}
        isActive={true}
        frameProcessor={frameProcessor}
      />

      <View style={styles.overlay}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>

        <View style={styles.infoPanel}>
          <Text style={styles.modelName}>{model?.name || '3D Model'}</Text>
          <Text style={styles.instructions}>
            Gesture controls:{'\n'}
            • Pinch + move = Rotate{'\n'}
            • Two hands = Zoom
          </Text>
        </View>
      </View>

      {/* 3D Model rendering would go here */}
      {/* For now, this is a placeholder - you'd integrate Three.js or similar */}
      <View style={styles.modelPlaceholder}>
        <Text style={styles.placeholderText}>3D Model View</Text>
        <Text style={styles.placeholderSubtext}>
          Model: {model?.name}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 10,
  },
  backButton: {
    position: 'absolute',
    top: 50,
    left: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 12,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  infoPanel: {
    position: 'absolute',
    bottom: 50,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 16,
    borderRadius: 8,
  },
  modelName: {
    color: '#00ffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  instructions: {
    color: '#ffffff',
    fontSize: 14,
    lineHeight: 20,
  },
  modelPlaceholder: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 5,
  },
  placeholderText: {
    color: '#00ffff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  placeholderSubtext: {
    color: '#888888',
    fontSize: 16,
  },
  errorText: {
    color: '#ff0000',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#00ffff',
    padding: 16,
    borderRadius: 8,
    alignSelf: 'center',
  },
  buttonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
