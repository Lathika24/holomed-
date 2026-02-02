"""
HoloMed Backend API
FastAPI server for managing users, 3D models, and sessions
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
from datetime import datetime

from database import get_db, engine, Base
from models import User, Model3D, Session as SessionModel
from auth import verify_token, get_current_user, create_access_token, hash_password, verify_password
from schemas import UserCreate, UserResponse, ModelCreate, ModelResponse, SessionCreate, SessionResponse

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HoloMed API",
    description="Backend API for HoloMed - Holographic Medical Visualization",
    version="1.0.0"
)

# CORS configuration for web/mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "HoloMed API"}

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        subscription_tier="free"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        subscription_tier=new_user.subscription_tier,
        created_at=new_user.created_at
    )

@app.post("/api/auth/login")
async def login(user_data: UserCreate, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            subscription_tier=user.subscription_tier,
            created_at=user.created_at
        )
    }

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        subscription_tier=current_user.subscription_tier,
        created_at=current_user.created_at
    )

# 3D Model management endpoints
@app.post("/api/models/upload", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def upload_model(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a 3D model file"""
    # Validate file format
    allowed_formats = [".stl", ".obj", ".ply", ".vtk", ".gltf", ".glb"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_formats)}"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create database record
    new_model = Model3D(
        user_id=current_user.id,
        name=file.filename,
        file_path=file_path,
        file_format=file_ext[1:],  # Remove the dot
        file_size=len(content)
    )
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return ModelResponse(
        id=new_model.id,
        name=new_model.name,
        file_path=new_model.file_path,
        file_format=new_model.file_format,
        file_size=new_model.file_size,
        created_at=new_model.created_at
    )

@app.get("/api/models", response_model=List[ModelResponse])
async def list_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all models for the current user"""
    models = db.query(Model3D).filter(Model3D.user_id == current_user.id).all()
    return [
        ModelResponse(
            id=m.id,
            name=m.name,
            file_path=m.file_path,
            file_format=m.file_format,
            file_size=m.file_size,
            created_at=m.created_at
        )
        for m in models
    ]

@app.get("/api/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific model by ID"""
    model = db.query(Model3D).filter(
        Model3D.id == model_id,
        Model3D.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        file_path=model.file_path,
        file_format=model.file_format,
        file_size=model.file_size,
        created_at=model.created_at
    )

@app.delete("/api/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a model"""
    model = db.query(Model3D).filter(
        Model3D.id == model_id,
        Model3D.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Delete file if it exists
    if os.path.exists(model.file_path):
        os.remove(model.file_path)
    
    db.delete(model)
    db.commit()
    return None

# Session management endpoints
@app.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new visualization session"""
    # Verify model belongs to user
    model = db.query(Model3D).filter(
        Model3D.id == session_data.model_id,
        Model3D.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    new_session = SessionModel(
        user_id=current_user.id,
        model_id=session_data.model_id
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return SessionResponse(
        id=new_session.id,
        user_id=new_session.user_id,
        model_id=new_session.model_id,
        started_at=new_session.started_at,
        ended_at=new_session.ended_at
    )

@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all sessions for the current user"""
    sessions = db.query(SessionModel).filter(SessionModel.user_id == current_user.id).all()
    return [
        SessionResponse(
            id=s.id,
            user_id=s.user_id,
            model_id=s.model_id,
            started_at=s.started_at,
            ended_at=s.ended_at
        )
        for s in sessions
    ]

@app.patch("/api/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a session"""
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        model_id=session.model_id,
        started_at=session.started_at,
        ended_at=session.ended_at
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
