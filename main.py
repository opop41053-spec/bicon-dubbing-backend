import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai


# ============================================================
# BICON DUBBING STUDIO
# FastAPI Backend
# ============================================================

APP_NAME = "BICON DUBBING STUDIO API"
APP_VERSION = "2.0.0"

# ============================================================
# CONFIGURATION
# ============================================================

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

# ============================================================
# CORS
# ============================================================

# GitHub Pages
# Local frontend
# Common Codespaces forwarded HTTPS URLs
ALLOWED_ORIGINS = [
    "https://opop41053-spec.github.io",

    "http://localhost:3000",
    "http://127.0.0.1:3000",

    "http://localhost:5500",
    "http://127.0.0.1:5500",

    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Codespaces URLs normally look like:
# https://something-8000.app.github.dev
CODESPACES_ORIGIN_REGEX = (
    r"^https://[a-zA-Z0-9-]+-\d+\.app\.github\.dev$"
)


# ============================================================
# GOOGLE GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client: Optional[genai.Client] = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        # Never crash the backend just because the client
        # could not be initialized.
        gemini_client = None

# Gemini model used for speech transcription.
# This is the dedicated Gemini transcription model.
GEMINI_TRANSCRIBE_MODEL = "gemini-3.5-transcribe"

# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="BICON Dubbing Studio Backend API",
)


# ============================================================
# CORS MIDDLEWARE
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=CODESPACES_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================
# HELPERS
# ============================================================

def get_extension(filename: Optional[str]) -> str:
    if not filename:
        return ""

    return Path(filename).suffix.lower()


def validate_extension(filename: Optional[str]) -> str:
    extension = get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "UNSUPPORTED_FILE_TYPE",
                "message": (
                    "Unsupported file type. "
                    f"Allowed types: "
                    f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            },
        )

    return extension


async def save_upload_with_limit(
    upload_file: UploadFile,
    destination: str,
) -> int:
    """
    Saves an uploaded file in chunks.

    The 25 MB limit is enforced while reading,
    so oversized files are rejected safely.
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
                            "message": (
                                "Maximum allowed file size is 25 MB."
                            ),
                            "max_size_mb": 25,
                        },
                    )

                output_file.write(chunk)

    except HTTPException:
        safe_remove(destination)
        raise

    except Exception as exc:
        safe_remove(destination)

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
    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def normalize_language(language: Optional[str]) -> str:
    if not language:
        return "en"

    return language.strip().lower()


EXTENSION_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".mp4": "video/mp4",
    ".mpeg": "audio/mpeg",
    ".mpga": "audio/mpeg",
    ".flac": "audio/flac",
}


def get_safe_mime_type(upload_file: UploadFile, extension: str) -> str:
    content_type = (upload_file.content_type or "").strip().lower()
    if content_type:
        return content_type
    return EXTENSION_MIME_TYPES.get(extension, "application/octet-stream")


def safe_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    return message[:1000]


# ============================================================
# REQUEST MODELS
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
        "success": True,
        "name": APP_NAME,
        "status": "online",
        "version": APP_VERSION,
        "gemini_configured": gemini_client is not None,
        "max_upload_size_mb": 25,
        "routes": {
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
        "success": True,
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "gemini_configured": gemini_client is not None,
        "transcription_model": GEMINI_TRANSCRIBE_MODEL,
        "max_upload_size_mb": 25,
    }


# ============================================================
# API INFORMATION
# ============================================================

@app.get("/api")
async def api_info():
    return {
        "success": True,
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "gemini_configured": gemini_client is not None,
        "max_upload_size_mb": 25,
        "endpoints": [
            "GET /",
            "GET /health",
            "GET /api",
            "POST /api/upload",
            "POST /api/transcribe",
            "POST /api/translate",
            "POST /api/dubbing",
        ],
    }


# ============================================================
# POST /api/upload
# ============================================================

@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
):
    """
    Upload and validate an audio/video file.

    The file is stored temporarily only for validation
    and then deleted.
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
            "mode": "ready" if gemini_client is not None else "demo",
            "message": "File uploaded and validated successfully.",
            "filename": file.filename,
            "extension": extension,
            "size_bytes": file_size,
            "size_mb": round(
                file_size / (1024 * 1024),
                2,
            ),
            "max_size_mb": 25,
            "gemini_configured": gemini_client is not None,
        }

    finally:
        safe_remove(temporary_path)


# ============================================================
# POST /api/transcribe
# ============================================================

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
):
    """Speech-to-text using the Gemini Files API + Interactions API."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "stage": "request_validation",
                "error": "NO_FILENAME",
                "message": "No filename was provided.",
            },
        )

    extension = validate_extension(file.filename)
    mime_type = get_safe_mime_type(file, extension)
    temporary_path = None
    gemini_file = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temporary_path = temp_file.name

        try:
            file_size = await save_upload_with_limit(file, temporary_path)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            detail.setdefault("stage", "temporary_file_save")
            raise HTTPException(status_code=exc.status_code, detail=detail) from exc

        if file_size <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "stage": "temporary_file_save",
                    "error": "EMPTY_AUDIO_FILE",
                    "message": "The uploaded audio file is empty.",
                },
            )

        if gemini_client is None:
            return {
                "success": False,
                "mode": "demo",
                "endpoint": "/api/transcribe",
                "stage": "gemini_configuration",
                "error": "GEMINI_NOT_CONFIGURED",
                "message": "GEMINI_API_KEY is not configured on the backend.",
                "text": "",
                "filename": file.filename,
                "extension": extension,
                "mime_type": mime_type,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "gemini_configured": False,
            }

        # Stage 1: upload the saved audio to Gemini Files API.
        try:
            gemini_file = gemini_client.files.upload(file=temporary_path)
        except Exception as exc:
            return {
                "success": False,
                "mode": "gemini",
                "endpoint": "/api/transcribe",
                "stage": "gemini_files_upload",
                "error": "GEMINI_FILE_UPLOAD_FAILED",
                "message": safe_error_message(exc),
                "text": "",
                "filename": file.filename,
                "extension": extension,
                "mime_type": mime_type,
                "size_bytes": file_size,
                "gemini_configured": True,
            }

        gemini_uri = getattr(gemini_file, "uri", None)
        gemini_mime_type = getattr(gemini_file, "mime_type", None) or mime_type

        if not gemini_uri:
            return {
                "success": False,
                "mode": "gemini",
                "endpoint": "/api/transcribe",
                "stage": "gemini_files_upload",
                "error": "GEMINI_FILE_URI_MISSING",
                "message": "Gemini accepted the upload but did not return a file URI.",
                "text": "",
                "filename": file.filename,
                "mime_type": gemini_mime_type,
                "gemini_configured": True,
            }

        # Stage 2: send the uploaded file to the dedicated transcription model.
        try:
            interaction = gemini_client.interactions.create(
                model=GEMINI_TRANSCRIBE_MODEL,
                input=[
                    {
                        "type": "audio",
                        "uri": gemini_uri,
                        "mime_type": gemini_mime_type,
                    }
                ],
            )
        except Exception as exc:
            return {
                "success": False,
                "mode": "gemini",
                "endpoint": "/api/transcribe",
                "stage": "gemini_interaction",
                "error": "GEMINI_TRANSCRIPTION_REQUEST_FAILED",
                "message": safe_error_message(exc),
                "text": "",
                "filename": file.filename,
                "extension": extension,
                "mime_type": gemini_mime_type,
                "size_bytes": file_size,
                "model": GEMINI_TRANSCRIBE_MODEL,
                "gemini_configured": True,
            }

        # Stage 3: extract the documented output_text field.
        text = (getattr(interaction, "output_text", "") or "").strip()

        if not text:
            return {
                "success": False,
                "mode": "gemini",
                "endpoint": "/api/transcribe",
                "stage": "transcript_extraction",
                "error": "EMPTY_TRANSCRIPTION",
                "message": "Gemini completed the request but returned no transcript text. Check that the audio contains audible speech.",
                "text": "",
                "filename": file.filename,
                "extension": extension,
                "mime_type": gemini_mime_type,
                "size_bytes": file_size,
                "model": GEMINI_TRANSCRIBE_MODEL,
                "gemini_configured": True,
            }

        return {
            "success": True,
            "mode": "gemini",
            "endpoint": "/api/transcribe",
            "stage": "complete",
            "model": GEMINI_TRANSCRIBE_MODEL,
            "text": text,
            "filename": file.filename,
            "extension": extension,
            "mime_type": gemini_mime_type,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "gemini_configured": True,
        }

    finally:
        safe_remove(temporary_path)


# ============================================================
# POST /api/translate
# ============================================================

@app.post("/api/translate")
async def translate_text(
    request: TranslateRequest,
):
    """
    Text translation using Google Gemini.

    No Google Gemini API is used.
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

    if (
        source_language != "auto"
        and source_language == target_language
    ):
        return {
            "success": True,
            "mode": "passthrough",
            "endpoint": "/api/translate",
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": text,
            "gemini_configured": gemini_client is not None,
        }

    if gemini_client is None:
        return {
            "success": False,
            "mode": "demo",
            "endpoint": "/api/translate",
            "error": "GEMINI_NOT_CONFIGURED",
            "message": (
                "GEMINI_API_KEY is not configured. "
                "Add GEMINI_API_KEY to the backend environment."
            ),
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": "",
            "gemini_configured": False,
        }

    try:
        prompt = (
            "Translate the following text accurately.\n\n"
            f"Source language: {source_language}\n"
            f"Target language: {target_language}\n\n"
            "Return ONLY the translated text. "
            "Do not add explanations.\n\n"
            f"Text:\n{text}"
        )

        response = gemini_client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
        )

        translated_text = (
            getattr(response, "text", "")
            or ""
        ).strip()

        if not translated_text:
            return {
                "success": False,
                "mode": "gemini",
                "endpoint": "/api/translate",
                "stage": "translation_extraction",
                "error": "EMPTY_TRANSLATION",
                "message": "Gemini returned an empty translation.",
                "source_language": source_language,
                "target_language": target_language,
                "original_text": text,
                "translated_text": "",
                "gemini_configured": True,
            }

        return {
            "success": True,
            "mode": "gemini",
            "endpoint": "/api/translate",
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": translated_text,
            "gemini_configured": True,
        }

    except Exception as exc:
        return {
            "success": False,
            "mode": "gemini",
            "endpoint": "/api/translate",
            "stage": "translation_request",
            "error": "TRANSLATION_FAILED",
            "message": safe_error_message(exc),
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": "",
            "gemini_configured": True,
        }


# ============================================================
# POST /api/dubbing
# ============================================================

@app.post("/api/dubbing")
async def generate_dubbing(
    text: str = Form(...),
    target_language: str = Form("en"),
    voice: str = Form("alloy"),
    voice_reference: Optional[UploadFile] = File(None),
):
    """
    Dubbing endpoint placeholder.

    Google Gemini TTS/voice-cloning calls have been removed.
    Gemini transcription and translation are supported by this backend.

    This endpoint currently validates the request but does not generate
    an audio file. A Gemini TTS implementation can be added separately
    if audio synthesis is required.
    """

    text = text.strip()

    target_language = normalize_language(
        target_language
    )

    voice = (
        voice.strip()
        if voice
        else "alloy"
    )

    if not text:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "EMPTY_TEXT",
                "message": "Dubbing text cannot be empty.",
            },
        )

    reference_path = None
    reference_size = 0
    reference_filename = None

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

        reference_filename = voice_reference.filename
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

    safe_remove(reference_path)

    return {
        "success": False,
        "mode": "not_implemented",
        "endpoint": "/api/dubbing",
        "stage": "tts_not_configured",
        "error": "TTS_NOT_CONFIGURED",
        "message": (
            "Google Gemini TTS has been removed. "
            "This backend currently uses Gemini for transcription "
            "and translation only."
        ),
        "target_language": target_language,
        "voice": voice,
        "text": text,
        "audio_generated": False,
        "audio_url": None,
        "voice_cloning": False,
        "voice_reference_received": reference_filename is not None,
        "voice_reference_filename": reference_filename,
        "voice_reference_size_bytes": reference_size,
        "gemini_configured": gemini_client is not None,
    }


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "8000",
            )
        ),
        reload=False,
    )
