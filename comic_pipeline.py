"""Four-panel silent cyberpunk comic: image on left, editorial caption on right.

One generated 2x2 illustration is split into four scenes, then laid out as
four horizontal rows in a single 720x1280 frame. Last row carries the
original Chinese Taoist quote, its English translation and attribution.
"""
import hashlib, json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from production import OUT, image, run

BG=(10,18,31); GOLD=(231,195,120); WHITE=(245,242,233); MUTED=(185,204,214)
WIDTH,HEIGHT=720,1280

def choose_font(size, chinese=False):
    paths=(
        ['/System/Library/Fonts/PingFang.ttc',
         '/System/Library/Fonts/Hiragino Sans GB.ttc',
         '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
        if chinese else
        ['/System/Library/Fonts/Supplemental/Arial.ttf',
         '/Library/Fonts/Arial.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    )
    for path in paths:
        try:return ImageFont.truetype(path,size)
        except OSError:pass
    return ImageFont.load_default()

def lines_for(draw, text, font, max_width):
    # Chinese quotes wrap by character; English captions wrap by word.
    tokens=list(text) if re.search(r'[\u3400-\u9fff]',text) else text.split()
    join='' if re.search(r'[\u3400-\u9fff]',text) else ' '
    lines=[]; current=''
    for token in tokens:
        trial=current+join+token if current else token
        if draw.textbbox((0,0),trial,font=font)[2]>max_width and current:
            lines.append(current);current=token
        else:current=trial
    if current:lines.append(current)
    return lines

def draw_wrapped(draw, text, x, y, width, height, base_size, color, chinese=False):
    for size in range(base_size,15,-2):
        f=choose_font(size,chinese)
        lines=lines_for(draw,text,f,width)
        step=int(size*1.38)
        if len(lines)*step<=height:break
    for line in lines:
        draw.text((x,y),line,font=f,fill=color)
        y+=step
    return y

def make_comic_video(row):
    work=OUT/('comic_'+str(row['id']))
    work.mkdir(parents=True,exist_ok=True)
    raw=work/'four_panel_art.png'
    final=work/'four_panel_final.png'
    dest=OUT/f"tao_{row['id']}.mp4"
    insight=(row.get('insight') or '').strip()
    translation=(row.get('translation') or '').strip()
    quote=(row.get('quote') or '').strip()
    chapter=(row.get('chapter') or '').strip()
    if not quote or not translation or not chapter:
        raise ValueError('Taoist quote, English translation and chapter must be supplied')
    prompt=(
      'A SINGLE 2x2 grid of EXACTLY FOUR distinct Chinese donghua cyberpunk anime '
      'story illustrations, no words, no captions, no letters, no watermarks. '
      'Same protagonist in every panel: young Chinese woman with short black hair '
      'and indigo jacket with gold trim. Rich cyan-magenta neon with gold accents. '
      'Upper-left: the news topic '+row['headline']+'. '
      'Upper-right: a human conflict specifically about '+insight+'. '
      'Lower-left: symbolic Taoist insight '+translation+'. '
      'Lower-right: the protagonist making a specific thoughtful choice that resolves the conflict. '
      'Beautiful 2D anime composition, four equally sized panels with clear borders.'
    )
    sig=hashlib.sha256(prompt.encode()).hexdigest()
    marker=work/'image_prompt.sha256'
    if not raw.exists() or not marker.exists() or marker.read_text()!=sig:
        image(('FOUR-PANEL STORY',row['headline'],prompt),raw,'production')
        marker.write_text(sig)
    source=Image.open(raw).convert('RGB')
    w,h=source.size
    crops=[source.crop(box) for box in [
      (0,0,w//2,h//2),(w//2,0,w,h//2),
      (0,h//2,w//2,h),(w//2,h//2,w,h)]]
    canvas=Image.new('RGB',(WIDTH,HEIGHT),BG)
    draw=ImageDraw.Draw(canvas)
    draw.text((25,13),'TAO TECH DAILY',font=choose_font(24),fill=GOLD)
    draw.text((25,43),'TECHNOLOGY  /  TAOISM',font=choose_font(14),fill=MUTED)
    captions=[
      ('01  THE NEWS',row['headline']),
      ('02  THE DILEMMA',insight or 'What does this change for people?'),
      ('03  THE WISDOM','A different way to see progress.'),
      ('04  THE TAO',None)
    ]
    top=78;row_h=290;img_w=315
    for idx,(pic,(label,caption)) in enumerate(zip(crops,captions)):
        y=top+idx*row_h
        # 4 equally sized illustrations on the left; captions alongside on the right.
        ratio=max(img_w/pic.width,272/pic.height)
        resized=pic.resize((round(pic.width*ratio),round(pic.height*ratio)),Image.Resampling.LANCZOS)
        dx=(resized.width-img_w)//2;dy=(resized.height-272)//2
        canvas.paste(resized.crop((dx,dy,dx+img_w,dy+272)),(20,y+4))
        draw.rectangle((20,y+4,335,y+276),outline=GOLD,width=2)
        x=353
        draw.text((x,y+8),label,font=choose_font(18),fill=GOLD)
        if idx<3:
            draw_wrapped(draw,caption,x,y+48,335,210,25,WHITE)
        else:
            yy=draw_wrapped(draw,quote,x,y+44,335,86,26,GOLD,True)
            yy=draw_wrapped(draw,translation,x,yy+12,335,110,22,WHITE)
            draw_wrapped(draw,chapter,x,min(yy+10,y+246),335,35,16,MUTED)
        draw.line((20,y+row_h-5,700,y+row_h-5),fill=(49,67,82),width=1)
    draw.text((25,1250),'Ancient wisdom. Future worlds.',font=choose_font(17),fill=MUTED)
    canvas.save(final)
    # Silent 30-second MP4; no OpenAI speech request and no audio track.
    run(['ffmpeg','-y','-loglevel','error','-loop','1','-framerate','24',
         '-i',str(final),'-t','30','-c:v','libx264','-pix_fmt','yuv420p',
         '-movflags','+faststart',str(dest)])
    (work/'manifest.json').write_text(json.dumps({
      'story_id':row['id'],'style':'four_panel_captioned_comic',
      'mode':'production','narration':False,'image':str(final),
      'video':str(dest),'status':'awaiting_review'
    },indent=2))
    return {'video':'/videos/'+dest.name,'mode':'production',
            'style':'four_panel_captioned_comic','status':'awaiting_review'}
