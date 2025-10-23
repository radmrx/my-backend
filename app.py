from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import moviepy.editor as mp
import whisper
from huggingface_hub import login

# Initialize FastAPI app
app = FastAPI()

# Ensure outputs folder exists
os.makedirs("outputs", exist_ok=True)

# Serve outputs folder publicly
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Optional: authenticate to Hugging Face if HF_TOKEN exists
hf_token = os.getenv("HF_TOKEN")
if hf_token:
    login(token=hf_token)

@app.get("/")
def root():
    return {"message": "Backend running successfully"}

@app.get("/process")
def get_info():
    return {"message": "Use POST to upload video"}

@app.post("/process")
async def process_video(
    file: UploadFile = File(...),
    addIntro: bool = Form(False),
    addCaptions: bool = Form(False),
    addTTS: bool = Form(False),
    ttsText: str = Form("")
):
    try:
        # Save uploaded file
        input_path = f"inputs_{file.filename}"
        with open(input_path, "wb") as f:
            f.write(await file.read())

        clip = mp.VideoFileClip(input_path)

        # Optional: add captions or TTS later
        final_clip = clip

        # Export processed video
        output_filename = f"processed_{os.path.basename(file.filename)}"
        output_path = os.path.join("outputs", output_filename)
        final_clip.write_videofile(output_path)

        result_url = f"https://my-backend-1-9tp1.onrender.com/outputs/{output_filename}"
        return JSONResponse({"success": True, "result_url": result_url})

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
