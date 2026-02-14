# HoloMed Codebase - Errors and Required Fixes

## 🔴 Critical Issues

### 1. Backend - Missing Static File Serving
**Location:** `backend/main.py`
**Issue:** Uploaded files are saved to disk but there's no endpoint to serve them. Frontend cannot access uploaded models.
**Fix Required:** Add a static file serving endpoint using FastAPI's `StaticFiles` or `FileResponse`.

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add after app creation
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Or add a specific endpoint:
@app.get("/api/models/{model_id}/file")
async def get_model_file(model_id: str, current_user: User = Depends(get_current_user)):
    # ... validation logic ...
    return FileResponse(model.file_path)
```

---

### 2. Backend - Deprecated `datetime.utcnow()`
**Location:** `backend/models.py`, `backend/main.py`, `backend/auth.py`
**Issue:** `datetime.utcnow()` is deprecated in Python 3.12+. Should use `datetime.now(timezone.utc)`.
**Files Affected:**
- `backend/models.py` (lines 15, 28, 38)
- `backend/main.py` (line 328)
- `backend/auth.py` (lines 36, 38)

**Fix Required:**
```python
from datetime import datetime, timezone

# Replace all instances of:
datetime.utcnow()
# With:
datetime.now(timezone.utc)
```

---

### 3. Backend - Bare Exception Handlers
**Location:** `backend/main.py`, `backend/auth.py`
**Issue:** Using bare `except:` clauses catches all exceptions including system exits, making debugging difficult.
**Files Affected:**
- `backend/main.py` (lines 187, 221, 254, 311)
- `backend/auth.py` (line 73)

**Fix Required:**
```python
# Replace:
except:
    raise HTTPException(...)

# With:
except (ValueError, TypeError) as e:
    raise HTTPException(...)
# Or more specifically:
except Exception as e:
    raise HTTPException(...)
```

---

### 4. Frontend - Incorrect Three.js Loader Imports
**Location:** `Webapp/src/components/HoloViewer.tsx` (lines 233-283)
**Issue:** Dynamic imports using string paths like `three/addons/loaders/GLTFLoader.js` won't work in Next.js. Need to use proper imports from `three/examples/jsm/loaders/`.

**Fix Required:**
```typescript
// Replace the getLoader function with:
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js';

const getLoader = (url: string) => {
  const ext = url.split('.').pop()?.toLowerCase();
  
  switch (ext) {
    case 'gltf':
    case 'glb':
      return new GLTFLoader();
    case 'obj':
      return new OBJLoader();
    case 'stl':
      return new STLLoader();
    case 'ply':
      return new PLYLoader();
    default:
      return new GLTFLoader();
  }
};
```

---

### 5. Type Mismatch - ID Types
**Location:** Multiple files
**Issue:** Backend returns string IDs (ObjectId as string), but frontend interfaces expect `number`.

**Files Affected:**
- `Webapp/src/store/authStore.ts` (line 6: `id: number`)
- `Webapp/src/components/ModelSelector.tsx` (line 9: `id: number`)
- `Mobileapp/src/store/authStore.ts` (line 7: `id: number`)

**Fix Required:**
```typescript
// Change all instances of:
interface User {
  id: number;  // ❌
  // ...
}

// To:
interface User {
  id: string;  // ✅
  // ...
}
```

---

## ⚠️ High Priority Issues

### 6. Backend - Hardcoded Secret Key
**Location:** `backend/auth.py` (line 15)
**Issue:** JWT secret key is hardcoded. Should use environment variable.
**Fix Required:**
```python
import os
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
if SECRET_KEY == "your-secret-key-change-in-production":
    raise ValueError("SECRET_KEY environment variable must be set in production")
```

---

### 7. Backend - CORS Allows All Origins
**Location:** `backend/main.py` (line 40)
**Issue:** `allow_origins=["*"]` is insecure for production.
**Fix Required:**
```python
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8081").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 8. Frontend - Model File Path Construction
**Location:** `Webapp/src/components/ModelSelector.tsx` (lines 72-76)
**Issue:** File path construction assumes files are served from root, but they're in `/uploads/` directory.
**Fix Required:**
```typescript
const handleModelSelect = (model: Model) => {
  const modelUrl = model.file_path.startsWith('http') 
    ? model.file_path 
    : `${API_URL}/uploads/${model.file_path.replace('uploads/', '')}`;
  onSelect(modelUrl);
};
```

---

### 9. Backend - Missing File Validation
**Location:** `backend/main.py` (line 124)
**Issue:** File extension check doesn't handle cases where filename might be None or empty.
**Fix Required:**
```python
if not file.filename:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Filename is required"
    )
file_ext = os.path.splitext(file.filename)[1].lower()
```

---

### 10. Backend - Missing Error Handling for File Operations
**Location:** `backend/main.py` (lines 139-140, 239-240)
**Issue:** File read/write operations don't have error handling.
**Fix Required:**
```python
try:
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)
except IOError as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to save file: {str(e)}"
    )
```

---

## 🔧 Medium Priority Issues

### 11. Backend - Missing Dependencies (Linter Warnings)
**Location:** `backend/database.py`
**Issue:** Linter shows warnings for `beanie` and `motor` imports, but they're in requirements.txt. This is likely a Python environment issue, but should be verified.

**Fix Required:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Verify imports work

---

### 12. Frontend - Unused Imports
**Location:** `Webapp/src/components/HoloViewer.tsx`
**Issue:** `OrbitControls`, `Environment`, `useGLTF` are imported but not used.
**Fix Required:** Remove unused imports:
```typescript
// Remove:
import { OrbitControls, Environment, useGLTF } from '@react-three/drei';
```

---

### 13. Frontend - Missing Error Boundaries
**Location:** `Webapp/src/app/page.tsx`, `Mobileapp/src/App.tsx`
**Issue:** No error boundaries to catch React errors gracefully.
**Fix Required:** Add React error boundaries around main components.

---

### 14. Backend - Database Connection Error Handling
**Location:** `backend/database.py` (line 21)
**Issue:** No error handling if MongoDB connection fails.
**Fix Required:**
```python
async def init_db():
    global client
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        # Test connection
        await client.admin.command('ping')
        # ... rest of initialization
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
```

---

### 15. Frontend - HoloViewer Material Application
**Location:** `Webapp/src/components/HoloViewer.tsx` (lines 324-348)
**Issue:** Material is applied incorrectly to cloned primitives. Materials should be applied to meshes within the group, not the group itself.
**Fix Required:** Traverse the model and apply materials to individual meshes.

---

## 📝 Low Priority / Code Quality Issues

### 16. Backend - Inconsistent Error Messages
**Location:** Multiple files
**Issue:** Error messages vary in detail and format.
**Fix Required:** Standardize error message format across all endpoints.

---

### 17. Backend - Missing Input Validation
**Location:** `backend/main.py` (upload endpoint)
**Issue:** No file size limit validation.
**Fix Required:**
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
content = await file.read()
if len(content) > MAX_FILE_SIZE:
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File size exceeds maximum of {MAX_FILE_SIZE / 1024 / 1024}MB"
    )
```

---

### 18. Frontend - Missing Loading States
**Location:** `Webapp/src/components/ModelSelector.tsx`
**Issue:** Upload mutation doesn't show proper loading feedback.
**Fix Required:** Already has `uploading` state, but could improve UX with progress indicator.

---

### 19. Backend - Missing API Documentation
**Location:** `backend/main.py`
**Issue:** Some endpoints lack detailed docstrings.
**Fix Required:** Add comprehensive docstrings with examples.

---

### 20. Security - File Upload Path Traversal
**Location:** `backend/main.py` (line 137)
**Issue:** Filename from user input could contain path traversal sequences.
**Fix Required:**
```python
import os
from pathlib import Path

# Sanitize filename
safe_filename = os.path.basename(file.filename)  # Remove any path components
file_path = os.path.join(upload_dir, f"{current_user.id}_{datetime.now().timestamp()}_{safe_filename}")
```

---

## 📋 Summary

### Critical (Must Fix):
1. ✅ Add static file serving endpoint
2. ✅ Fix deprecated `datetime.utcnow()`
3. ✅ Fix bare exception handlers
4. ✅ Fix Three.js loader imports
5. ✅ Fix ID type mismatches

### High Priority:
6. ✅ Move secret key to environment variable
7. ✅ Configure CORS properly
8. ✅ Fix model file path construction
9. ✅ Add file validation
10. ✅ Add file operation error handling

### Medium Priority:
11. ✅ Verify Python dependencies
12. ✅ Remove unused imports
13. ✅ Add error boundaries
14. ✅ Add database connection error handling
15. ✅ Fix material application in HoloViewer

### Low Priority:
16-20. Code quality and security improvements

---

## 🚀 Quick Fix Checklist

- [ ] Fix all `datetime.utcnow()` calls
- [ ] Replace bare `except:` clauses
- [ ] Add static file serving endpoint
- [ ] Fix Three.js loader imports
- [ ] Update all ID types from `number` to `string`
- [ ] Move SECRET_KEY to environment variable
- [ ] Configure CORS with specific origins
- [ ] Add file path sanitization
- [ ] Add file size validation
- [ ] Add database connection error handling
