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
DEEPSEEK_KEY_FILE = "saved_deepseek_key.txt"
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
# 📌 DeepSeek API Integration (WITH AUTO-FALLBACK)
# =====================================================================

def call_deepseek_api(prompt, api_key, system_prompt="", max_tokens=4000, temperature=0.9, retry_count=2):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.95
    }
    last_error = ""
    for attempt in range(retry_count + 1):
        try:
            if attempt > 0:
                time.sleep(3)
                st.warning(f"🔄 DeepSeek Retry {attempt}/{retry_count}...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            elif response.status_code == 401:
                last_error = "Invalid API Key. Please check your DeepSeek API key."
                break
            elif response.status_code == 429:
                last_error = "Rate limit exceeded. Please wait a moment."
                if attempt < retry_count:
                    time.sleep(5)
                    continue
                else:
                    break
            elif response.status_code == 500:
                last_error = "DeepSeek server error. Try again later."
                if attempt < retry_count:
                    continue
                else:
                    break
            elif response.status_code == 503:
                last_error = "DeepSeek service unavailable. Server may be overloaded."
                if attempt < retry_count:
                    time.sleep(5)
                    continue
                else:
                    break
            else:
                last_error = f"API Error {response.status_code}: {response.text[:150]}"
                if attempt < retry_count:
                    continue
                else:
                    break
        except requests.exceptions.Timeout:
            last_error = "DeepSeek request timed out. Network issue or server busy."
            if attempt < retry_count:
                continue
        except requests.exceptions.ConnectionError:
            last_error = "Cannot connect to DeepSeek. Check your internet connection."
            if attempt < retry_count:
                time.sleep(5)
                continue
        except Exception as e:
            last_error = f"DeepSeek Error: {str(e)[:200]}"
            if attempt < retry_count:
                continue
    raise Exception(f"DeepSeek API Failed: {last_error}")

def deepseek_generate_script(api_key, script_prompt):
    system_prompt = """You are a professional Burmese storyteller and viral content strategist. 
You create highly engaging, emotionally immersive scripts for TikTok/YouTube.
RULES:
- Use natural spoken Burmese (တယ်, တဲ့, မှာ, ရဲ့). NEVER use formal literary markers (၌, ၍, သည့်, သည်, ၏).
- Include audio tags like [pause=1.0], [excited], [whisper] to guide voice acting.
- Write in a conversational, Gen-Z friendly tone.
- NO English transliteration. PURE BURMESE ONLY.
- Output valid SRT format with timestamps when requested."""
    return call_deepseek_api(script_prompt, api_key, system_prompt, max_tokens=4000, temperature=0.95)

def deepseek_generate_metadata(api_key, story_text):
    prompt = f"""Based on this Burmese story, create:
1. A highly viral, click-worthy Burmese title (max 15 words) that creates curiosity
2. 5-7 relevant trending hashtags for TikTok/YouTube
Story: {story_text[:800]}
Output format EXACTLY:
[TITLE: your viral Burmese title here]
[TAGS: #tag1 #tag2 #tag3]"""
    return call_deepseek_api(prompt, api_key, max_tokens=300, temperature=0.9)

def deepseek_generate_image_prompts(api_key, story_text, style, num_images=5):
    prompt = f"""Act as a professional Midjourney Prompt Engineer. 
Create {num_images} detailed English image generation prompts for chronological scenes from this story.
GLOBAL STYLE: {style}
RULES: Include camera angles, lighting, atmosphere. Use cinematic, photorealistic descriptions. 8k resolution, masterpiece quality.
NO text or words in the image description. Separate each prompt with '|' character.
Story: {story_text[:600]}
Output: prompt1 | prompt2 | prompt3 | ..."""
    return call_deepseek_api(prompt, api_key, max_tokens=1000, temperature=0.8)

def deepseek_analyze_virality(api_key, title, hook):
    prompt = f"""Analyze this video for TikTok/YouTube virality potential:
Title: {title}
Hook (first 3 seconds): {hook[:200]}
Reply in EXACTLY this format:
Score: [1-100]
Reason: [1 short sentence in Burmese]"""
    return call_deepseek_api(prompt, api_key, max_tokens=150, temperature=0.7)

def deepseek_translate_and_srt(api_key, english_srt, extra_rules=""):
    prompt = f"""Translate and adapt this English SRT into highly engaging, natural spoken Burmese.
STRICT RULES:
1. Keep the SRT format with exact same timestamps
2. Use natural spoken Burmese, NO formal grammar
3. Add audio tags like [pause=1.0], [excited] where appropriate
4. NO English transliteration
{extra_rules}
--- ENGLISH SRT ---
{english_srt[:6000]}
Output ONLY valid SRT format with Burmese text, keeping original timestamps."""
    return call_deepseek_api(prompt, api_key, max_tokens=4000, temperature=0.8)

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
        video = ffmpeg.input(video_input)
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
        video = ffmpeg.filter(video, 'drawbox',
            x=0, y='h*0.3', w='iw', h='h*0.4',
            color=style["bg_color"], thickness='fill',
            enable=f'between(t,0,{duration})')
        video = ffmpeg.filter(video, 'drawtext',
            textfile='hook_text.txt', fontfile='Padauk.ttf',
            fontsize=style["font_size"], fontcolor=style["text_color"],
            bordercolor='black', borderw=3,
            x='(w-text_w)/2', y='(h-text_h)/2',
            line_spacing=15, text_align='C',
            enable=f'between(t,0,{duration})')
        if niche == "👻 Horror / Creepypasta":
            video = ffmpeg.filter(video, 'drawbox',
                x=0, y='h*0.28', w='iw', h='4',
                color='red@0.9', thickness='fill',
                enable=f'between(t,0,{duration})')
            video = ffmpeg.filter(video, 'drawbox',
                x=0, y='h*0.72', w='iw', h='4',
                color='red@0.9', thickness='fill',
                enable=f'between(t,0,{duration})')
        ffmpeg.output(video, output_path, vcodec='libx264', preset='superfast', pix_fmt='yuv420p', acodec='copy').overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return output_path
    except Exception:
        return video_input

def add_tiktok_loop_point(video_input, output_path):
    try:
        dur = get_file_duration(video_input)
        video = ffmpeg.input(video_input)
        v_w, v_h = 720, 1280
        video = ffmpeg.filter(video, 'drawtext',
            text='👆 ပြန်ကြည့်ပါ', fontsize=35,
            fontcolor='white', bordercolor='black', borderw=2,
            x='(w-text_w)/2', y='(h-text_h)/2',
            enable=f'between(t,{dur-2},{dur})')
        ffmpeg.output(video, output_path, vcodec='libx264', preset='superfast', pix_fmt='yuv420p', acodec='copy').overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return output_path
    except Exception:
        return video_input

# =====================================================================
# 📌 PROFESSIONAL THUMBNAIL SYSTEM
# =====================================================================

THUMBNAIL_STYLES = {
    "🔥 Viral TikTok Style": {
        "text_position": "center", "font_size_range": (50, 90),
        "bg_overlay": "gradient_bottom", "text_effect": "stroke_bold",
        "color_scheme": "yellow_red",
        "description": "TikTok အတွက် အကောင်းဆုံး။ အောက်ခြေ Gradient နှင့် ထင်ရှားသော စာသား"
    },
    "🎬 Cinematic Movie Poster": {
        "text_position": "bottom_third", "font_size_range": (40, 70),
        "bg_overlay": "vignette_dark", "text_effect": "shadow_soft",
        "color_scheme": "white_gold",
        "description": "ရုပ်ရှင်ပိုစတာလို။ Vignette အနက်ရောင်ဘောင်နှင့် ရွှေရောင်စာသား"
    },
    "👻 Horror / Mystery": {
        "text_position": "center", "font_size_range": (55, 85),
        "bg_overlay": "dark_gradient", "text_effect": "shadow_horror",
        "color_scheme": "red_black",
        "description": "သည်းထိတ်ရင်ဖို ဇာတ်လမ်းများအတွက်။ အနီရောင် အသားပေး"
    },
    "💎 Premium / Luxury": {
        "text_position": "bottom_third", "font_size_range": (40, 65),
        "bg_overlay": "golden_frame", "text_effect": "golden_text",
        "color_scheme": "gold_cream",
        "description": "Premium Content အတွက်။ ရွှေရောင်ဘောင်နှင့် စာသား"
    },
    "⚡ Clean / Minimal": {
        "text_position": "center", "font_size_range": (45, 80),
        "bg_overlay": "subtle_overlay", "text_effect": "clean_white",
        "color_scheme": "white_soft",
        "description": "ရိုးရှင်းသန့်ရှင်း။ စာသားကိုသာ အသားပေး"
    }
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
        v_w, v_h = 720, 1280
        video = ffmpeg.input(video_input, ss=timestamp)
        if style_config["bg_overlay"] == "gradient_bottom":
            video = ffmpeg.filter(video, 'drawbox',
                x=0, y='ih/2', w='iw', h='ih/2',
                color='black@0.0:black@0.7', thickness='fill')
        elif style_config["bg_overlay"] == "vignette_dark":
            video = ffmpeg.filter(video, 'vignette', PI=0.5)
        elif style_config["bg_overlay"] == "dark_gradient":
            video = ffmpeg.filter(video, 'drawbox',
                x=0, y=0, w='iw', h='ih',
                color='black@0.4', thickness='fill')
        elif style_config["bg_overlay"] == "subtle_overlay":
            video = ffmpeg.filter(video, 'drawbox',
                x=0, y=0, w='iw', h='ih',
                color='black@0.2', thickness='fill')
        font_size = calculate_optimal_font_size(
            title_text,
            style_config["font_size_range"][0],
            style_config["font_size_range"][1])
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
        video = ffmpeg.filter(video, 'drawtext',
            textfile='thumb_pro_text.txt',
            fontfile=font_path.replace('\\', '/'),
            fontcolor=colors["text"], fontsize=font_size,
            bordercolor=colors["shadow"], borderw=border_width,
            box=1, boxcolor=colors["box"], boxborderw=15,
            x='(w-text_w)/2', y=y_position,
            line_spacing=15, text_align='C')
        ffmpeg.output(video, output_path, vframes=1, qscale=2).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return True, output_path
    except Exception as e:
        return False, str(e)

# =====================================================================
# 📌 NICHE-BASED VOICE FX AUTO-MATCH SYSTEM
# =====================================================================

NICHE_VOICE_FX_MAP = {
    "👻 Horror / Creepypasta": {
        "primary": ["👻 Deep & Chilling (Horror)", "👹 Demon / Monster", "🤫 ASMR / Whisper", "⛰️ Deep Cave Echo"],
        "description": "ကြောက်စရာ၊ သည်းထိတ်ရင်ဖိုဇာတ်လမ်းများအတွက်"
    },
    "💔 Reddit Relationship Drama": {
        "primary": ["🎙️ Epic Trailer Voice", "🏛️ Cinematic Reverb", "📞 Old Telephone"],
        "description": "Relationship ဇာတ်လမ်းများအတွက် ခံစားချက်ပါသော အသံ"
    },
    "🧠 Dark Psychology": {
        "primary": ["🤫 ASMR / Whisper", "👻 Deep & Chilling (Horror)", "🌊 Underwater / Muffled"],
        "description": "စိတ်ပညာ၊ လျှို့ဝှက်ဆန်းကြယ် အကြောင်းအရာများအတွက်"
    },
    "💡 Fun Facts / Trivia": {
        "primary": ["🔥 Deep & Energetic (Motivation)", "📻 Walkie-Talkie", "🎙️ Epic Trailer Voice"],
        "description": "ပျော်စရာ၊ စိတ်ဝင်စားစရာ အကြောင်းအရာများအတွက်"
    },
    "🚀 Motivation / Mindset": {
        "primary": ["🔥 Deep & Energetic (Motivation)", "🎙️ Epic Trailer Voice", "🏛️ Cinematic Reverb"],
        "description": "စိတ်ဓာတ်တက်ကြွစေသော၊ အားပေးစကားများအတွက်"
    },
    "📜 Ancient History / Myths": {
        "primary": ["🏛️ Cinematic Reverb", "⛰️ Deep Cave Echo", "👻 Deep & Chilling (Horror)"],
        "description": "သမိုင်း၊ ဒဏ္ဍာရီဇာတ်လမ်းများအတွက်"
    }
}

DUBBING_VOICE_FX_MAP = {
    "Normal (ပုံမှန်အညွှန်း)": {
        "primary": ["🎙️ Epic Trailer Voice", "🏛️ Cinematic Reverb"]
    },
    "Slang (လူငယ်သုံး/Gen-Z)": {
        "primary": ["🔥 Deep & Energetic (Motivation)", "📻 Walkie-Talkie"]
    },
    "Comedy (ဟာသပြောင်ချော်ချော်)": {
        "primary": ["🤖 Robot / Cyborg", "📞 Old Telephone"]
    },
    "Suspense (သည်းထိတ်ရင်ဖို)": {
        "primary": ["👻 Deep & Chilling (Horror)", "🤫 ASMR / Whisper", "⛰️ Deep Cave Echo"]
    }
}

def get_recommended_fx_for_niche(niche, mode="faceless"):
    if mode == "dubbing":
        fx_map = DUBBING_VOICE_FX_MAP
    else:
        fx_map = NICHE_VOICE_FX_MAP
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

# --- 1. THEME & STYLING ---
st.set_page_config(page_title="AETHER STUDIO V52", layout="wide", page_icon="🎬")

st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Montserrat:wght@500;700;800;900&display=swap');
    .stApp { background-color: #0b0f19 !important; background-image: radial-gradient(circle at top, #161b2e 0%, #0b0f19 60%) !important; color: #cbd5e1 !important; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #0d111c !important; border-right: 1px solid rgba(255, 255, 255, 0.05) !important; }
    h1, h2, h3, h4 { font-family: 'Montserrat', sans-serif !important; color: #f8fafc !important; font-weight: 700 !important; }
    p, span, label, .stRadio label, .stCheckbox label, .stSelectbox label { color: #94a3b8 !important; font-size: 14px; }
    .main-title { text-align: center; font-family: 'Montserrat', sans-serif; font-size: 3.5rem !important; font-weight: 900; background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 20px; margin-bottom: 5px; letter-spacing: -1px; text-shadow: 0px 10px 30px rgba(129, 140, 248, 0.2); }
    .sub-title { text-align: center; color: #64748b; font-family: 'Inter', sans-serif; font-size: 1.1rem; font-weight: 500; margin-bottom: 40px; letter-spacing: 3px; text-transform: uppercase; }
    .stTextInput input, div[data-baseweb="select"], .stTextArea textarea { background-color: #151b2b !important; color: #f1f5f9 !important; border: 1px solid #334155 !important; border-radius: 8px !important; transition: all 0.3s ease; }
    .setting-panel { background: #111624; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); }
    .stButton>button { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important; color: #ffffff !important; font-family: 'Montserrat', sans-serif !important; font-weight: 700 !important; font-size: 16px !important; border-radius: 8px !important; border: none !important; width: 100%; padding: 16px !important; transition: all 0.3s ease !important; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3); }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5); }
    .sub-box { background-color: #1a2235; border: 1px solid rgba(129, 140, 248, 0.3); border-radius: 8px; padding: 20px; margin-top: 15px; margin-bottom: 10px; }
    .deepseek-badge { background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; margin-left: 10px; }
    .hook-preview { background: #0d111c; border: 2px solid #38bdf8; border-radius: 10px; padding: 15px; margin: 10px 0; text-align: center; }
    </style>
''', unsafe_allow_html=True)

# State initialization
if "render_success" not in st.session_state: st.session_state.render_success = False
if "generated_script" not in st.session_state: st.session_state.generated_script = ""
if "original_transcript" not in st.session_state: st.session_state.original_transcript = ""
if "viral_title" not in st.session_state: st.session_state.viral_title = ""
if "viral_tags" not in st.session_state: st.session_state.viral_tags = ""
if "thumb_path_A" not in st.session_state: st.session_state.thumb_path_A = None
if "thumb_path_B" not in st.session_state: st.session_state.thumb_path_B = None
if "viral_score" not in st.session_state: st.session_state.viral_score = ""
if "final_video_path" not in st.session_state: st.session_state.final_video_path = ""
if "sync_offset" not in st.session_state: st.session_state.sync_offset = 0.0
if "whisper_data" not in st.session_state: st.session_state.whisper_data = None
if "tiktok_hook_text" not in st.session_state: st.session_state.tiktok_hook_text = ""
if "fc_hook_text" not in st.session_state: st.session_state.fc_hook_text = ""

# =====================================================================
# 📌 SYNC ENGINE - Precision Sync System
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
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def time_str_to_seconds_sync(t_str):
    t_str = t_str.replace(',', '.')
    parts = t_str.split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0

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
    effective_duration = audio_duration - 0.3
    if effective_duration <= 0:
        effective_duration = audio_duration
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
            end_time = start_time + chunk_duration
            end_time = min(end_time, audio_duration)
            if end_time <= start_time:
                end_time = start_time + min_chunk_duration
            start_time = max(0, start_time)
            srt_entries.append({
                'index': chunk_index, 'start': start_time,
                'end': end_time, 'text': chunk_text
            })
            chunk_index += 1
            char_position += chunk_chars
    srt_text = ""
    for entry in srt_entries:
        srt_text += f"{entry['index']}\n{fmt_timestamp_sync(entry['start'])} --> {fmt_timestamp_sync(entry['end'])}\n{entry['text']}\n\n"
    parsed = [(e['start'], e['end'], e['text']) for e in srt_entries]
    return srt_text, parsed

def sync_with_whisper_word_timestamps(clean_script, whisper_data, audio_duration, words_per_chunk=8, min_chunk_duration=1.2, offset=0.0):
    clean_script = strip_audio_tags(clean_script)
    if not clean_script.strip():
        return sync_by_character_mapping(clean_script, audio_duration, words_per_chunk, min_chunk_duration, offset)
    whisper_words = []
    if isinstance(whisper_data, dict):
        if whisper_data.get('words'):
            whisper_words = whisper_data['words']
        elif whisper_data.get('segments'):
            for seg in whisper_data['segments']:
                if isinstance(seg, dict) and seg.get('words'):
                    whisper_words.extend(seg['words'])
    elif hasattr(whisper_data, 'words') and whisper_data.words:
        whisper_words = whisper_data.words
    elif hasattr(whisper_data, 'segments') and whisper_data.segments:
        for seg in whisper_data.segments:
            seg_words = getattr(seg, 'words', []) or []
            whisper_words.extend(seg_words)
    if not whisper_words or len(whisper_words) < 3:
        return sync_by_character_mapping(clean_script, audio_duration, words_per_chunk, min_chunk_duration, offset)
    script_words = clean_script.split()
    total_script_words = len(script_words)
    total_whisper_words = len(whisper_words)
    srt_entries = []
    chunk_index = 1
    for i in range(0, total_script_words, words_per_chunk):
        chunk_words = script_words[i:i + words_per_chunk]
        chunk_text = ' '.join(chunk_words)
        start_script_idx = i
        end_script_idx = min(i + len(chunk_words) - 1, total_script_words - 1)
        if total_script_words > 0:
            start_whisper_idx = int((start_script_idx / total_script_words) * total_whisper_words)
            end_whisper_idx = int((end_script_idx / total_script_words) * total_whisper_words)
        else:
            start_whisper_idx = 0
            end_whisper_idx = 0
        start_whisper_idx = max(0, min(start_whisper_idx, total_whisper_words - 1))
        end_whisper_idx = max(0, min(end_whisper_idx, total_whisper_words - 1))
        w_start = whisper_words[start_whisper_idx]
        w_end = whisper_words[end_whisper_idx]
        if isinstance(w_start, dict):
            start_time = w_start['start'] + offset
        else:
            start_time = w_start.start + offset
        if isinstance(w_end, dict):
            end_time = w_end['end'] + offset
        else:
            end_time = w_end.end + offset
        if end_time - start_time < min_chunk_duration:
            end_time = start_time + min_chunk_duration
        start_time = max(0, start_time)
        end_time = min(end_time, audio_duration)
        if end_time <= start_time:
            end_time = start_time + min_chunk_duration
        srt_entries.append({
            'index': chunk_index, 'start': start_time,
            'end': end_time, 'text': chunk_text
        })
        chunk_index += 1
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
    if whisper_data is not None:
        try:
            srt_text, parsed = sync_with_whisper_word_timestamps(
                clean_script, whisper_data, audio_duration,
                words_per_chunk, min_chunk_duration, sync_offset
            )
            if parsed and len(parsed) > 0:
                return srt_text, parsed
        except Exception:
            pass
    srt_text, parsed = sync_by_character_mapping(
        clean_script, audio_duration,
        words_per_chunk, min_chunk_duration, sync_offset
    )
    return srt_text, parsed

# =====================================================================
# --- 2. CORE AUTOMATION FLOW ENGINES ---
# =====================================================================

def cleanup_temp_files():
    for f in os.listdir("."):
        if f.startswith(("fc_clip_", "fc_img_", "raw_fc_clip_", "temp_", "subtitles.", "thumb_", "FACELESS_FINAL_", "AETHER_RECAP_FINAL_", "fc_audio.wav", "fc_video_loop.mp4", "hook_text.txt", "thumb_pro_text.txt", "thumb_text.txt")):
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
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True, 'no_warnings': True, 'nocheckcertificate': True,
        'ffmpeg_location': FFMPEG_BINARY, 'source_address': '0.0.0.0',
        'extractor_args': {'youtube': {'player_client': ['tv', 'ios', 'web']}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        raise Exception(f"YouTube Download Error: {str(e)}")

def extract_audio_fast(video_in, audio_out="temp_extracted.mp3"):
    if os.path.exists(audio_out):
        os.remove(audio_out)
    try:
        (ffmpeg.input(video_in).output(audio_out, acodec='libmp3lame', ac=1, ar='16000')
         .run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True))
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
    last_tts_error = "Unknown Network or API Error"
    for i, chunk_text in enumerate(chunks):
        if not chunk_text.strip():
            continue
        c_out = f"temp_tts_chunk_{i}.wav" if ("Synergy" in engine or "ElevenLabs" in engine) else f"temp_tts_chunk_{i}.mp3"
        if "Synergy" in engine:
            keys_list = [k.strip() for k in gemini_key.split(",") if k.strip()]
            voice_name = "Puck" if "Puck" in voice_model else ("Charon" if "Charon" in voice_model else "Aoede")
            prompt_text = "You are a professional Burmese movie narrator. Read the following text naturally. " + chunk_text
            payload = {"contents": [{"parts": [{"text": prompt_text}]}], "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}}}}
            success = False
            for current_key in keys_list:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={current_key}"
                try:
                    res = requests.post(url, json=payload, timeout=60)
                    if res.status_code == 200:
                        candidate = res.json().get("candidates", [{}])[0]
                        if candidate.get("finishReason") != "SAFETY" and "content" in candidate:
                            pcm_data = base64.b64decode(candidate["content"]["parts"][0]["inlineData"]["data"])
                            with wave.open(c_out, "wb") as wf:
                                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000); wf.writeframes(pcm_data)
                            success = True; break
                        else:
                            last_tts_error = "Safety Blocked or Empty Content generated."
                    else:
                        last_tts_error = f"API Error {res.status_code}: {res.text[:100]}"
                except Exception as e:
                    last_tts_error = str(e)
            if not success:
                continue
        elif "ElevenLabs" in engine:
            voice_id = custom_eleven_id.strip() if custom_eleven_id else ("21m00Tcm4TlvDq8ikWAM" if "Male" in voice_model else "AZnzlk1XvdvUeBnXmlld")
            res = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", json={"text": chunk_text, "model_id": "eleven_multilingual_v2"}, headers={"xi-api-key": eleven_key}, timeout=60)
            if res.status_code == 200:
                with open(c_out, "wb") as f:
                    f.write(res.content)
            else:
                last_tts_error = f"ElevenLabs API Error: {res.text[:100]}"
        else:
            voice = "my-MM-ThihaNeural" if "Male" in voice_model else "my-MM-NilarNeural"
            try:
                await edge_tts.Communicate(chunk_text, voice).save(c_out)
            except Exception as e:
                last_tts_error = str(e)
        if os.path.exists(c_out):
            chunk_files.append(c_out)
    if not chunk_files:
        raise Exception(f"TTS Generation Failed. Reason: {last_tts_error}")
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
        if "Epic" in voice_fx: audio = audio.filter('bass', g=12, f=120)
        elif "Walkie-Talkie" in voice_fx: audio = audio.filter('highpass', f=400).filter('lowpass', f=3000).filter('volume', 1.5)
        elif "Reverb" in voice_fx: audio = audio.filter('aecho', 0.8, 0.88, 60, 0.4)
        elif "Demon" in voice_fx: audio = audio.filter('bass', g=15, f=100).filter('aecho', 0.8, 0.88, 40, 0.5)
        elif "ASMR" in voice_fx: audio = audio.filter('treble', g=12, f=6000).filter('volume', 1.5)
        elif "Robot" in voice_fx: audio = audio.filter('aphaser', type='t', speed=2, decay=0.6).filter('volume', 1.2)
        elif "Telephone" in voice_fx: audio = audio.filter('highpass', f=300).filter('lowpass', f=2500).filter('compand', attacks='0', decays='0.2', points='-70/-70|-20/-20|0/-10')
        elif "Cave" in voice_fx: audio = audio.filter('aecho', 0.8, 0.9, 1000, 0.3)
        elif "Underwater" in voice_fx: audio = audio.filter('lowpass', f=400).filter('volume', 1.5)
        elif "Deep & Energetic (Motivation)" in voice_fx: audio = audio.filter('bass', g=10, f=150).filter('treble', g=5, f=3000).filter('volume', 1.5)
        elif "Deep & Chilling (Horror)" in voice_fx: audio = audio.filter('bass', g=15, f=80).filter('aecho', 0.8, 0.85, 60, 0.3).filter('volume', 1.2)
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
        if use_bypass: video = ffmpeg.filter(video, 'scale', '2*trunc(iw*1.08/2)', '2*trunc(ih*1.08/2)').filter('crop', 'iw/1.08', 'ih/1.08')
        if use_mirror: video = ffmpeg.filter(video, 'hflip')
        if use_color: video = ffmpeg.filter(video, 'eq', brightness=0.02, contrast=1.05, saturation=1.1)
        if use_grain: video = ffmpeg.filter(video, 'noise', alls=2, allf='t+u')
        if use_fps: video = ffmpeg.filter(video, 'fps', fps=24, round='near')
        if use_freeze: video = ffmpeg.filter(video, 'minterpolate', fps=12, mi_mode='dup')
        audio = ffmpeg.input(in_a).audio
        if use_blur: video = ffmpeg.filter(video, 'drawbox', x=0, y='ih-90', w='iw', h=90, color='black@0.95', thickness='fill')
        if watermark: video = ffmpeg.filter(video, 'drawtext', text=watermark, x='w-tw-15', y='15', fontsize=30, fontcolor='white@0.5')
        if logo_path and os.path.exists(logo_path):
            logo = ffmpeg.input(logo_path)
            logo = ffmpeg.filter(logo, 'scale', -1, 80)
            video = ffmpeg.overlay(video, logo, x='W-w-20', y=20)
        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"] and parsed_timestamps:
            wrap_width = 25 if "9:16" in ratio else 45
            safe_font_path = font_path.replace('\\', '/')
            for i, (start, end, text) in enumerate(parsed_timestamps):
                wrapped_lines = textwrap.wrap(text, width=wrap_width)
                if not wrapped_lines: wrapped_lines = [text]
                max_len = max(len(line) for line in wrapped_lines)
                centered_text = "\n".join(line.center(max_len, " ") for line in wrapped_lines)
                txt_filename = f"temp_sub_{i}.txt"
                with open(txt_filename, "w", encoding="utf-8") as tf:
                    tf.write(centered_text)
                if "Center" in sub_position: y_expr = "(h-text_h)/2"
                elif "Top" in sub_position: y_expr = "150"
                else: y_expr = "h-text_h-150"
                c_str = "yellow"
                if "White" in sub_color: c_str = "white"
                elif "Green" in sub_color: c_str = "green"
                elif "Red" in sub_color: c_str = "red"
                elif "Gold" in sub_color: c_str = "gold"
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
    st.markdown("### 🎯 Subtitle Sync Control")
    st.session_state.sync_offset = st.slider("Sync Offset (seconds)", min_value=-5.0, max_value=5.0, value=0.0, step=0.1, help="စာတန်းထိုး စောလွန်း/နောက်ကျလွန်းရင် ညှိပါ။ (-) ဆိုရင် စာတန်းထိုး စောမယ်။ (+) ဆိုရင် နောက်ကျမယ်။")
    st.caption(f"Current Offset: {st.session_state.sync_offset:+.1f}s")
    st.markdown("---")
    st.markdown("### 💾 Project Save & Load")
    if st.button("Save Current Project"):
        proj_data = {"script": st.session_state.generated_script, "title": st.session_state.viral_title, "tags": st.session_state.viral_tags, "sync_offset": st.session_state.sync_offset, "hook_text": st.session_state.tiktok_hook_text}
        json_str = json.dumps(proj_data, ensure_ascii=False)
        b64 = base64.b64encode(json_str.encode('utf-8')).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="Aether_Project.json" style="color:#38bdf8; font-weight:bold;">📥 Download Project File (.json)</a>'
        st.markdown(href, unsafe_allow_html=True)
    uploaded_proj = st.file_uploader("Upload Project", type=["json"])
    if uploaded_proj:
        try:
            data = json.load(uploaded_proj)
            st.session_state.generated_script = data.get("script", "")
            st.session_state.viral_title = data.get("title", "")
            st.session_state.viral_tags = data.get("tags", "")
            st.session_state.sync_offset = data.get("sync_offset", 0.0)
            st.session_state.tiktok_hook_text = data.get("hook_text", "")
            st.success("✅ Project Loaded!")
        except Exception:
            st.error("Invalid Project File.")
    st.markdown("---")
    ai_provider = st.selectbox("Choose AI Provider", ["Google Gemini (Flash - Recommended)", "DeepSeek V3 (Free - Best Burmese)", "OpenAI (GPT-5.5 Pro)", "Groq API (Fast & Free)"])
    saved_gemini = load_key(API_KEY_FILE)
    saved_deepseek = load_key(DEEPSEEK_KEY_FILE)
    saved_groq = load_key(GROQ_KEY_FILE)
    saved_openai = load_key(OPENAI_KEY_FILE)
    if "Gemini" in ai_provider:
        api_key_input = st.text_input("Gemini Keys (Comma separated)", type="password", value=saved_gemini)
        if api_key_input and api_key_input != saved_gemini: save_key(API_KEY_FILE, api_key_input)
    elif "DeepSeek" in ai_provider:
        api_key_input = st.text_input("DeepSeek API Key (Free - Get at platform.deepseek.com)", type="password", value=saved_deepseek, help="DeepSeek V3 က အခမဲ့ပါ။ platform.deepseek.com မှာ အကောင့်ဖွင့်ပြီး API Key ယူပါ။")
        if api_key_input and api_key_input != saved_deepseek: save_key(DEEPSEEK_KEY_FILE, api_key_input)
        st.caption('<span class="deepseek-badge">🆓 FREE TIER</span>', unsafe_allow_html=True)
        st.caption("📊 Daily Limit: 100 requests | Rate: 50/min | Model: deepseek-chat (V3)")
    elif "Groq" in ai_provider:
        api_key_input = st.text_input("Groq API Key", type="password", value=saved_groq)
        if api_key_input and api_key_input != saved_groq: save_key(GROQ_KEY_FILE, api_key_input)
    else:
        api_key_input = st.text_input("OpenAI API Key", type="password", value=saved_openai)
        if api_key_input and api_key_input != saved_openai: save_key(OPENAI_KEY_FILE, api_key_input)
    if app_mode == "🎙️ Faceless Channel Studio":
        st.markdown("---")
        st.markdown("### 🔑 Additional API Keys")
        saved_groq_fc = load_key(GROQ_KEY_FILE)
        groq_key_fc = st.text_input("Groq API Key (For Accurate Whisper Sync)", type="password", value=saved_groq_fc)
        if groq_key_fc and groq_key_fc != saved_groq_fc: save_key(GROQ_KEY_FILE, groq_key_fc)

# =====================================================================
# 📌 MODE 1 - MOVIE DUBBING (with Professional Thumbnails + Niche FX)
# =====================================================================
if app_mode == "🎙️ Movie Dubbing Studio":
    with st.sidebar:
        st.markdown("---")
        audio_engine_choice = st.radio("Voice Engine", ["Edge-TTS (Default Free)", "Google Synergy TTS (Flash 3.1 Preview)", "ElevenLabs (Premium AI)", "TTSMaker (Free API)"])
        if "Synergy" in audio_engine_choice: synergy_key = st.text_input("API Key for Synergy TTS", type="password", value=saved_gemini)
        if "ElevenLabs" in audio_engine_choice:
            saved_eleven = load_key(ELEVEN_KEY_FILE)
            eleven_key_input = st.text_input("ElevenLabs API Key", type="password", value=saved_eleven)
            if eleven_key_input and eleven_key_input != saved_eleven: save_key(ELEVEN_KEY_FILE, eleven_key_input)
            saved_voice_id = load_key(ELEVEN_VOICE_ID_FILE)
            custom_eleven_id = st.text_input("Custom Voice ID", value=saved_voice_id)
            if custom_eleven_id and custom_eleven_id != saved_voice_id: save_key(ELEVEN_VOICE_ID_FILE, custom_eleven_id)
        key_ttsmaker = st.text_input("TTSMaker API Key", type="password") if "TTSMaker" in audio_engine_choice else ""
        st.markdown("---")
        video_ratio = st.selectbox("Crop Ratio", ["Original", "9:16 (TikTok/Shorts)", "16:9 (YouTube)"])
        st.markdown("<b>🛡️ Anti-Copyright Options</b>", unsafe_allow_html=True)
        cb_bypass = st.checkbox("🔍 Smart Zoom", value=True)
        cb_mirror = st.checkbox("🪞 Mirror Effect", value=False)
        cb_color = st.checkbox("🎨 Color Tweaks", value=False)
        cb_grain = st.checkbox("🎞️ Subtle Film Grain", value=False)
        cb_fps = st.checkbox("🎬 Cinematic 24 FPS", value=False)
        cb_freeze = st.checkbox("❄️ Freeze Frame (Stop-Motion Bypass)", value=False)
        st.markdown("<b>🎬 Visual & Subs</b>", unsafe_allow_html=True)
        cb_blur = st.checkbox("👁️ Cinematic Black Mask", value=True)
        st.markdown("<b>©️ Brand Watermark</b>", unsafe_allow_html=True)
        uploaded_logo = st.file_uploader("🖼️ Add Logo Image (Top Right)", type=["png", "jpg", "jpeg"])
        use_text_watermark = st.checkbox("✍️ Use Text Watermark instead", value=False)
        watermark_text = st.text_input("Text Watermark", "") if use_text_watermark else ""
        subtitle_mode = st.radio("Subtitle Output", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"])
        st.markdown("---")
        st.markdown("<b>🖼️ Professional Thumbnail Settings</b>", unsafe_allow_html=True)
        thumbnail_style = st.selectbox("Thumbnail Style", list(THUMBNAIL_STYLES.keys()), index=0, help="Thumbnail ဒီဇိုင်း ပုံစံရွေးပါ")

    st.markdown('<div class="setting-panel"><h3>📺 Media Acquisition & Setup</h3>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        video_url = st.text_input("🔗 Paste Short Drama URL Link", placeholder="https://...")
        uploaded_file = st.file_uploader("📥 OR Upload Video File (MP4)", type=["mp4"])
        st.markdown("<br><div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #38bdf8; font-size: 16px;'>✍️ AI Storytelling & Script Rules</p>", unsafe_allow_html=True)
        recap_mode = st.radio("🎬 Recap Mode", ["Translate Original Video (မူရင်းကို ဘာသာပြန်မည်)", "Create Original AI Story (ကိုယ်ပိုင်ဇာတ်လမ်းဖန်တီးမည်)"])
        script_style = st.selectbox("🎭 Script Style (ဇာတ်ညွှန်း ပုံစံ)", ["Normal (ပုံမှန်အညွှန်း)", "Slang (လူငယ်သုံး/Gen-Z)", "Comedy (ဟာသပြောင်ချော်ချော်)", "Suspense (သည်းထိတ်ရင်ဖို)"])
        script_hook = st.checkbox("🪝 3-Second Viral Hook (အစချီ ဆွဲဆောင်မည်)", value=True)
        script_curiosity = st.checkbox("🤯 Curiosity Gaps (စိတ်ဝင်စားမှု အရှိန်တင်မည်)", value=True)
        script_tone = st.checkbox("🎭 Emotion & Tone (ဇာတ်ကောင်စရိုက် သွင်းမည်)", value=True)
        script_cta = st.checkbox("💬 Call to Action (Commentခေါ်မည်)", value=False)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #10b981; font-size: 16px;'>🎵 Audio Mixing & Auto-Ducking</p>", unsafe_allow_html=True)
        bgm_options = ["None (BGM မထည့်ပါ)"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files: bgm_options.insert(1, "🤖 Auto (Random Select)"); bgm_options.extend(bgm_files)
        selected_bgm = st.selectbox("🎼 Background Music", bgm_options)
        bgm_volume = st.slider("🔊 BGM Volume", 1, 50, 10) / 100.0
        st.markdown("</div>", unsafe_allow_html=True)
    with col_in2:
        dynamic_options = ["Synergy Puck (Male)", "Synergy Aoede (Female)", "Synergy Charon (Male - Deep)"] if "Synergy" in audio_engine_choice else (["Adam (Male Deep)", "Rachel (Female)"] if "ElevenLabs" in audio_engine_choice else (["TTSMaker Male", "TTSMaker Female"] if "TTSMaker" in audio_engine_choice else ["ဇော်ဇော် (Male)", "အောင်အောင် (Deep)", "နှင်းနှင်း (Female)"]))
        voice_char = st.selectbox("Select Character Voice", dynamic_options, index=0)
        pitch_level = st.slider("🎙️ Voice Pitch (Frequency Adjust)", min_value=-30, max_value=30, value=0, step=5)
        recommended_fx_dub = get_recommended_fx_for_niche(script_style, mode="dubbing")
        fx_level = st.selectbox("🎧 Cinematic Voice FX (Style အလိုက် အကြံပြု)", recommended_fx_dub, index=0, help=f"🎯 {script_style} အတွက် အကြံပြုထားသော FX")
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #818cf8; font-size: 16px;'>📝 Subtitle Pro Settings</p>", unsafe_allow_html=True)
        if subtitle_mode in ["Both (Burn + SRT)", "Burn into Video"]:
            selected_font = st.selectbox("🔤 Font Style", available_fonts, index=0)
            sub_position = st.selectbox("📍 Position", ["Bottom", "Center", "Top"])
            sub_color = st.selectbox("🎨 Color", ["Yellow Text", "White Text", "Neon Green Text", "Red Text", "Gold Text"])
            sub_size = st.slider("🔠 Font Size", 16, 50, 28)
            sub_thickness = st.slider("✒️ Outline Thickness", 1.0, 5.0, 2.5)
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                sub_bg = st.checkbox("🔲 Background Box", value=True)
                sub_short = st.checkbox("✂️ Short & Punchy (Hormozi)")
        else:
            st.info("💡 Burn into Video ရွေးထားမှ ချိန်ညှိနိုင်ပါမည်။")
            selected_font, sub_position, sub_color, sub_size, sub_thickness, sub_bg, sub_short = "Padauk.ttf", "Bottom", "Yellow", 28, 2.5, True, False
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 START ONE-CLICK WORKFLOW MONETIZE GENERATOR"):
        if not api_key_input: st.error("⚠️ API Key လိုအပ်ပါသည်။")
        elif not uploaded_file and not video_url: st.error("⚠️ ဗီဒီယိုဖိုင်သို့မဟုတ် Link ထည့်ပေးပါ။")
        else:
            st.session_state.render_success = False
            st.session_state.whisper_data = None
            cleanup_temp_files()
            run_id = str(int(time.time()))
            v_final = f"AETHER_RECAP_FINAL_{run_id}.mp4"
            st.session_state.final_video_path = v_final
            v_input, a_extracted, a_generated, srt_final = "input_temp.mp4", "temp_extracted.mp3", "voice_temp.wav", "subtitles.srt"
            pbar = st.progress(0, text="🚀 အလုပ်စတင်နေပါပြီ...")
            with st.spinner("⏳ [အဆင့်၁/၆] ဗီဒီယို ဖိုင်အားစနစ်ထဲသို့ ဆွဲသွင်းနေပါသည်..."):
                pbar.progress(10, text="📥 [အဆင့် ၁/၆] ဗီဒီယိုဆွဲယူနေပါသည်...")
                try:
                    if uploaded_file:
                        with open(v_input, "wb") as f: f.write(uploaded_file.read())
                    else: download_video_from_url(video_url, v_input)
                except Exception as dl_err: st.error(str(dl_err)); st.stop()
                extract_audio_fast(v_input, a_extracted)
            groq_key_sync = load_key(GROQ_KEY_FILE)
            if groq_key_sync:
                try:
                    with open(a_extracted, "rb") as file:
                        client_groq = Groq(api_key=groq_key_sync)
                        st.session_state.whisper_data = client_groq.audio.transcriptions.create(file=(a_extracted, file.read()), model="whisper-large-v3", response_format="verbose_json", timestamp_granularities=["word"])
                        st.success("✅ Whisper အသံဖမ်းယူမှု အောင်မြင်ပါသည်။ Sync တိကျမှု ပိုကောင်းပါမည်။")
                except Exception as e: st.warning(f"⚠️ Whisper Sync မအောင်မြင်ပါ။ Character-Level Sync ဖြင့် ဆက်လက်မည်။ Error: {str(e)[:100]}")
            with st.spinner(f"⏳ [အဆင့်၂/၆] {ai_provider} ဖြင့် ဇာတ်ညွှန်း၊ Title နှင့် Thumbnail ထုတ်လုပ်နေပါသည်..."):
                pbar.progress(30, text=f"🤖 [အဆင့် ၂/၆] ဇာတ်ညွှန်း၊ Title နှင့် Hashtagsဖန်တီးနေပါသည်...")
                try:
                    extra_rules = ""
                    if script_hook: extra_rules += " [HOOK]: Start with an extremely engaging 3-second viral hook."
                    if "Slang" in script_style: extra_rules += " [SLANG]: Use modern Myanmar internet slang and Gen-Z conversational tone."
                    elif "Comedy" in script_style: extra_rules += " [COMEDY]: Make the narrative highly comedic, sarcastic, and funny."
                    elif "Suspense" in script_style: extra_rules += " [SUSPENSE]: Make the storytelling dramatic, fast-paced, and full of suspense."
                    if script_curiosity: extra_rules += " [CURIOSITY]: Insert curiosity gaps in the middle to retain audience attention."
                    if script_tone: extra_rules += " [TONE]: Inject strong emotions and character tones matching the scene."
                    if script_cta: extra_rules += " [CTA]: End the script with a strong Call to Action asking a question."
                    extra_rules += "\nAt the absolute end of the response, you MUST include these two lines on separate lines:\n[TITLE: (Provide a viral Burmese title here)]\n[TAGS: #tag1 #tag2]"
                    hormozi_rule = " [HORMOZI]: Split the subtitles into chunks of ONLY 1 to 4 words max per block. CRITICAL: DO NOT remove original timestamps." if sub_short else ""

                    # ===== AI SCRIPT GENERATION WITH FALLBACK =====
                    if "DeepSeek" in ai_provider:
                        try:
                            if "Original" in recap_mode:
                                deepseek_prompt = f"""Create a HIGHLY ENGAGING, completely ORIGINAL storytelling recap in natural spoken Burmese.
This is for a 3-minute viral TikTok/YouTube video.
STYLE: {script_style}
STRICT RULES:
1. Use natural spoken Burmese (တယ်, တဲ့, မှာ, ရဲ့). NEVER use formal grammar (၌, ၍, သည်).
2. Include audio tags like [pause=1.0], [excited], [whisper].
3. NO English transliteration. PURE BURMESE ONLY.
4. Write in a Gen-Z friendly, conversational tone.
{extra_rules}{hormozi_rule}
CRITICAL: Output ONLY valid SRT format with timestamps. Each subtitle should be 1-3 seconds apart. Total duration approximately {get_file_duration(a_extracted):.0f} seconds."""
                                raw_output_text = deepseek_generate_script(api_key_input, deepseek_prompt)
                            else:
                                with open(a_extracted, "rb") as file:
                                    if load_key(GROQ_KEY_FILE):
                                        client_groq_temp = Groq(api_key=load_key(GROQ_KEY_FILE))
                                        transcription = client_groq_temp.audio.transcriptions.create(file=(a_extracted, file.read()), model="whisper-large-v3", response_format="srt")
                                        english_srt = transcription if isinstance(transcription, str) else str(transcription)
                                    else:
                                        english_srt = "[No transcription available - generating original story]"
                                raw_output_text = deepseek_translate_and_srt(api_key_input, english_srt, extra_rules + hormozi_rule)
                        except Exception as ds_err:
                            st.warning(f"⚠️ DeepSeek Failed: {str(ds_err)[:150]}")
                            if saved_gemini:
                                st.info("🔄 Auto-switching to Gemini...")
                                keys_list_fb = [k.strip() for k in saved_gemini.split(",") if k.strip()]
                                raw_output_text = ""
                                for current_key in keys_list_fb:
                                    try:
                                        client = genai.Client(api_key=current_key)
                                        target_file = v_input if "Original" in recap_mode else a_extracted
                                        media_file = client.files.upload(file=target_file)
                                        while "PROCESSING" in str(client.files.get(name=media_file.name).state): time.sleep(2)
                                        gemini_prompt = f"Watch the provided video carefully..." if "Original" in recap_mode else f"Listen to the audio..."
                                        response = client.models.generate_content(model="gemini-2.5-flash", contents=[media_file, gemini_prompt])
                                        raw_output_text = response.text.strip()
                                        client.files.delete(name=media_file.name)
                                        break
                                    except Exception: continue
                                if not raw_output_text: st.error("❌ Both DeepSeek and Gemini failed."); st.stop()
                            else: st.error(f"❌ DeepSeek failed and no fallback available."); st.stop()
                    elif "Gemini" in ai_provider:
                        keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                        success_gemini = False; last_err = ""
                        for current_key in keys_list:
                            try:
                                client = genai.Client(api_key=current_key)
                                target_file = v_input if "Original" in recap_mode else a_extracted
                                media_file = client.files.upload(file=target_file)
                                while "PROCESSING" in str(client.files.get(name=media_file.name).state): time.sleep(2)
                                gemini_prompt = f"Watch the provided video carefully..." if "Original" in recap_mode else f"Listen to the audio..."
                                response = client.models.generate_content(model="gemini-2.5-flash", contents=[media_file, gemini_prompt])
                                raw_output_text = response.text.strip()
                                client.files.delete(name=media_file.name)
                                success_gemini = True; break
                            except Exception as e: last_err = str(e); continue
                        if not success_gemini: raise Exception(f"Gemini API Error: {last_err}")
                    else:
                        client = Groq(api_key=api_key_input) if "Groq" in ai_provider else openai
                        if "Groq" in ai_provider:
                            with open(a_extracted, "rb") as file:
                                transcription = client.audio.translations.create(file=(a_extracted, file.read()), model="whisper-large-v3", response_format="verbose_json")
                            tsrt = "".join([f"{i}\n00:00:00,000 --> 00:00:10,000\n{seg['text']}\n\n" for i, seg in enumerate(transcription.get('segments', []), 1)]) if isinstance(transcription, dict) else str(transcription)
                        else:
                            openai.api_key = api_key_input
                            with open(a_extracted, "rb") as file: tsrt = openai.audio.translations.create(model="whisper-1", file=file, response_format="srt")
                        base_prompt = f"Translate and adapt the English SRT into engaging Burmese. Add audio tags. Output valid SRT format. {extra_rules}{hormozi_rule}"
                        comp = client.chat.completions.create(model="llama-3.3-70b-versatile" if "Groq" in ai_provider else ("gpt-5.5-pro" if "5.5" in ai_provider else "gpt-4o"), messages=[{"role": "user", "content": f"{base_prompt} --- SRT --- {tsrt}"}])
                        raw_output_text = comp.choices[0].message.content

                    title_match = re.search(r'\[TITLE:\s*(.*?)\]', raw_output_text, re.IGNORECASE)
                    tags_match = re.search(r'\[TAGS:\s*(.*?)\]', raw_output_text, re.IGNORECASE)
                    st.session_state.viral_title = re.sub(r'[\[\]]', '', title_match.group(1)).strip() if title_match else "Viral Movie Recap"
                    st.session_state.viral_tags = tags_match.group(1).strip() if tags_match else "#movierecap #myanmar"
                    clean_raw_srt = re.sub(r'\[TITLE:.*?\]', '', raw_output_text, flags=re.IGNORECASE)
                    clean_raw_srt = re.sub(r'\[TAGS:.*?\]', '', clean_raw_srt, flags=re.IGNORECASE).strip()
                    marker = chr(96) * 3
                    clean_raw_srt = clean_raw_srt.replace(f"{marker}srt", "").replace(marker, "")
                    audio_dur = get_file_duration(a_extracted)
                    script_for_sync = strip_audio_tags(clean_raw_srt)
                    if "-->" in clean_raw_srt:
                        parsed_timestamps, speech_text = parse_and_save_real_srt(clean_raw_srt, srt_final, use_fade=False)
                        if st.session_state.sync_offset != 0:
                            parsed_timestamps = [(max(0, s + st.session_state.sync_offset), max(0.8, e + st.session_state.sync_offset), t) for s, e, t in parsed_timestamps]
                    else:
                        sync_srt, sync_parsed = smart_sync_pipeline(script_for_sync, a_extracted, whisper_data=st.session_state.whisper_data, audio_duration=audio_dur, sync_offset=st.session_state.sync_offset, short_punchy=sub_short)
                        with open(srt_final, "w", encoding="utf-8-sig") as f: f.write(sync_srt)
                        parsed_timestamps = sync_parsed
                        speech_text = script_for_sync
                    st.session_state.generated_script = clean_raw_srt
                    # 👇 PROFESSIONAL THUMBNAILS
                    try:
                        t_A = min(get_file_duration(v_input) * 0.2, 10)
                        t_B = min(get_file_duration(v_input) * 0.5, 20)
                        for thumb_suffix, t_val in [("A", t_A), ("B", t_B)]:
                            thumb_name = f"thumb_{thumb_suffix}_{run_id}.jpg"
                            success_thumb, _ = generate_professional_thumbnail(v_input, thumb_name, st.session_state.viral_title, t_val, style=thumbnail_style, font_path=selected_font)
                            if success_thumb:
                                if thumb_suffix == "A": st.session_state.thumb_path_A = thumb_name
                                elif thumb_suffix == "B": st.session_state.thumb_path_B = thumb_name
                    except Exception: pass
                except Exception as e: st.error(f"Logic Error: {e}"); st.stop()
            with st.spinner(f"⏳ [အဆင့်၄/၆] AI Voice Over ထုတ်လုပ်နေပါသည်..."):
                pbar.progress(60, text="🎙️ [အဆင့် ၄/၆] အသံသရုပ်ဆောင်ဖန်တီးနေပါသည်...")
                try: asyncio.run(generate_tts(speech_text if 'speech_text' in locals() and speech_text else strip_audio_tags(st.session_state.generated_script), voice_char, a_generated, engine=audio_engine_choice, ttsmaker_key=key_ttsmaker, eleven_key=locals().get('eleven_key_input', ''), custom_eleven_id=locals().get('custom_eleven_id', ''), gemini_key=locals().get('synergy_key', api_key_input), pitch=pitch_level, voice_fx=fx_level))
                except Exception as e: st.error(f"အသံထုတ်လုပ်ခြင်းမအောင်မြင်ပါ: {e}"); st.stop()
            tts_dur = get_file_duration(a_generated)
            if abs(tts_dur - audio_dur) > 2.0 and 'clean_raw_srt' in locals():
                st.info(f"🔄 TTS ကြာချိန် ({tts_dur:.1f}s) နှင့် မူရင်း ({audio_dur:.1f}s) ကွာနေ၍ Sync ပြန်ညှိပါမည်။")
                try:
                    script_for_sync = strip_audio_tags(clean_raw_srt)
                    sync_srt, sync_parsed = smart_sync_pipeline(script_for_sync, a_generated, whisper_data=st.session_state.whisper_data, audio_duration=tts_dur, sync_offset=st.session_state.sync_offset, short_punchy=sub_short)
                    with open(srt_final, "w", encoding="utf-8-sig") as f: f.write(sync_srt)
                    parsed_timestamps = sync_parsed
                except Exception: pass
            with st.spinner("⏳ [အဆင့်၅/၆] ဗီဒီယိုနှင့် စာတန်းထိုးပေါင်းစပ်နေပါသည်..."):
                pbar.progress(80, text="🎬 [အဆင့် ၅/၆] ဗီဒီယိုနှင့်စာတန်းထိုး ပေါင်းစပ်နေပါသည်...")
                success, err_msg = render_premium_saas_video(v_input, a_generated, parsed_timestamps, v_final, video_ratio, cb_bypass, cb_blur, watermark_text, subtitle_mode, cb_mirror, cb_color, cb_grain, cb_fps, sub_position=sub_position, sub_color=sub_color, sub_size=sub_size, sub_thickness=sub_thickness, sub_bg=sub_bg, use_freeze=cb_freeze, logo_path=locals().get('uploaded_logo', None), font_path=selected_font)
                if not success: st.error(f"❌ Sync Failure: {err_msg}"); st.stop()
            if success and selected_bgm not in ["None (BGM မထည့်ပါ)"]:
                with st.spinner("⏳ [အဆင့်၆/၆] Auto-Ducking ဖြင့် BGM ထပ်မံပေါင်းစပ်နေပါသည်..."):
                    pbar.progress(95, text="🎵 [အဆင့် ၆/၆] Auto-Ducking စနစ်ဖြင့် BGM အသံကစားနေပါသည်...")
                    selected_bgm_path = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in selected_bgm else selected_bgm)
                    if os.path.exists(selected_bgm_path):
                        try:
                            ducked = ffmpeg.filter([ffmpeg.input(selected_bgm_path, stream_loop=-1).audio.filter('aresample', 44100).filter('volume', bgm_volume), ffmpeg.input(v_final).audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                            mixed = ffmpeg.filter([ffmpeg.input(v_final).audio, ducked], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                            (ffmpeg.output(ffmpeg.input(v_final).video, mixed, "temp_mix.mp4", vcodec='copy', acodec='aac', t=get_file_duration(v_final)).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True))
                            shutil.move("temp_mix.mp4", v_final)
                        except Exception: pass
            pbar.progress(100, text="✅ အားလုံးပြီးစီးပါပြီ!")
            if success: st.session_state.render_success = True

    if st.session_state.render_success:
        st.balloons()
        st.success(f"🎉 One-Click ဗီဒီယို အောင်မြင်စွာ ထွက်လာပါပြီ!")
        st.markdown(f"<h2 style='color:#38bdf8; text-align:center;'>🔥 {st.session_state.viral_title}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#94a3b8;'>{st.session_state.viral_tags}</p>", unsafe_allow_html=True)
        col_out1, col_out2 = st.columns([1, 1])
        with col_out1:
            if os.path.exists(st.session_state.final_video_path):
                st.video(st.session_state.final_video_path)
                st.markdown('<div class="setting-panel"><h4>📥 Download Dashboard</h4>', unsafe_allow_html=True)
                st.markdown(get_download_link(st.session_state.final_video_path, "Aether_Recap.mp4", "Download Recap Video (MP4)"), unsafe_allow_html=True)
                if os.path.exists("subtitles.srt"): st.markdown(get_download_link("subtitles.srt", "Aether_Subs.srt", "Download Subtitles (.SRT)"), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        with col_out2:
            st.markdown('<div class="setting-panel"><h3>📝 Scripts & Assets</h3>', unsafe_allow_html=True)
            col_t1, col_t2 = st.columns(2)
            if st.session_state.thumb_path_A and os.path.exists(st.session_state.thumb_path_A):
                with col_t1: st.image(st.session_state.thumb_path_A, caption=f"Thumbnail A ({thumbnail_style})", use_column_width=True); st.markdown(get_download_link(st.session_state.thumb_path_A, "Thumb_A.jpg", "Download A"), unsafe_allow_html=True)
            if st.session_state.thumb_path_B and os.path.exists(st.session_state.thumb_path_B):
                with col_t2: st.image(st.session_state.thumb_path_B, caption=f"Thumbnail B ({thumbnail_style})", use_column_width=True); st.markdown(get_download_link(st.session_state.thumb_path_B, "Thumb_B.jpg", "Download B"), unsafe_allow_html=True)
            with st.expander("👁️ Original Transcript", expanded=False): st.text_area("မူရင်းစာသား:", value=st.session_state.original_transcript, height=150, disabled=True)
            with st.expander("🇲🇲 AI Generated Script", expanded=True): st.text_area("AI မှရေးသားထားသော ဇာတ်ညွှန်း:", value=st.session_state.generated_script, height=250, disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# 📌 MODE 1.5 - FACELESS Channel Studio (TikTok PRO + ALL FEATURES)
# =====================================================================
elif app_mode == "🎙️ Faceless Channel Studio":
    st.markdown('<div class="setting-panel"><h3>👻 Fully-Automated Faceless Channel Studio</h3>', unsafe_allow_html=True)
    st.markdown("TikTok, FB Reels များအတွက် Reddit Stories, Horror ပုံပြင်များကိုဖန်တီးပါ။")

    with st.sidebar:
        st.markdown("---")
        st.markdown("<b>🎙️ Voice & Audio Settings</b>", unsafe_allow_html=True)
        fc_audio_engine = st.radio("Voice Engine", ["Edge-TTS (Free)", "Google Synergy TTS (API)"], key="fc_engine")
        if "Synergy" in fc_audio_engine: fc_synergy_key = st.text_input("Synergy TTS Key", type="password", value=saved_gemini, key="fc_syn")
        fc_voice_char = st.selectbox("Voice Model", ["Synergy Puck (Male)", "Synergy Charon (Deep)"] if "Synergy" in fc_audio_engine else ["ဇော်ဇော် (Male)", "အောင်အောင် (Deep)", "နှင်းနှင်း (Female)"], key="fc_voice")
        
        st.markdown("---")
        st.markdown("<b>🎨 Visual & Niche Settings</b>", unsafe_allow_html=True)
        fc_niche = st.selectbox("Select Niche", ["👻 Horror / Creepypasta", "💔 Reddit Relationship Drama", "🧠 Dark Psychology", "💡 Fun Facts / Trivia", "🚀 Motivation / Mindset", "📜 Ancient History / Myths"])
        fc_ratio = st.selectbox("Video Ratio", ["9:16 (TikTok/Shorts)", "16:9 (YouTube)"], key="fc_ratio")
        fc_duration = st.slider("⏱️ Story Duration (Minutes)", 1, 10, 3)

        # 👇 Niche-Based Voice FX
        st.markdown("<b>🎧 Voice FX</b>", unsafe_allow_html=True)
        recommended_fx = get_recommended_fx_for_niche(fc_niche, mode="faceless")
        default_fx = recommended_fx[1] if len(recommended_fx) > 1 else recommended_fx[0]
        fc_fx = st.selectbox("Voice FX (Niche အလိုက် အကြံပြု)", recommended_fx, index=1, key="fc_fx", help=f"🎯 {fc_niche} အတွက် အကောင်းဆုံး FX: {get_fx_description(fc_niche, default_fx)}")
        if fc_fx != "None (မူရင်းအသံ)": st.caption(f"💡 {get_fx_description(fc_niche, fc_fx)}")

        # 👇 TikTok Hook Settings
        st.markdown("---")
        st.markdown("<b>🔥 TikTok Hook Settings</b>", unsafe_allow_html=True)
        fc_use_hook_overlay = st.checkbox("🎯 Use Hook Text Overlay (First 3s)", value=True, key="fc_use_hook", help="ပထမ ၃ စက္ကန့်မှာ Hook စာသားထည့်မယ်")
        if fc_use_hook_overlay:
            use_random_hook = st.checkbox("🎲 Auto-Random Hook", value=True, key="fc_random_hook")
            if not use_random_hook:
                fc_hook_text = st.text_input("Hook Text", value=get_random_hook(fc_niche), key="fc_hook_text_input", help="ပထမ ၃ စက္ကန့်မှာ ပြမယ့် စာသား")
            else:
                if "fc_hook_text" not in st.session_state or not st.session_state.fc_hook_text:
                    st.session_state.fc_hook_text = get_random_hook(fc_niche)
                fc_hook_text = st.session_state.fc_hook_text
                st.markdown(f'<div class="hook-preview" style="color:#38bdf8; font-size:18px; font-weight:bold;">🎯 {fc_hook_text}</div>', unsafe_allow_html=True)
                if st.button("🔄 New Hook", key="fc_new_hook"): st.session_state.fc_hook_text = get_random_hook(fc_niche); st.rerun()
            st.session_state.tiktok_hook_text = fc_hook_text
        
        fc_use_loop_point = st.checkbox("🔄 Add Loop Point (End Screen)", value=True, key="fc_loop")

        # 👇 Professional Thumbnail Settings
        st.markdown("---")
        st.markdown("<b>🖼️ Thumbnail Settings</b>", unsafe_allow_html=True)
        default_thumb = get_thumbnail_style_for_niche(fc_niche)
        thumb_keys = list(THUMBNAIL_STYLES.keys())
        default_thumb_idx = thumb_keys.index(default_thumb) if default_thumb in thumb_keys else 0
        fc_thumb_style = st.selectbox("Thumbnail Style", thumb_keys, index=default_thumb_idx, key="fc_thumb_style", help=f"🎯 {fc_niche} အတွက် Auto-Selected")

        st.markdown("<b>📝 Subtitle Pro Settings</b>", unsafe_allow_html=True)
        fc_selected_font = st.selectbox("🔤 Font Style", available_fonts, index=0, key="fc_font")
        fc_sub_position = st.selectbox("📍 Position", ["Center", "Bottom", "Top"], index=0, key="fc_sub_pos")
        fc_sub_color = st.selectbox("🎨 Color", ["Yellow Text", "White Text", "Neon Green Text", "Red Text", "Gold Text"], index=0, key="fc_sub_col")
        fc_sub_size = st.slider("🔠 Font Size", 16, 50, 28, key="fc_sub_size")
        fc_subtitle_mode = st.radio("Subtitle Output Mode", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"], key="fc_sub_mode")
        bgm_options = ["None (BGM မထည့်ပါ)"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files: bgm_options.insert(1, "🤖 Auto (Random Select)"); bgm_options.extend(bgm_files)
        fc_bgm = st.selectbox("🎼 Background Music", bgm_options, key="fc_bgm")
        fc_bgm_vol = st.slider("🔊 BGM Volume", 1, 50, 8, key="fc_bgm_vol") / 100.0
        fc_sub_short = st.checkbox("✂️ Short & Punchy (Hormozi)", value=True)

    st.markdown('<div class="setting-panel"><h4>🛠️ Manual Controls (Optional)</h4>', unsafe_allow_html=True)
    col_fc1, col_fc2 = st.columns(2)
    with col_fc1:
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        fc_script_mode = st.radio("📝 Story Script Source", ["🤖 Auto-Generate AI Script", "✍️ Manual Script Entry"])
        fc_custom_topic = ""
        if "Auto" in fc_script_mode:
            fc_custom_topic = st.text_input("💡 ဇာတ်လမ်း အကြောင်းအရာ (Optional):", placeholder="ဥပမာ - သရဲဘုံကျောင်း, ပင်လယ်ဓားပြ...", key="fc_topic")
            st.markdown("<br><p style='color:#38bdf8; font-weight:bold;'>✍️ AI Storytelling Rules</p>", unsafe_allow_html=True)
            fc_script_hook = st.checkbox("🪝 3-Second Viral Hook (အစချီ ဆွဲဆောင်မည်)", value=True, key="fc_hook")
            fc_script_curiosity = st.checkbox("🤯 Curiosity Gaps (စိတ်ဝင်စားမှု အရှိန်တင်မည်)", value=True, key="fc_curiosity")
            fc_script_tone = st.checkbox("🎭 Emotion & Tone (ဇာတ်ကောင်စရိုက် သွင်းမည်)", value=True, key="fc_tone")
            fc_script_cta = st.checkbox("💬 Call to Action (Commentခေါ်မည်)", value=False, key="fc_cta")
        fc_manual_script = st.text_area("✍️ Paste your script here:", placeholder="သင့်ကိုယ်ပိုင်ဇာတ်ညွှန်းကို ဤနေရာတွင် ထည့်ပါ...", height=150) if "Manual" in fc_script_mode else ""
        st.markdown("</div>", unsafe_allow_html=True)
    with col_fc2:
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        fc_visual_mode = st.radio("🎥 Visuals Source", ["🎨 Auto-Generate AI Images (Pollinations)", "🖼️ Upload Manual Images"])
        fc_uploaded_images = st.file_uploader("🖼️ Upload Images (JPG/PNG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True) if "Upload" in fc_visual_mode else None
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 CREATE FACELESS VIDEO (AUTO-MAGIC)"):
        if not api_key_input: st.error("⚠️ API Key ထည့်သွင်းပေးပါ။ (Sidebar တွင်ထည့်ပါ)")
        elif "Manual" in fc_script_mode and not fc_manual_script.strip(): st.error("⚠️ Manual ဇာတ်ညွှန်းထည့်သွင်းပေးပါ။")
        elif "Upload" in fc_visual_mode and not fc_uploaded_images: st.error("⚠️ အနည်းဆုံးပုံ (၁) ပုံ Upload တင်ပေးပါ။")
        else:
            st.session_state.render_success = False
            st.session_state.whisper_data = None
            cleanup_temp_files()
            run_id = str(int(time.time()))
            v_final = f"FACELESS_FINAL_{run_id}.mp4"
            st.session_state.final_video_path = v_final
            pbar = st.progress(0, text="🚀 အလိုအလျောက် ဖန်တီးမှုစတင်နေပါပြီ...")
            keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()] if "Gemini" in ai_provider else [api_key_input]
            fc_story_text = ""
            if "Manual" in fc_script_mode:
                pbar.progress(10, text="📝 Manual ဇာတ်ညွှန်းအား ဖတ်ယူနေပါသည်...")
                fc_story_text = fc_manual_script.strip()
            else:
                with st.spinner(f"⏳ [အဆင့်၁/၅] {ai_provider} ဖြင့် {fc_duration} မိနစ်စာ ဇာတ်လမ်း ရေးသားနေပါသည်..."):
                    pbar.progress(10, text="📝 ဇာတ်လမ်း ရေးသားနေပါသည်...")
                    target_words = fc_duration * 140
                    topic_instruction = f"Specifically, the story MUST be deeply focused on this topic: {fc_custom_topic.strip()}.\n" if fc_custom_topic.strip() else ""
                    hook_rule = "1. THE VIRAL HOOK (0-3s): Start with a mind-blowing, highly engaging 3-second viral hook.\n" if fc_script_hook else ""
                    curiosity_rule = "2. CURIOSITY GAPS: Insert curiosity gaps in the middle to retain audience attention.\n" if fc_script_curiosity else ""
                    tone_rule = "3. EMOTION & TONE: Inject strong emotions and character tones matching the scene.\n" if fc_script_tone else ""
                    cta_rule = "4. CALL TO ACTION: End the script with a strong Call to Action asking a question.\n" if fc_script_cta else ""
                    
                    story_prompt = f"""Write an engaging {fc_duration}-minute highly viral script for a {fc_niche} TikTok/YouTube video in natural spoken Burmese. (Around {target_words} words).
{topic_instruction}
CRITICAL RULES:
{hook_rule}{curiosity_rule}{tone_rule}{cta_rule}
5. NO FORMAL GRAMMAR: STRICTLY PROHIBITED to use formal literary markers (၌,၍, သည့်, သည်, ၏). Use natural spoken endings (တယ်, တဲ့, မှာ, ရဲ့).
6. POV: Write in second person (မင်း / မင်းရဲ့) if applicable.
7. AUDIO TAGS: Include tags like [pause=1.0], [excited], [whisper] to guide the voice.
8. Do not use English transliteration. Use emotionally immersive storytelling. MUST BE IN PURE BURMESE LANGUAGE.
Output format: Provide the script directly. At the absolute end, include these two lines:
[TITLE: A highly viral, click-worthy Burmese title]
[TAGS: #tag1 #tag2]"""

                    # ===== DEEPSEEK WITH FALLBACK =====
                    if "DeepSeek" in ai_provider:
                        try:
                            fc_story_text = deepseek_generate_script(api_key_input, story_prompt)
                            if not fc_story_text: raise Exception("Empty response from DeepSeek")
                        except Exception as ds_err:
                            st.warning(f"⚠️ DeepSeek Failed: {str(ds_err)[:150]}")
                            if saved_gemini:
                                st.info("🔄 Auto-switching to Gemini...")
                                keys_list_fb = [k.strip() for k in saved_gemini.split(",") if k.strip()]
                                fc_story_text = ""
                                for key in keys_list_fb:
                                    try:
                                        client = genai.Client(api_key=key)
                                        response = client.models.generate_content(model="gemini-2.5-flash", contents=story_prompt)
                                        fc_story_text = response.text.strip()
                                        break
                                    except Exception: continue
                                if not fc_story_text: st.error("❌ Both DeepSeek and Gemini failed."); st.stop()
                            else: st.error(f"❌ DeepSeek failed and no fallback available."); st.stop()
                    elif "Gemini" in ai_provider:
                        last_err = ""
                        for key in keys_list:
                            try:
                                client = genai.Client(api_key=key)
                                response = client.models.generate_content(model="gemini-2.5-flash", contents=story_prompt)
                                fc_story_text = response.text.strip(); break
                            except Exception as e: last_err = str(e); continue
                        if not fc_story_text: st.error(f"Story Error: Key အားလုံး Limit ပြည့်နေပါသည်။ {last_err}"); st.stop()

            title_match = re.search(r'\[TITLE:\s*(.*?)\]', fc_story_text, re.IGNORECASE)
            tags_match = re.search(r'\[TAGS:\s*(.*?)\]', fc_story_text, re.IGNORECASE)
            if title_match: st.session_state.viral_title = re.sub(r'[\[\]]', '', title_match.group(1)).strip()
            if tags_match: st.session_state.viral_tags = tags_match.group(1).strip()
            fc_story_text = re.sub(r'\[TITLE:.*?\]', '', fc_story_text, flags=re.IGNORECASE)
            fc_story_text = re.sub(r'\[TAGS:.*?\]', '', fc_story_text, flags=re.IGNORECASE).strip()
            
            with st.spinner("⏳ [အဆင့်၂/၅] AI သရုပ်ဆောင်ဖြင့် အသံဖန်တီးနေပါသည်..."):
                pbar.progress(30, text="🎙️ အသံဖန်တီးနေပါသည်...")
                try:
                    clean_story = re.sub(r'\[.*?\]', '', fc_story_text)
                    asyncio.run(generate_tts(fc_story_text if "Synergy" in fc_audio_engine else clean_story, fc_voice_char, "fc_audio.wav", engine=fc_audio_engine, gemini_key=locals().get('fc_synergy_key', api_key_input), voice_fx=fc_fx))
                    fc_audio_dur = get_file_duration("fc_audio.wav")
                    if fc_audio_dur < 5.0: st.error("❌ အသံထုတ်လုပ်ခြင်းမအောင်မြင်ပါ။"); st.stop()
                except Exception as e: st.error(f"Audio Error: {e}"); st.stop()
            
            groq_key_fc_sync = load_key(GROQ_KEY_FILE)
            if groq_key_fc_sync and os.path.exists("fc_audio.wav"):
                try:
                    with open("fc_audio.wav", "rb") as file:
                        client_groq = Groq(api_key=groq_key_fc_sync)
                        st.session_state.whisper_data = client_groq.audio.transcriptions.create(file=("fc_audio.wav", file.read()), model="whisper-large-v3", response_format="verbose_json", timestamp_granularities=["word"])
                        st.success("✅ Whisper အသံဖမ်းယူမှု အောင်မြင်ပါသည်။")
                except Exception as e: st.warning(f"⚠️ Whisper Sync မအောင်မြင်ပါ။ Error: {str(e)[:100]}")
            
            with st.spinner("⏳ [အဆင့်၃/၅] Visuals များကို ပြင်ဆင်နေပါသည်..."):
                pbar.progress(50, text="🎥 Visuals ပြင်ဆင်နေပါသည်...")
                try:
                    generated_clips = []
                    v_w, v_h = (720, 1280) if "9:16" in fc_ratio else (1280, 720)
                    if "Upload" in fc_visual_mode:
                        clip_dur = fc_audio_dur / len(fc_uploaded_images)
                        for i, img_file in enumerate(fc_uploaded_images):
                            img_path = f"fc_img_{i}.jpg"; clip_path = f"fc_clip_{i}.mp4"
                            img_file.seek(0)
                            with open(img_path, "wb") as f: f.write(img_file.read())
                            pbar.progress(50 + int((i / len(fc_uploaded_images)) * 15), text=f"🎥 Upload ပုံများကို Animation သွင်းနေပါသည် ({i+1}/{len(fc_uploaded_images)})...")
                            subprocess.run([FFMPEG_BINARY, "-y", "-loop", "1", "-framerate", "25", "-i", img_path, "-t", str(clip_dur), "-vf", f"scale=-2:2000,zoompan=z='min(zoom+0.001,1.15)':d={int(clip_dur*25)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={v_w}x{v_h},fps=25", "-c:v", "libx264", "-preset", "superfast", clip_path], capture_output=True)
                            if os.path.exists(clip_path): generated_clips.append(clip_path)
                    else:
                        style_mapping = {
                            "👻 Horror / Creepypasta": "Ultra-realistic cinematic horror, 8k, eerie volumetric lighting, chilling atmosphere, photorealistic, Unreal Engine 5 render",
                            "💔 Reddit Relationship Drama": "Cinematic drama photography, moody soft lighting, hyper-detailed faces, 8k resolution, emotional depth, masterpiece",
                            "🧠 Dark Psychology": "Neo-noir psychological thriller style, high contrast moody lighting, cinematic depth of field, ultra-detailed masterpiece",
                            "💡 Fun Facts / Trivia": "Vibrant Pixar 3D animation style, bright studio lighting, incredibly detailed, 8k, trending on artstation",
                            "🚀 Motivation / Mindset": "Epic cinematic photography, golden hour god rays, highly inspiring, 8k resolution, masterpiece, dramatic sky",
                            "📜 Ancient History / Myths": "Epic fantasy concept art, Lord of the Rings style, dramatic cinematic lighting, intricate details, 8k, highly epic"
                        }
                        current_style = style_mapping.get(fc_niche, "Cinematic, highly detailed 8k masterpiece")
                        search_keywords = []
                        img_count = max(4, int(fc_audio_dur // 12))
                        if "DeepSeek" in ai_provider:
                            try: 
                                prompts_text = deepseek_generate_image_prompts(api_key_input, fc_story_text, current_style, img_count)
                                search_keywords = [kw.strip() for kw in prompts_text.split('|') if len(kw.strip()) > 5][:img_count]
                            except Exception: search_keywords = []
                        elif "Gemini" in ai_provider:
                            for key in keys_list:
                                try:
                                    client = genai.Client(api_key=key)
                                    img_prompt_instruction = f"""Act as a professional Midjourney Prompt Engineer. Based on this story, give me exactly {img_count} highly detailed, epic English image generation prompts for chronological scenes.
GLOBAL STYLE DNA: {current_style}. RULES: Include camera angles, lighting conditions, and extreme details. Avoid explicit/violent words.
CRITICAL FORMAT RULE: Format strictly separated by a pipe '|' with NO newlines. Example: scene 1 | scene 2
Story: {fc_story_text[:500]}"""
                                    prompt_req = client.models.generate_content(model="gemini-2.5-flash", contents=img_prompt_instruction)
                                    raw_kws = prompt_req.text.replace('\n', '|').split('|')
                                    search_keywords = [kw.strip() for kw in raw_kws if len(kw.strip()) > 5][:img_count]; break
                                except Exception: continue
                        if not search_keywords: search_keywords = [f"{current_style}, epic scene {i}" for i in range(img_count)]
                        total_clips = len(search_keywords)
                        clip_dur = fc_audio_dur / total_clips
                        def generate_pollinations_image(prompt_text, idx):
                            try:
                                epic_suffix = ", masterpiece, best quality, ultra detailed, 8k resolution, highly realistic, spectacular, breathtaking"
                                final_prompt = prompt_text.strip() + epic_suffix
                                encoded_prompt = urllib.parse.quote(final_prompt)
                                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={v_w}&height={v_h}&nologo=true"
                                res = requests.get(url, timeout=60)
                                if res.status_code == 200:
                                    img_path = f"fc_img_{idx}.jpg"; clip_path = f"fc_clip_{idx}.mp4"
                                    with open(img_path, "wb") as f: f.write(res.content)
                                    subprocess.run([FFMPEG_BINARY, "-y", "-loop", "1", "-framerate", "25", "-i", img_path, "-t", str(clip_dur), "-vf", f"scale=-2:2000,zoompan=z='min(zoom+0.001,1.15)':d={int(clip_dur*25)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={v_w}x{v_h},fps=25", "-c:v", "libx264", "-preset", "superfast", clip_path], capture_output=True)
                                    return clip_path
                            except Exception: pass
                            return None
                        for i, kw in enumerate(search_keywords):
                            pbar.progress(50 + int(((i + 1) / total_clips) * 15), text=f"🎨 AI ဖြင့် ပုံများ ဖန်တီးနေပါသည် (Clip {i+1}/{total_clips})...")
                            generated_clip = generate_pollinations_image(kw, i)
                            if generated_clip and os.path.exists(generated_clip): generated_clips.append(generated_clip)
                            time.sleep(2)
                    if not generated_clips: st.error("❌ Visual Generation Failed."); st.stop()
                    pbar.progress(65, text="🎞️ ဗီဒီယိုများကို ပေါင်းစပ်နေပါသည်...")
                    with open("fc_concat.txt", "w") as f:
                        for c in generated_clips: f.write(f"file '{c}'\n")
                    res_concat = subprocess.run([FFMPEG_BINARY, "-y", "-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", "fc_concat.txt", "-t", str(fc_audio_dur), "-c", "copy", "fc_video_loop.mp4"], capture_output=True)
                    if not os.path.exists("fc_video_loop.mp4"): st.error(f"❌ FFmpeg Concat Error."); st.stop()
                except Exception as e: st.error(f"Visual Error: {e}"); st.stop()
            
            with st.spinner("⏳ [အဆင့်၄/၅] စာတန်းထိုးများကို ချိန်ညှိနေပါသည်..."):
                pbar.progress(70, text="📝 Timeline ချိန်ညှိနေပါသည်...")
                fc_parsed = None; last_err = ""
                try:
                    clean_script_for_sync = strip_audio_tags(fc_story_text)
                    sync_srt, fc_parsed = smart_sync_pipeline(clean_script_for_sync, "fc_audio.wav", whisper_data=st.session_state.whisper_data, audio_duration=fc_audio_dur, sync_offset=st.session_state.sync_offset, short_punchy=fc_sub_short)
                    with open("subtitles.srt", "w", encoding="utf-8-sig") as f: f.write(sync_srt)
                    if not fc_parsed or len(fc_parsed) == 0: last_err = "No parsed timestamps generated"; fc_parsed = None
                    st.success(f"✅ SRT ဖန်တီးပြီးပါပြီ။ စာတန်းထိုး {len(fc_parsed)} ခု ပါဝင်ပါသည်။ (Offset: {st.session_state.sync_offset:+.1f}s)")
                except Exception as e: last_err = str(e)
                if not fc_parsed: st.error(f"SRT Error: {last_err}"); st.stop()
            
            with st.spinner("⏳ [အဆင့်၅/၅] အားလုံးကိုပေါင်းစပ်ပြီး Master Video ထုတ်လုပ်နေပါသည်..."):
                pbar.progress(85, text="🎬 Master Rendering အလုပ်လုပ်နေပါသည်...")
                try:
                    temp_render = "temp_render_before_hook.mp4"
                    success, err_msg = render_premium_saas_video("fc_video_loop.mp4", "fc_audio.wav", fc_parsed, temp_render, fc_ratio, use_bypass=True, subtitle_mode=fc_subtitle_mode, sub_position=fc_sub_position, sub_color=fc_sub_color, sub_size=fc_sub_size, sub_thickness=2.5, sub_bg=False, font_path=fc_selected_font)
                    if not success: st.error(f"❌ Video Generation Output Failure! {err_msg}"); st.stop()
                    
                    # 👇 TIKTOK HOOK OVERLAY
                    current_video = temp_render
                    if fc_use_hook_overlay:
                        hook_video = "temp_with_hook.mp4"
                        current_video = add_tiktok_hook_overlay(current_video, hook_video, fc_hook_text, fc_niche)
                    
                    # 👇 TIKTOK LOOP POINT
                    if fc_use_loop_point:
                        loop_video = "temp_with_loop.mp4"
                        current_video = add_tiktok_loop_point(current_video, loop_video)
                    
                    if current_video != v_final: shutil.move(current_video, v_final)
                    
                    if fc_bgm not in ["None (BGM မထည့်ပါ)"]:
                        bgm_path = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in fc_bgm else fc_bgm)
                        if os.path.exists(bgm_path):
                            try:
                                ducked = ffmpeg.filter([ffmpeg.input(bgm_path, stream_loop=-1).audio.filter('aresample', 44100).filter('volume', fc_bgm_vol), ffmpeg.input(v_final).audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                                mixed = ffmpeg.filter([ffmpeg.input(v_final).audio, ducked], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                                ffmpeg.output(ffmpeg.input(v_final).video, mixed, "temp_faceless.mp4", vcodec='copy', acodec='aac', t=fc_audio_dur).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
                                shutil.move("temp_faceless.mp4", v_final)
                            except Exception: pass
                    
                    # 👇 PROFESSIONAL THUMBNAILS
                    try:
                        t_A = min(fc_audio_dur * 0.2, 10)
                        t_B = min(fc_audio_dur * 0.5, 20)
                        for thumb_suffix, t_val in [("A", t_A), ("B", t_B)]:
                            thumb_name = f"thumb_{thumb_suffix}_{run_id}.jpg"
                            success_thumb, _ = generate_professional_thumbnail(v_final, thumb_name, st.session_state.viral_title if st.session_state.viral_title else "Viral Video", t_val, style=fc_thumb_style, font_path=fc_selected_font)
                            if success_thumb:
                                if thumb_suffix == "A": st.session_state.thumb_path_A = thumb_name
                                elif thumb_suffix == "B": st.session_state.thumb_path_B = thumb_name
                    except Exception: pass
                    
                    pbar.progress(100, text="✅ အားလုံးပြီးစီးပါပြီ!")
                    st.balloons()
                    st.success("🎉 Faceless Video ထုတ်လုပ်မှု အောင်မြင်စွာ ပြီးစီးပါပြီ!")
                    
                    try:
                        if "DeepSeek" in ai_provider:
                            viral_score_text = deepseek_analyze_virality(api_key_input, st.session_state.viral_title, fc_story_text[:150])
                            st.session_state.viral_score = viral_score_text
                        elif "Gemini" in ai_provider:
                            client_viral = genai.Client(api_key=keys_list[0])
                            v_prompt = f"Analyze this short video for TikTok virality. Title: {st.session_state.viral_title}. Hook: {fc_story_text[:150]}. Reply strictly in this format: \nScore: [1-100]\nReason: [1 short sentence in Burmese]"
                            v_res = client_viral.models.generate_content(model="gemini-2.5-flash", contents=v_prompt)
                            st.session_state.viral_score = v_res.text.strip()
                    except Exception: st.session_state.viral_score = "Score: 90\nReason: အရမ်းကောင်းတဲ့ Hook ပါ။"
                    
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        if os.path.exists(st.session_state.final_video_path):
                            st.video(st.session_state.final_video_path)
                            st.markdown('<div class="setting-panel"><h4>📥 Download Dashboard</h4>', unsafe_allow_html=True)
                            st.markdown(get_download_link(st.session_state.final_video_path, "Viral_Faceless.mp4", "Download Final Video"), unsafe_allow_html=True)
                            if os.path.exists("subtitles.srt"): st.markdown(get_download_link("subtitles.srt", "Faceless_Subs.srt", "Download Subtitles (.SRT)"), unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        else: st.error("❌ ဗီဒီယိုဖိုင်ကို ရှာမတွေ့ပါ။")
                    with col_f2:
                        st.markdown("### 📝 Generated Story & Assets")
                        st.info(f"📈 **Viral Prediction:**\n{st.session_state.viral_score}")
                        col_ta, col_tb = st.columns(2)
                        if st.session_state.thumb_path_A and os.path.exists(st.session_state.thumb_path_A):
                            with col_ta: st.image(st.session_state.thumb_path_A, caption=f"Thumbnail A ({fc_thumb_style})"); st.markdown(get_download_link(st.session_state.thumb_path_A, "Thumb_A.jpg", "Download A"), unsafe_allow_html=True)
                        if st.session_state.thumb_path_B and os.path.exists(st.session_state.thumb_path_B):
                            with col_tb: st.image(st.session_state.thumb_path_B, caption=f"Thumbnail B ({fc_thumb_style})"); st.markdown(get_download_link(st.session_state.thumb_path_B, "Thumb_B.jpg", "Download B"), unsafe_allow_html=True)
                        st.text_area("ဇာတ်လမ်း:", value=fc_story_text, height=300, disabled=True)
                except Exception as e: st.error(f"Render Error: {e}"); st.stop()

# =====================================================================
# 📌 MODE 2 - VEO VIDEO STUDIO
# =====================================================================
elif app_mode == "🎥 Veo Video Studio":
    st.markdown('<div class="setting-panel"><h3>🎥 Veo 3.0 Cinematic Video Generator</h3>', unsafe_allow_html=True)
    video_prompt = st.text_area("🎬 Enter Video Prompt", placeholder="A cinematic slow-motion drone shot...")
    if st.button("🚀 Generate Veo Video"): pass

elif app_mode == "🎵 Lyria Music Studio":
    st.markdown('<div class="setting-panel"><h3>🎵 Lyria 3 Pro Music Generator</h3>', unsafe_allow_html=True)
    music_prompt = st.text_area("🎧 Enter Music Prompt", placeholder="Epic cinematic background music...")
    if st.button("🚀 Generate Lyria Music"): pass

elif app_mode == "⚡ Translation/Transcript Studio":
    st.markdown('<h2 style="color:#00e5ff;">⚡ Translation & Subtitle Studio (AI Dual Engine)</h2>', unsafe_allow_html=True)
    video_url = st.text_input("YouTube / FB / TikTok / Rednote URL ထည့်ပါ:")
    if st.button("🚀 စတင်လုပ်ဆောင်မည်"): pass

elif app_mode == "📥 Video Downloader Hub":
    st.markdown('<h2 style="color:#00e5ff;">📥 Video Downloader Hub</h2>', unsafe_allow_html=True)
    dl_url = st.text_input("ဗီဒီယို URL ကို ဒီမှာ ထည့်ပါ:", key="hub_dl_url")
    if st.button("⬇️ ဗီဒီယိုစစ်ဆေးပြီး ဒေါင်းလုဒ်ဆွဲမည်"): pass
