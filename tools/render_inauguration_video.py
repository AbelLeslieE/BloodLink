"""Render the 16-second BloodLink/NSS inauguration film.

The animation is authored at 1920x1080 and encoded to a 3840x2160 H.264 master.
It intentionally uses clean, symbolic medical imagery rather than graphic anatomy.
"""

from __future__ import annotations

import math
import os
import random
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "media" / "inauguration"
LOGO_PATH = ROOT / "frontend" / "assets" / "lf_logo.png"
W, H = 1920, 1080
FPS = 30
DURATION = 16
FRAMES = FPS * DURATION

NAVY = (3, 13, 31)
DEEP_RED = (92, 0, 18)
CRIMSON = (196, 18, 45)
BRIGHT_RED = (236, 35, 52)
GOLD = (229, 181, 80)
WHITE = (250, 252, 255)


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def smooth(x: float) -> float:
    x = clamp(x)
    return x * x * (3.0 - 2.0 * x)


def ease_out(x: float) -> float:
    return 1.0 - (1.0 - clamp(x)) ** 3


def seg(t: float, start: float, end: float) -> float:
    return clamp((t - start) / (end - start))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("segoeuib.ttf" if bold else "segoeui.ttf"),
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


F_TITLE = font(116, True)
F_SUBTITLE = font(45, True)
F_LABEL = font(31, True)
F_SMALL = font(28, False)
F_TINY = font(22, True)


def centered(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, fnt, fill, spacing=0):
    if spacing <= 0:
        box = draw.textbbox((0, 0), text, font=fnt)
        draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=fnt, fill=fill)
        return
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + spacing * max(0, len(text) - 1)
    x = xy[0] - total / 2
    for ch, width in zip(text, widths):
        draw.text((x, xy[1] - fnt.size / 2), ch, font=fnt, fill=fill)
        x += width + spacing


def glow_circle(layer: Image.Image, xy, radius, color, alpha=255, blur=30):
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    x, y = xy
    gd.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    if blur:
        glow = glow.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(glow)


def draw_heartbeat(draw: ImageDraw.ImageDraw, y: int, progress: float, alpha: int = 255):
    pts = [
        (100, y), (390, y), (450, y - 5), (510, y + 4),
        (575, y), (625, y - 110), (675, y + 170), (735, y - 45),
        (795, y), (1130, y), (1190, y - 4), (1240, y + 3),
        (1310, y), (1365, y - 65), (1410, y + 85), (1460, y), (1820, y),
    ]
    lengths = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        length = math.dist(a, b)
        lengths.append(length)
        total += length
    target = total * clamp(progress)
    built = [pts[0]]
    walked = 0.0
    for (a, b), length in zip(zip(pts, pts[1:]), lengths):
        if walked + length <= target:
            built.append(b)
            walked += length
        else:
            remain = max(0.0, target - walked)
            if remain > 0:
                q = remain / length
                built.append((a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q))
            break
    if len(built) > 1:
        draw.line(built, fill=(255, 54, 69, alpha), width=8, joint="curve")


def draw_vessel_scene(base: Image.Image, t: float):
    draw = ImageDraw.Draw(base, "RGBA")
    p = seg(t, 0.0, 6.2)
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 2.1)

    # Curved tunnel bands convey depth without graphic anatomy.
    for i in range(15):
        z = ((i / 15.0 + p * 0.34) % 1.0)
        radius = int(90 + z * 920)
        center_x = W / 2 + math.sin(z * 7 + t * 0.8) * 130 * (1 - z)
        center_y = H / 2 + math.cos(z * 5 - t * 0.45) * 70 * (1 - z)
        width = max(3, int(14 * z))
        c = (150 + int(70 * pulse), 8, 25, int(40 + 125 * z))
        draw.ellipse((center_x - radius * 1.45, center_y - radius, center_x + radius * 1.45, center_y + radius), outline=c, width=width)

    # Blood cells stream toward camera along a deterministic flow.
    rnd = random.Random(481516)
    for i in range(68):
        seed = rnd.random()
        z = (seed + p * (0.7 + (i % 5) * 0.035)) % 1.0
        theta = rnd.uniform(0, math.tau) + t * (0.18 + (i % 3) * 0.05)
        spread_x = (70 + z * 730) * math.cos(theta)
        spread_y = (35 + z * 390) * math.sin(theta)
        cx = W / 2 + spread_x + math.sin(t + i) * 18
        cy = H / 2 + spread_y
        rx = 8 + z * 55
        ry = 4 + z * 24
        color = (210 + int(35 * z), 12 + int(20 * z), 32, int(80 + 175 * z))
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=color, outline=(255, 76, 76, int(90 + 120 * z)), width=max(1, int(3 * z)))
        draw.ellipse((cx - rx * .45, cy - ry * .4, cx + rx * .45, cy + ry * .4), fill=(100, 0, 16, int(45 + 100 * z)))

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse((-180, -300, W + 180, H + 300), fill=220)
    vignette = vignette.filter(ImageFilter.GaussianBlur(160))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    base.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), black, vignette))


def draw_network_scene(base: Image.Image, t: float):
    draw = ImageDraw.Draw(base, "RGBA")
    p = smooth(seg(t, 5.0, 10.2))
    fade = smooth(seg(t, 5.0, 6.0)) * (1 - smooth(seg(t, 9.5, 10.2)))
    if fade <= 0:
        return
    nodes = [
        (960, 540), (690, 380), (1220, 370), (570, 650), (1350, 650),
        (380, 450), (1540, 430), (330, 790), (1590, 790), (960, 820),
    ]
    edges = [(0,1),(0,2),(0,3),(0,4),(1,5),(2,6),(3,7),(4,8),(3,9),(4,9)]
    for idx, (a, b) in enumerate(edges):
        edge_p = clamp(p * 1.55 - idx * 0.065)
        ax, ay = nodes[a]; bx, by = nodes[b]
        qx, qy = ax + (bx-ax)*edge_p, ay + (by-ay)*edge_p
        draw.line((ax, ay, qx, qy), fill=(215, 23, 48, int(200*fade)), width=9)
        draw.line((ax, ay, qx, qy), fill=(255, 108, 110, int(80*fade)), width=3)
    for idx, (x, y) in enumerate(nodes):
        npg = clamp(p * 1.6 - idx * .055)
        if npg > 0:
            r = 10 + 20 * smooth(npg)
            glow_circle(base, (x,y), r*1.5, BRIGHT_RED, int(100*fade), 22)
            draw.ellipse((x-r,y-r,x+r,y+r), fill=(243,37,56,int(235*fade)), outline=(255,190,178,int(220*fade)), width=3)
    draw_heartbeat(draw, 540, clamp(seg(t, 5.3, 7.2)), int(220*fade))


def droplet_points(cx: float, cy: float, s: float):
    return [
        (cx, cy - 1.25*s), (cx - .22*s, cy - .83*s), (cx - .62*s, cy - .28*s),
        (cx - .72*s, cy + .20*s), (cx - .54*s, cy + .66*s), (cx, cy + .94*s),
        (cx + .54*s, cy + .66*s), (cx + .72*s, cy + .20*s), (cx + .62*s, cy - .28*s),
        (cx + .22*s, cy - .83*s),
    ]


def draw_connection_scene(base: Image.Image, t: float):
    p = smooth(seg(t, 8.3, 12.0))
    fade = smooth(seg(t, 8.3, 9.0)) * (1 - smooth(seg(t, 11.5, 12.15)))
    if fade <= 0:
        return
    draw = ImageDraw.Draw(base, "RGBA")
    cy = 565
    icons = [(390, "DONOR"), (960, "BLOOD BANK"), (1530, "RECIPIENT")]
    for i in range(2):
        a = icons[i][0]; b = icons[i+1][0]
        lp = clamp(p * 1.5 - i * .18)
        draw.line((a+95,cy,b-95,cy), fill=(225,181,80,int(70*fade)), width=4)
        ex = a + 95 + (b-a-190)*lp
        glow_circle(base, (ex,cy), 10, GOLD, int(200*fade), 20)
        draw.ellipse((ex-7,cy-7,ex+7,cy+7), fill=(*GOLD,int(255*fade)))
    for idx,(x,label) in enumerate(icons):
        ip = clamp(p * 1.8 - idx*.14)
        if ip <= 0: continue
        r = 82 * ease_out(ip)
        glow_circle(base, (x,cy), r, CRIMSON if idx != 1 else GOLD, int(85*fade), 35)
        ring_color = GOLD if idx == 1 else BRIGHT_RED
        draw.ellipse((x-r,cy-r,x+r,cy+r), fill=(8,19,43,int(235*fade)), outline=(*ring_color,int(245*fade)), width=5)
        if idx == 1:
            pts = droplet_points(x,cy,36)
            draw.polygon(pts, fill=(226,25,48,int(245*fade)))
            draw.rectangle((x-8,cy-14,x+8,cy+14), fill=(255,255,255,int(250*fade)))
            draw.rectangle((x-14,cy-8,x+14,cy+8), fill=(255,255,255,int(250*fade)))
        else:
            draw.ellipse((x-22,cy-38,x+22,cy+6), outline=(255,255,255,int(240*fade)), width=5)
            draw.arc((x-40,cy-8,x+40,cy+55), 190, 350, fill=(255,255,255,int(240*fade)), width=5)
        centered(draw,(x,cy+132),label,F_LABEL,(245,247,252,int(245*fade)),spacing=2)
    centered(draw,(W/2,215),"ONE PULSE.  ONE PURPOSE.",F_SUBTITLE,(245,248,255,int(245*fade)),spacing=5)


def prepare_logo() -> Image.Image:
    logo = Image.open(LOGO_PATH).convert("RGBA")
    # Remove nearly-white pixels so the mark can float over the dark reveal.
    arr = np.array(logo)
    rgb = arr[:,:,:3]
    alpha = np.where(np.min(rgb, axis=2) > 246, 0, arr[:,:,3])
    arr[:,:,3] = alpha.astype(np.uint8)
    return Image.fromarray(arr).crop(Image.fromarray(alpha).getbbox()).resize((650,650),Image.Resampling.LANCZOS)


LOGO = prepare_logo()


def draw_logo_final(base: Image.Image, t: float):
    intro = smooth(seg(t, 11.25, 12.65))
    final = smooth(seg(t, 12.25, 13.15))
    exit_p = smooth(seg(t, 15.55, 16.0))
    if intro <= 0:
        return

    # The expanding halo becomes the clean, white application transition.
    halo_r = 95 + 1250 * smooth(seg(t, 11.35, 13.15))
    glow_circle(base, (W/2, 470), halo_r, WHITE, int(245*intro), 65)
    draw = ImageDraw.Draw(base,"RGBA")
    draw.ellipse((W/2-halo_r,H/2-halo_r,W/2+halo_r,H/2+halo_r),fill=(247,249,253,int(250*intro)))

    scale = 0.72 + 0.28 * ease_out(intro) + 0.14*exit_p
    logo = LOGO.resize((int(650*scale),int(650*scale)),Image.Resampling.LANCZOS)
    logo_alpha = int(255*(1-exit_p*.65))
    if logo_alpha < 255:
        logo.putalpha(ImageEnhance.Brightness(logo.getchannel("A")).enhance(logo_alpha/255))
    base.alpha_composite(logo,(int(W/2-logo.width/2),int(455-logo.height/2)))

    if final > 0:
        a = int(255*final*(1-exit_p))
        centered(draw,(W/2,845),"BLOODLINK",F_TITLE,(7,27,62,a),spacing=10)
        centered(draw,(W/2,948),"OFFICIALLY INAUGURATED",F_SUBTITLE,(190,20,43,a),spacing=4)
        centered(draw,(W/2,1020),"NSS  •  DONATE BLOOD. SAVE LIVES.",F_SMALL,(38,56,84,a),spacing=2)

    if exit_p > 0:
        draw.rectangle((0,0,W,H),fill=(255,255,255,int(255*exit_p)))


def frame_at(t: float) -> Image.Image:
    # Multi-stop navy/crimson cinematic background.
    y = np.linspace(0,1,H,dtype=np.float32)[:,None,None]
    x = np.linspace(0,1,W,dtype=np.float32)[None,:,None]
    top = np.array(NAVY,dtype=np.float32)[None,None,:]
    bottom = np.array((28,0,14),dtype=np.float32)[None,None,:]
    rgb = top*(1-y)+bottom*y
    rgb = np.broadcast_to(rgb,(H,W,3)).copy()
    radial = np.exp(-(((x-.5)/.55)**2 + ((y-.5)/.62)**2)*3.8)
    rgb += radial*np.array([52,2,8],dtype=np.float32)
    rgb = np.clip(rgb,0,255).astype(np.uint8)
    img = Image.fromarray(rgb,"RGB").convert("RGBA")

    # Opening electrical pulse.
    if t < 2.2:
        d = ImageDraw.Draw(img,"RGBA")
        p = smooth(seg(t,.1,1.45))
        flash = (1-smooth(seg(t,0.0,.55)))*120
        glow_circle(img,(W/2,H/2),60+420*p,BRIGHT_RED,int(150*(1-p)),70)
        draw_heartbeat(d,H//2,p,int(255*(1-smooth(seg(t,1.5,2.2)))))
        d.rectangle((0,0,W,H),fill=(255,255,255,int(flash)))

    vessel_opacity = 1-smooth(seg(t,5.6,6.7))
    if vessel_opacity > 0:
        vessel = Image.new("RGBA",(W,H),(0,0,0,0))
        draw_vessel_scene(vessel,t)
        vessel.putalpha(ImageEnhance.Brightness(vessel.getchannel("A")).enhance(vessel_opacity))
        img.alpha_composite(vessel)

    draw_network_scene(img,t)
    draw_connection_scene(img,t)
    draw_logo_final(img,t)

    # Subtle film grain, deterministic per frame.
    rng = np.random.default_rng(int(t*FPS)+2026)
    noise = rng.normal(0,2.0,(H,W,1)).astype(np.int16)
    arr = np.array(img.convert("RGB"),dtype=np.int16)
    arr = np.clip(arr+noise,0,255).astype(np.uint8)
    return Image.fromarray(arr,"RGB")


def make_audio(path: Path):
    rate = 48_000
    n = int(DURATION*rate)
    tt = np.arange(n,dtype=np.float64)/rate
    audio = np.zeros(n,dtype=np.float64)

    # Low cinematic foundation and a slowly opening harmonic bed.
    rise = np.clip(tt/13.0,0,1)
    audio += .07*np.sin(2*np.pi*(42+10*rise)*tt)*(0.35+0.65*rise)
    audio += .035*np.sin(2*np.pi*84*tt)*(0.25+0.75*rise)
    audio += .022*np.sin(2*np.pi*168*tt)*np.clip((tt-5)/7,0,1)

    def thump(at: float, amp: float=0.7):
        nonlocal audio
        dt = tt-at
        mask = (dt>=0)&(dt<.48)
        env = np.exp(-dt[mask]*11)
        audio[mask] += amp*env*np.sin(2*np.pi*(58-18*dt[mask])*dt[mask])

    for beat in [0.32,0.74,1.72,2.14,3.12,3.54,4.52,4.94,6.05,6.47,7.58,8.0,9.1,9.52,10.62,11.04]:
        thump(beat,0.46 if beat>2 else 0.72)

    # Rising shimmer into the logo reveal.
    for freq,phase in [(220,0),(330,.4),(440,.8),(660,1.3)]:
        mask=(tt>=10.6)&(tt<15.6)
        env=np.sin(np.pi*(tt[mask]-10.6)/5.0)**1.5
        audio[mask]+=.035*env*np.sin(2*np.pi*freq*tt[mask]+phase)
    # Final clean impact.
    dt=tt-12.45; mask=(dt>=0)&(dt<2.5)
    audio[mask]+=.16*np.exp(-dt[mask]*1.5)*np.sin(2*np.pi*110*dt[mask])
    fade=np.ones(n); fade[int(15.3*rate):]=np.linspace(1,0,n-int(15.3*rate))
    audio*=fade
    audio=np.tanh(audio*1.35)
    pcm=(np.clip(audio,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate); wf.writeframes(pcm.tobytes())


def ffmpeg_path() -> str:
    configured = os.environ.get("BLOODLINK_FFMPEG")
    if configured and Path(configured).exists():
        return configured
    found = shutil.which("ffmpeg")
    if found:
        return found
    package_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    candidates = list(package_root.glob("Gyan.FFmpeg_*/ffmpeg-*/bin/ffmpeg.exe"))
    if not candidates:
        raise RuntimeError("FFmpeg was not found after installation")
    return str(candidates[-1])


def render():
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    audio_path=OUT_DIR/"bloodlink_inauguration_score.wav"
    video_path=OUT_DIR/"BloodLink_NSS_Inauguration_4K.mp4"
    preview_path=OUT_DIR/"BloodLink_NSS_Inauguration_preview.jpg"
    make_audio(audio_path)
    frame_at(13.8).save(preview_path,quality=94)

    cmd=[
        ffmpeg_path(),"-y","-hide_banner","-loglevel","warning",
        "-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","-",
        "-i",str(audio_path),
        "-vf","scale=3840:2160:flags=lanczos,format=yuv420p",
        "-c:v","libx264","-preset","medium","-crf","16","-profile:v","high","-level","5.1",
        "-c:a","aac","-b:a","256k","-ar","48000","-movflags","+faststart","-shortest",str(video_path)
    ]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for i in range(FRAMES):
            proc.stdin.write(frame_at(i/FPS).tobytes())
            if i % 30 == 0:
                print(f"Rendered {i//30:02d}/{DURATION}s",flush=True)
    finally:
        proc.stdin.close()
    code=proc.wait()
    if code:
        raise SystemExit(code)
    print(video_path)


if __name__ == "__main__":
    render()
