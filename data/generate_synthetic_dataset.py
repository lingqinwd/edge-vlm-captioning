from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import csv

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'images'
OUT.mkdir(parents=True,exist_ok=True)
W=H=512
try:
    font=ImageFont.truetype('arial.ttf',48)
    small=ImageFont.truetype('arial.ttf',30)
except Exception:
    font=ImageFont.load_default(); small=font

def base(): return Image.new('RGB',(W,H),'white')
def save(name,cat,caption,draw_fn):
    im=base(); d=ImageDraw.Draw(im); draw_fn(d); im.save(OUT/name); rows.append((name,cat,'generated locally',caption,'No personal data; deterministic synthetic image.'))
rows=[]
# objects
save('06_yellow_star.png','object','A yellow star on a blue background.',lambda d:(d.rectangle((0,0,W,H),fill='#dbeafe'),d.polygon([(256,70),(294,190),(420,190),(318,265),(356,390),(256,315),(156,390),(194,265),(92,190),(218,190)],fill='#facc15')))
save('07_orange_circle.png','object','An orange circle on a gray background.',lambda d:(d.rectangle((0,0,W,H),fill='#e5e7eb'),d.ellipse((126,126,386,386),fill='#f97316')))
save('08_purple_rectangle.png','object','A purple rectangle on a white background.',lambda d:d.rectangle((110,170,402,342),fill='#8b5cf6'))
save('09_red_ball.png','object','A red ball with a small shadow.',lambda d:(d.ellipse((150,120,360,330),fill='#ef4444'),d.ellipse((120,350,390,390),fill='#d1d5db')))
# patterns
save('10_vertical_stripes.png','pattern','A pattern of alternating blue and white vertical stripes.',lambda d:[d.rectangle((i,0,i+64,H),fill=('#2563eb' if (i//64)%2==0 else 'white')) for i in range(0,W,64)])
save('11_horizontal_stripes.png','pattern','A pattern of alternating green and white horizontal stripes.',lambda d:[d.rectangle((0,i,W,i+64),fill=('#16a34a' if (i//64)%2==0 else 'white')) for i in range(0,H,64)])
save('12_concentric_circles.png','pattern','Several concentric circles in different colors.',lambda d:[d.ellipse((30+i,30+i,W-30-i,H-30-i),outline=c,width=14) for i,c in [(0,'#ef4444'),(35,'#f59e0b'),(70,'#22c55e'),(105,'#3b82f6'),(140,'#8b5cf6')]])
save('13_diagonal_pattern.png','pattern','A blue and white diagonal line pattern.',lambda d:[d.line((i,0,i-240,H),fill='#1d4ed8',width=12) for i in range(0,W+250,70)])
# scenes

def sunset(d):
    for y in range(H):
        t=y/H; c=(int(30+220*t),int(80+80*t),int(180-130*t)); d.line((0,y,W,y),fill=c)
    d.ellipse((190,220,322,352),fill='#fde047'); d.rectangle((0,350,W,H),fill='#1f2937')
save('14_sunset_scene.png','scene','A yellow sun is setting over a dark horizon.',sunset)
def house(d):
    d.rectangle((0,0,W,H),fill='#bfdbfe'); d.rectangle((0,360,W,H),fill='#65a30d'); d.polygon([(100,250),(256,110),(412,250)],fill='#b91c1c'); d.rectangle((130,245,382,390),fill='#fef3c7'); d.rectangle((205,300,275,390),fill='#92400e'); d.rectangle((155,275,205,330),fill='#60a5fa'); d.rectangle((305,275,355,330),fill='#60a5fa')
save('15_house_scene.png','scene','A small house with a red roof on green grass.',house)
def road(d):
    d.rectangle((0,0,W,H),fill='#bfdbfe'); d.polygon([(160,512),(352,512),(290,230),(222,230)],fill='#4b5563'); d.line((256,512,256,230),fill='#fef08a',width=12); d.ellipse((80,80,150,150),fill='#fde047')
save('16_road_scene.png','scene','A road leads toward the horizon under a blue sky.',road)
def park(d):
    d.rectangle((0,0,W,H),fill='#bae6fd'); d.rectangle((0,350,W,H),fill='#4ade80'); d.rectangle((235,220,275,390),fill='#92400e'); d.ellipse((145,120,365,280),fill='#16a34a'); d.ellipse((90,160,220,300),fill='#22c55e'); d.ellipse((290,160,430,300),fill='#15803d')
save('17_park_scene.png','scene','A green tree stands in a sunny park.',park)
# simple animals

def cat(d):
    d.ellipse((150,170,360,380),fill='#9ca3af'); d.polygon([(165,210),(175,105),(235,175)],fill='#9ca3af'); d.polygon([(275,175),(340,105),(345,220)],fill='#9ca3af'); d.ellipse((205,245,225,265),fill='black'); d.ellipse((285,245,305,265),fill='black'); d.line((255,275,255,310),fill='black',width=5)
save('18_cat_icon.png','animal','A gray cat icon with pointed ears.',cat)
def fish(d):
    d.ellipse((120,190,370,340),fill='#38bdf8'); d.polygon([(370,265),(455,195),(455,335)],fill='#0ea5e9'); d.ellipse((175,235,200,260),fill='black')
save('19_fish_icon.png','animal','A blue fish swimming to the right.',fish)
# text
for name,textv,color,caption in [('20_sign_ai.png','AI','#1d4ed8','A blue sign with the letters AI.'),('21_sign_stop.png','STOP','#dc2626','A red sign with the word STOP.'),('22_number_123.png','123','#111827','A black number 123 on a white background.'),('23_sign_ok.png','OK','#16a34a','A green sign with the word OK.')]:
    def fn(d,txt=textv,c=color):
        d.rounded_rectangle((70,150,442,362),radius=28,fill=c); box=d.textbbox((0,0),txt,font=font); d.text(((W-(box[2]-box[0]))/2,220-(box[3]-box[1])/2),txt,font=font,fill='white')
    save(name,'text',caption,fn)
# gradients and textures

def gradient(d):
    for y in range(H):
        t=y/H; d.line((0,y,W,y),fill=(int(255*t),int(80+120*t),int(255-100*t)))
save('24_color_gradient.png','abstract','A smooth gradient from purple to orange.',gradient)
def checker(d):
    for y in range(0,H,64):
        for x in range(0,W,64): d.rectangle((x,y,x+64,y+64),fill=('#111827' if ((x//64+y//64)%2==0) else '#f9fafb'))
save('25_large_checker.png','pattern','A large black and white checkerboard.',checker)
def dots(d):
    d.rectangle((0,0,W,H),fill='#fef3c7')
    for y in range(60,480,90):
        for x in range(60,480,90): d.ellipse((x-18,y-18,x+18,y+18),fill='#f59e0b')
save('26_orange_dots.png','pattern','An orange dotted pattern on a pale background.',dots)
def mountain(d):
    d.rectangle((0,0,W,H),fill='#bfdbfe'); d.polygon([(0,420),(140,180),(270,420)],fill='#64748b'); d.polygon([(160,420),(330,130),(512,420)],fill='#475569'); d.polygon([(330,130),(285,210),(360,190)],fill='white'); d.rectangle((0,420,W,H),fill='#166534')
save('27_mountain_scene.png','scene','Two gray mountains rise above a green foreground.',mountain)
with (ROOT/'manifest.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['file','category','license_or_source','reference_caption','notes']); w.writerows(rows)
print(f'created {len(rows)} images in {OUT}')

