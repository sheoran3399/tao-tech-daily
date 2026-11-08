## v7: Captioned four-scene comic (no narration)

The default `ANIMATION_PROVIDER=comic` mode now generates **one four-panel image**, splits it into four illustrations, and places **a readable English caption to the right of each**. The final panel displays the original Chinese Taoist quote, its English translation, and chapter attribution. The 30-second MP4 is **silent**: there is no text-to-speech request and no Runway charge.

```bash
cd ~/Documents/tao-tech-daily
git pull
source .venv/bin/activate
set -a; source .env; set +a
python studio.py render 18 --mode production
open output/tao_18.mp4
```

Replace 18 with the story you want. The prompt is cached: if the underlying story and insight haven't changed, the existing illustration is reused, but the final composition is rebuilt. Review the quote and translation carefully before approving. The output is still one static page shown for 30 seconds, not four successive scenes.

# Recommended: Four-panel static comic (no Runway)

Update the project with `git pull`. Configure `OPENAI_API_KEY` and `ANIMATION_PROVIDER=comic` in your local `.env`. You do **not** need `RUNWAYML_API_SECRET`.

The app does not automatically load `.env`. In Terminal, run:

```bash
cd ~/Documents/tao-tech-daily
source .venv/bin/activate
set -a; source .env; set +a
python studio.py list
python studio.py render 20 --mode production
```

Replace 20 with the selected story ID. One AI image is generated containing four cyberpunk anime story panels, and one English narration track is created. FFmpeg renders a 30-second video showing that static four-panel image. Review `output/tao_20.mp4` before running `python studio.py approve 20` and `python studio.py publish 20`.

**Cost:** one OpenAI image call plus one TTS call per episode, instead of six images and six Runway clips. Check current OpenAI pricing and model availability. No Runway billing.

# Tao Tech Daily v3: Production and gallery

## First-time update on your Mac

1. Stop your running server with Control+C.
2. Run:
   ```bash
   cd ~/Documents/tao-tech-daily
   git pull
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```
3. Start the gallery with `python -m uvicorn app:app --host 127.0.0.1 --port 8000`.
4. Open `http://127.0.0.1:8000`. You will see only published videos.

## Private production

Open a second Terminal window, activate the environment and run `python studio.py --help`.

```bash
python studio.py ingest
python studio.py list
python studio.py show 20
python studio.py render 20 --mode preview
```

Replace 20 with a valid story ID. Preview mode uses placeholder art and no voice. To produce a visually richer AI version:

```bash
export OPENAI_API_KEY='your-private-key'
export RUNWAYML_API_SECRET='your-private-runway-key'
export ANIMATION_PROVIDER=runway
python studio.py render 20 --mode production
```

Do not share or commit your API key. For a longer-term configuration, store it in a local `.env` file and load it into the Terminal before running the command. The application does not automatically load `.env`.

Open the resulting `output/tao_20.mp4` in Finder or QuickTime. Check source facts, quote authenticity, pacing, captions, pronunciation and visual quality.

```bash
python studio.py approve 20
python studio.py publish 20
```

Refresh the gallery page. Only approved/published films are displayed.

## Costs and caveats

OpenAI image and voice calls incur API usage charges. Animated mode requests six images, six Runway clips, and one narration per production run. Confirm current provider models and prices before rendering. It does not yet generate genuine moving anime scenes; it animates stills with camera motion. The Runway pipeline now assembles six genuine 5-second animated clips, but requires live provider testing and incurs costs. It caches finished raw clips for retries. The website is not deployed publicly and YouTube Shorts publishing is not implemented.

For a real public website, configure HTTPS, durable video storage, a production database, backups, and deployment. Keep `studio.py` and secrets off the public server if possible.
