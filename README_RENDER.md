# video-backend (Render-ready)

This repository contains a simple FastAPI backend that accepts an uploaded video, optionally adds intro/outro, auto-generates captions using Whisper (Hugging Face Inference API), optionally generates TTS narration, and returns a processed MP4.

## How to deploy on Render (quick)
1. Create a Render account: https://render.com
2. Create a new **Web Service** and choose to deploy from a repo or upload this ZIP (Manual Deploy).
3. Select **Environment: Docker**.
4. Add the environment variable `HF_TOKEN` with your Hugging Face token (from https://huggingface.co/settings/tokens).
5. Deploy. When build finishes you'll get a public URL (e.g. https://video-backend.onrender.com).
6. Paste the public URL + `/process` into your DeepSite frontend JavaScript:
   `const BACKEND = 'https://your-render-url.onrender.com/process';`

## Notes
- The service currently allows CORS from any origin (`allow_origins=["*"]`). For production, restrict this to your DeepSite domain.
- Replace `intro.mp4` / `outro.mp4` with your branding clips.
- For large-scale or heavy ML usage, consider using Hugging Face paid inference endpoints or self-hosting models with GPU.
