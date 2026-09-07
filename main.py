import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI


# ============================================================
# BICON DUBBING STUDIO - FASTAPI BACKEND
# ============================================================

APP_NAME = "BICON DUBBING STUDIO API"
APP_VERSION = "2.0.0"

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".webm",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".flac",
}

# GitHub Pages + common local development origins
ALLOWED_ORIGINS = [
    "https://opop41053-spec.github.io",

    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# ------------------------------------------------------------
# OpenAI configuration
# ------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client: Optional[OpenAI] = None

if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client = None


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Backend API for BICON Dubbing Studio",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================
# Helper functions
# ============================================================

def get_extension(filename: Optional[str]) -> str:
    """
    Safely return a lowercase file extension.
    """
    if not filename:
        return ""

    return Path(filename).suffix.lower()


def validate_extension(filename: Optional[str]) -> str:
    """
    Validate the uploaded file extension.
    """
    extension = get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "UNSUPPORTED_FILE_TYPE",
                "message": (
                    f"Unsupported file type: {extension or 'unknown'}. "
                    f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            },
        )

    return extension


async def save_upload_with_limit(
    upload_file: UploadFile,
    destination: str,
) -> int:
    """
    Save an UploadFile in chunks while enforcing the 25 MB limit.

    Returns:
        int: number of bytes written.
    """

    total_size = 0
    chunk_size = 1024 * 1024  # 1 MB

    try:
        with open(destination, "wb") as output_file:

            while True:
                chunk = await upload_file.read(chunk_size)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_AUDIO_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "success": False,
                            "error": "FILE_TOO_LARGE",
                            "message": "Maximum allowed file size is 25 MB.",
                            "max_size_mb": 25,
                        },
                    )

                output_file.write(chunk)

    except HTTPException:
        try:
            os.remove(destination)
        except OSError:
            pass
        raise

    except Exception as exc:
        try:
            os.remove(destination)
        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "UPLOAD_SAVE_FAILED",
                "message": str(exc),
            },
        )

    finally:
        await upload_file.close()

    return total_size


def safe_remove(path: Optional[str]) -> None:
    """
    Safely delete a temporary file.
    """
    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def normalize_language(language: Optional[str]) -> str:
    """
    Normalize language input.
    """
    if not language:
        return "en"

    return language.strip().lower()


# ============================================================
# Request models
# ============================================================

class TranslateRequest(BaseModel):
    text: str
    source_language: str = "auto"
    target_language: str = "en"


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "status": "online",
        "version": APP_VERSION,
        "openai_configured": client is not None,
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /api/upload",
            "transcribe": "POST /api/transcribe",
            "translate": "POST /api/translate",
            "dubbing": "POST /api/dubbing",
        },
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "openai_configured": client is not None,
        "max_upload_size_mb": 25,
    }


# ============================================================
# UPLOAD
# ============================================================

@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
):
    """
    Upload an audio/video file.

    The file is temporarily stored only for validation.
    It is deleted after the response is prepared.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "NO_FILENAME",
                "message": "No filename was provided.",
            },
        )

    extension = validate_extension(file.filename)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temporary_path = temp_file.name

        file_size = await save_upload_with_limit(
            file,
            temporary_path,
        )

        return {
            "success": True,
            "message": "File uploaded successfully.",
            "filename": file.filename,
            "extension": extension,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "max_size_mb": 25,
            "openai_configured": client is not None,
        }

    finally:
        safe_remove(temporary_path)


# ============================================================
# TRANSCRIBE
# ============================================================

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
):
    """
    Convert uploaded audio to text.

    If OPENAI_API_KEY is configured:
        Uses OpenAI transcription.

    If OPENAI_API_KEY is missing:
        Returns a structured demo response instead of crashing.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "NO_FILENAME",
                "message": "No filename was provided.",
            },
        )

    extension = validate_extension(file.filename)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temporary_path = temp_file.name

        file_size = await save_upload_with_limit(
            file,
            temporary_path,
        )

        # ----------------------------------------------------
        # DEMO MODE: OpenAI key not configured
        # ----------------------------------------------------

        if client is None:
            return {
                "success": True,
                "mode": "demo",
                "message": (
                    "Transcription endpoint is working, "
                    "but OPENAI_API_KEY is not configured."
                ),
                "text": (
                    "[DEMO TRANSCRIPT] "
                    "OpenAI transcription is disabled because no API key "
                    "is configured on the backend."
                ),
                "filename": file.filename,
                "size_bytes": file_size,
                "openai_configured": False,
            }

        # ----------------------------------------------------
        # REAL MODE
        # ----------------------------------------------------

        try:
            with open(temporary_path, "rb") as audio_file:

                result = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file,
                )

            text = getattr(result, "text", "") or ""

            return {
                "success": True,
                "mode": "openai",
                "text": text,
                "filename": file.filename,
                "size_bytes": file_size,
                "openai_configured": True,
            }

        except Exception as exc:

            # Do not let OpenAI/API errors crash the application.
            return {
                "success": False,
                "mode": "openai",
                "error": "TRANSCRIPTION_FAILED",
                "message": str(exc),
                "text": "",
                "openai_configured": True,
            }

    finally:
        safe_remove(temporary_path)


# ============================================================
# TRANSLATE
# ============================================================

@app.post("/api/translate")
async def translate_text(request: TranslateRequest):
    """
    Translate transcript text.

    If OpenAI is configured:
        Attempts translation using the OpenAI Responses API.

    If OpenAI is not configured:
        Returns a structured demo translation.
    """

    text = request.text.strip()

    source_language = normalize_language(
        request.source_language
    )

    target_language = normalize_language(
        request.target_language
    )

    if not text:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "EMPTY_TEXT",
                "message": "Text cannot be empty.",
            },
        )

    # --------------------------------------------------------
    # Same-language shortcut
    # --------------------------------------------------------

    if (
        source_language != "auto"
        and source_language == target_language
    ):
        return {
            "success": True,
            "mode": "passthrough",
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": text,
            "openai_configured": client is not None,
        }

    # --------------------------------------------------------
    # DEMO MODE
    # --------------------------------------------------------

    if client is None:
        return {
            "success": True,
            "mode": "demo",
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": (
                f"[DEMO TRANSLATION → {target_language}] {text}"
            ),
            "message": (
                "Translation endpoint is working, but "
                "OPENAI_API_KEY is not configured."
            ),
            "openai_configured": False,
        }

    # --------------------------------------------------------
    # REAL MODE
    # --------------------------------------------------------

    try:
        prompt = (
            "Translate the following text accurately.\n"
            f"Source language: {source_language}\n"
            f"Target language: {target_language}\n\n"
            "Return only the translated text. "
            "Do not add explanations.\n\n"
            f"Text:\n{text}"
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
        )

        translated_text = getattr(
            response,
            "output_text",
            "",
        ) or ""

        translated_text = translated_text.strip()

        if not translated_text:
            return {
                "success": False,
                "mode": "openai",
                "error": "EMPTY_TRANSLATION",
                "message": "OpenAI returned an empty translation.",
                "source_language": source_language,
                "target_language": target_language,
                "original_text": text,
                "translated_text": "",
                "openai_configured": True,
            }

        return {
            "success": True,
            "mode": "openai",
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": translated_text,
            "openai_configured": True,
        }

    except Exception as exc:

        return {
            "success": False,
            "mode": "openai",
            "error": "TRANSLATION_FAILED",
            "message": str(exc),
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": "",
            "openai_configured": True,
        }


# ============================================================
# DUBBING / TEXT-TO-SPEECH
# ============================================================

@app.post("/api/dubbing")
async def generate_dubbing(
    text: str = Form(...),
    target_language: str = Form("en"),
    voice: str = Form("alloy"),
    voice_reference: Optional[UploadFile] = File(None),
):
    """
    Generate speech from translated text.

    IMPORTANT:
    This endpoint does NOT perform voice cloning.

    With OpenAI configured:
        Generates standard TTS audio.

    Without OpenAI configured:
        Returns structured demo JSON.

    voice_reference:
        Accepted as an optional uploaded reference, but it is not
        used for cloning in this implementation.
    """

    text = text.strip()
    target_language = normalize_language(target_language)
    voice = voice.strip() or "alloy"

    if not text:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "EMPTY_TEXT",
                "message": "Dubbing text cannot be empty.",
            },
        )

    # --------------------------------------------------------
    # Validate voice reference if supplied
    # --------------------------------------------------------

    reference_path = None
    reference_size = 0

    if voice_reference is not None:

        if not voice_reference.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "INVALID_VOICE_REFERENCE",
                    "message": "Voice reference filename is missing.",
                },
            )

        reference_extension = validate_extension(
            voice_reference.filename
        )

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=reference_extension,
            ) as temp_file:
                reference_path = temp_file.name

            reference_size = await save_upload_with_limit(
                voice_reference,
                reference_path,
            )

        except Exception:
            safe_remove(reference_path)
            raise

    # --------------------------------------------------------
    # DEMO MODE
    # --------------------------------------------------------

    if client is None:

        safe_remove(reference_path)

        return {
            "success": True,
            "mode": "demo",
            "message": (
                "Dubbing endpoint is working, but "
                "OPENAI_API_KEY is not configured. "
                "No audio was generated."
            ),
            "target_language": target_language,
            "voice": voice,
            "text": text,
            "audio_generated": False,
            "audio_url": None,
            "voice_reference_received": reference_path is not None,
            "voice_reference_size_bytes": reference_size,
            "voice_cloning": False,
            "openai_configured": False,
        }

    # --------------------------------------------------------
    # REAL TTS MODE
    # --------------------------------------------------------

    output_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3",
        ) as output_file:
            output_path = output_file.name

        try:

            with open(output_path, "wb") as audio_output:

                response = client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice=voice,
                    input=text,
                    response_format="mp3",
                )

                response.write_to_file(output_path)

            # ------------------------------------------------
            # Return generated MP3
            # ------------------------------------------------

            return FileResponse(
                path=output_path,
                media_type="audio/mpeg",
                filename="bicon_dubbed_audio.mp3",
                background=None,
            )

        except Exception as exc:

            safe_remove(output_path)

            return {
                "success": False,
                "mode": "openai",
                "error": "DUBBING_FAILED",
                "message": str(exc),
                "target_language": target_language,
                "voice": voice,
                "text": text,
                "audio_generated": False,
                "audio_url": None,
                "voice_cloning": False,
                "openai_configured": True,
            }

    finally:
        safe_remove(reference_path)


# ============================================================
# OPTIONS / API information
# ============================================================

@app.get("/api")
async def api_info():
    return {
        "success": True,
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "openai_configured": client is not None,
        "max_upload_size_mb": 25,
        "routes": {
            "GET /": "API information",
            "GET /health": "Health check",
            "GET /api": "API information",
            "POST /api/upload": "Upload and validate media",
            "POST /api/transcribe": "Speech-to-text",
            "POST /api/translate": "Text translation",
            "POST /api/dubbing": "Text-to-speech",
        },
    }


# ============================================================
# LOCAL DEVELOPMENT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
