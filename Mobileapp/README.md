# HoloMed Mobile Application

React Native mobile application for HoloMed - Holographic Medical Visualization Platform.

## Features

- 📱 Native iOS and Android support
- 📷 Camera integration for hand tracking
- 🎭 3D model visualization
- 📤 Upload and manage 3D models
- 🔐 User authentication
- 🤲 Gesture-based interaction

## Prerequisites

- Node.js 18+
- React Native development environment set up
- iOS: Xcode and CocoaPods
- Android: Android Studio and Android SDK
- Backend API running (see backend/README.md)

## Setup

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. For iOS, install CocoaPods:
```bash
cd ios && pod install && cd ..
```

3. Configure API URL in:
   - `src/screens/HomeScreen.tsx`
   - `src/screens/LoginScreen.tsx`
   - `src/store/authStore.ts`

   Change `const API_URL = 'http://localhost:8000';` to your backend URL.

   For Android emulator, use `http://10.0.2.2:8000`
   For iOS simulator, use `http://localhost:8000`
   For physical devices, use your computer's IP address: `http://YOUR_IP:8000`

## Running the App

### iOS
```bash
npm run ios
# or
yarn ios
```

### Android
```bash
npm run android
# or
yarn android
```

## Building for Production

### iOS
```bash
cd ios
xcodebuild -workspace HoloMed.xcworkspace -scheme HoloMed -configuration Release
```

### Android
```bash
cd android
./gradlew assembleRelease
```

## Permissions

The app requires camera permissions for hand tracking. These are automatically requested when the app starts.

## Troubleshooting

- **Camera not working**: Ensure camera permissions are granted in device settings
- **Cannot connect to backend**: Check that the API_URL is correct for your device/emulator
- **Build errors**: Make sure all dependencies are installed and native modules are properly linked

## Development Notes

- MediaPipe integration for hand tracking is a placeholder - full implementation would require native MediaPipe SDK integration
- 3D model rendering is a placeholder - would need Three.js React Native or similar library
- File upload uses react-native-document-picker (needs to be added to package.json)

## Next Steps

1. Integrate MediaPipe native SDK for hand tracking
2. Add Three.js or React Native 3D rendering library
3. Implement full gesture recognition
4. Add model preview thumbnails
5. Implement offline mode
