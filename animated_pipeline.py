"""Real motion-video pipeline: 6 Runway image-to-video shots, composited with captions and English narration."""
import base64, json, os, subprocess
from pathlib import Path
from urllib.request import urlopen
from PIL import Image, ImageDraw, ImageFont
from production import OUT, PipelineError, image, voice, run, font

STYLE = ("Premium cinematic cyberpunk Chinese donghua animation, futuristic Shanghai "
         "megacity, neon magenta and electric cyan with warm gold Taoist symbols, "
         "atmospheric rain, expressive hand-drawn characters, layered parallax, "
         "beautiful detailed 2D anime aesthetic, vertical composition, no text or logos.")
CHARACTER = ("Recurring protagonist: young Chinese woman with short black hair, "
             "dark indigo tech jacket with gold trim. Keep costume and face consistent.")
def storyboard(row):
 return [
  ("THE NEWS",row["headline"],"Wide establishing shot: neon Chinese megacity, aerial trains and holographic towers. Slow cinematic push-in."),
  ("THE IMPACT","A world accelerating","The protagonist runs through rain-lit futuristic market streets. Tracking camera, animated crowds and reflections."),
  ("THE CONTRAST","But what is wisdom?","She steps through an ancient stone moon gate. City light transitions into quiet misty mountains. Camera follows."),
  ("THE TAO",row["translation"],"An elderly Taoist sage stands beside a flowing river as glowing data particles drift like fireflies. Water visibly moves."),
  ("THE INSIGHT",row["insight"],"The protagonist watches digital circuitry transform into flowing water and mountain contours. Fluid animated metamorphosis."),
  ("THE QUESTION","What would wisdom change?","She looks out over the city at sunrise, neon lights fading to golden sky. Slow pullback, cloth and hair moving.")
 ]
def artwork(scene,path):
 image((scene[0],scene[1],STYLE+" "+CHARACTER+" "+scene[2]),path,"production")
def runway_clip(client,raw,scene,dest):
 try:
  data_uri="data:image/png;base64,"+base64.b64encode(raw.read_bytes()).decode("ascii")
  task=client.image_to_video.create(
    model=os.getenv("RUNWAY_MODEL","gen4_turbo"),
    prompt_image=data_uri,
    prompt_text=STYLE+" "+CHARACTER+" "+scene[2]+" Natural motion throughout the entire 5 second shot.",
    ratio="720:1280",duration=5
  ).wait_for_task_output()
  if not task.output:raise PipelineError("Runway did not return a video")
  with urlopen(task.output[0],timeout=180) as response:dest.write_bytes(response.read())
 except PipelineError:raise
 except Exception as e:raise PipelineError("Runway generation failed: "+str(e)) from e
def overlay(scene,path):
 im=Image.new("RGBA",(720,1280),(0,0,0,0))
 d=ImageDraw.Draw(im,"RGBA")
 d.rounded_rectangle((32,900,688,1210),radius=20,fill=(4,10,22,194))
 d.text((60,920),scene[0],font=font(31),fill=(251,199,101,255))
 words=scene[1].split();lines=[];line=""
 for word in words:
  trial=(line+" "+word).strip()
  if d.textbbox((0,0),trial,font=font(36))[2]>585 and line:lines.append(line);line=word
  else:line=trial
 if line:lines.append(line)
 for n,line in enumerate(lines[:5]):d.text((60,984+43*n),line,font=font(36),fill=(255,255,255,255))
 im.save(path)
def make_animated_video(row):
 if not os.getenv("OPENAI_API_KEY"):raise PipelineError("OPENAI_API_KEY required")
 if not os.getenv("RUNWAYML_API_SECRET"):raise PipelineError("RUNWAYML_API_SECRET required")
 try:from runwayml import RunwayML
 except ImportError:raise PipelineError("Install runwayml with pip")
 scenes=storyboard(row);work=OUT/("animated_"+str(row["id"]));work.mkdir(parents=True,exist_ok=True)
 client=RunwayML()
 clips=[]
 for i,scene in enumerate(scenes):
  raw=work/f"art_{i}.png";motion=work/f"motion_{i}.mp4";cap=work/f"caption_{i}.png";clip=work/f"final_{i}.mp4"
  # Reuse completed expensive provider calls if the assembly needs a retry.
  if not raw.exists():artwork(scene,raw)
  if not motion.exists():runway_clip(client,raw,scene,motion)
  overlay(scene,cap)
  run(["ffmpeg","-y","-loglevel","error","-i",str(motion),"-loop","1","-i",str(cap),
       "-filter_complex","[0:v]fps=24,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1[bg];[bg][1:v]overlay=0:0:shortest=1,format=yuv420p[v]",
       "-map","[v]","-t","5","-an","-c:v","libx264","-pix_fmt","yuv420p",str(clip)])
  clips.append(clip)
 listing=work/"clips.txt"
 listing.write_text("".join("file '"+str(c.resolve())+"'\n" for c in clips))
 silent=work/"silent.mp4"
 run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(listing),"-t","30","-c:v","libx264","-pix_fmt","yuv420p",str(silent)])
 audio=work/"narration.mp3"
 if not audio.exists():voice(row["script"],audio)
 try:
  duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(audio)]).decode().strip())
 except Exception as e:raise PipelineError("Unable to measure narration: "+str(e))
 if duration>42:raise PipelineError("Narration too long for 30 seconds. Shorten script.")
 factor=max(0.5,duration/29.5)
 dest=OUT/f"tao_{row['id']}.mp4"
 run(["ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(audio),
      "-filter_complex",f"[1:a]atempo={factor:.4f},apad,atrim=0:30[a]",
      "-map","0:v","-map","[a]","-t","30","-c:v","copy","-c:a","aac",str(dest)])
 (work/"manifest.json").write_text(json.dumps({"story_id":row["id"],"provider":"runway","clips":[str(p) for p in clips],"status":"awaiting_review"},indent=2))
 return {"video":"/videos/"+dest.name,"mode":"production","status":"awaiting_review","animation":"runway"}
