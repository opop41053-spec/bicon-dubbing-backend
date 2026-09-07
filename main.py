<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<meta name="description"
      content="BICON Dubbing Studio - AI Voice Dubbing Studio">

<meta name="theme-color"
      content="#050b18">

<title>BICON Dubbing Studio</title>

<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

html{
    scroll-behavior:smooth;
}

body{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    min-height:100vh;

    color:#ffffff;

    background:
        radial-gradient(
            circle at 20% 20%,
            rgba(0,180,255,.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 80% 70%,
            rgba(0,255,170,.12),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #02040a,
            #061326,
            #02050c
        );

    overflow-x:hidden;
}


/* =========================
   BACKGROUND
========================= */

.background{
    position:fixed;
    inset:0;
    overflow:hidden;
    pointer-events:none;
    z-index:-1;
}

.glow{
    position:absolute;
    width:320px;
    height:320px;
    border-radius:50%;
    filter:blur(100px);
    opacity:.18;
}

.glow.one{
    background:#00aaff;
    top:-100px;
    left:-80px;
}

.glow.two{
    background:#00ff99;
    right:-100px;
    bottom:-100px;
}

.glow.three{
    background:#7b2cff;
    left:45%;
    top:40%;
}


/* =========================
   MAIN
========================= */

.wrapper{
    width:min(1200px,94%);
    margin:40px auto;
}

.panel{
    background:
        rgba(5,15,30,.78);

    border:
        1px solid rgba(0,190,255,.35);

    border-radius:24px;

    padding:35px;

    box-shadow:
        0 0 40px rgba(0,170,255,.10),
        0 20px 60px rgba(0,0,0,.55);

    backdrop-filter:blur(18px);
}


/* =========================
   HEADER
========================= */

.logo{
    text-align:center;
    margin-bottom:35px;
}

.logo h1{
    font-size:
        clamp(2.2rem,6vw,4.5rem);

    letter-spacing:3px;

    color:#ffffff;

    text-shadow:
        0 0 10px #00aaff,
        0 0 25px #00eaff;
}

.logo p{
    margin-top:10px;

    color:#8edfff;

    font-size:1.05rem;
}


/* =========================
   NOTICE
========================= */

.notice{
    padding:18px;

    margin-bottom:25px;

    border:
        1px solid rgba(255,200,0,.45);

    border-radius:14px;

    background:
        rgba(255,190,0,.06);

    color:#ffeaa0;

    line-height:1.7;
}


/* =========================
   GRID
========================= */

.grid{
    display:grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(280px,1fr)
        );

    gap:22px;
}


/* =========================
   CARD
========================= */

.card{
    background:
        rgba(255,255,255,.045);

    border:
        1px solid rgba(255,255,255,.10);

    border-radius:18px;

    padding:24px;

    transition:.3s ease;
}

.card:hover{
    transform:translateY(-5px);

    border-color:
        rgba(0,220,255,.5);

    box-shadow:
        0 0 25px rgba(0,200,255,.12);
}

.card h2{
    color:#00d9ff;

    margin-bottom:18px;

    font-size:1.25rem;
}

.card p{
    color:#c7d8e8;

    line-height:1.7;
}


/* =========================
   INPUTS
========================= */

label{
    display:block;

    margin:
        15px 0 8px;

    color:#bcecff;

    font-weight:600;
}

select,
textarea,
input{
    width:100%;

    padding:13px;

    border-radius:10px;

    border:
        1px solid rgba(0,200,255,.3);

    background:#071323;

    color:#ffffff;

    outline:none;
}

textarea{
    min-height:130px;

    resize:vertical;
}

select:focus,
textarea:focus,
input:focus{
    border-color:#00d9ff;

    box-shadow:
        0 0 12px rgba(0,210,255,.15);
}


/* =========================
   BUTTONS
========================= */

.buttons{
    display:flex;

    flex-wrap:wrap;

    gap:12px;

    margin-top:20px;
}

button{
    border:none;

    border-radius:10px;

    padding:13px 20px;

    font-size:15px;

    font-weight:700;

    cursor:pointer;

    color:#ffffff;

    background:
        linear-gradient(
            135deg,
            #007bff,
            #00c896
        );

    transition:.25s;
}

button:hover{
    transform:
        translateY(-2px);

    box-shadow:
        0 0 20px
        rgba(0,220,255,.3);
}

button.secondary{
    background:
        linear-gradient(
            135deg,
            #344b70,
            #526b91
        );
}

button:disabled{
    opacity:.55;
    cursor:not-allowed;
    transform:none;
    box-shadow:none;
}


/* =========================
   STATUS
========================= */

.status{
    margin-top:18px;

    padding:13px;

    border-radius:10px;

    background:
        rgba(0,255,150,.06);

    border:
        1px solid rgba(0,255,150,.18);

    color:#63ffb0;

    line-height:1.5;

    word-break:break-word;
}


/* =========================
   AUDIO
========================= */

audio{
    width:100%;
    margin-top:15px;
}

.hidden{
    display:none !important;
}

.file-info{
    margin-top:12px;
    color:#8edfff;
    font-size:.9rem;
    line-height:1.5;
    word-break:break-word;
}


/* =========================
   BACKEND URL
========================= */

.backend-box{
    margin-top:20px;
    padding:15px;

    border-radius:12px;

    background:
        rgba(0,150,255,.05);

    border:
        1px solid rgba(0,180,255,.18);
}

.backend-box small{
    color:#8fa9bd;
    display:block;
    margin-top:7px;
    line-height:1.5;
}


/* =========================
   FOOTER
========================= */

footer{
    text-align:center;

    margin-top:35px;

    color:#71879b;

    font-size:.9rem;
}


/* =========================
   MOBILE
========================= */

@media(max-width:600px){

    .wrapper{
        width:96%;
        margin:18px auto;
    }

    .panel{
        padding:20px;
    }

    .buttons{
        flex-direction:column;
    }

    button{
        width:100%;
    }
}

</style>
</head>


<body>

<div class="background">
    <div class="glow one"></div>
    <div class="glow two"></div>
    <div class="glow three"></div>
</div>


<div class="wrapper">

<div class="panel">

<header class="logo">

    <h1>🎙️ BICON DUBBING STUDIO</h1>

    <p>
        AI Voice Dubbing Studio
        — Connected Frontend
    </p>

</header>


<div class="notice">

<strong>IMPORTANT:</strong>

Use only your own voice or a voice for
which you have explicit permission.
Audio is sent to the configured BICON
backend for processing.

</div>


<div class="grid">


<!-- USER INPUT -->

<section class="card">

<h2>🎤 1. Voice Input</h2>

<p>
Speak into your microphone or select
your own audio file.
</p>

<label for="audioFile">
Audio File
</label>

<input
    id="audioFile"
    type="file"
    accept="audio/*"
>


<div class="file-info" id="audioInfo">
No audio selected.
</div>


<div class="buttons">

<button
    type="button"
    id="recordBtn"
>
🎙️ Record
</button>

<button
    type="button"
    class="secondary"
    id="stopBtn"
    disabled
>
⏹ Stop
</button>

<button
    type="button"
    class="secondary"
    id="uploadBtn"
    disabled
>
☁ Upload
</button>

</div>


<audio
    id="sourceAudio"
    controls
    class="hidden"
></audio>

</section>


<!-- LANGUAGE -->

<section class="card">

<h2>🌐 2. Language</h2>

<label for="sourceLanguage">
Source Language
</label>

<select id="sourceLanguage">

<option value="hi">
Hindi
</option>

<option value="en">
English
</option>

<option value="es">
Spanish
</option>

<option value="fr">
French
</option>

<option value="de">
German
</option>

</select>


<label for="targetLanguage">
Target Language
</label>

<select id="targetLanguage">

<option value="es">
Spanish
</option>

<option value="en">
English
</option>

<option value="hi">
Hindi
</option>

<option value="fr">
French
</option>

<option value="de">
German
</option>

</select>

</section>


<!-- TRANSCRIPT -->

<section class="card">

<h2>📝 3. Transcript</h2>

<label for="transcript">
Transcript
</label>

<textarea
    id="transcript"
    placeholder="Transcript will appear here..."
></textarea>


<div class="buttons">

<button
    type="button"
    id="transcribeBtn"
    disabled
>
📝 Transcribe
</button>

<button
    type="button"
    id="translateBtn"
>
🌐 Translate
</button>

<button
    type="button"
    id="generateBtn"
>
🚀 Generate Dub
</button>

<button
    type="button"
    class="secondary"
    id="previewBtn"
>
▶ Preview
</button>

</div>

</section>


<!-- VOICE REFERENCE -->

<section class="card">

<h2>🗣️ 4. Voice Reference</h2>

<p>
Use only your own voice or a voice for
which you have explicit permission.
</p>

<label for="voiceFile">
Voice Reference
</label>

<input
    id="voiceFile"
    type="file"
    accept="audio/*"
>

<div
    class="file-info"
    id="voiceInfo"
>
No voice reference selected.
</div>

<div class="buttons">

<button
    type="button"
    class="secondary"
    id="voiceUploadBtn"
    disabled
>
☁ Upload Reference
</button>

</div>

</section>


<!-- STATUS -->

<section class="card">

<h2>⚙️ 5. Processing Status</h2>

<div
    id="status"
    class="status"
>
🟢 READY
</div>

<div class="backend-box">

<strong>Backend:</strong>

<div id="backendStatus">
Checking...
</div>

<small>
Connected to the live BICON FastAPI
backend through HTTPS.
</small>

</div>

</section>


<!-- OUTPUT -->

<section class="card">

<h2>📥 6. Output</h2>

<p id="outputMessage">
Generated audio will appear here after
a successful dubbing request.
</p>


<audio
    id="outputAudio"
    controls
    class="hidden"
></audio>


<div class="buttons">

<button
    type="button"
    class="secondary"
    id="downloadBtn"
    disabled
>
⬇ Download Audio
</button>

<button
    type="button"
    class="secondary"
    id="downloadTranscriptBtn"
    disabled
>
⬇ Download Transcript
</button>

</div>

</section>

</div>


<footer>

© 2026 BICON Dubbing Studio

</footer>

</div>

</div>


<script>

/* ========================================================
   BICON DUBBING STUDIO
   FRONTEND ↔ FASTAPI BACKEND
======================================================== */


/* ========================================================
   LIVE FASTAPI BACKEND
======================================================== */

const API_BASE =
    "https://orange-trout-q7wg7qj54jqp29qwq-8000.app.github.dev";


/* ========================================================
   DOM ELEMENTS
======================================================== */

const statusBox =
    document.getElementById("status");

const backendStatus =
    document.getElementById("backendStatus");

const audioFile =
    document.getElementById("audioFile");

const audioInfo =
    document.getElementById("audioInfo");

const voiceFile =
    document.getElementById("voiceFile");

const voiceInfo =
    document.getElementById("voiceInfo");

const sourceAudio =
    document.getElementById("sourceAudio");

const outputAudio =
    document.getElementById("outputAudio");

const transcript =
    document.getElementById("transcript");

const sourceLanguage =
    document.getElementById("sourceLanguage");

const targetLanguage =
    document.getElementById("targetLanguage");

const recordBtn =
    document.getElementById("recordBtn");

const stopBtn =
    document.getElementById("stopBtn");

const uploadBtn =
    document.getElementById("uploadBtn");

const transcribeBtn =
    document.getElementById("transcribeBtn");

const translateBtn =
    document.getElementById("translateBtn");

const generateBtn =
    document.getElementById("generateBtn");

const previewBtn =
    document.getElementById("previewBtn");

const voiceUploadBtn =
    document.getElementById("voiceUploadBtn");

const downloadBtn =
    document.getElementById("downloadBtn");

const downloadTranscriptBtn =
    document.getElementById(
        "downloadTranscriptBtn"
    );

const outputMessage =
    document.getElementById(
        "outputMessage"
    );


/* ========================================================
   STATE
======================================================== */

let mediaRecorder = null;

let recordedChunks = [];

let recordedBlob = null;

let recordedUrl = null;

let sourceFileUrl = null;

let selectedAudioFile = null;

let selectedVoiceFile = null;

let uploadedAudioReady = false;

let uploadedVoiceReady = false;

let generatedAudioUrl = null;


/* ========================================================
   HELPERS
======================================================== */

function setStatus(message){

    statusBox.textContent =
        message;

}


function setBusy(button, busy){

    if(!button){
        return;
    }

    button.disabled =
        busy;

}


function getApiUrl(path){

    return (
        API_BASE.replace(/\/+$/, "") +
        "/" +
        path.replace(/^\/+/, "")
    );

}


/* ========================================================
   JSON RESPONSE PARSER
======================================================== */

async function parseJsonResponse(response){

    const contentType =
        response.headers.get(
            "content-type"
        ) || "";

    if(
        !contentType.includes(
            "application/json"
        )
    ){

        const text =
            await response.text();

        throw new Error(
            text ||
            `Backend returned a non-JSON response (${response.status}).`
        );

    }

    let data;

    try{

        data =
            await response.json();

    }catch(error){

        throw new Error(
            "Backend returned invalid JSON."
        );

    }

    if(!response.ok){

        const detail =
            data?.detail;

        const message =
            typeof detail === "string"
                ? detail
                : detail?.message ||
                  data?.message ||
                  data?.error ||
                  `Backend request failed (${response.status}).`;

        throw new Error(
            message
        );

    }

    return data;

}


/* ========================================================
   ERROR MESSAGE
======================================================== */

function getBackendMessage(data){

    const detail =
        data?.detail;

    if(
        typeof detail ===
        "string"
    ){

        return detail;

    }

    if(
        detail &&
        typeof detail.message ===
        "string"
    ){

        return detail.message;

    }

    return (
        data?.message ||
        data?.error ||
        "Backend request failed."
    );

}


/* ========================================================
   BACKEND HEALTH CHECK
======================================================== */

async function checkBackend(){

    backendStatus.textContent =
        "🟡 CHECKING...";

    try{

        const response =
            await fetch(
                getApiUrl(
                    "/health"
                ),
                {
                    method:"GET",
                    headers:{
                        "Accept":
                            "application/json"
                    },
                    cache:"no-store"
                }
            );

        const data =
            await parseJsonResponse(
                response
            );

        if(
            data.success === true &&
            data.status === "healthy"
        ){

            backendStatus.textContent =
                "🟢 ONLINE";

            setStatus(
                "🟢 Backend connected successfully."
            );

            return true;

        }

        backendStatus.textContent =
            "🟡 CONNECTED";

        setStatus(
            "🟡 Backend responded, but health status is unexpected."
        );

        return true;

    }catch(error){

        backendStatus.textContent =
            "🔴 OFFLINE / CONNECTION ERROR";

        setStatus(
            "🔴 Backend connection failed: " +
            error.message
        );

        console.error(
            "Health check error:",
            error
        );

        return false;

    }

}


/* ========================================================
   FILE SIZE
======================================================== */

function formatBytes(bytes){

    if(bytes === 0){

        return "0 Bytes";

    }

    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];

    const index =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );

    return (
        parseFloat(
            (
                bytes /
                Math.pow(
                    1024,
                    index
                )
            ).toFixed(2)
        ) +
        " " +
        units[index]
    );

}


/* ========================================================
   SOURCE AUDIO PREVIEW
======================================================== */

function createSourcePreview(file){

    if(sourceFileUrl){

        URL.revokeObjectURL(
            sourceFileUrl
        );

        sourceFileUrl =
            null;

    }

    sourceFileUrl =
        URL.createObjectURL(
            file
        );

    sourceAudio.src =
        sourceFileUrl;

    sourceAudio.classList.remove(
        "hidden"
    );

}


/* ========================================================
   AUDIO FILE SELECTION
======================================================== */

audioFile.addEventListener(
    "change",
    function(){

        selectedAudioFile =
            audioFile.files[0] ||
            null;

        uploadedAudioReady =
            false;

        uploadBtn.disabled =
            !selectedAudioFile;

        transcribeBtn.disabled =
            !selectedAudioFile;

        if(!selectedAudioFile){

            audioInfo.textContent =
                "No audio selected.";

            sourceAudio.removeAttribute(
                "src"
            );

            sourceAudio.classList.add(
                "hidden"
            );

            return;

        }

        audioInfo.textContent =
            `${selectedAudioFile.name} — ` +
            `${formatBytes(selectedAudioFile.size)}`;

        createSourcePreview(
            selectedAudioFile
        );

        setStatus(
            "🟢 Audio selected. Ready."
        );

    }
);


/* ========================================================
   VOICE REFERENCE SELECTION
======================================================== */

voiceFile.addEventListener(
    "change",
    function(){

        selectedVoiceFile =
            voiceFile.files[0] ||
            null;

        uploadedVoiceReady =
            false;

        voiceUploadBtn.disabled =
            !selectedVoiceFile;

        if(!selectedVoiceFile){

            voiceInfo.textContent =
                "No voice reference selected.";

            return;

        }

        voiceInfo.textContent =
            `${selectedVoiceFile.name} — ` +
            `${formatBytes(selectedVoiceFile.size)}`;

        setStatus(
            "🟢 Voice reference selected."
        );

    }
);


/* ========================================================
   MICROPHONE RECORDING
======================================================== */

recordBtn.addEventListener(
    "click",
    async function(){

        try{

            if(
                !navigator.mediaDevices ||
                !navigator.mediaDevices.getUserMedia
            ){

                throw new Error(
                    "Microphone recording is not supported by this browser."
                );

            }

            const stream =
                await navigator.mediaDevices
                    .getUserMedia({
                        audio:true
                    });

            recordedChunks = [];

            mediaRecorder =
                new MediaRecorder(
                    stream
                );

            mediaRecorder.addEventListener(
                "dataavailable",
                function(event){

                    if(
                        event.data &&
                        event.data.size > 0
                    ){

                        recordedChunks.push(
                            event.data
                        );

                    }

                }
            );

            mediaRecorder.addEventListener(
                "stop",
                function(){

                    recordedBlob =
                        new Blob(
                            recordedChunks,
                            {
                                type:
                                    mediaRecorder.mimeType ||
                                    "audio/webm"
                            }
                        );

                    if(recordedUrl){

                        URL.revokeObjectURL(
                            recordedUrl
                        );

                    }

                    recordedUrl =
                        URL.createObjectURL(
                            recordedBlob
                        );

                    sourceAudio.src =
                        recordedUrl;

                    sourceAudio.classList.remove(
                        "hidden"
                    );

                    selectedAudioFile =
                        new File(
                            [
                                recordedBlob
                            ],
                            "bicon-recording.webm",
                            {
                                type:
                                    recordedBlob.type
                            }
                        );

                    audioInfo.textContent =
                        "🎙️ New recording ready — " +
                        formatBytes(
                            recordedBlob.size
                        );

                    uploadBtn.disabled =
                        false;

                    transcribeBtn.disabled =
                        false;

                    uploadedAudioReady =
                        false;

                    setStatus(
                        "🟢 Recording stopped. Audio ready."
                    );

                }
            );

            mediaRecorder.start();

            recordBtn.disabled =
                true;

            stopBtn.disabled =
                false;

            setStatus(
                "🔴 Recording..."
            );

        }catch(error){

            console.error(
                error
            );

            setStatus(
                "🔴 Microphone error: " +
                error.message
            );

        }

    }
);


/* ========================================================
   STOP RECORDING
======================================================== */

stopBtn.addEventListener(
    "click",
    function(){

        if(
            mediaRecorder &&
            mediaRecorder.state !==
            "inactive"
        ){

            mediaRecorder.stop();

            if(
                mediaRecorder.stream
            ){

                mediaRecorder.stream
                    .getTracks()
                    .forEach(
                        track =>
                            track.stop()
                    );

            }

        }

        recordBtn.disabled =
            false;

        stopBtn.disabled =
            true;

    }
);


/* ========================================================
   POST /api/upload
======================================================== */

uploadBtn.addEventListener(
    "click",
    async function(){

        if(!selectedAudioFile){

            setStatus(
                "🟡 Please select or record audio first."
            );

            return;

        }

        setBusy(
            uploadBtn,
            true
        );

        setStatus(
            "🟡 Uploading audio..."
        );

        try{

            const formData =
                new FormData();

            formData.append(
                "file",
                selectedAudioFile,
                selectedAudioFile.name
            );

            const response =
                await fetch(
                    getApiUrl(
                        "/api/upload"
                    ),
                    {
                        method:"POST",
                        body:formData,
                        headers:{
                            "Accept":
                                "application/json"
                        }
                    }
                );

            const data =
                await parseJsonResponse(
                    response
                );

            if(
                data.success === true
            ){

                uploadedAudioReady =
                    true;

                setStatus(
                    "🟢 Audio uploaded and validated successfully."
                );

            }else{

                throw new Error(
                    getBackendMessage(data)
                );

            }

        }catch(error){

            uploadedAudioReady =
                false;

            setStatus(
                "🔴 Upload error: " +
                error.message
            );

            console.error(
                "Upload error:",
                error
            );

        }finally{

            setBusy(
                uploadBtn,
                false
            );

        }

    }
);


/* ========================================================
   POST /api/transcribe
======================================================== */

transcribeBtn.addEventListener(
    "click",
    async function(){

        if(!selectedAudioFile){

            setStatus(
                "🟡 Select or record audio first."
            );

            return;

        }

        setBusy(
            transcribeBtn,
            true
        );

        setStatus(
            "🟡 Sending audio for transcription..."
        );

        try{

            const formData =
                new FormData();

            formData.append(
                "file",
                selectedAudioFile,
                selectedAudioFile.name
            );

            const response =
                await fetch(
                    getApiUrl(
                        "/api/transcribe"
                    ),
                    {
                        method:"POST",
                        body:formData,
                        headers:{
                            "Accept":
                                "application/json"
                        }
                    }
                );

            const data =
                await parseJsonResponse(
                    response
                );

            if(
                data.success === true &&
                data.text
            ){

                transcript.value =
                    data.text;

                downloadTranscriptBtn.disabled =
                    false;

                setStatus(
                    "🟢 Transcription completed."
                );

            }else{

                throw new Error(
                    getBackendMessage(data)
                );

            }

        }catch(error){

            setStatus(
                "🔴 Transcription error: " +
                error.message
            );

            console.error(
                "Transcription error:",
                error
            );

        }finally{

            setBusy(
                transcribeBtn,
                false
            );

        }

    }
);


/* ========================================================
   POST /api/translate
======================================================== */

translateBtn.addEventListener(
    "click",
    async function(){

        const text =
            transcript.value.trim();

        if(!text){

            setStatus(
                "🟡 Enter or generate transcript first."
            );

            return;

        }

        if(
            sourceLanguage.value ===
            targetLanguage.value
        ){

            setStatus(
                "🟡 Source and target languages are the same."
            );

            return;

        }

        setBusy(
            translateBtn,
            true
        );

        setStatus(
            "🟡 Sending transcript for translation..."
        );

        try{

            const response =
                await fetch(
                    getApiUrl(
                        "/api/translate"
                    ),
                    {
                        method:"POST",

                        headers:{
                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"
                        },

                        body:JSON.stringify({

                            text:text,

                            source_language:
                                sourceLanguage.value,

                            target_language:
                                targetLanguage.value

                        })
                    }
                );

            const data =
                await parseJsonResponse(
                    response
                );

            if(
                data.success === true &&
                data.translated_text
            ){

                transcript.value =
                    data.translated_text;

                downloadTranscriptBtn.disabled =
                    false;

                setStatus(
                    "🟢 Translation completed."
                );

            }else{

                throw new Error(
                    getBackendMessage(data)
                );

            }

        }catch(error){

            setStatus(
                "🔴 Translation error: " +
                error.message
            );

            console.error(
                "Translation error:",
                error
            );

        }finally{

            setBusy(
                translateBtn,
                false
            );

        }

    }
);


/* ========================================================
   VOICE REFERENCE UPLOAD
   POST /api/upload
======================================================== */

voiceUploadBtn.addEventListener(
    "click",
    async function(){

        if(!selectedVoiceFile){

            setStatus(
                "🟡 Select a voice reference first."
            );

            return;

        }

        setBusy(
            voiceUploadBtn,
            true
        );

        setStatus(
            "🟡 Uploading voice reference..."
        );

        try{

            const formData =
                new FormData();

            formData.append(
                "file",
                selectedVoiceFile,
                selectedVoiceFile.name
            );

            const response =
                await fetch(
                    getApiUrl(
                        "/api/upload"
                    ),
                    {
                        method:"POST",
                        body:formData,
                        headers:{
                            "Accept":
                                "application/json"
                        }
                    }
                );

            const data =
                await parseJsonResponse(
                    response
                );

            if(
                data.success === true
            ){

                uploadedVoiceReady =
                    true;

                setStatus(
                    "🟢 Voice reference uploaded and validated."
                );

            }else{

                throw new Error(
                    getBackendMessage(data)
                );

            }

        }catch(error){

            uploadedVoiceReady =
                false;

            setStatus(
                "🔴 Voice reference error: " +
                error.message
            );

            console.error(
                "Voice reference error:",
                error
            );

        }finally{

            setBusy(
                voiceUploadBtn,
                false
            );

        }

    }
);


/* ========================================================
   POST /api/dubbing
========================================================

   IMPORTANT BACKEND CONTRACT:

   FastAPI expects:

       text
       target_language
       voice
       voice_reference (optional file)

   Therefore JSON is NOT used here.

   Real mode returns:
       audio/mpeg

   Demo mode returns:
       application/json

======================================================== */

generateBtn.addEventListener(
    "click",
    async function(){

        const text =
            transcript.value.trim();

        if(!text){

            setStatus(
                "🟡 Transcript is empty."
            );

            return;

        }

        setBusy(
            generateBtn,
            true
        );

        downloadBtn.disabled =
            true;

        if(generatedAudioUrl){

            URL.revokeObjectURL(
                generatedAudioUrl
            );

            generatedAudioUrl =
                null;

        }

        outputAudio.pause();

        outputAudio.removeAttribute(
            "src"
        );

        outputAudio.load();

        outputAudio.classList.add(
            "hidden"
        );

        outputMessage.textContent =
            "Generating dubbed audio...";

        setStatus(
            "🟡 Sending dubbing request..."
        );

        try{

            const formData =
                new FormData();

            /*
             * Exact FastAPI field:
             * text: str = Form(...)
             */
            formData.append(
                "text",
                text
            );

            /*
             * Exact FastAPI field:
             * target_language: str = Form("en")
             */
            formData.append(
                "target_language",
                targetLanguage.value
            );

            /*
             * Exact FastAPI field:
             * voice: str = Form("alloy")
             */
            formData.append(
                "voice",
                "alloy"
            );

            /*
             * Exact FastAPI field:
             * voice_reference: Optional[UploadFile]
             *
             * Send it directly with the dubbing
             * request if the user selected one.
             */
            if(selectedVoiceFile){

                formData.append(
                    "voice_reference",
                    selectedVoiceFile,
                    selectedVoiceFile.name
                );

            }

            const response =
                await fetch(
                    getApiUrl(
                        "/api/dubbing"
                    ),
                    {
                        method:"POST",
                        body:formData
                    }
                );


            /* =================================================
               REAL MODE
               FastAPI returns FileResponse(audio/mpeg)
            ================================================= */

            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";


            if(
                response.ok &&
                contentType.includes(
                    "audio/"
                )
            ){

                const audioBlob =
                    await response.blob();

                generatedAudioUrl =
                    URL.createObjectURL(
                        audioBlob
                    );

                outputAudio.src =
                    generatedAudioUrl;

                outputAudio.classList.remove(
                    "hidden"
                );

                downloadBtn.disabled =
                    false;

                outputMessage.textContent =
                    "Generated audio is ready.";

                setStatus(
                    "🟢 Dub generated successfully."
                );

                return;

            }


            /* =================================================
               DEMO / ERROR MODE
               Backend returns JSON
            ================================================= */

            if(
                contentType.includes(
                    "application/json"
                )
            ){

                const data =
                    await response.json();

                if(
                    !response.ok ||
                    data.success === false
                ){

                    throw new Error(
                        getBackendMessage(
                            data
                        )
                    );

                }

                if(
                    data.audio_generated === false
                ){

                    outputMessage.textContent =
                        data.message ||
                        "Dubbing endpoint is working, but no audio was generated.";

                    setStatus(
                        "🟡 Dubbing endpoint is working, but audio generation is not configured."
                    );

                    return;

                }

                throw new Error(
                    data.message ||
                    "Dubbing backend did not return audio."
                );

            }


            /* =================================================
               UNKNOWN RESPONSE
            ================================================= */

            const fallbackText =
                await response.text();

            throw new Error(
                fallbackText ||
                `Unexpected backend response (${response.status}).`
            );

        }catch(error){

            outputMessage.textContent =
                "Unable to generate dubbed audio.";

            setStatus(
                "🔴 Dubbing error: " +
                error.message
            );

            console.error(
                "Dubbing error:",
                error
            );

        }finally{

            setBusy(
                generateBtn,
                false
            );

        }

    }
);


/* ========================================================
   BROWSER PREVIEW
======================================================== */

previewBtn.addEventListener(
    "click",
    function(){

        const text =
            transcript.value.trim();

        if(!text){

            setStatus(
                "🟡 Enter some transcript text first."
            );

            return;

        }

        if(
            !("speechSynthesis" in window)
        ){

            setStatus(
                "🔴 Browser speech preview is not supported."
            );

            return;

        }

        window.speechSynthesis.cancel();

        const utterance =
            new SpeechSynthesisUtterance(
                text
            );

        const languageMap = {

            hi:"hi-IN",

            en:"en-US",

            es:"es-ES",

            fr:"fr-FR",

            de:"de-DE"

        };

        utterance.lang =
            languageMap[
                targetLanguage.value
            ] ||
            "en-US";

        utterance.rate =
            1;

        utterance.pitch =
            1;

        utterance.volume =
            1;

        utterance.onstart =
            function(){

                setStatus(
                    "🔊 Browser preview playing..."
                );

            };

        utterance.onend =
            function(){

                setStatus(
                    "🟢 Preview finished."
                );

            };

        utterance.onerror =
            function(){

                setStatus(
                    "🔴 Browser preview failed."
                );

            };

        window.speechSynthesis.speak(
            utterance
        );

    }
);


/* ========================================================
   DOWNLOAD GENERATED AUDIO
======================================================== */

downloadBtn.addEventListener(
    "click",
    async function(){

        if(!generatedAudioUrl){

            setStatus(
                "🟡 No generated audio is available."
            );

            return;

        }

        try{

            const response =
                await fetch(
                    generatedAudioUrl
                );

            if(!response.ok){

                throw new Error(
                    `Audio download failed (${response.status}).`
                );

            }

            const blob =
                await response.blob();

            const url =
                URL.createObjectURL(
                    blob
                );

            const link =
                document.createElement(
                    "a"
                );

            link.href =
                url;

            link.download =
                "bicon_dubbed_audio.mp3";

            document.body.appendChild(
                link
            );

            link.click();

            link.remove();

            URL.revokeObjectURL(
                url
            );

            setStatus(
                "🟢 Audio download started."
            );

        }catch(error){

            console.error(
                "Audio download error:",
                error
            );

            setStatus(
                "🔴 Audio download error: " +
                error.message
            );

        }

    }
);


/* ========================================================
   DOWNLOAD TRANSCRIPT
======================================================== */

downloadTranscriptBtn.addEventListener(
    "click",
    function(){

        const text =
            transcript.value.trim();

        if(!text){

            setStatus(
                "🟡 Transcript is empty."
            );

            return;

        }

        const blob =
            new Blob(
                [text],
                {
                    type:
                        "text/plain;charset=utf-8"
                }
            );

        const url =
            URL.createObjectURL(
                blob
            );

        const link =
            document.createElement(
                "a"
            );

        link.href =
            url;

        link.download =
            "bicon-transcript.txt";

        document.body.appendChild(
            link
        );

        link.click();

        link.remove();

        URL.revokeObjectURL(
            url
        );

        setStatus(
            "🟢 Transcript downloaded."
        );

    }
);


/* ========================================================
   TRANSCRIPT INPUT
======================================================== */

transcript.addEventListener(
    "input",
    function(){

        downloadTranscriptBtn.disabled =
            transcript.value.trim().length === 0;

    }
);


/* ========================================================
   INITIALIZATION
======================================================== */

downloadTranscriptBtn.disabled =
    transcript.value.trim().length === 0;

transcribeBtn.disabled =
    true;

uploadBtn.disabled =
    true;

voiceUploadBtn.disabled =
    true;

downloadBtn.disabled =
    true;


/*
   Check the live FastAPI backend
   immediately when the page loads.
*/

checkBackend();


/* ========================================================
   END
======================================================== */

</script>

</body>
</html>
