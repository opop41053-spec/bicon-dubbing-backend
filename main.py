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
APP_VERSION = "2.0.1"

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

ALLOWED_ORIGINS = [
    "https://opop41053-spec.github.io",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

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
                    f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            },
        )
    return extension


async def save_upload_with_limit(
    upload_file: UploadFile,
    destination: str,
) -> int:
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
# ROOT & HEALTH
# ============================================================

@app.get("/")
async def root():
    return {
        "success": True,
        "name": APP_NAME,
        "status": "online",
        "version": APP_VERSION,
        "openai_configured": client is not None,
    }


@app.get("/health")
async def health():
    return {
        "success": True,
        "status": "healthy",
        "openai_configured": client is not None,
    }


# ============================================================
# POST /api/transcribe
# ============================================================

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "NO_FILENAME", "message": "No filename was provided."},
        )

    extension = validate_extension(file.filename)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temporary_path = temp_file.name

        file_size = await save_upload_with_limit(file, temporary_path)

        if file_size <= 0:
            raise HTTPException(
                status_code=400,
                detail={"success": False, "error": "EMPTY_AUDIO_FILE", "message": "The uploaded audio file is empty."},
            )

        if client is None:
            return {
                "success": True,
                "mode": "demo",
                "text": "[DEMO TRANSCRIPT] OpenAI API key not configured.",
                "filename": file.filename,
                "openai_configured": False,
            }

        try:
            with open(temporary_path, "rb") as audio_file:
                # Fixed OpenAI Whisper SDK call with proper tuple structure
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=(file.filename, audio_file, f"audio/{extension.lstrip('.')}"),
                    response_format="json",
                )

            text = getattr(result, "text", "").strip()

            if not text:
                raise RuntimeError("OpenAI returned an empty transcription.")

            return {
                "success": True,
                "mode": "openai",
                "text": text,
                "filename": file.filename,
                "openai_configured": True,
            }

        except Exception as exc:
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
# POST /api/translate
# ============================================================

@app.post("/api/translate")
async def translate_text(
    request: TranslateRequest,
):
    text = request.text.strip()
    source_language = normalize_language(request.source_language)
    target_language = normalize_language(request.target_language)

    if not text:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "EMPTY_TEXT", "message": "Text cannot be empty."},
        )

    if source_language != "auto" and source_language == target_language:
        return {
            "success": True,
            "mode": "passthrough",
            "translated_text": text,
            "openai_configured": client is not None,
        }

    if client is None:
        return {
            "success": True,
            "mode": "demo",
            "translated_text": f"[DEMO TRANSLATION -> {target_language}] {text}",
            "openai_configured": False,
        }

    try:
        prompt = (
            "Translate the following text accurately.\n\n"
            f"Source language: {source_language}\n"
            f"Target language: {target_language}\n\n"
            "Return ONLY the translated text. Do not add explanations.\n\n"
            f"Text:\n{text}"
        )

        # Fixed OpenAI Chat Completions call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        translated_text = response.choices[0].message.content.strip()

        return {
            "success": True,
            "mode": "openai",
            "translated_text": translated_text,
            "openai_configured": True,
        }

    except Exception as exc:
        return {
            "success": False,
            "mode": "openai",
            "error": "TRANSLATION_FAILED",
            "message": str(exc),
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
    text = text.strip()
    target_language = normalize_language(target_language)
    voice = voice.strip() if voice else "alloy"

    if not text:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "EMPTY_TEXT", "message": "Dubbing text cannot be empty."},
        )

    reference_path = None
    if voice_reference is not None and voice_reference.filename:
        reference_extension = validate_extension(voice_reference.filename)
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=reference_extension) as temp_file:
                reference_path = temp_file.name
            await save_upload_with_limit(voice_reference, reference_path)
        except Exception:
            safe_remove(reference_path)
            raise

    if client is None:
        safe_remove(reference_path)
        return {
            "success": True,
            "mode": "demo",
            "message": "Dubbing endpoint working in demo mode.",
            "audio_generated": False,
            "openai_configured": False,
        }

    output_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as output_file:
            output_path = output_file.name

        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3",
            )
            response.stream_to_file(output_path)

            return FileResponse(
                path=output_path,
                media_type="audio/mpeg",
                filename="bicon_dubbed_audio.mp3",
            )
        except Exception as exc:
            safe_remove(output_path)
            return {
                "success": False,
                "error": "DUBBING_FAILED",
                "message": str(exc),
                "audio_generated": False,
                "openai_configured": True,
            }
    finally:
        safe_remove(reference_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
