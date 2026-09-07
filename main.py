import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BICON DUBBING STUDIO API",
    version="2.0.0"
)

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://opop41053-spec.github.io",
        "https://opop41053-spec.github.io/",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MAX_AUDIO_SIZE = 25 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".webm",
    ".flac",
    ".mpeg",
    ".mpga",
}

# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
async def root():
    return {
        "name": "BICON DUBBING STUDIO API",
        "status": "online",
        "version": "2.0.0"
    }

# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "backend": "BICON DUBBING STUDIO",
        "api_keys_required": False
    }

# ---------------------------------------------------------
# Audio Upload
# ---------------------------------------------------------

@app.post("/api/upload")
async def upload_audio(file: UploadFile = File(...)):

    filename = file.filename or "audio"

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format."
        )

    audio_data = await file.read()

    if not audio_data:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty."
        )

    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio file is larger than 25 MB."
        )

    return {
        "success": True,
        "filename": filename,
        "size": len(audio_data),
        "content_type": file.content_type,
        "message": "Audio received successfully."
    }

# ---------------------------------------------------------
# Transcription
# ---------------------------------------------------------

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...)
):

    filename = file.filename or "audio"

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format."
        )

    audio_data = await file.read()

    if not audio_data:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty."
        )

    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio file is larger than 25 MB."
        )

    return {
        "success": False,
        "status": "engine_not_connected",
        "text": "",
        "message": (
            "The audio upload was received, "
            "but a speech-to-text engine has not been connected yet."
        )
    }

# ---------------------------------------------------------
# Translation
# ---------------------------------------------------------

@app.post("/api/translate")
async def translate(data: dict):

    text = str(data.get("text", "")).strip()
    source_language = str(
        data.get("source_language", "")
    ).strip()
    target_language = str(
        data.get("target_language", "")
    ).strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text is required."
        )

    if not target_language:
        raise HTTPException(
            status_code=400,
            detail="Target language is required."
        )

    return {
        "success": False,
        "status": "engine_not_connected",
        "translated_text": "",
        "source_language": source_language,
        "target_language": target_language,
        "message": (
            "Translation engine has not been connected yet."
        )
    }

# ---------------------------------------------------------
# Dubbing
# ---------------------------------------------------------

@app.post("/api/dubbing")
async def dubbing(data: dict):

    text = str(data.get("text", "")).strip()
    source_language = str(
        data.get("source_language", "")
    ).strip()
    target_language = str(
        data.get("target_language", "")
    ).strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text is required."
        )

    return {
        "success": False,
        "status": "voice_engine_not_connected",
        "source_language": source_language,
        "target_language": target_language,
        "message": (
            "Authorized voice-generation engine "
            "has not been connected yet."
        )
    }
