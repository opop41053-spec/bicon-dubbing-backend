import os
import asyncio
import base64
import tempfile
import time
import wave
import uuid
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
APP_VERSION = "2.1.0"

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

# Gemini text-to-speech configuration.
GEMINI_TTS_MODEL = "gemini-3.1-flash-tts-preview"
GEMINI_DEFAULT_TTS_VOICE = "Kore"

# Gemini translation configuration.
# Temporary 503/high-demand failures are retried automatically.
GEMINI_TRANSLATION_PRIMARY_MODEL = "gemini-3.7-flash"
GEMINI_TRANSLATION_FALLBACK_MODEL = "gemini-3.6-flash"
GEMINI_TRANSLATION_RETRIES = 3
GEMINI_TRANSLATION_BACKOFF_SECONDS = 1.5

OUTPUT_DIR = Path(tempfile.gettempdir()) / "bicon_dubbing_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Small audio files can be sent inline. This avoids the Gemini Files API
# processing-state race (PROCESSING -> ACTIVE) for short browser recordings.
# Keep this below the documented 20 MB inline-audio request limit because
# base64 encoding increases the request size.
INLINE_AUDIO_MAX_BYTES = 15 * 1024 * 1024
GEMINI_FILE_ACTIVE_TIMEOUT_SECONDS = 60
GEMINI_FILE_POLL_SECONDS = 2

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
# GEMINI TRANSLATION RETRY HELPERS
# ============================================================

def is_temporary_gemini_unavailable(exc: Exception) -> bool:
    """Return True for Gemini temporary 503/high-demand failures."""
    message = safe_error_message(exc).lower()
    return (
        "503" in message
        or "unavailable" in message
        or "high demand" in message
        or "temporarily unavailable" in message
        or "service unavailable" in message
    )


async def generate_translation_with_retry(prompt: str):
    """
    Try the primary translation model with exponential backoff.
    If temporary 503/high-demand errors continue, use a stable fallback.
    """
    models_to_try = [
        GEMINI_TRANSLATION_PRIMARY_MODEL,
        GEMINI_TRANSLATION_FALLBACK_MODEL,
    ]

    last_exception = None
    attempts = 0

    for model_index, model_name in enumerate(models_to_try):
        max_attempts = (
            GEMINI_TRANSLATION_RETRIES
            if model_index == 0
            else 1
        )

        for attempt_index in range(max_attempts):
            attempts += 1

            try:
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response, model_name, attempts

            except Exception as exc:
                last_exception = exc

                # Retry only transient availability/high-demand failures.
                if not is_temporary_gemini_unavailable(exc):
                    raise

                if attempt_index < max_attempts - 1:
                    delay = (
                        GEMINI_TRANSLATION_BACKOFF_SECONDS
                        * (2 ** attempt_index)
                    )
                    await asyncio.sleep(delay)
                    continue

                # Primary model exhausted: give the fallback model a chance.
                if model_index == 0:
                    await asyncio.sleep(1.0)

    if last_exception is not None:
        raise last_exception

    raise RuntimeError("Gemini translation failed without an exception.")


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
    """
    Speech-to-text using Gemini 3.5 Transcribe.

    Strategy:
      1. Save and validate the upload locally.
      2. For small audio (<= 15 MB), send it inline as base64.
         This avoids the Gemini Files API processing-state race.
      3. For larger audio, use Gemini Files API and explicitly wait until
         the uploaded file reaches ACTIVE before calling the model.
    """

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

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temporary_path = temp_file.name

        try:
            file_size = await save_upload_with_limit(file, temporary_path)
        except HTTPException as exc:
            detail = (
                exc.detail
                if isinstance(exc.detail, dict)
                else {"message": str(exc.detail)}
            )
            detail.setdefault("stage", "temporary_file_save")
            raise HTTPException(
                status_code=exc.status_code,
                detail=detail,
            ) from exc

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

        # --------------------------------------------------------
        # PATH A: SMALL AUDIO -> INLINE BASE64
        # --------------------------------------------------------
        if file_size <= INLINE_AUDIO_MAX_BYTES:
            try:
                with open(temporary_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()

                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

                interaction = gemini_client.interactions.create(
                    model=GEMINI_TRANSCRIBE_MODEL,
                    input=[
                        {
                            "type": "text",
                            "text": "Generate a transcript of the speech. Return only the spoken transcript text.",
                        },
                        {
                            "type": "audio",
                            "data": audio_b64,
                            "mime_type": mime_type,
                        },
                    ],
                )

                text = (
                    getattr(interaction, "output_text", "") or ""
                ).strip()

                if not text:
                    return {
                        "success": False,
                        "mode": "gemini_inline",
                        "endpoint": "/api/transcribe",
                        "stage": "transcript_extraction",
                        "error": "EMPTY_TRANSCRIPTION",
                        "message": "Gemini completed the request but returned no transcript text. Check that the audio contains audible speech.",
                        "text": "",
                        "filename": file.filename,
                        "extension": extension,
                        "mime_type": mime_type,
                        "size_bytes": file_size,
                        "model": GEMINI_TRANSCRIBE_MODEL,
                        "gemini_configured": True,
                    }

                return {
                    "success": True,
                    "mode": "gemini_inline",
                    "endpoint": "/api/transcribe",
                    "stage": "complete",
                    "model": GEMINI_TRANSCRIBE_MODEL,
                    "text": text,
                    "filename": file.filename,
                    "extension": extension,
                    "mime_type": mime_type,
                    "size_bytes": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "transport": "inline_base64",
                    "gemini_configured": True,
                }

            except Exception as exc:
                return {
                    "success": False,
                    "mode": "gemini_inline",
                    "endpoint": "/api/transcribe",
                    "stage": "gemini_interaction_inline",
                    "error": "GEMINI_TRANSCRIPTION_REQUEST_FAILED",
                    "message": safe_error_message(exc),
                    "text": "",
                    "filename": file.filename,
                    "extension": extension,
                    "mime_type": mime_type,
                    "size_bytes": file_size,
                    "model": GEMINI_TRANSCRIBE_MODEL,
                    "transport": "inline_base64",
                    "gemini_configured": True,
                }

        # --------------------------------------------------------
        # PATH B: LARGE AUDIO -> FILES API + WAIT FOR ACTIVE
        # --------------------------------------------------------
        try:
            gemini_file = gemini_client.files.upload(file=temporary_path)
        except Exception as exc:
            return {
                "success": False,
                "mode": "gemini_files",
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

        file_name = getattr(gemini_file, "name", None)
        gemini_uri = getattr(gemini_file, "uri", None)
        gemini_mime_type = getattr(gemini_file, "mime_type", None) or mime_type

        if not file_name or not gemini_uri:
            return {
                "success": False,
                "mode": "gemini_files",
                "endpoint": "/api/transcribe",
                "stage": "gemini_files_upload",
                "error": "GEMINI_FILE_METADATA_MISSING",
                "message": "Gemini accepted the upload but did not return the required file name/URI.",
                "text": "",
                "filename": file.filename,
                "mime_type": gemini_mime_type,
                "gemini_configured": True,
            }

        # Gemini Files can initially be PROCESSING. It must be ACTIVE before
        # the file URI is used for inference. This is the exact failure seen
        # in the user's diagnostic board.
        deadline = time.monotonic() + GEMINI_FILE_ACTIVE_TIMEOUT_SECONDS
        current_file = gemini_file
        last_state = None

        while True:
            state = getattr(current_file, "state", None)
            state_name = getattr(state, "name", None) or str(state or "")
            last_state = state_name

            if state_name.upper() == "ACTIVE":
                break

            if state_name.upper() == "FAILED":
                file_error = getattr(current_file, "error", None)
                return {
                    "success": False,
                    "mode": "gemini_files",
                    "endpoint": "/api/transcribe",
                    "stage": "gemini_file_processing",
                    "error": "GEMINI_FILE_PROCESSING_FAILED",
                    "message": str(file_error or "Gemini failed to process the uploaded file."),
                    "text": "",
                    "filename": file.filename,
                    "mime_type": gemini_mime_type,
                    "file_state": state_name,
                    "gemini_configured": True,
                }

            if time.monotonic() >= deadline:
                return {
                    "success": False,
                    "mode": "gemini_files",
                    "endpoint": "/api/transcribe",
                    "stage": "gemini_file_processing",
                    "error": "GEMINI_FILE_NOT_ACTIVE_TIMEOUT",
                    "message": f"Gemini file did not become ACTIVE within {GEMINI_FILE_ACTIVE_TIMEOUT_SECONDS} seconds.",
                    "text": "",
                    "filename": file.filename,
                    "mime_type": gemini_mime_type,
                    "file_state": last_state,
                    "gemini_configured": True,
                }

            time.sleep(GEMINI_FILE_POLL_SECONDS)

            try:
                current_file = gemini_client.files.get(name=file_name)
            except Exception as exc:
                return {
                    "success": False,
                    "mode": "gemini_files",
                    "endpoint": "/api/transcribe",
                    "stage": "gemini_file_status_check",
                    "error": "GEMINI_FILE_STATUS_CHECK_FAILED",
                    "message": safe_error_message(exc),
                    "text": "",
                    "filename": file.filename,
                    "mime_type": gemini_mime_type,
                    "file_state": last_state,
                    "gemini_configured": True,
                }

        gemini_uri = getattr(current_file, "uri", None) or gemini_uri
        gemini_mime_type = getattr(current_file, "mime_type", None) or gemini_mime_type

        try:
            interaction = gemini_client.interactions.create(
                model=GEMINI_TRANSCRIBE_MODEL,
                input=[
                    {
                        "type": "text",
                        "text": "Generate a transcript of the speech. Return only the spoken transcript text.",
                    },
                    {
                        "type": "audio",
                        "uri": gemini_uri,
                        "mime_type": gemini_mime_type,
                    },
                ],
            )
        except Exception as exc:
            return {
                "success": False,
                "mode": "gemini_files",
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
                "file_state": "ACTIVE",
                "transport": "files_api",
                "gemini_configured": True,
            }

        text = (getattr(interaction, "output_text", "") or "").strip()

        if not text:
            return {
                "success": False,
                "mode": "gemini_files",
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
                "file_state": "ACTIVE",
                "transport": "files_api",
                "gemini_configured": True,
            }

        return {
            "success": True,
            "mode": "gemini_files",
            "endpoint": "/api/transcribe",
            "stage": "complete",
            "model": GEMINI_TRANSCRIBE_MODEL,
            "text": text,
            "filename": file.filename,
            "extension": extension,
            "mime_type": gemini_mime_type,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "file_state": "ACTIVE",
            "transport": "files_api",
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

    Temporary 503/high-demand failures are handled automatically
    with retries, exponential backoff, and a fallback model.
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

        response, translation_model, translation_attempts = (
            await generate_translation_with_retry(prompt)
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
            "model": translation_model,
            "attempts": translation_attempts,
            "gemini_configured": True,
        }

    except Exception as exc:
        return {
            "success": False,
            "mode": "gemini",
            "endpoint": "/api/translate",
            "stage": "translation_request",
            "error": "TRANSLATION_FAILED",
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": "",
            "retryable": is_temporary_gemini_unavailable(exc),
            "message": (
                safe_error_message(exc)
                + (
                    " Gemini was temporarily unavailable even after "
                    "automatic retries and fallback model."
                    if is_temporary_gemini_unavailable(exc)
                    else ""
                )
            ),
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
    """Generate translated speech with Gemini TTS.

    Gemini TTS uses Google's built-in voices. The optional voice reference
    is accepted and validated for future authorized voice-generation
    integration, but it is NOT used to clone a person's voice here.
    """

    text = text.strip()
    target_language = normalize_language(target_language)
    voice = voice.strip() if voice else GEMINI_DEFAULT_TTS_VOICE

    if not text:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "stage": "request_validation",
                "error": "EMPTY_TEXT",
                "message": "Dubbing text cannot be empty.",
            },
        )

    if gemini_client is None:
        return {
            "success": False,
            "mode": "demo",
            "endpoint": "/api/dubbing",
            "stage": "gemini_configuration",
            "error": "GEMINI_NOT_CONFIGURED",
            "message": "GEMINI_API_KEY is not configured on the backend.",
            "target_language": target_language,
            "voice": voice,
            "audio_generated": False,
            "audio_url": None,
            "voice_cloning": False,
            "voice_reference_received": voice_reference is not None,
        }

    reference_path = None
    reference_size = 0
    reference_filename = None

    if voice_reference is not None:
        if not voice_reference.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "stage": "voice_reference_validation",
                    "error": "INVALID_VOICE_REFERENCE",
                    "message": "Voice reference filename is missing.",
                },
            )

        reference_filename = voice_reference.filename
        reference_extension = validate_extension(voice_reference.filename)

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
        finally:
            safe_remove(reference_path)

    # The frontend historically sends "alloy". Map it to a valid Gemini voice.
    valid_voices = {
        "zephyr", "puck", "charon", "kore", "fenrir",
        "leda", "orus", "aoede", "callirrhoe", "autonoe",
        "enceladus", "iapetus", "umbriel", "alnilam", "schedar",
        "achird", "sadachbia", "vindemiatrix", "sadaltager", "sulafat",
        "gacrux", "pulcherrima", "achernar", "zubenelgenubi",
        "algieba", "despina", "erinome", "laomedeia", "rasalgethi",
        "algenib",
    }
    tts_voice = "Kore" if voice.lower() == "alloy" else voice
    if tts_voice.lower() not in valid_voices:
        tts_voice = GEMINI_DEFAULT_TTS_VOICE

    prompt = (
        f"Speak naturally in {target_language}. "
        f"Return only the spoken content, with clear pronunciation.\n\n"
        f"{text}"
    )

    try:
        interaction = gemini_client.interactions.create(
            model=GEMINI_TTS_MODEL,
            input=prompt,
            response_format={"type": "audio"},
            generation_config={
                "speech_config": [
                    {"voice": tts_voice}
                ]
            },
        )

        output_audio = getattr(interaction, "output_audio", None)
        audio_data = getattr(output_audio, "data", None)

        if not audio_data:
            raise RuntimeError(
                "Gemini TTS completed without returning audio data."
            )

        pcm_bytes = base64.b64decode(audio_data)

        filename = f"bicon_dub_{uuid.uuid4().hex}.wav"
        output_path = OUTPUT_DIR / filename

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(pcm_bytes)

        return {
            "success": True,
            "mode": "gemini_tts",
            "endpoint": "/api/dubbing",
            "stage": "complete",
            "model": GEMINI_TTS_MODEL,
            "target_language": target_language,
            "voice": tts_voice,
            "requested_voice": voice,
            "text": text,
            "audio_generated": True,
            "audio_url": f"/api/audio/{filename}",
            "voice_cloning": False,
            "voice_reference_received": reference_filename is not None,
            "voice_reference_filename": reference_filename,
            "voice_reference_size_bytes": reference_size,
            "gemini_configured": True,
        }

    except Exception as exc:
        return {
            "success": False,
            "mode": "gemini_tts",
            "endpoint": "/api/dubbing",
            "stage": "gemini_tts_request",
            "error": "GEMINI_TTS_REQUEST_FAILED",
            "message": safe_error_message(exc),
            "target_language": target_language,
            "voice": tts_voice,
            "text": text,
            "audio_generated": False,
            "audio_url": None,
            "voice_cloning": False,
            "voice_reference_received": reference_filename is not None,
            "gemini_configured": True,
        }


@app.get("/api/audio/{filename}")
async def get_generated_audio(filename: str):
    """Serve a generated BICON WAV file."""

    if (
        Path(filename).name != filename
        or not filename.lower().endswith(".wav")
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "stage": "audio_validation",
                "error": "INVALID_AUDIO_FILENAME",
                "message": "Invalid generated audio filename.",
            },
        )

    audio_path = OUTPUT_DIR / filename

    if not audio_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "stage": "audio_lookup",
                "error": "AUDIO_NOT_FOUND",
                "message": "Generated audio file was not found.",
            },
        )

    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        filename=filename,
    )


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
