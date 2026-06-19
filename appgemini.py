# =====================================================================
# 📌 AETHER FILMWORKS AI // STUDIO V52 (SINGLE FILE MASTER CODE)
# =====================================================================

import streamlit as st
import os
import asyncio
import time
import json
import base64
import random
import shutil
import textwrap
import urllib.parse
import urllib.request
import concurrent.futures
import re
import wave
import requests
import subprocess
import ffmpeg
import imageio_ffmpeg
import yt_dlp
import edge_tts
from google import genai
from groq import Groq
import openai

# 👇 FIX: Prioritize system FFmpeg
if shutil.which("ffmpeg"):
    FFMPEG_BINARY = "ffmpeg"
else:
    FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

# 👇 FIX: Download Default Font
local_font_path = "Padauk.ttf"
if not os.path.exists(local_font_path):
    try:
        urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/padauk/Padauk-Regular.ttf", local_font_path)
    except Exception:
        pass

# 👇 FIX: Dynamic Font Scanner
def get_available_fonts():
    font_list = ["Padauk.ttf"]
    if os.path.exists("font"):
        for f in os.listdir("font"):
            if f.endswith(".ttf") or f.endswith(".otf"):
                font_list.append(os.path.join("font", f))
    return list(set(font_list))

available_fonts = get_available_fonts()

# --- Key Save Files ---
API_KEY_FILE = "saved_api_key.txt"
ELEVEN_KEY_FILE = "saved_eleven_key.txt"
GROQ_KEY_FILE = "saved_groq_key.txt"
OPENAI_KEY_FILE = "saved_openai_key.txt"
ELEVEN_VOICE_ID_FILE = "saved_eleven_voice_id.txt"

def load_key(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_key(file_path, key):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(key)

def get_download_link(file_path, file_name, link_text):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" style="display:block; text-align:center; margin-top:10px; padding:12px 20px; background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color:white; text-decoration:none; border-radius:8px; font-weight:bold;">📥 {link_text}</a>'

# =====================================================================
# 📌 TIKTOK HOOK SYSTEM
# =====================================================================

TIKTOK_HOOK_TEMPLATES = {
    "👻 Horror / Creepypasta": [
        "ဒီတစ်ခါတော့ သေလုမတတ်ပဲ...",
        "ဒီနေရာကို ဘယ်တော့မှ မသွားပါနဲ့...",
        "ည ၃ နာရီမှာ ဒီလိုလုပ်ရင်...",
        "ဒီဇာတ်လမ်းက တကယ့်ဖြစ်ရပ်မှန်ပါ...",
        "ဒါကိုကြားရင် မင်းကြက်သီးထမယ်..."
    ],
    "🚀 Motivation / Mindset": [
        "ဒီတစ်ချက်က မင်းဘဝကိုပြောင်းလဲစေမယ်...",
        "အောင်မြင်တဲ့သူတိုင်း ဒါကိုလုပ်တယ်...",
        "မနက်ဖြန်ကစပြီး ဒါကိုလုပ်ကြည့်...",
        "ဒီအချက်ကိုသိရင် မင်းဘယ်တော့မှ...",
        "သူဌေးတွေရဲ့ လျှို့ဝှက်ချက်..."
    ],
    "🧠 Dark Psychology": [
        "လူတွေက မင်းကို ဒီလိုထိန်းချုပ်နေတယ်...",
        "ဒီစိတ်ပညာလှည့်ကွက်က အံ့ဩစရာပဲ...",
        "မင်းမသိလိုက်ဘဲ ဒါကိုလုပ်မိနေတယ်...",
        "ဒီအချက်က မင်းရဲ့စိတ်ကို ပြောင်းလဲစေမယ်..."
    ],
    "💡 Fun Facts / Trivia": [
        "ဒီအချက်ကို လူ ၉၉% မသိကြဘူး...",
        "ဒါကိုသိရင် မင်းအံ့ဩသွားမယ်...",
        "တစ်ကမ္ဘာလုံး ဒါကိုမှားသိနေကြတယ်...",
        "ဒီအကြောင်းကို ကျောင်းမှာ သင်မှာမဟုတ်ဘူး..."
    ],
    "📜 Ancient History / Myths": [
        "နှစ်ထောင်ချီတဲ့ ဒီလျှို့ဝှက်ချက်က...",
        "ရှေးခေတ်လူတွေ ဒါကိုဘယ်လိုလုပ်ခဲ့သလဲ...",
        "ဒီဒဏ္ဍာရီရဲ့နောက်ကွယ်က အမှန်တရား...",
        "သမိုင်းစာအုပ်တွေမှာ ဒါကိုရေးမထားဘူး..."
    ]
}

def get_random_hook(niche):
    templates = TIKTOK_HOOK_TEMPLATES.get(niche, TIKTOK_HOOK_TEMPLATES["💡 Fun Facts / Trivia"])
    return random.choice(templates)

def add_tiktok_hook_overlay(video_input, output_path, hook_text, niche="💡 Fun Facts / Trivia", duration=3.5):
    try:
        v_w, v_h = 720, 1280
        video = ffmpeg.input(video_input).video
        audio = ffmpeg.input(video_input).audio
        hook_styles = {
            "👻 Horror / Creepypasta": {"text_color": "red", "bg_color": "black@0.8", "font_size": 55},
            "🚀 Motivation / Mindset": {"text_color": "gold", "bg_color": "black@0.6", "font_size": 50},
            "💡 Fun Facts / Trivia": {"text_color": "cyan", "bg_color": "black@0.7", "font_size": 45},
            "🧠 Dark Psychology": {"text_color": "white", "bg_color": "black@0.9", "font_size": 50},
            "📜 Ancient History / Myths": {"text_color": "gold", "bg_color": "black@0.7", "font_size": 48}
        }
        style = hook_styles.get(niche, hook_styles["💡 Fun Facts / Trivia"])
        wrapped_hook = textwrap.wrap(hook_text, width=20)
        if not wrapped_hook:
            wrapped_hook = [hook_text]
        max_len = max(len(line) for line in wrapped_hook)
        centered_hook = "\n".join(line.center(max_len, " ") for line in wrapped_hook)
        with open("hook_text.txt", "w", encoding="utf-8") as f:
            f.write(centered_hook)
        video = ffmpeg.filter(video, 'drawbox', x=0, y='h*0.3', w='iw', h='h*0.4', color=style["bg_color"], thickness='fill', enable=f'between(t,0,{duration})')
        video = ffmpeg.filter(video, 'drawtext', textfile='hook_text.txt', fontfile='Padauk.ttf', fontsize=style["font_size"], fontcolor=style["text_color"], bordercolor='black', borderw=3, x='(w-text_w)/2', y='(h-text_h)/2', line_spacing=15, text_align='C', enable=f'between(t,0,{duration})')
        if niche == "👻 Horror / Creepypasta":
            video = ffmpeg.filter(video, 'drawbox', x=0, y='h*0.28', w='iw', h='4', color='red@0.9', thickness='fill', enable=f'between(t,0,{duration})')
            video = ffmpeg.filter(video, 'drawbox', x=0, y='h*0.72', w='iw', h='4', color='red@0.9', thickness='fill', enable=f'between(t,0,{duration})')
        out = ffmpeg.output(video, audio, output_path, vcodec='libx264', pix_fmt='yuv420p', acodec='aac', audio_bitrate='128k', preset='superfast')
        out.overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return output_path
    except Exception:
        return video_input

def add_tiktok_loop_point(video_input, output_path):
    try:
        dur = get_file_duration(video_input)
        video = ffmpeg.input(video_input).video
        audio = ffmpeg.input(video_input).audio
        video = ffmpeg.filter(video, 'drawtext', text='👆 ပြန်ကြည့်ပါ', fontsize=35, fontcolor='white', bordercolor='black', borderw=2, x='(w-text_w)/2', y='(h-text_h)/2', enable=f'between(t,{dur-2},{dur})')
        out = ffmpeg.output(video, audio, output_path, vcodec='libx264', pix_fmt='yuv420p', acodec='aac', audio_bitrate='128k', preset='superfast')
        out.overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return output_path
    except Exception:
        return video_input

# =====================================================================
# 📌 PROFESSIONAL THUMBNAIL SYSTEM
# =====================================================================

THUMBNAIL_STYLES = {
    "🔥 Viral TikTok Style": {"text_position": "center", "font_size_range": (50, 90), "bg_overlay": "gradient_bottom", "text_effect": "stroke_bold", "color_scheme": "yellow_red", "description": "TikTok အတွက် အကောင်းဆုံး"},
    "🎬 Cinematic Movie Poster": {"text_position": "bottom_third", "font_size_range": (40, 70), "bg_overlay": "vignette_dark", "text_effect": "shadow_soft", "color_scheme": "white_gold", "description": "ရုပ်ရှင်ပိုစတာလို"},
    "👻 Horror / Mystery": {"text_position": "center", "font_size_range": (55, 85), "bg_overlay": "dark_gradient", "text_effect": "shadow_horror", "color_scheme": "red_black", "description": "သည်းထိတ်ရင်ဖိုအတွက်"},
    "💎 Premium / Luxury": {"text_position": "bottom_third", "font_size_range": (40, 65), "bg_overlay": "golden_frame", "text_effect": "golden_text", "color_scheme": "gold_cream", "description": "Premium Content"},
    "⚡ Clean / Minimal": {"text_position": "center", "font_size_range": (45, 80), "bg_overlay": "subtle_overlay", "text_effect": "clean_white", "color_scheme": "white_soft", "description": "ရိုးရှင်းသန့်ရှင်း"}
}

NICHE_THUMBNAIL_MAP = {
    "👻 Horror / Creepypasta": "👻 Horror / Mystery",
    "💔 Reddit Relationship Drama": "🔥 Viral TikTok Style",
    "🧠 Dark Psychology": "👻 Horror / Mystery",
    "💡 Fun Facts / Trivia": "🔥 Viral TikTok Style",
    "🚀 Motivation / Mindset": "💎 Premium / Luxury",
    "📜 Ancient History / Myths": "🎬 Cinematic Movie Poster"
}

def get_thumbnail_style_for_niche(niche):
    return NICHE_THUMBNAIL_MAP.get(niche, "🔥 Viral TikTok Style")

def calculate_optimal_font_size(text, min_size, max_size):
    text_length = len(text)
    if text_length < 20:
        return max_size
    elif text_length < 40:
        return int(max_size * 0.85)
    elif text_length < 60:
        return int(max_size * 0.7)
    elif text_length < 80:
        return int(max_size * 0.55)
    else:
        return max(min_size, int(max_size * 0.45))

def wrap_text_for_thumbnail(text, max_width=25):
    text = re.sub(r'\[.*?\]', '', text)
    lines = textwrap.wrap(text, width=max_width, break_long_words=False)
    if not lines:
        lines = [text[:max_width]]
    max_len = max(len(line) for line in lines)
    centered_lines = [line.center(max_len, " ") for line in lines]
    return "\n".join(centered_lines)

def generate_professional_thumbnail(video_input, output_path, title_text, timestamp, style="🔥 Viral TikTok Style", font_path="Padauk.ttf"):
    try:
        style_config = THUMBNAIL_STYLES.get(style, THUMBNAIL_STYLES["🔥 Viral TikTok Style"])
        video = ffmpeg.input(video_input, ss=timestamp)
        if style_config["bg_overlay"] == "gradient_bottom":
            video = ffmpeg.filter(video, 'drawbox', x=0, y='ih/2', w='iw', h='ih/2', color='black@0.0:black@0.7', thickness='fill')
        elif style_config["bg_overlay"] == "vignette_dark":
            video = ffmpeg.filter(video, 'vignette', PI=0.5)
        elif style_config["bg_overlay"] == "dark_gradient":
            video = ffmpeg.filter(video, 'drawbox', x=0, y=0, w='iw', h='ih', color='black@0.4', thickness='fill')
        elif style_config["bg_overlay"] == "subtle_overlay":
            video = ffmpeg.filter(video, 'drawbox', x=0, y=0, w='iw', h='ih', color='black@0.2', thickness='fill')
        font_size = calculate_optimal_font_size(title_text, style_config["font_size_range"][0], style_config["font_size_range"][1])
        if style_config["text_position"] == "center":
            y_position = "(h-text_h)/2"
        elif style_config["text_position"] == "bottom_third":
            y_position = "h*0.65"
        elif style_config["text_position"] == "top_third":
            y_position = "h*0.15"
        else:
            y_position = "(h-text_h)/2"
        color_schemes = {
            "yellow_red": {"text": "yellow", "shadow": "red", "box": "red@0.8"},
            "white_gold": {"text": "white", "shadow": "gold", "box": "black@0.6"},
            "red_black": {"text": "red", "shadow": "black", "box": "black@0.8"},
            "gold_cream": {"text": "gold", "shadow": "brown", "box": "black@0.5"},
            "white_soft": {"text": "white", "shadow": "gray", "box": "black@0.4"}
        }
        colors = color_schemes.get(style_config["color_scheme"], color_schemes["yellow_red"])
        if style_config["text_effect"] == "stroke_bold":
            border_width = 4
        elif style_config["text_effect"] == "shadow_soft":
            border_width = 2
        elif style_config["text_effect"] == "shadow_horror":
            border_width = 5
        elif style_config["text_effect"] == "golden_text":
            border_width = 2
        else:
            border_width = 3
        wrapped_text = wrap_text_for_thumbnail(title_text)
        with open("thumb_pro_text.txt", "w", encoding="utf-8") as f:
            f.write(wrapped_text)
        video = ffmpeg.filter(video, 'drawtext', textfile='thumb_pro_text.txt', fontfile=font_path.replace('\\', '/'), fontcolor=colors["text"], fontsize=font_size, bordercolor=colors["shadow"], borderw=border_width, box=1, boxcolor=colors["box"], boxborderw=15, x='(w-text_w)/2', y=y_position, line_spacing=15, text_align='C')
        ffmpeg.output(video, output_path, vframes=1, qscale=2).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return True, output_path
    except Exception:
        return False, ""

# =====================================================================
# 📌 NICHE-BASED VOICE FX AUTO-MATCH SYSTEM
# =====================================================================

NICHE_VOICE_FX_MAP = {
    "👻 Horror / Creepypasta": {"primary": ["👻 Deep & Chilling (Horror)", "👹 Demon / Monster", "🤫 ASMR / Whisper", "⛰️ Deep Cave Echo"], "description": "ကြောက်စရာ၊ သည်းထိတ်ရင်ဖိုဇာတ်လမ်းများအတွက်"},
    "💔 Reddit Relationship Drama": {"primary": ["🎙️ Epic Trailer Voice", "🏛️ Cinematic Reverb", "📞 Old Telephone"], "description": "Relationship ဇာတ်လမ်းများအတွက်"},
    "🧠 Dark Psychology": {"primary": ["🤫 ASMR / Whisper", "👻 Deep & Chilling (Horror)", "🌊 Underwater / Muffled"], "description": "စိတ်ပညာ၊ လျှို့ဝှက်ဆန်းကြယ်"},
    "💡 Fun Facts / Trivia": {"primary": ["🔥 Deep & Energetic (Motivation)", "📻 Walkie-Talkie", "🎙️ Epic Trailer Voice"], "description": "ပျော်စရာ၊ စိတ်ဝင်စားစရာ"},
    "🚀 Motivation / Mindset": {"primary": ["🔥 Deep & Energetic (Motivation)", "🎙️ Epic Trailer Voice", "🏛️ Cinematic Reverb"], "description": "စိတ်ဓာတ်တက်ကြွစေသော"},
    "📜 Ancient History / Myths": {"primary": ["🏛️ Cinematic Reverb", "⛰️ Deep Cave Echo", "👻 Deep & Chilling (Horror)"], "description": "သမိုင်း၊ ဒဏ္ဍာရီ"}
}

DUBBING_VOICE_FX_MAP = {
    "Normal (ပုံမှန်)": {"primary": ["🎙️ Epic Trailer Voice", "🏛️ Cinematic Reverb"]},
    "Slang (Gen-Z)": {"primary": ["🔥 Deep & Energetic (Motivation)", "📻 Walkie-Talkie"]},
    "Comedy (ဟာသ)": {"primary": ["🤖 Robot / Cyborg", "📞 Old Telephone"]},
    "Suspense (သည်းထိတ်)": {"primary": ["👻 Deep & Chilling (Horror)", "🤫 ASMR / Whisper", "⛰️ Deep Cave Echo"]}
}

def get_recommended_fx_for_niche(niche, mode="faceless"):
    fx_map = DUBBING_VOICE_FX_MAP if mode == "dubbing" else NICHE_VOICE_FX_MAP
    if niche in fx_map:
        recommended = fx_map[niche]["primary"]
        return ["None (မူရင်းအသံ)"] + recommended + ["👹 Demon / Monster", "🌊 Underwater / Muffled"]
    return ["None (မူရင်းအသံ)", "🎙️ Epic Trailer Voice", "👻 Deep & Chilling (Horror)", "🤫 ASMR / Whisper"]

def get_fx_description(niche, fx_name, mode="faceless"):
    fx_descriptions = {
        "None (မူရင်းအသံ)": "မူရင်းအတိုင်း ဘာ Effect မှမထည့်ဘဲ ထားမည်",
        "👻 Deep & Chilling (Horror)": "ကြောက်စရာ ဇာတ်ဝင်ခန်းများအတွက် အကောင်းဆုံး",
        "👹 Demon / Monster": "မကောင်းဆိုးဝါး၊ ဘီလူးသရဲ အသံများအတွက်",
        "🤫 ASMR / Whisper": "တိုးညှင်းစွာ ပြောသလို ခံစားရမည်။ လျှို့ဝှက်ဆန်းကြယ်",
        "⛰️ Deep Cave Echo": "ဂူထဲမှာ ပြောနေသလို ပဲ့တင်သံထပ်မည်",
        "🎙️ Epic Trailer Voice": "ရုပ်ရှင်နမူနာ Trailer လို ဟိန်းဟိန်းကြီး",
        "🏛️ Cinematic Reverb": "ရုပ်ရှင်ဇာတ်ဝင်ခန်း အသံကဲ့သို့ ခံစားရမည်",
        "🔥 Deep & Energetic (Motivation)": "စိတ်ဓာတ်တက်ကြွစေသော အားပေးအသံ",
        "📻 Walkie-Talkie": "Walkie-Talkie မှ ပြောနေသလို ခံစားရမည်",
        "📞 Old Telephone": "ဖုန်းဟောင်းမှ ပြောနေသလို ခံစားရမည်",
        "🤖 Robot / Cyborg": "စက်ရုပ်အသံကဲ့သို့ ပြောင်းလဲမည်",
        "🌊 Underwater / Muffled": "ရေအောက်မှ ပြောနေသလို မှုန်ဝါးသောအသံ"
    }
    return fx_descriptions.get(fx_name, "")

# =====================================================================
# 📌 SYNC PREVIEW SYSTEM
# =====================================================================

def generate_sync_preview_html(parsed_timestamps, audio_duration):
    if not parsed_timestamps:
        return "<p style='color:#94a3b8;'>No subtitle data</p>"
    total_seconds = audio_duration
    if total_seconds <= 0:
        total_seconds = 60
    bar_width = 600
    scale = bar_width / total_seconds
    html = f"""
    <style>
    .sync-preview {{ background: #0d111c; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin: 10px 0; font-family: 'Inter', sans-serif; overflow-x: auto; }}
    .sync-timeline {{ position: relative; height: 40px; background: #1a2235; border-radius: 4px; margin: 5px 0; width: {bar_width}px; }}
    .sync-sub-block {{ position: absolute; height: 35px; background: rgba(56, 189, 248, 0.3); border: 1px solid #38bdf8; border-radius: 3px; top: 2px; font-size: 10px; color: #e2e8f0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding: 2px 4px; cursor: pointer; }}
    .sync-sub-block:hover {{ background: rgba(56, 189, 248, 0.6); z-index: 10; }}
    .sync-sub-block.early {{ background: rgba(239, 68, 68, 0.3); border-color: #ef4444; }}
    .sync-sub-block.late {{ background: rgba(234, 179, 8, 0.3); border-color: #eab308; }}
    .sync-sub-block.good {{ background: rgba(34, 197, 94, 0.3); border-color: #22c55e; }}
    .sync-legend {{ display: flex; gap: 15px; margin: 10px 0; font-size: 12px; color: #94a3b8; }}
    .sync-time-marker {{ position: absolute; bottom: -18px; font-size: 10px; color: #64748b; transform: translateX(-50%); }}
    </style>
    <div class="sync-preview">
    <h4 style="color:#38bdf8;">📊 Subtitle Timeline (Audio: {total_seconds:.1f}s)</h4>
    <div class="sync-legend"><span>🟢 Good (1.5-4s)</span><span>🔴 Too Short</span><span>🟡 Too Long</span></div>
    <div class="sync-timeline">"""
    for i, (start, end, text) in enumerate(parsed_timestamps):
        left = start * scale
        width = max((end - start) * scale, 4)
        duration = end - start
        css_class = "early" if duration < 1.0 else ("late" if duration > 5.0 else "good")
        display_text = text[:20] + "..." if len(text) > 20 else text
        html += f'<div class="sync-sub-block {css_class}" style="left:{left:.0f}px; width:{width:.0f}px;" title="#{i+1}: {start:.1f}s-{end:.1f}s\n{text}">#{i+1}</div>'
    for t in range(0, int(total_seconds) + 1, max(1, int(total_seconds / 10))):
        html += f'<div class="sync-time-marker" style="left:{t*scale:.0f}px;">{t}s</div>'
    html += '</div></div>'
    return html

def analyze_sync_quality(parsed_timestamps, audio_duration):
    if not parsed_timestamps:
        return {"score": 0, "issues": ["No data"], "recommendation": "Generate first"}
    issues = []
    short_count = 0
    long_count = 0
    gap_count = 0
    overlap_count = 0
    prev_end = 0
    for start, end, text in parsed_timestamps:
        duration = end - start
        if duration < 1.0:
            short_count += 1
        if duration > 5.0:
            long_count += 1
        gap = start - prev_end
        if gap > 2.0:
            gap_count += 1
        if gap < -0.5:
            overlap_count += 1
        prev_end = end
    if short_count > 0:
        issues.append(f"{short_count} too short (<1s)")
    if long_count > 0:
        issues.append(f"{long_count} too long (>5s)")
    if gap_count > 0:
        issues.append(f"{gap_count} gaps")
    if overlap_count > 0:
        issues.append(f"{overlap_count} overlaps")
    score = 100 - (short_count * 10) - (long_count * 5) - (gap_count * 15) - (overlap_count * 20)
    score = max(0, min(100, score))
    if score >= 80:
        recommendation = "✅ Good! Render now."
    elif score >= 50:
        recommendation = "⚠️ Adjust offset."
    else:
        recommendation = "❌ Check audio/script."
    return {"score": score, "issues": issues, "recommendation": recommendation}

# =====================================================================
# 📌 SYNC ENGINE
# =====================================================================

def fmt_timestamp_sync(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def strip_audio_tags(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\{.*?\}', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def sync_by_character_mapping(clean_script, audio_duration, words_per_chunk=8, min_chunk_duration=1.2, offset=0.0):
    clean_script = strip_audio_tags(clean_script)
    if not clean_script.strip():
        return "", []
    raw_chunks = re.split(r'([။!?\n]+)', clean_script)
    segments = []
    for i in range(0, len(raw_chunks) - 1, 2):
        segment = raw_chunks[i].strip()
        if i + 1 < len(raw_chunks):
            segment += raw_chunks[i + 1]
        if segment.strip():
            segments.append(segment.strip())
    if len(raw_chunks) % 2 != 0 and raw_chunks[-1].strip():
        segments.append(raw_chunks[-1].strip())
    if not segments:
        return "", []
    total_chars = sum(len(seg) for seg in segments)
    if total_chars == 0:
        return "", []
    effective_duration = max(audio_duration - 0.3, audio_duration)
    time_per_char = effective_duration / total_chars
    srt_entries = []
    chunk_index = 1
    char_position = 0.0
    for segment in segments:
        words = segment.split()
        if not words:
            continue
        for i in range(0, len(words), words_per_chunk):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = ' '.join(chunk_words)
            chunk_chars = len(chunk_text)
            start_time = char_position * time_per_char + offset
            chunk_duration = max(chunk_chars * time_per_char, min_chunk_duration)
            end_time = min(start_time + chunk_duration, audio_duration)
            if end_time <= start_time:
                end_time = start_time + min_chunk_duration
            start_time = max(0, start_time)
            srt_entries.append({'index': chunk_index, 'start': start_time, 'end': end_time, 'text': chunk_text})
            chunk_index += 1
            char_position += chunk_chars
    srt_text = ""
    for entry in srt_entries:
        srt_text += f"{entry['index']}\n{fmt_timestamp_sync(entry['start'])} --> {fmt_timestamp_sync(entry['end'])}\n{entry['text']}\n\n"
    parsed = [(e['start'], e['end'], e['text']) for e in srt_entries]
    return srt_text, parsed

def smart_sync_pipeline(clean_script, audio_path, whisper_data=None, audio_duration=None, sync_offset=0.0, short_punchy=False):
    if audio_duration is None:
        audio_duration = get_file_duration(audio_path)
    words_per_chunk = 4 if short_punchy else 8
    min_chunk_duration = 1.0 if short_punchy else 1.5
    return sync_by_character_mapping(clean_script, audio_duration, words_per_chunk, min_chunk_duration, sync_offset)

# =====================================================================
# --- 2. CORE AUTOMATION FLOW ENGINES ---
# =====================================================================

def cleanup_temp_files():
    for f in os.listdir("."):
        if f.startswith(("fc_clip_", "fc_img_", "temp_", "subtitles.", "thumb_", "FACELESS_", "AETHER_RECAP_", "fc_audio.wav", "fc_video_loop.mp4", "hook_text.txt", "thumb_pro_text.txt", "thumb_text.txt")):
            try:
                os.remove(f)
            except Exception:
                pass

def get_file_duration(file_path):
    try:
        cmd = [FFMPEG_BINARY, "-i", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        pass
    return 600.0

def download_video_from_url(url, output_path="input_temp.mp4"):
    if os.path.exists(output_path):
        os.remove(output_path)
    ydl_opts = {'outtmpl': output_path, 'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'quiet': True, 'no_warnings': True, 'ffmpeg_location': FFMPEG_BINARY}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        raise Exception(f"Download Error: {str(e)}")

def extract_audio_fast(video_in, audio_out="temp_extracted.mp3"):
    if os.path.exists(audio_out):
        os.remove(audio_out)
    try:
        (ffmpeg.input(video_in).output(audio_out, acodec='libmp3lame', ac=1, ar='16000').run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True))
        if os.path.exists(audio_out):
            return audio_out
    except Exception:
        pass
    return None

async def generate_tts(text, voice_model, output_file, engine="Edge-TTS", ttsmaker_key="", eleven_key="", custom_eleven_id="", gemini_key="", pitch=0, voice_fx="None"):
    if not text.strip():
        return
    if "Synergy" not in engine:
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\{.*?\}', '', text)
    parts = re.split(r'([။?!.\n]+)', text)
    sentences = []
    for i in range(0, len(parts)-1, 2):
        sentences.append(parts[i] + parts[i+1])
    if len(parts) % 2 != 0 and parts[-1].strip():
        sentences.append(parts[-1])
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence += ' '
        if len(current_chunk) + len(sentence) < 300:
            current_chunk += sentence
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    needs_ffmpeg = pitch != 0 or voice_fx != "None"
    temp_out = "temp_raw_audio_fx.wav" if needs_ffmpeg else output_file
    chunk_files = []
    last_tts_error = "Unknown Error"
    for i, chunk_text in enumerate(chunks):
        if not chunk_text.strip():
            continue
        c_out = f"temp_tts_chunk_{i}.wav" if ("Synergy" in engine or "ElevenLabs" in engine) else f"temp_tts_chunk_{i}.mp3"
        if "Synergy" in engine:
            keys_list = [k.strip() for k in gemini_key.split(",") if k.strip()]
            voice_name = "Puck" if "Puck" in voice_model else ("Charon" if "Charon" in voice_model else "Aoede")
            prompt_text = "Read this naturally. " + chunk_text
            payload = {"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}}}}
            success = False
            for ck in keys_list:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={ck}"
                try:
                    res = requests.post(url, json=payload, timeout=60)
                    if res.status_code == 200:
                        candidate = res.json().get("candidates", [{}])[0]
                        if "content" in candidate:
                            pcm_data = base64.b64decode(candidate["content"]["parts"][0]["inlineData"]["data"])
                            with wave.open(c_out, "wb") as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(24000)
                                wf.writeframes(pcm_data)
                            success = True
                            break
                except Exception:
                    pass
            if not success:
                continue
        elif "ElevenLabs" in engine:
            voice_id = custom_eleven_id.strip() if custom_eleven_id else ("21m00Tcm4TlvDq8ikWAM" if "Male" in voice_model else "AZnzlk1XvdvUeBnXmlld")
            res = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", json={"text": chunk_text, "model_id": "eleven_multilingual_v2"}, headers={"xi-api-key": eleven_key}, timeout=60)
            if res.status_code == 200:
                with open(c_out, "wb") as f:
                    f.write(res.content)
            else:
                last_tts_error = f"ElevenLabs: {res.text[:100]}"
        else:
            voice = "my-MM-ThihaNeural" if "Male" in voice_model else "my-MM-NilarNeural"
            try:
                await edge_tts.Communicate(chunk_text, voice).save(c_out)
            except Exception as e:
                last_tts_error = str(e)
        if os.path.exists(c_out):
            chunk_files.append(c_out)
    if not chunk_files:
        raise Exception(f"TTS Failed: {last_tts_error}")
    with open("audio_concat.txt", "w", encoding="utf-8") as f:
        for c in chunk_files:
            f.write(f"file '{c}'\n")
    subprocess.run([FFMPEG_BINARY, "-y", "-f", "concat", "-safe", "0", "-i", "audio_concat.txt", "-c:a", "pcm_s16le", "-ar", "44100", temp_out], capture_output=True)
    for c in chunk_files:
        if os.path.exists(c):
            os.remove(c)
    if os.path.exists("audio_concat.txt"):
        os.remove("audio_concat.txt")
    if needs_ffmpeg:
        audio = ffmpeg.input(temp_out)
        if pitch != 0:
            factor = 1.0 + (pitch / 100.0)
            audio = audio.filter('asetrate', int(44100 * factor)).filter('atempo', 1.0 / factor)
        if "Epic" in voice_fx:
            audio = audio.filter('bass', g=12, f=120)
        elif "Walkie-Talkie" in voice_fx:
            audio = audio.filter('highpass', f=400).filter('lowpass', f=3000).filter('volume', 1.5)
        elif "Reverb" in voice_fx:
            audio = audio.filter('aecho', 0.8, 0.88, 60, 0.4)
        elif "Demon" in voice_fx:
            audio = audio.filter('bass', g=15, f=100).filter('aecho', 0.8, 0.88, 40, 0.5)
        elif "ASMR" in voice_fx:
            audio = audio.filter('treble', g=12, f=6000).filter('volume', 1.5)
        elif "Robot" in voice_fx:
            audio = audio.filter('aphaser', type='t', speed=2, decay=0.6).filter('volume', 1.2)
        elif "Telephone" in voice_fx:
            audio = audio.filter('highpass', f=300).filter('lowpass', f=2500).filter('compand', attacks='0', decays='0.2', points='-70/-70|-20/-20|0/-10')
        elif "Cave" in voice_fx:
            audio = audio.filter('aecho', 0.8, 0.9, 1000, 0.3)
        elif "Underwater" in voice_fx:
            audio = audio.filter('lowpass', f=400).filter('volume', 1.5)
        elif "Deep & Energetic" in voice_fx:
            audio = audio.filter('bass', g=10, f=150).filter('treble', g=5, f=3000).filter('volume', 1.5)
        elif "Deep & Chilling" in voice_fx:
            audio = audio.filter('bass', g=15, f=80).filter('aecho', 0.8, 0.85, 60, 0.3).filter('volume', 1.2)
        try:
            (audio.output(output_file, acodec='pcm_s16le', ac=1, ar='44100').overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True))
        except Exception:
            shutil.copy(temp_out, output_file)
        finally:
            if os.path.exists(temp_out):
                os.remove(temp_out)

def parse_and_save_real_srt(raw_srt_text, output_file, use_fade=False):
    lines = raw_srt_text.strip().split('\n')
    parsed_lines = []
    current_start, current_end = 0.0, 0.0
    current_text = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit() and len(line) < 5:
            continue
        if "-->" in line:
            if current_text:
                parsed_lines.append((current_start, current_end, " ".join(current_text)))
                current_text = []
            parts = line.split("-->")
            try:
                def parse_lenient(t_str):
                    t_str = t_str.strip().replace('.', ',')
                    if ',' not in t_str:
                        t_str += ",000"
                    main_t, ms = t_str.split(',')
                    tp = main_t.split(':')
                    if len(tp) == 1:
                        return int(tp[0]) + float(ms.ljust(3, '0')) / 1000.0
                    elif len(tp) == 2:
                        return int(tp[0]) * 60 + int(tp[1]) + float(ms.ljust(3, '0')) / 1000.0
                    else:
                        return int(tp[0]) * 3600 + int(tp[1]) * 60 + int(tp[2]) + float(ms.ljust(3, '0')) / 1000.0
                current_start = parse_lenient(parts[0])
                current_end = parse_lenient(parts[1])
            except Exception:
                pass
        else:
            if not re.match(r'^\[.*?\]$', line):
                current_text.append(line)
    if current_text:
        parsed_lines.append((current_start, current_end, " ".join(current_text)))
    final_parsed = []
    prev_end = 0.0
    full_speech = []
    for start, end, txt in parsed_lines:
        if start < prev_end:
            start = prev_end + 0.1
        if end - start < 0.8:
            end = start + 0.8
        prev_end = end
        clean_speech_text = re.sub(r'[^\w\s\u1000-\u109F]', '', txt)
        if clean_speech_text.strip():
            full_speech.append(clean_speech_text)
        final_parsed.append((start, end, txt))
    with open(output_file, "w", encoding="utf-8-sig") as f:
        for i, (s, e, t) in enumerate(final_parsed, 1):
            def fmt_sec(sec):
                return f"{int(sec//3600):02d}:{int((sec%3600)//60):02d}:{int(sec%60):02d},{int((sec%1)*1000):03d}"
            f.write(f"{i}\n{fmt_sec(s)} --> {fmt_sec(e)}\n{t}\n\n")
    return final_parsed, " ".join(full_speech)

def render_premium_saas_video(in_v, in_a, parsed_timestamps, out_v, ratio, use_bypass=False, use_blur=False, watermark="", subtitle_mode="Both (Burn + SRT)", use_mirror=False, use_color=False, use_grain=False, use_fps=False, sub_position="Bottom", sub_color="Yellow", sub_size=28, sub_thickness=2.5, sub_bg=False, use_freeze=False, logo_path=None, font_path="Padauk.ttf"):
    try:
        a_dur = get_file_duration(in_a)
        video = ffmpeg.input(in_v).video
        v_w, v_h = (720, 1280) if "9:16" in ratio else (1280, 720)
        video = ffmpeg.filter(video, 'scale', v_w, v_h, force_original_aspect_ratio='increase').filter('crop', v_w, v_h)
        if use_bypass:
            video = ffmpeg.filter(video, 'scale', '2*trunc(iw*1.08/2)', '2*trunc(ih*1.08/2)').filter('crop', 'iw/1.08', 'ih/1.08')
        if use_mirror:
            video = ffmpeg.filter(video, 'hflip')
        if use_color:
            video = ffmpeg.filter(video, 'eq', brightness=0.02, contrast=1.05, saturation=1.1)
        if use_grain:
            video = ffmpeg.filter(video, 'noise', alls=2, allf='t+u')
        if use_fps:
            video = ffmpeg.filter(video, 'fps', fps=24, round='near')
        if use_freeze:
            video = ffmpeg.filter(video, 'minterpolate', fps=12, mi_mode='dup')
        audio = ffmpeg.input(in_a).audio
        if use_blur:
            video = ffmpeg.filter(video, 'drawbox', x=0, y='ih-90', w='iw', h=90, color='black@0.95', thickness='fill')
        if watermark:
            video = ffmpeg.filter(video, 'drawtext', text=watermark, x='w-tw-15', y='15', fontsize=30, fontcolor='white@0.5')
        if logo_path and os.path.exists(logo_path):
            logo = ffmpeg.input(logo_path)
            logo = ffmpeg.filter(logo, 'scale', -1, 80)
            video = ffmpeg.overlay(video, logo, x='W-w-20', y=20)
        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"] and parsed_timestamps:
            wrap_width = 25 if "9:16" in ratio else 45
            safe_font_path = font_path.replace('\\', '/')
            for i, (start, end, text) in enumerate(parsed_timestamps):
                wrapped_lines = textwrap.wrap(text, width=wrap_width)
                if not wrapped_lines:
                    wrapped_lines = [text]
                max_len = max(len(line) for line in wrapped_lines)
                centered_text = "\n".join(line.center(max_len, " ") for line in wrapped_lines)
                txt_filename = f"temp_sub_{i}.txt"
                with open(txt_filename, "w", encoding="utf-8") as tf:
                    tf.write(centered_text)
                if "Center" in sub_position:
                    y_expr = "(h-text_h)/2"
                elif "Top" in sub_position:
                    y_expr = "150"
                else:
                    y_expr = "h-text_h-150"
                c_str = "yellow"
                if "White" in sub_color:
                    c_str = "white"
                elif "Green" in sub_color:
                    c_str = "green"
                elif "Red" in sub_color:
                    c_str = "red"
                elif "Gold" in sub_color:
                    c_str = "gold"
                box_str = 1 if sub_bg else 0
                box_color = 'black@0.6' if sub_bg else 'black@0.0'
                video = ffmpeg.filter(video, 'drawtext', textfile=txt_filename, fontfile=safe_font_path, fontcolor=c_str, fontsize=sub_size, bordercolor='black', borderw=sub_thickness, box=box_str, boxcolor=box_color, boxborderw=10, x='(w-text_w)/2', y=y_expr, line_spacing=20, text_align='C', enable=f'between(t,{start},{end})')
        out = ffmpeg.output(video, audio, out_v, vcodec='libx264', pix_fmt='yuv420p', acodec='aac', preset='superfast', crf=23, t=a_dur)
        out.run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "Success"
    except ffmpeg.Error as e:
        return False, e.stderr.decode('utf-8', errors='ignore')

# --- 3. UI INTERFACE & NAVIGATION ---
st.markdown('<div class="main-title">AETHER FILMWORKS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI Studio V52 ⚡ SaaS Edition</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 Navigation Menu")
    app_mode = st.radio("Select Studio Mode:", ["🎙️ Movie Dubbing Studio", "🎙️ Faceless Channel Studio", "🎥 Veo Video Studio", "🎵 Lyria Music Studio"])
    st.markdown("---")
    
    # 👇 SYNC OFFSET FORM (No auto-rerun)
    st.markdown("### 🎯 Subtitle Sync Control")
    with st.form("sync_form", clear_on_submit=False):
        new_offset = st.slider("Sync Offset (seconds)", min_value=-5.0, max_value=5.0, value=st.session_state.get("sync_offset", 0.0), step=0.1, help="(-) စာ​တန်းထိုးစော | (+) စာတန်းထိုးနောက်ကျ")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.form_submit_button("✅ Apply", use_container_width=True):
                st.session_state.sync_offset = new_offset
                st.rerun()
        with col_f2:
            if st.form_submit_button("🔄 Reset", use_container_width=True):
                st.session_state.sync_offset = 0.0
                st.rerun()
    st.caption(f"📌 Active Offset: **{st.session_state.get('sync_offset', 0.0):+.1f}s**")
    
    st.markdown("---")
    ai_provider = st.selectbox("Choose AI Provider", ["Google Gemini (Flash - Recommended)", "OpenAI (GPT-5.5 Pro)", "Groq API (Fast & Free)"])
    saved_gemini = load_key(API_KEY_FILE)
    if "Gemini" in ai_provider:
        api_key_input = st.text_input("Gemini Keys (Comma separated)", type="password", value=saved_gemini)
        if api_key_input and api_key_input != saved_gemini:
            save_key(API_KEY_FILE, api_key_input)
    elif "Groq" in ai_provider:
        saved_groq = load_key(GROQ_KEY_FILE)
        api_key_input = st.text_input("Groq API Key", type="password", value=saved_groq)
    else:
        saved_openai = load_key(OPENAI_KEY_FILE)
        api_key_input = st.text_input("OpenAI API Key", type="password", value=saved_openai)
    
    if app_mode == "🎙️ Faceless Channel Studio":
        st.markdown("---")
        st.markdown("### 🔑 Additional Keys")
        saved_groq_fc = load_key(GROQ_KEY_FILE)
        groq_key_fc = st.text_input("Groq Key (Whisper Sync)", type="password", value=saved_groq_fc)
        if groq_key_fc:
            save_key(GROQ_KEY_FILE, groq_key_fc)

# =====================================================================
# 📌 MODE 1 - MOVIE DUBBING (Step-by-Step)
# =====================================================================
if app_mode == "🎙️ Movie Dubbing Studio":
    with st.sidebar:
        st.markdown("---")
        audio_engine_choice = st.radio("Voice Engine", ["Edge-TTS (Default Free)", "Google Synergy TTS (Flash 3.1 Preview)", "ElevenLabs (Premium AI)", "TTSMaker (Free API)"])
        if "Synergy" in audio_engine_choice:
            synergy_key = st.text_input("Synergy TTS Key", type="password", value=saved_gemini)
        if "ElevenLabs" in audio_engine_choice:
            eleven_key_input = st.text_input("ElevenLabs Key", type="password", value=load_key(ELEVEN_KEY_FILE))
            if eleven_key_input:
                save_key(ELEVEN_KEY_FILE, eleven_key_input)
        key_ttsmaker = st.text_input("TTSMaker Key", type="password") if "TTSMaker" in audio_engine_choice else ""
        st.markdown("---")
        video_ratio = st.selectbox("Crop Ratio", ["Original", "9:16 (TikTok/Shorts)", "16:9 (YouTube)"])
        st.markdown("<b>🛡️ Anti-Copyright</b>", unsafe_allow_html=True)
        cb_bypass = st.checkbox("🔍 Smart Zoom", value=True)
        cb_mirror = st.checkbox("🪞 Mirror", value=False)
        cb_color = st.checkbox("🎨 Color", value=False)
        cb_grain = st.checkbox("🎞️ Grain", value=False)
        cb_fps = st.checkbox("🎬 24 FPS", value=False)
        cb_freeze = st.checkbox("❄️ Freeze", value=False)
        st.markdown("<b>🎬 Visual</b>", unsafe_allow_html=True)
        cb_blur = st.checkbox("👁️ Black Mask", value=True)
        subtitle_mode = st.radio("Subtitle Output", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"])
        st.markdown("---")
        st.markdown("<b>🖼️ Thumbnail</b>", unsafe_allow_html=True)
        thumbnail_style = st.selectbox("Style", list(THUMBNAIL_STYLES.keys()), index=0)

    st.markdown('<div class="setting-panel"><h3>📺 Media Setup</h3>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        video_url = st.text_input("🔗 Video URL", placeholder="https://...")
        uploaded_file = st.file_uploader("📥 OR Upload MP4", type=["mp4"])
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='color:#38bdf8;'>✍️ Script Rules</p>", unsafe_allow_html=True)
        recap_mode = st.radio("🎬 Mode", ["Translate Original Video (မူရင်းကို ဘာသာပြန်မည်)", "Create Original AI Story (ကိုယ်ပိုင်ဇာတ်လမ်းဖန်တီးမည်)"])
        script_style = st.selectbox("🎭 Style", ["Normal (ပုံမှန်)", "Slang (Gen-Z)", "Comedy (ဟာသ)", "Suspense (သည်းထိတ်)"])
        script_hook = st.checkbox("🪝 Hook", True)
        script_curiosity = st.checkbox("🤯 Curiosity", True)
        script_tone = st.checkbox("🎭 Tone", True)
        script_cta = st.checkbox("💬 CTA", False)
        st.markdown("</div>", unsafe_allow_html=True)
        bgm_options = ["None (BGM မထည့်ပါ)"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files:
            bgm_options.insert(1, "🤖 Auto")
            bgm_options.extend(bgm_files)
        selected_bgm = st.selectbox("🎼 BGM", bgm_options)
        bgm_volume = st.slider("🔊 BGM Vol", 1, 50, 10) / 100.0
    with col_in2:
        dynamic_options = ["Synergy Puck (Male)", "Synergy Aoede (Female)", "Synergy Charon (Deep)"] if "Synergy" in audio_engine_choice else (["Adam (Male)", "Rachel (Female)"] if "ElevenLabs" in audio_engine_choice else ["ဇော်ဇော် (Male)", "အောင်အောင် (Deep)", "နှင်းနှင်း (Female)"])
        voice_char = st.selectbox("Voice", dynamic_options, index=0)
        pitch_level = st.slider("🎙️ Pitch", -30, 30, 0, 5)
        recommended_fx_dub = get_recommended_fx_for_niche(script_style, mode="dubbing")
        fx_level = st.selectbox("🎧 Voice FX", recommended_fx_dub, index=0)
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='color:#818cf8;'>📝 Subs</p>", unsafe_allow_html=True)
        if subtitle_mode in ["Both (Burn + SRT)", "Burn into Video"]:
            selected_font = st.selectbox("🔤 Font", available_fonts, index=0)
            sub_position = st.selectbox("📍 Position", ["Bottom", "Center", "Top"])
            sub_color = st.selectbox("🎨 Color", ["Yellow", "White", "Green", "Red", "Gold"])
            sub_size = st.slider("🔠 Size", 16, 50, 28)
            sub_thickness = st.slider("✒️ Outline", 1.0, 5.0, 2.5)
            sub_bg = st.checkbox("🔲 BG Box", True)
            sub_short = st.checkbox("✂️ Short & Punchy")
        else:
            selected_font = "Padauk.ttf"
            sub_position = "Bottom"
            sub_color = "Yellow"
            sub_size = 28
            sub_thickness = 2.5
            sub_bg = True
            sub_short = False
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ===== STEP 1: GENERATE SCRIPT =====
    if st.button("🚀 STEP 1: GENERATE SCRIPT & PREVIEW", use_container_width=True, type="primary"):
        if not api_key_input:
            st.error("⚠️ API Key လိုအပ်ပါသည်။")
        elif not uploaded_file and not video_url:
            st.error("⚠️ ဗီဒီယိုထည့်ပါ။")
        else:
            st.session_state.render_success = False
            cleanup_temp_files()
            run_id = str(int(time.time()))
            v_input = "input_temp.mp4"
            
            with st.spinner("📥 Downloading..."):
                if uploaded_file:
                    with open(v_input, "wb") as f:
                        f.write(uploaded_file.read())
                else:
                    download_video_from_url(video_url, v_input)
            
            a_extracted = extract_audio_fast(v_input) or "temp_extracted.mp3"
            
            with st.spinner("🤖 Generating script..."):
                extra_rules = ""
                if script_hook:
                    extra_rules += " [HOOK]"
                if "Slang" in script_style:
                    extra_rules += " [SLANG]"
                elif "Comedy" in script_style:
                    extra_rules += " [COMEDY]"
                elif "Suspense" in script_style:
                    extra_rules += " [SUSPENSE]"
                if script_curiosity:
                    extra_rules += " [CURIOSITY]"
                if script_tone:
                    extra_rules += " [TONE]"
                if script_cta:
                    extra_rules += " [CTA]"
                extra_rules += "\n[TITLE: ...]\n[TAGS: #...]"
                hormozi_rule = " [HORMOZI]" if sub_short else ""
                
                if "Gemini" in ai_provider:
                    keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                    success_g = False
                    for ck in keys_list:
                        try:
                            client = genai.Client(api_key=ck)
                            target_file = v_input if "Original" in recap_mode else a_extracted
                            media_file = client.files.upload(file=target_file)
                            while "PROCESSING" in str(client.files.get(name=media_file.name).state):
                                time.sleep(2)
                            prompt = f"Watch video. Create ORIGINAL Burmese recap with SRT timestamps.{extra_rules}{hormozi_rule}" if "Original" in recap_mode else f"Listen to audio. Translate to Burmese SRT.{extra_rules}{hormozi_rule}"
                            response = client.models.generate_content(model="gemini-2.5-flash", contents=[media_file, prompt])
                            raw_output_text = response.text.strip()
                            client.files.delete(name=media_file.name)
                            success_g = True
                            break
                        except Exception:
                            continue
                    if not success_g:
                        st.error("Gemini failed")
                        st.stop()
                
                title_match = re.search(r'\[TITLE:\s*(.*?)\]', raw_output_text, re.IGNORECASE)
                tags_match = re.search(r'\[TAGS:\s*(.*?)\]', raw_output_text, re.IGNORECASE)
                st.session_state.viral_title = re.sub(r'[\[\]]', '', title_match.group(1)).strip() if title_match else "Viral Recap"
                st.session_state.viral_tags = tags_match.group(1).strip() if tags_match else "#recap"
                clean_raw_srt = re.sub(r'\[TITLE:.*?\]', '', raw_output_text, flags=re.IGNORECASE)
                clean_raw_srt = re.sub(r'\[TAGS:.*?\]', '', clean_raw_srt, flags=re.IGNORECASE).strip()
                clean_raw_srt = clean_raw_srt.replace("```srt", "").replace("```", "")
                
                audio_dur = get_file_duration(a_extracted)
                if "-->" in clean_raw_srt:
                    parsed_timestamps, speech_text = parse_and_save_real_srt(clean_raw_srt, "subtitles.srt")
                else:
                    sync_srt, sync_parsed = smart_sync_pipeline(strip_audio_tags(clean_raw_srt), a_extracted, None, audio_dur, st.session_state.sync_offset, sub_short)
                    with open("subtitles.srt", "w", encoding="utf-8-sig") as f:
                        f.write(sync_srt)
                    parsed_timestamps = sync_parsed
                    speech_text = strip_audio_tags(clean_raw_srt)
                
                st.session_state.dub_parsed = parsed_timestamps
                st.session_state.dub_audio_dur = audio_dur
                st.session_state.dub_speech = speech_text
                st.session_state.dub_ready = True
                st.session_state.dub_v_input = v_input
                st.session_state.dub_a_extracted = a_extracted
                st.session_state.dub_clean_srt = clean_raw_srt
                st.session_state.dub_run_id = run_id
                st.session_state.generated_script = clean_raw_srt
                st.success("✅ Script ready! Review timeline below ↓")
    
    # ===== STEP 2: PREVIEW =====
    if st.session_state.get("dub_ready", False):
        st.markdown("---")
        st.markdown("### 📊 Step 2: Review Sync Timeline")
        parsed = st.session_state.dub_parsed
        audio_dur = st.session_state.dub_audio_dur
        preview_parsed = [(max(0, s + st.session_state.sync_offset), max(0.8, e + st.session_state.sync_offset), t) for s, e, t in parsed]
        sq = analyze_sync_quality(preview_parsed, audio_dur)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Score", f"{sq['score']}/100")
        with c2:
            st.metric("Subs", len(parsed))
        with c3:
            st.metric("Offset", f"{st.session_state.sync_offset:+.1f}s")
        if sq['issues']:
            for i in sq['issues']:
                st.warning(f"• {i}")
        st.info(f"💡 {sq['recommendation']}")
        with st.expander("🔍 Timeline", expanded=True):
            st.components.v1.html(generate_sync_preview_html(preview_parsed, audio_dur), height=400, scrolling=True)
        
        # ===== STEP 3: RENDER =====
        st.markdown("---")
        st.markdown("### 🎬 Step 3: Render Video")
        if st.button("🎬 RENDER VIDEO NOW", use_container_width=True, type="primary"):
            a_generated = "voice_temp.wav"
            with st.spinner("🎙️ Voice..."):
                asyncio.run(generate_tts(
                    st.session_state.dub_speech, voice_char, a_generated,
                    audio_engine_choice, key_ttsmaker,
                    locals().get('eleven_key_input', ''),
                    locals().get('custom_eleven_id', ''),
                    locals().get('synergy_key', api_key_input),
                    pitch_level, fx_level
                ))
            
            tts_dur = get_file_duration(a_generated)
            if abs(tts_dur - audio_dur) > 2.0:
                sync_srt, sync_parsed = smart_sync_pipeline(strip_audio_tags(st.session_state.dub_clean_srt), a_generated, None, tts_dur, st.session_state.sync_offset, sub_short)
                final_parsed = sync_parsed
            else:
                final_parsed = preview_parsed
            
            v_final = f"AETHER_RECAP_FINAL_{st.session_state.dub_run_id}.mp4"
            with st.spinner("🎬 Rendering..."):
                success, err = render_premium_saas_video(
                    st.session_state.dub_v_input, a_generated, final_parsed, v_final, video_ratio,
                    cb_bypass, cb_blur, "", subtitle_mode, cb_mirror, cb_color, cb_grain, cb_fps,
                    sub_position, sub_color, sub_size, sub_thickness, sub_bg, cb_freeze,
                    None, selected_font
                )
            
            if success:
                if selected_bgm != "None (BGM မထည့်ပါ)":
                    bgm_path = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in selected_bgm else selected_bgm)
                    if os.path.exists(bgm_path):
                        try:
                            ducked = ffmpeg.filter([ffmpeg.input(bgm_path, stream_loop=-1).audio.filter('aresample', 44100).filter('volume', bgm_volume), ffmpeg.input(v_final).audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                            mixed = ffmpeg.filter([ffmpeg.input(v_final).audio, ducked], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                            ffmpeg.output(ffmpeg.input(v_final).video, mixed, "temp_mix.mp4", vcodec='copy', acodec='aac').overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
                            shutil.move("temp_mix.mp4", v_final)
                        except Exception:
                            pass
                st.session_state.final_video_path = v_final
                st.session_state.render_success = True
                st.session_state.dub_ready = False
                try:
                    for ts, tv in [("A", min(audio_dur*0.2, 10)), ("B", min(audio_dur*0.5, 20))]:
                        tn = f"thumb_{ts}_{st.session_state.dub_run_id}.jpg"
                        ok, _ = generate_professional_thumbnail(v_final, tn, st.session_state.viral_title, tv, thumbnail_style, selected_font)
                        if ok:
                            if ts == "A":
                                st.session_state.thumb_path_A = tn
                            else:
                                st.session_state.thumb_path_B = tn
                except Exception:
                    pass
                st.rerun()
            else:
                st.error(f"❌ {err}")
    
    # ===== OUTPUT =====
    if st.session_state.render_success:
        st.balloons()
        st.success("🎉 Done!")
        st.markdown(f"<h2 style='color:#38bdf8; text-align:center;'>🔥 {st.session_state.viral_title}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{st.session_state.viral_tags}</p>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if os.path.exists(st.session_state.final_video_path):
                st.video(st.session_state.final_video_path)
                st.markdown(get_download_link(st.session_state.final_video_path, "Recap.mp4", "Download Video"), unsafe_allow_html=True)
                if os.path.exists("subtitles.srt"):
                    st.markdown(get_download_link("subtitles.srt", "Subs.srt", "Download SRT"), unsafe_allow_html=True)
        with c2:
            if st.session_state.thumb_path_A and os.path.exists(st.session_state.thumb_path_A):
                st.image(st.session_state.thumb_path_A, caption="Thumb A")
                st.markdown(get_download_link(st.session_state.thumb_path_A, "Thumb_A.jpg", "Download"), unsafe_allow_html=True)
            if st.session_state.thumb_path_B and os.path.exists(st.session_state.thumb_path_B):
                st.image(st.session_state.thumb_path_B, caption="Thumb B")
                st.markdown(get_download_link(st.session_state.thumb_path_B, "Thumb_B.jpg", "Download"), unsafe_allow_html=True)
            with st.expander("📝 Script"):
                st.text_area("", value=st.session_state.generated_script, height=250, disabled=True)

# =====================================================================
# 📌 MODE 1.5 - FACELESS Channel Studio
# =====================================================================
elif app_mode == "🎙️ Faceless Channel Studio":
    st.markdown('<div class="setting-panel"><h3>👻 Faceless Channel Studio</h3>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("---")
        fc_audio_engine = st.radio("Voice Engine", ["Edge-TTS (Free)", "Google Synergy TTS (API)"], key="fc_eng")
        if "Synergy" in fc_audio_engine:
            fc_synergy_key = st.text_input("Synergy Key", type="password", value=saved_gemini, key="fc_syn")
        fc_voice_char = st.selectbox("Voice", ["Synergy Puck", "Synergy Charon"] if "Synergy" in fc_audio_engine else ["ဇော်ဇော်", "အောင်အောင်", "နှင်းနှင်း"], key="fc_vc")
        
        fc_niche = st.selectbox("Niche", ["👻 Horror", "💔 Relationship", "🧠 Dark Psychology", "💡 Fun Facts", "🚀 Motivation", "📜 History"])
        fc_ratio = st.selectbox("Ratio", ["9:16 (TikTok)", "16:9 (YouTube)"], key="fc_r")
        fc_duration = st.slider("Duration (min)", 1, 10, 3)
        
        rec_fx = get_recommended_fx_for_niche(fc_niche)
        fc_fx = st.selectbox("🎧 Voice FX", rec_fx, index=1, key="fc_fx")
        
        st.markdown("<b>🔥 TikTok Hook</b>", unsafe_allow_html=True)
        fc_use_hook = st.checkbox("Hook Overlay", True, key="fc_hk")
        if fc_use_hook:
            if "fc_hook_text" not in st.session_state:
                st.session_state.fc_hook_text = get_random_hook(fc_niche)
            fc_hook_text = st.session_state.fc_hook_text
            st.markdown(f'<div style="background:#0d111c; border:2px solid #38bdf8; border-radius:10px; padding:10px; text-align:center; color:#38bdf8; font-weight:bold;">🎯 {fc_hook_text}</div>', unsafe_allow_html=True)
            if st.button("🔄 New Hook"):
                st.session_state.fc_hook_text = get_random_hook(fc_niche)
                st.rerun()
        fc_use_loop = st.checkbox("Loop Point", True, key="fc_lp")
        
        dt = get_thumbnail_style_for_niche(fc_niche)
        tk = list(THUMBNAIL_STYLES.keys())
        fc_thumb = st.selectbox("🖼️ Thumbnail", tk, index=tk.index(dt) if dt in tk else 0, key="fc_th")
        
        fc_font = st.selectbox("🔤 Font", available_fonts, index=0, key="fc_fnt")
        fc_sub_pos = st.selectbox("📍 Position", ["Center", "Bottom", "Top"], index=0, key="fc_sp")
        fc_sub_col = st.selectbox("🎨 Color", ["Yellow", "White", "Green", "Red", "Gold"], index=0, key="fc_sc")
        fc_sub_sz = st.slider("🔠 Size", 16, 50, 28, key="fc_ss")
        fc_sub_mode = st.radio("Mode", ["Both", "SRT Only", "Burn"], key="fc_sm")
        
        bgm_opts = ["None"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files:
            bgm_opts.insert(1, "🤖 Auto")
            bgm_opts.extend(bgm_files)
        fc_bgm = st.selectbox("🎼 BGM", bgm_opts, key="fc_bg")
        fc_bgm_vol = st.slider("🔊 BGM Vol", 1, 50, 8, key="fc_bv") / 100.0
        fc_sub_short = st.checkbox("✂️ Short & Punchy", True)
    
    st.markdown('<div class="setting-panel"><h4>🛠️ Manual Controls</h4>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fc_script_mode = st.radio("Script", ["🤖 Auto", "✍️ Manual"])
        if "Auto" in fc_script_mode:
            fc_topic = st.text_input("💡 Topic", key="fc_tp")
            fc_sh = st.checkbox("🪝 Hook", True, key="fc_sh")
            fc_sc_ = st.checkbox("🤯 Curiosity", True, key="fc_sc_")
            fc_st = st.checkbox("🎭 Tone", True, key="fc_st")
            fc_cta = st.checkbox("💬 CTA", False, key="fc_ct")
        fc_manual = st.text_area("✍️ Script", height=150) if "Manual" in fc_script_mode else ""
    with c2:
        fc_vis = st.radio("Visuals", ["🎨 AI Images", "🖼️ Upload"])
        fc_imgs = st.file_uploader("Upload Images", type=["png","jpg","jpeg"], accept_multiple_files=True) if "Upload" in fc_vis else None
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== STEP 1 =====
    if st.button("🚀 STEP 1: GENERATE CONTENT & PREVIEW", use_container_width=True, type="primary"):
        if not api_key_input:
            st.error("⚠️ API Key လိုအပ်ပါသည်။")
        elif "Manual" in fc_script_mode and not fc_manual.strip():
            st.error("⚠️ Script ထည့်ပါ။")
        elif "Upload" in fc_vis and not fc_imgs:
            st.error("⚠️ ပုံထည့်ပါ။")
        else:
            st.session_state.render_success = False
            cleanup_temp_files()
            run_id = str(int(time.time()))
            
            fc_story = fc_manual.strip() if "Manual" in fc_script_mode else ""
            if "Auto" in fc_script_mode:
                with st.spinner("🤖 Generating story..."):
                    keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                    ti = f"Topic: {fc_topic}.\n" if fc_topic else ""
                    hr = "1. HOOK\n" if fc_sh else ""
                    cr = "2. CURIOSITY\n" if fc_sc_ else ""
                    tr = "3. TONE\n" if fc_st else ""
                    ctr = "4. CTA\n" if fc_cta else ""
                    prompt = f"""Write {fc_duration}min viral script for {fc_niche}. Burmese. {fc_duration*140} words.
{ti}{hr}{cr}{tr}{ctr}NO formal grammar. Audio tags. [TITLE: ...] [TAGS: ...]"""
                    for k in keys_list:
                        try:
                            client = genai.Client(api_key=k)
                            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                            fc_story = resp.text.strip()
                            break
                        except Exception:
                            continue
                    if not fc_story:
                        st.error("Story failed")
                        st.stop()
            
            tm = re.search(r'\[TITLE:\s*(.*?)\]', fc_story, re.IGNORECASE)
            tg = re.search(r'\[TAGS:\s*(.*?)\]', fc_story, re.IGNORECASE)
            st.session_state.viral_title = re.sub(r'[\[\]]', '', tm.group(1)).strip() if tm else "Viral Story"
            st.session_state.viral_tags = tg.group(1).strip() if tg else "#story"
            fc_story = re.sub(r'\[TITLE:.*?\]', '', fc_story, flags=re.IGNORECASE)
            fc_story = re.sub(r'\[TAGS:.*?\]', '', fc_story, flags=re.IGNORECASE).strip()
            
            with st.spinner("🎙️ TTS..."):
                clean_story = re.sub(r'\[.*?\]', '', fc_story)
                asyncio.run(generate_tts(
                    fc_story if "Synergy" in fc_audio_engine else clean_story,
                    fc_voice_char, "fc_audio.wav", fc_audio_engine,
                    gemini_key=locals().get('fc_synergy_key', api_key_input),
                    voice_fx=fc_fx
                ))
                fc_audio_dur = get_file_duration("fc_audio.wav")
                if fc_audio_dur < 5:
                    st.error("TTS failed")
                    st.stop()
            
            with st.spinner("🎥 Visuals..."):
                v_w, v_h = (720, 1280) if "9:16" in fc_ratio else (1280, 720)
                generated_clips = []
                if "Upload" in fc_vis:
                    cd = fc_audio_dur / len(fc_imgs)
                    for i, img in enumerate(fc_imgs):
                        ip = f"fc_img_{i}.jpg"
                        cp = f"fc_clip_{i}.mp4"
                        img.seek(0)
                        with open(ip, "wb") as f:
                            f.write(img.read())
                        subprocess.run([FFMPEG_BINARY, "-y", "-loop", "1", "-i", ip, "-t", str(cd), "-vf", f"scale={v_w}:{v_h},zoompan=z='min(zoom+0.001,1.15)':d={int(cd*25)}:s={v_w}x{v_h}", "-c:v", "libx264", cp], capture_output=True)
                        if os.path.exists(cp):
                            generated_clips.append(cp)
                else:
                    sm = {"👻 Horror": "horror 8k", "💔 Relationship": "drama cinematic", "🧠 Dark Psychology": "neo-noir", "💡 Fun Facts": "Pixar style", "🚀 Motivation": "epic golden", "📜 History": "fantasy epic"}
                    cs = sm.get(fc_niche, "cinematic 8k")
                    img_count = max(4, int(fc_audio_dur // 12))
                    sk = []
                    for k in keys_list if 'keys_list' in dir() else [api_key_input]:
                        try:
                            cl = genai.Client(api_key=k)
                            r = cl.models.generate_content(model="gemini-2.5-flash", contents=f"Create {img_count} image prompts separated by '|'. Style: {cs}. Story: {fc_story[:500]}")
                            sk = [kw.strip() for kw in r.text.replace('\n','|').split('|') if len(kw.strip()) > 5][:img_count]
                            break
                        except Exception:
                            continue
                    if not sk:
                        sk = [f"{cs}, scene {i}" for i in range(img_count)]
                    cd = fc_audio_dur / len(sk)
                    for i, kw in enumerate(sk):
                        try:
                            ep = kw.strip() + ", masterpiece, 8k"
                            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(ep)}?width={v_w}&height={v_h}&nologo=true"
                            r = requests.get(url, timeout=60)
                            if r.status_code == 200:
                                ip = f"fc_img_{i}.jpg"
                                cp = f"fc_clip_{i}.mp4"
                                with open(ip, "wb") as f:
                                    f.write(r.content)
                                subprocess.run([FFMPEG_BINARY, "-y", "-loop", "1", "-i", ip, "-t", str(cd), "-vf", f"scale={v_w}:{v_h},zoompan=z='min(zoom+0.001,1.15)':d={int(cd*25)}:s={v_w}x{v_h}", "-c:v", "libx264", cp], capture_output=True)
                                if os.path.exists(cp):
                                    generated_clips.append(cp)
                        except Exception:
                            pass
                        time.sleep(2)
                if not generated_clips:
                    st.error("Visuals failed")
                    st.stop()
                with open("fc_concat.txt", "w") as f:
                    for c in generated_clips:
                        f.write(f"file '{c}'\n")
                subprocess.run([FFMPEG_BINARY, "-y", "-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", "fc_concat.txt", "-t", str(fc_audio_dur), "-c", "copy", "fc_video_loop.mp4"], capture_output=True)
            
            with st.spinner("📝 SRT..."):
                sync_srt, fc_parsed = smart_sync_pipeline(strip_audio_tags(fc_story), "fc_audio.wav", None, fc_audio_dur, st.session_state.sync_offset, fc_sub_short)
                with open("subtitles.srt", "w", encoding="utf-8-sig") as f:
                    f.write(sync_srt)
            
            st.session_state.fc_parsed = fc_parsed
            st.session_state.fc_audio_dur = fc_audio_dur
            st.session_state.fc_ready = True
            st.session_state.fc_story = fc_story
            st.session_state.fc_run_id = run_id
            st.session_state.generated_script = fc_story
            st.success("✅ Content ready! Review below ↓")
    
    # ===== STEP 2: PREVIEW =====
    if st.session_state.get("fc_ready", False):
        st.markdown("---")
        st.markdown("### 📊 Step 2: Review Timeline")
        p = st.session_state.fc_parsed
        ad = st.session_state.fc_audio_dur
        pp = [(max(0, s+st.session_state.sync_offset), max(0.8, e+st.session_state.sync_offset), t) for s, e, t in p]
        sq = analyze_sync_quality(pp, ad)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Score", f"{sq['score']}/100")
        with c2:
            st.metric("Subs", len(p))
        with c3:
            st.metric("Offset", f"{st.session_state.sync_offset:+.1f}s")
        st.info(f"💡 {sq['recommendation']}")
        with st.expander("🔍 Timeline", expanded=True):
            st.components.v1.html(generate_sync_preview_html(pp, ad), height=400, scrolling=True)
        
        # ===== STEP 3: RENDER =====
        st.markdown("---")
        st.markdown("### 🎬 Step 3: Render")
        if st.button("🎬 RENDER VIDEO", use_container_width=True, type="primary"):
            v_final = f"FACELESS_FINAL_{st.session_state.fc_run_id}.mp4"
            temp_r = "temp_base.mp4"
            with st.spinner("🎬 Rendering..."):
                s, e = render_premium_saas_video("fc_video_loop.mp4", "fc_audio.wav", pp, temp_r, fc_ratio, True, subtitle_mode=fc_sub_mode, sub_position=fc_sub_pos, sub_color=fc_sub_col, sub_size=fc_sub_sz, sub_thickness=2.5, sub_bg=False, font_path=fc_font)
            if s:
                cv = temp_r
                if fc_use_hook:
                    cv = add_tiktok_hook_overlay(cv, "temp_h.mp4", fc_hook_text, fc_niche)
                if fc_use_loop:
                    cv = add_tiktok_loop_point(cv, "temp_l.mp4")
                shutil.move(cv, v_final)
                if fc_bgm != "None":
                    bp = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in fc_bgm else fc_bgm)
                    if os.path.exists(bp):
                        try:
                            dk = ffmpeg.filter([ffmpeg.input(bp, stream_loop=-1).audio.filter('aresample', 44100).filter('volume', fc_bgm_vol), ffmpeg.input(v_final).audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                            mx = ffmpeg.filter([ffmpeg.input(v_final).audio, dk], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                            ffmpeg.output(ffmpeg.input(v_final).video, mx, "tmp_b.mp4", vcodec='copy', acodec='aac', audio_bitrate='128k', t=ad).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
                            shutil.move("tmp_b.mp4", v_final)
                        except Exception:
                            pass
                st.session_state.final_video_path = v_final
                st.session_state.render_success = True
                st.session_state.fc_ready = False
                try:
                    for ts, tv in [("A", min(ad*0.2,10)), ("B", min(ad*0.5,20))]:
                        tn = f"thumb_{ts}_{st.session_state.fc_run_id}.jpg"
                        ok, _ = generate_professional_thumbnail(v_final, tn, st.session_state.viral_title or "Video", tv, fc_thumb, fc_font)
                        if ok:
                            if ts == "A":
                                st.session_state.thumb_path_A = tn
                            else:
                                st.session_state.thumb_path_B = tn
                except Exception:
                    pass
                st.rerun()
            else:
                st.error(f"❌ {e}")
    
    # ===== OUTPUT =====
    if st.session_state.render_success:
        st.balloons()
        st.success("🎉 Done!")
        st.markdown(f"<h2 style='color:#38bdf8;'>🔥 {st.session_state.viral_title}</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if os.path.exists(st.session_state.final_video_path):
                st.video(st.session_state.final_video_path)
                st.markdown(get_download_link(st.session_state.final_video_path, "Faceless.mp4", "Download Video"), unsafe_allow_html=True)
                if os.path.exists("subtitles.srt"):
                    st.markdown(get_download_link("subtitles.srt", "Subs.srt", "Download SRT"), unsafe_allow_html=True)
        with c2:
            if st.session_state.thumb_path_A and os.path.exists(st.session_state.thumb_path_A):
                st.image(st.session_state.thumb_path_A, caption="Thumb A")
                st.markdown(get_download_link(st.session_state.thumb_path_A, "Thumb_A.jpg", "Download"), unsafe_allow_html=True)
            if st.session_state.thumb_path_B and os.path.exists(st.session_state.thumb_path_B):
                st.image(st.session_state.thumb_path_B, caption="Thumb B")
                st.markdown(get_download_link(st.session_state.thumb_path_B, "Thumb_B.jpg", "Download"), unsafe_allow_html=True)
            with st.expander("📝 Script"):
                st.text_area("", value=st.session_state.generated_script, height=250, disabled=True)

# =====================================================================
# 📌 MODE 2 & 3
# =====================================================================
elif app_mode == "🎥 Veo Video Studio":
    st.markdown('<div class="setting-panel"><h3>🎥 Veo 3.0</h3>', unsafe_allow_html=True)
    st.text_area("🎬 Prompt", placeholder="Cinematic drone shot...")
    if st.button("🚀 Generate"):
        pass

elif app_mode == "🎵 Lyria Music Studio":
    st.markdown('<div class="setting-panel"><h3>🎵 Lyria 3 Pro</h3>', unsafe_allow_html=True)
    st.text_area("🎧 Prompt", placeholder="Epic background music...")
    if st.button("🚀 Generate"):
        pass
