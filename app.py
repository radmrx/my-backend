import os
import uuid
import tempfile
import shutil
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip

HF_TOKEN = os.environ.get("HF_TOKEN", "")
if not HF_TOKEN:
    raise RuntimeError("Set HF_TOKEN environment variable with your Hugging Face token.")

HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
WHISPER_MODEL = "openai/whisper-large-v3"
TTS_MODEL = "microsoft/VibeVoice-1.5B"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your DeepSite origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def hf_asr_from_file(audio_path: str) -> str:
    url = f"https://api-inference.huggingface.co/models/{WHISPER_MODEL}"
    with open(audio_path, "rb") as f:
        data = f.read()
    resp = requests.post(url, headers=HF_HEADERS, data=data, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"HF ASR error {resp.status_code}: {resp.text}")
    res_json = resp.json()
    return res_json.get("text", "")

def hf_tts_from_text(text: str) -> bytes:
    url = f"https://api-inference.huggingface.co/models/{TTS_MODEL}"
    payload = {"inputs": text}
    headers = HF_HEADERS.copy()
    headers["Accept"] = "application/octet-stream"
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"HF TTS error {resp.status_code}: {resp.text}")
    return resp.content

@app.post("/process")
async def process_video(
    file: UploadFile = File(...),
    addIntro: bool = Form(True),
    addCaptions: bool = Form(True),
    addTTS: bool = Form(True),
    ttsText: str = Form("")
):
    job_id = str(uuid.uuid4())
    tmpdir = tempfile.mkdtemp(prefix=f"job_{job_id}_")
    in_path = os.path.join(tmpdir, "input_video.mp4")
    try:
        with open(in_path, "wb") as f:
            f.write(await file.read())

        clip = VideoFileClip(in_path)
        clips = [clip]

        if addIntro and os.path.exists("intro.mp4"):
            intro = VideoFileClip("intro.mp4").resize((clip.w, clip.h))
            clips.insert(0, intro)
        if addIntro and os.path.exists("outro.mp4"):
            outro = VideoFileClip("outro.mp4").resize((clip.w, clip.h))
            clips.append(outro)

        combined = concatenate_videoclips(clips, method="compose")

        transcript_text = ""
        if addCaptions and combined.audio:
            audio_temp = os.path.join(tmpdir, "audio.wav")
            combined.audio.write_audiofile(audio_temp, logger=None)
            try:
                transcript_text = hf_asr_from_file(audio_temp)
            except Exception:
                transcript_text = ""

        if addTTS:
            text_for_tts = ttsText.strip() or transcript_text or ""
            if text_for_tts:
                try:
                    audio_bytes = hf_tts_from_text(text_for_tts)
                    tts_path = os.path.join(tmpdir, "tts_audio.wav")
                    with open(tts_path, "wb") as ta:
                        ta.write(audio_bytes)
                    aclip = AudioFileClip(tts_path)
                    combined = combined.set_audio(aclip)
                except Exception:
                    pass

        final = combined
        if addCaptions and transcript_text:
            caption = TextClip(transcript_text, fontsize=28, method='caption', size=(combined.w - 40, None))
            caption = caption.set_duration(combined.duration).set_position(("center", "bottom"))
            final = CompositeVideoClip([combined, caption])

        out_name = f"{job_id}_final.mp4"
        out_path = os.path.join(OUT_DIR, out_name)
        final.write_videofile(out_path, codec="libx264", audio_codec="aac", threads=2, logger=None)

        shutil.rmtree(tmpdir, ignore_errors=True)
        return JSONResponse({"success": True, "result_url": f"/outputs/{out_name}"})
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/outputs/{fname}")
async def get_output(fname: str):
    path = os.path.join(OUT_DIR, fname)
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=fname)
    return JSONResponse({"error": "file not found"}, status_code=404)