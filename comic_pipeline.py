"""Four-panel cyberpunk donghua comic: one AI image + English narration, 30s MP4."""
import json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from production import OUT, PipelineError, image, voice, run, font

def make_comic_video(row):
    work=OUT/("comic_"+str(row["id"]))
    work.mkdir(parents=True,exist_ok=True)
    raw=work/"four_panel_art.png"
    final_image=work/"four_panel_final.png"
    audio=work/"narration.mp3"
    dest=OUT/f"tao_{row['id']}.mp4"
    scene=(
      "ONE unified vertical 2-by-2 COMIC PAGE with EXACTLY FOUR clearly separated equally sized "
      "cinematic Chinese donghua anime panels. Thin gold dividing lines, NO speech bubbles, "
      "NO typography, NO letters. Same protagonist throughout: young Chinese woman, short black hair, "
      "indigo tech jacket with gold trim. Beautiful futuristic Shanghai cyberpunk aesthetic, "
      "electric cyan, magenta, deep indigo and warm gold, cinematic hand-painted 2D anime. "
      "Read panels LEFT TO RIGHT, TOP TO BOTTOM. "
      "PANEL 1 upper left: breaking technology news symbolized by glowing AI skyscrapers, "
      "holographic circuitry and neon city; topic: "+row["headline"]+". "
      "PANEL 2 upper right: protagonist encounters a dilemma about technological progress, "
      "facing an imposing luminous machine in the rain. "
      "PANEL 3 lower left: she meets an elderly Taoist sage beside flowing water in an ancient "
      "courtyard hidden within the futuristic city; calm philosophical revelation. "
      "PANEL 4 lower right: protagonist finds harmony between the natural world and technology "
      "at golden sunrise, hopeful thoughtful conclusion. "
      "One cohesive story across four distinct panels, consistent characters and world, "
      "expressive faces, sophisticated compositions, absolutely no text."
    )
    # Generate one image, not four separate paid calls.
    if not raw.exists():
        image(("FOUR-PANEL STORY",row["headline"],scene),raw,"production")
    im=Image.open(raw).convert("RGB")
    w,h=im.size
    # Preserve all four panels while fitting a vertical frame.
    scale=min(720/w,1100/h)
    im=im.resize((round(w*scale),round(h*scale)),Image.Resampling.LANCZOS)
    canvas=Image.new("RGB",(720,1280),(10,17,30))
    x=(720-im.width)//2
    y=28+(1100-im.height)//2
    canvas.paste(im,(x,y))
    d=ImageDraw.Draw(canvas)
    title="TAO TECH DAILY"
    d.text((32,1160),title,font=font(29),fill=(229,196,125))
    d.text((32,1205),"Ancient wisdom. Future worlds.",font=font(20),fill=(226,230,236))
    canvas.save(final_image)
    if not audio.exists():voice(row["script"],audio)
    try:
        duration=float(subprocess.check_output([
          "ffprobe","-v","error","-show_entries","format=duration",
          "-of","default=noprint_wrappers=1:nokey=1",str(audio)
        ]).decode().strip())
    except Exception as e:raise PipelineError("Cannot inspect narration: "+str(e))
    if duration>42:raise PipelineError("Narration exceeds supported length; shorten the script.")
    speed=max(0.5,duration/29.5)
    run(["ffmpeg","-y","-loglevel","error","-loop","1","-framerate","24",
         "-i",str(final_image),"-i",str(audio),
         "-filter_complex",f"[1:a]atempo={speed:.4f},apad,atrim=0:30[a]",
         "-map","0:v","-map","[a]","-t","30",
         "-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-movflags","+faststart",str(dest)])
    (work/"manifest.json").write_text(json.dumps({
      "story_id":row["id"],"style":"four_panel_comic","mode":"production",
      "image":str(final_image),"video":str(dest),"status":"awaiting_review"
    },indent=2))
    return {"video":"/videos/"+dest.name,"mode":"production",
            "style":"four_panel_comic","status":"awaiting_review"}
