import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI


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
# OPENAI
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client: Optional[OpenAI] = None

if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        # Never crash the backend just because the client
        # could not be initialized.
        client = None


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
        "openai_configured": client is not None,
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
        "openai_configured": client is not None,
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
        "openai_configured": client is not None,
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
            "mode": "demo" if client is None else "ready",
            "message": "File uploaded and validated successfully.",
            "filename": file.filename,
            "extension": extension,
            "size_bytes": file_size,
            "size_mb": round(
                file_size / (1024 * 1024),
                2,
            ),
            "max_size_mb": 25,
            "openai_configured": client is not None,
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
    Speech-to-text.

    Without OPENAI_API_KEY:
        Returns structured demo response.

    With OPENAI_API_KEY:
        Attempts real transcription.
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

        if file_size <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "EMPTY_AUDIO_FILE",
                    "message": "The uploaded audio file is empty.",
                },
            )

        # ----------------------------------------------------
        # DEMO MODE
        # ----------------------------------------------------

        if client is None:
            return {
                "success": True,
                "mode": "demo",
                "endpoint": "/api/transcribe",
                "message": (
                    "Transcription endpoint is working, "
                    "but OPENAI_API_KEY is not configured."
                ),
                "text": (
                    "[DEMO TRANSCRIPT] "
                    "No OpenAI API key is configured, "
                    "so real transcription is disabled."
                ),
                "filename": file.filename,
                "size_bytes": file_size,
                "openai_configured": False,
            }

        # ----------------------------------------------------
        # REAL MODE
        # ----------------------------------------------------

        try:
            with open(
                temporary_path,
                "rb",
            ) as audio_file:

                # OpenAI's current transcription models return a JSON
                # transcription object. Explicitly request JSON so the SDK
                # always gives us a response object containing `.text`.
                result = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file,
                    response_format="json",
                )

            text = (
                getattr(result, "text", None)
                or ""
            ).strip()

            # Do not report success when OpenAI returned an empty transcript.
            # This makes the real failure visible to the frontend instead of
            # looking like a successful upload with missing text.
            if not text:
                raise RuntimeError(
                    "OpenAI accepted the audio file but returned an empty "
                    "transcription. Check that the uploaded file contains "
                    "audible speech and is a supported audio format."
                )

            return {
                "success": True,
                "mode": "openai",
                "endpoint": "/api/transcribe",
                "text": text,
                "filename": file.filename,
                "size_bytes": file_size,
                "openai_configured": True,
            }

        except Exception as exc:
            return {
                "success": False,
                "mode": "openai",
                "endpoint": "/api/transcribe",
                "error": "TRANSCRIPTION_FAILED",
                "message": str(exc),
                "text": "",
                "openai_configured": True,
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
    Text translation.

    Without OPENAI_API_KEY:
        Returns structured demo translation.

    With OPENAI_API_KEY:
        Attempts real translation.
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
    # SAME LANGUAGE
    # --------------------------------------------------------

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
            "openai_configured": client is not None,
        }

    # --------------------------------------------------------
    # DEMO MODE
    # --------------------------------------------------------

    if client is None:
        return {
            "success": True,
            "mode": "demo",
            "endpoint": "/api/translate",
            "message": (
                "Translation endpoint is working, "
                "but OPENAI_API_KEY is not configured."
            ),
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": (
                f"[DEMO TRANSLATION -> "
                f"{target_language}] {text}"
            ),
            "openai_configured": False,
        }

    # --------------------------------------------------------
    # REAL MODE
    # --------------------------------------------------------

    try:
        prompt = (
            "Translate the following text accurately.\n\n"
            f"Source language: {source_language}\n"
            f"Target language: {target_language}\n\n"
            "Return ONLY the translated text. "
            "Do not add explanations.\n\n"
            f"Text:\n{text}"
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
        )

        translated_text = (
            getattr(
                response,
                "output_text",
                "",
            )
            or ""
        ).strip()

        if not translated_text:
            return {
                "success": False,
                "mode": "openai",
                "endpoint": "/api/translate",
                "error": "EMPTY_TRANSLATION",
                "message": (
                    "The translation service returned "
                    "an empty result."
                ),
                "source_language": source_language,
                "target_language": target_language,
                "original_text": text,
                "translated_text": "",
                "openai_configured": True,
            }

        return {
            "success": True,
            "mode": "openai",
            "endpoint": "/api/translate",
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
            "endpoint": "/api/translate",
            "error": "TRANSLATION_FAILED",
            "message": str(exc),
            "source_language": source_language,
            "target_language": target_language,
            "original_text": text,
            "translated_text": "",
            "openai_configured": True,
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
    Text-to-speech / dubbing endpoint.

    IMPORTANT:
    This implementation does NOT clone a user's voice.

    voice_reference is accepted and validated as an optional
    reference file, but it is not used for voice cloning.

    Without OPENAI_API_KEY:
        Returns structured demo response.

    With OPENAI_API_KEY:
        Generates standard TTS audio.
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

    # --------------------------------------------------------
    # OPTIONAL VOICE REFERENCE
    # --------------------------------------------------------

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
                    "message": (
                        "Voice reference filename "
                        "is missing."
                    ),
                },
            )

        reference_filename = (
            voice_reference.filename
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

            reference_size = (
                await save_upload_with_limit(
                    voice_reference,
                    reference_path,
                )
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
            "endpoint": "/api/dubbing",
            "message": (
                "Dubbing endpoint is working, "
                "but OPENAI_API_KEY is not configured. "
                "No audio file was generated."
            ),
            "target_language": target_language,
            "voice": voice,
            "text": text,
            "audio_generated": False,
            "audio_url": None,
            "voice_cloning": False,
            "voice_reference_received": (
                reference_filename is not None
            ),
            "voice_reference_filename": (
                reference_filename
            ),
            "voice_reference_size_bytes": (
                reference_size
            ),
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

            response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text,
                response_format="mp3",
            )

            response.write_to_file(
                output_path
            )

            # Do NOT delete output_path here.
            # FileResponse needs the file to still exist.
            return FileResponse(
                path=output_path,
                media_type="audio/mpeg",
                filename="bicon_dubbed_audio.mp3",
            )

        except Exception as exc:

            safe_remove(output_path)

            return {
                "success": False,
                "mode": "openai",
                "endpoint": "/api/dubbing",
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
