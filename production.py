"""Video pipeline: OpenAI artwork + voice, optional Runway animation, FFmpeg."""
import os, json, base64, subprocess, shutil, textwrap
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).parent;OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
class PipelineError(RuntimeError):pass
def run(args):
 try:subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=240)
 except FileNotFoundError:raise PipelineError('FFmpeg is required')
 except subprocess.CalledProcessError as e:raise PipelineError(e.stderr.decode(errors='replace')[-500:])
def font(size):
 for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
  if Path(p).exists():return ImageFont.truetype(p,size)
 return ImageFont.load_default()
def scenes(row):
 return [
 ('THE HEADLINE',row['headline'],'cinematic wide view of a futuristic Chinese metropolis, glowing circuits, dramatic atmospheric perspective'),
 ('THE TURNING POINT','Technology changes everything.','a lone young engineer facing a luminous machine inside a centuries-old Chinese temple'),
 ('THE QUESTION','But what makes us wise?','a mysterious moon gate connecting ancient misty mountains to a futuristic neon skyline'),
 ('THE TAO',row['translation'],'a Taoist sage beside a waterfall, futuristic holograms gently dissolving into mist'),
 ('THE INSIGHT',row['insight'],'vast ink wash mountain peaks interwoven with delicate glowing electronic circuits'),
 ('REFLECT','What would wisdom change?','single golden lantern floating on a cyberpunk river at sunrise, peaceful cinematic finale')]
def image(scene,path,mode):
 if mode=='preview':
  im=Image.new('RGB',(720,1280),(16,34,54));d=ImageDraw.Draw(im);d.ellipse((80,230,640,790),outline=(196,166,105),width=8);d.text((70,800),'STORYBOARD PREVIEW',font=font(35),fill='white');im.save(path);return
 key=os.getenv('OPENAI_API_KEY')
 if not key:raise PipelineError('OPENAI_API_KEY missing')
 prompt='Premium cinematic Chinese donghua animation keyframe, consistent visual language, expressive hand-painted backgrounds, elegant linework, cinematic composition, rich layered depth, subtle jade and warm gold palette with restrained futuristic neon, ancient Chinese philosophy meeting future technology, emotionally evocative, sophisticated art direction, vertical 9:16, no text, no logos, no watermarks: '+scene[2]
 payload=json.dumps({'model':os.getenv('OPENAI_IMAGE_MODEL','gpt-image-1.5'),'prompt':prompt,'size':'1024x1536','n':1}).encode()
 req=Request('https://api.openai.com/v1/images/generations',data=payload,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 try:
  with urlopen(req,timeout=180) as resp:data=json.load(resp)['data'][0]
  if data.get('b64_json'):path.write_bytes(base64.b64decode(data['b64_json']))
  else:
   with urlopen(data['url'],timeout=120) as resp:path.write_bytes(resp.read())
 except Exception as e:raise PipelineError('Image provider failed: '+str(e))
def caption(scene,source,dest):
 im=Image.open(source).convert('RGB');w,h=im.size;target=9/16
 if w/h>target:
  nw=int(h*target);im=im.crop(((w-nw)//2,0,(w+nw)//2,h))
 else:
  nh=int(w/target);im=im.crop((0,(h-nh)//2,w,(h+nh)//2))
 im=im.resize((720,1280));d=ImageDraw.Draw(im,'RGBA')
 d.rounded_rectangle((25,850,695,1200),radius=24,fill=(5,15,28,225))
 d.text((55,880),scene[0],font=font(35),fill=(255,204,128))
 words=scene[1].split();lines=[];line=''
 for word in words:
  candidate=(line+' '+word).strip()
  if d.textbbox((0,0),candidate,font=font(38))[2]>600 and line:lines.append(line);line=word
  else:line=candidate
 if line:lines.append(line)
 for i,line in enumerate(lines[:5]):d.text((55,945+48*i),line,font=font(38),fill='white')
 im.save(dest)
def voice(script,path):
 key=os.getenv('OPENAI_API_KEY')
 if not key:raise PipelineError('OPENAI_API_KEY missing')
 req=Request('https://api.openai.com/v1/audio/speech',data=json.dumps({'model':os.getenv('OPENAI_TTS_MODEL','tts-1'),'voice':os.getenv('OPENAI_TTS_VOICE','alloy'),'input':script,'response_format':'mp3'}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 try:
  with urlopen(req,timeout=180) as resp:path.write_bytes(resp.read())
 except Exception as e:raise PipelineError('Speech provider failed: '+str(e))
def make_video(row,mode='preview'):
 if mode not in ('preview','production'):raise PipelineError('Mode must be preview or production')
 if mode=='production' and os.getenv('ANIMATION_PROVIDER','runway')=='runway':
  from animated_pipeline import make_animated_video
  return make_animated_video(row)
 if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise PipelineError('Install FFmpeg and FFprobe')
 work=OUT/('work_'+str(row['id']));work.mkdir(exist_ok=True)
 clips=[]
 for i,scene in enumerate(scenes(row)):
  raw=work/f'raw{i}.png';still=work/f'still{i}.png';clip=work/f'clip{i}.mp4'
  image(scene,raw,mode);caption(scene,raw,still)
  if mode=='production' and os.getenv('ANIMATION_PROVIDER','kenburns')=='runway':
   raise PipelineError('Runway animation is not yet supported in the final video. Use ANIMATION_PROVIDER=kenburns to avoid unnecessary charges.')
  run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(still),'-vf','zoompan=z=min(zoom+0.0005\\,1.06):d=120:s=720x1280:fps=24,format=yuv420p','-frames:v','120','-an','-c:v','libx264','-pix_fmt','yuv420p',str(clip)])
  clips.append(clip)
 concat=work/'concat.txt';concat.write_text(''.join("file '"+str(p.resolve())+"'\\n" for p in clips).replace('\\n','\n'))
 silent=work/'silent.mp4'
 run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-t','30','-c:v','libx264','-pix_fmt','yuv420p',str(silent)])
 dest=OUT/f"tao_{row['id']}.mp4"
 if mode=='production':
  audio=work/'voice.mp3';voice(row['script'],audio)
  duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(audio)]).decode().strip())
  factor=duration/29.5
  if factor>2:raise PipelineError('Narration too long; shorten the script')
  factor=max(0.5,factor)
  run(['ffmpeg','-y','-loglevel','error','-i',str(silent),'-i',str(audio),'-filter_complex',f'[1:a]atempo={factor:.4f},apad,atrim=0:30[a]','-map','0:v','-map','[a]','-t','30','-c:v','copy','-c:a','aac',str(dest)])
 else:shutil.copyfile(silent,dest)
 (work/'manifest.json').write_text(json.dumps({'story_id':row['id'],'mode':mode,'scenes':scenes(row),'status':'awaiting_review'},ensure_ascii=False,indent=2))
 return {'video':'/videos/'+dest.name,'mode':mode,'status':'awaiting_review'}
