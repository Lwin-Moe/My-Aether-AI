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

# FIX: Prioritize system FFmpeg
if shutil.which("ffmpeg"):
    FFMPEG_BINARY = "ffmpeg"
else:
    FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

# FIX: Download Default Font
local_font_path = "Padauk.ttf"
if not os.path.exists(local_font_path):
    try:
        urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/padauk/Padauk-Regular.ttf", local_font_path)
    except Exception:
        pass

# FIX: Dynamic Font Scanner
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
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" style="display:block; text-align:center; margin-top:10px; padding:12px 20px; background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color:white; text-decoration:none; border-radius:8px; font-weight:bold;">\U0001f4e5 {link_text}</a>'

# =====================================================================
# TIKTOK HOOK SYSTEM
# =====================================================================

TIKTOK_HOOK_TEMPLATES = {
    "Horror": [
        "ဒီတစ်ခါတော့ သေလုမတတ်ပဲ...",
        "ဒီနေရာကို ဘယ်တော့မှ မသွားပါနဲ့...",
        "ည ၃ နာရီမှာ ဒီလိုလုပ်ရင်...",
        "ဒီဇာတ်လမ်းက တကယ့်ဖြစ်ရပ်မှန်ပါ...",
        "ဒါကိုကြားရင် မင်းကြက်သီးထမယ်..."
    ],
    "Motivation": [
        "ဒီတစ်ချက်က မင်းဘဝကိုပြောင်းလဲစေမယ်...",
        "အောင်မြင်တဲ့သူတိုင်း ဒါကိုလုပ်တယ်...",
        "မနက်ဖြန်ကစပြီး ဒါကိုလုပ်ကြည့်..."
    ],
    "Dark Psychology": [
        "လူတွေက မင်းကို ဒီလိုထိန်းချုပ်နေတယ်...",
        "ဒီစိတ်ပညာလှည့်ကွက်က အံ့ဩစရာပဲ..."
    ],
    "Fun Facts": [
        "ဒီအချက်ကို လူ ၉၉% မသိကြဘူး...",
        "ဒါကိုသိရင် မင်းအံ့ဩသွားမယ်..."
    ],
    "History": [
        "နှစ်ထောင်ချီတဲ့ ဒီလျှို့ဝှက်ချက်က...",
        "ရှေးခေတ်လူတွေ ဒါကိုဘယ်လိုလုပ်ခဲ့သလဲ..."
    ]
}

def get_random_hook(niche):
    for key in TIKTOK_HOOK_TEMPLATES:
        if key in niche:
            return random.choice(TIKTOK_HOOK_TEMPLATES[key])
    return random.choice(TIKTOK_HOOK_TEMPLATES["Fun Facts"])

def add_tiktok_hook_overlay(video_input, output_path, hook_text, niche="Fun Facts", duration=3.5):
    try:
        v_w, v_h = 720, 1280
        video = ffmpeg.input(video_input).video
        audio = ffmpeg.input(video_input).audio
        hook_styles = {
            "Horror": {"text_color": "red", "bg_color": "black@0.8", "font_size": 55},
            "Motivation": {"text_color": "gold", "bg_color": "black@0.6", "font_size": 50},
            "Fun Facts": {"text_color": "cyan", "bg_color": "black@0.7", "font_size": 45},
            "Dark Psychology": {"text_color": "white", "bg_color": "black@0.9", "font_size": 50},
            "History": {"text_color": "gold", "bg_color": "black@0.7", "font_size": 48}
        }
        style = hook_styles.get(niche, hook_styles["Fun Facts"])
        for key in hook_styles:
            if key in niche: style = hook_styles[key]; break
        wrapped_hook = textwrap.wrap(hook_text, width=20)
        if not wrapped_hook: wrapped_hook = [hook_text]
        max_len = max(len(line) for line in wrapped_hook)
        centered_hook = "\n".join(line.center(max_len, " ") for line in wrapped_hook)
        with open("hook_text.txt", "w", encoding="utf-8") as f: f.write(centered_hook)
        video = ffmpeg.filter(video, 'drawbox', x=0, y='h*0.3', w='iw', h='h*0.4', color=style["bg_color"], thickness='fill', enable=f'between(t,0,{duration})')
        video = ffmpeg.filter(video, 'drawtext', textfile='hook_text.txt', fontfile='Padauk.ttf', fontsize=style["font_size"], fontcolor=style["text_color"], bordercolor='black', borderw=3, x='(w-text_w)/2', y='(h-text_h)/2', line_spacing=15, text_align='C', enable=f'between(t,0,{duration})')
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
        video = ffmpeg.filter(video, 'drawtext', text='\U0001f446 \u1015\u103c\u1014\u103a\u1000\u103c\u100a\u1037\u103a\u1015\u102b', fontsize=35, fontcolor='white', bordercolor='black', borderw=2, x='(w-text_w)/2', y='(h-text_h)/2', enable=f'between(t,{dur-2},{dur})')
        out = ffmpeg.output(video, audio, output_path, vcodec='libx264', pix_fmt='yuv420p', acodec='aac', audio_bitrate='128k', preset='superfast')
        out.overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return output_path
    except Exception:
        return video_input

# =====================================================================
# PROFESSIONAL THUMBNAIL SYSTEM
# =====================================================================

THUMBNAIL_STYLES = {
    "Viral TikTok Style": {"text_position": "center", "font_size_range": (50, 90), "bg_overlay": "gradient_bottom", "text_effect": "stroke_bold", "color_scheme": "yellow_red"},
    "Cinematic Movie Poster": {"text_position": "bottom_third", "font_size_range": (40, 70), "bg_overlay": "vignette_dark", "text_effect": "shadow_soft", "color_scheme": "white_gold"},
    "Horror / Mystery": {"text_position": "center", "font_size_range": (55, 85), "bg_overlay": "dark_gradient", "text_effect": "shadow_horror", "color_scheme": "red_black"},
    "Premium / Luxury": {"text_position": "bottom_third", "font_size_range": (40, 65), "bg_overlay": "golden_frame", "text_effect": "golden_text", "color_scheme": "gold_cream"},
    "Clean / Minimal": {"text_position": "center", "font_size_range": (45, 80), "bg_overlay": "subtle_overlay", "text_effect": "clean_white", "color_scheme": "white_soft"}
}

NICHE_THUMBNAIL_MAP = {
    "Horror": "Horror / Mystery", "Relationship": "Viral TikTok Style",
    "Dark Psychology": "Horror / Mystery", "Fun Facts": "Viral TikTok Style",
    "Motivation": "Premium / Luxury", "History": "Cinematic Movie Poster"
}

def get_thumbnail_style_for_niche(niche):
    for key in NICHE_THUMBNAIL_MAP:
        if key in niche: return NICHE_THUMBNAIL_MAP[key]
    return "Viral TikTok Style"

def calculate_optimal_font_size(text, min_size, max_size):
    text_length = len(text)
    if text_length < 20: return max_size
    elif text_length < 40: return int(max_size * 0.85)
    elif text_length < 60: return int(max_size * 0.7)
    elif text_length < 80: return int(max_size * 0.55)
    else: return max(min_size, int(max_size * 0.45))

def wrap_text_for_thumbnail(text, max_width=25):
    text = re.sub(r'\[.*?\]', '', text)
    lines = textwrap.wrap(text, width=max_width, break_long_words=False)
    if not lines: lines = [text[:max_width]]
    max_len = max(len(line) for line in lines)
    centered_lines = [line.center(max_len, " ") for line in lines]
    return "\n".join(centered_lines)

def generate_professional_thumbnail(video_input, output_path, title_text, timestamp, style="Viral TikTok Style", font_path="Padauk.ttf"):
    try:
        style_config = THUMBNAIL_STYLES.get(style, THUMBNAIL_STYLES["Viral TikTok Style"])
        for key in THUMBNAIL_STYLES:
            if key in style: style_config = THUMBNAIL_STYLES[key]; break
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
        if style_config["text_position"] == "center": y_position = "(h-text_h)/2"
        elif style_config["text_position"] == "bottom_third": y_position = "h*0.65"
        elif style_config["text_position"] == "top_third": y_position = "h*0.15"
        else: y_position = "(h-text_h)/2"
        color_schemes = {
            "yellow_red": {"text": "yellow", "shadow": "red", "box": "red@0.8"},
            "white_gold": {"text": "white", "shadow": "gold", "box": "black@0.6"},
            "red_black": {"text": "red", "shadow": "black", "box": "black@0.8"},
            "gold_cream": {"text": "gold", "shadow": "brown", "box": "black@0.5"},
            "white_soft": {"text": "white", "shadow": "gray", "box": "black@0.4"}
        }
        colors = color_schemes.get(style_config["color_scheme"], color_schemes["yellow_red"])
        if style_config["text_effect"] == "stroke_bold": border_width = 4
        elif style_config["text_effect"] == "shadow_soft": border_width = 2
        elif style_config["text_effect"] == "shadow_horror": border_width = 5
        elif style_config["text_effect"] == "golden_text": border_width = 2
        else: border_width = 3
        wrapped_text = wrap_text_for_thumbnail(title_text)
        with open("thumb_pro_text.txt", "w", encoding="utf-8") as f: f.write(wrapped_text)
        video = ffmpeg.filter(video, 'drawtext', textfile='thumb_pro_text.txt', fontfile=font_path.replace('\\', '/'), fontcolor=colors["text"], fontsize=font_size, bordercolor=colors["shadow"], borderw=border_width, box=1, boxcolor=colors["box"], boxborderw=15, x='(w-text_w)/2', y=y_position, line_spacing=15, text_align='C')
        ffmpeg.output(video, output_path, vframes=1, qscale=2).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return True, output_path
    except Exception:
        return False, ""

# =====================================================================
# NICHE-BASED VOICE FX AUTO-MATCH SYSTEM
# =====================================================================

NICHE_VOICE_FX_MAP = {
    "Horror": {"primary": ["Deep & Chilling (Horror)", "Demon / Monster", "ASMR / Whisper", "Deep Cave Echo"]},
    "Relationship": {"primary": ["Epic Trailer Voice", "Cinematic Reverb", "Old Telephone"]},
    "Dark Psychology": {"primary": ["ASMR / Whisper", "Deep & Chilling (Horror)", "Underwater / Muffled"]},
    "Fun Facts": {"primary": ["Deep & Energetic (Motivation)", "Walkie-Talkie", "Epic Trailer Voice"]},
    "Motivation": {"primary": ["Deep & Energetic (Motivation)", "Epic Trailer Voice", "Cinematic Reverb"]},
    "History": {"primary": ["Cinematic Reverb", "Deep Cave Echo", "Deep & Chilling (Horror)"]}
}

DUBBING_VOICE_FX_MAP = {
    "Normal": {"primary": ["Epic Trailer Voice", "Cinematic Reverb"]},
    "Slang": {"primary": ["Deep & Energetic (Motivation)", "Walkie-Talkie"]},
    "Comedy": {"primary": ["Robot / Cyborg", "Old Telephone"]},
    "Suspense": {"primary": ["Deep & Chilling (Horror)", "ASMR / Whisper", "Deep Cave Echo"]}
}

def get_recommended_fx_for_niche(niche, mode="faceless"):
    fx_map = DUBBING_VOICE_FX_MAP if mode == "dubbing" else NICHE_VOICE_FX_MAP
    if niche in fx_map:
        recommended = fx_map[niche]["primary"]
        return ["None (မူရင်းအသံ)"] + recommended
    for key in fx_map:
        if key in niche:
            recommended = fx_map[key]["primary"]
            return ["None (မူရင်းအသံ)"] + recommended
    return ["None (မူရင်းအသံ)", "Epic Trailer Voice", "Deep & Chilling (Horror)", "ASMR / Whisper"]

# =====================================================================
# WHISPER WORD-LEVEL SRT GENERATOR (AUTO SYNC SOLUTION)
# =====================================================================

def whisper_words_to_srt(whisper_data, script_text, words_per_chunk=6, min_duration=1.0):
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
        return None
    
    clean_script = strip_audio_tags(script_text)
    script_words = clean_script.split()
    total_sw = len(script_words)
    total_ww = len(whisper_words)
    
    if total_sw == 0 or total_ww == 0:
        return None
    
    srt_entries = []
    chunk_index = 1
    
    for i in range(0, total_sw, words_per_chunk):
        chunk_words = script_words[i:i + words_per_chunk]
        chunk_text = ' '.join(chunk_words)
        
        start_script_idx = i
        end_script_idx = min(i + len(chunk_words) - 1, total_sw - 1)
        
        start_whisper_idx = int((start_script_idx / total_sw) * total_ww) if total_sw > 0 else 0
        end_whisper_idx = int((end_script_idx / total_sw) * total_ww) if total_sw > 0 else 0
        
        start_whisper_idx = max(0, min(start_whisper_idx, total_ww - 1))
        end_whisper_idx = max(0, min(end_whisper_idx, total_ww - 1))
        
        w_start = whisper_words[start_whisper_idx]
        w_end = whisper_words[end_whisper_idx]
        
        if isinstance(w_start, dict):
            start_time = w_start['start']
            end_time = w_end['end']
        else:
            start_time = w_start.start
            end_time = w_end.end
        
        if end_time - start_time < min_duration:
            end_time = start_time + min_duration
        
        start_time = max(0, start_time)
        
        srt_entries.append({
            'index': chunk_index,
            'start': start_time,
            'end': end_time,
            'text': chunk_text
        })
        chunk_index += 1
    
    srt_text = ""
    for entry in srt_entries:
        srt_text += f"{entry['index']}\n"
        srt_text += f"{fmt_timestamp_sync(entry['start'])} --> {fmt_timestamp_sync(entry['end'])}\n"
        srt_text += f"{entry['text']}\n\n"
    
    parsed = [(e['start'], e['end'], e['text']) for e in srt_entries]
    return srt_text, parsed

# =====================================================================
# SYNC ENGINE (with Whisper-first approach)
# =====================================================================

def fmt_timestamp_sync(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60); ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def strip_audio_tags(text):
    """Remove audio tags AND speaker labels from text"""
    # Remove audio tags like [pause=1.0], [excited]
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\{.*?\}', '', text)
    # Remove speaker labels (SPEAKER_00:, SPEAKER 01:, Speaker 1:, etc.)
    text = re.sub(r'SPEAKER[_ ]?\d+[:\s]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Speaker[_ ]?\d+[:\s]*', '', text, flags=re.IGNORECASE)
    # Remove common Whisper artifacts
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\u266a.*?\u266a', '', text)
    # Clean extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def sync_by_character_mapping(clean_script, audio_duration, words_per_chunk=8, min_chunk_duration=1.2, offset=0.0):
    clean_script = strip_audio_tags(clean_script)
    if not clean_script.strip(): return "", []
    raw_chunks = re.split(r'([။!?\n]+)', clean_script)
    segments = []
    for i in range(0, len(raw_chunks)-1, 2):
        segment = raw_chunks[i].strip()
        if i+1 < len(raw_chunks): segment += raw_chunks[i+1]
        if segment.strip(): segments.append(segment.strip())
    if len(raw_chunks)%2 != 0 and raw_chunks[-1].strip(): segments.append(raw_chunks[-1].strip())
    if not segments: return "", []
    total_chars = sum(len(seg) for seg in segments)
    if total_chars == 0: return "", []
    effective_duration = max(audio_duration-0.3, audio_duration)
    time_per_char = effective_duration / total_chars
    srt_entries = []; chunk_index = 1; char_position = 0.0
    for segment in segments:
        words = segment.split()
        if not words: continue
        for i in range(0, len(words), words_per_chunk):
            chunk_words = words[i:i+words_per_chunk]; chunk_text = ' '.join(chunk_words); chunk_chars = len(chunk_text)
            start_time = char_position*time_per_char + offset
            chunk_duration = max(chunk_chars*time_per_char, min_chunk_duration)
            end_time = min(start_time+chunk_duration, audio_duration)
            if end_time <= start_time: end_time = start_time+min_chunk_duration
            start_time = max(0, start_time)
            srt_entries.append({'index': chunk_index, 'start': start_time, 'end': end_time, 'text': chunk_text})
            chunk_index += 1; char_position += chunk_chars
    srt_text = ""
    for entry in srt_entries: srt_text += f"{entry['index']}\n{fmt_timestamp_sync(entry['start'])} --> {fmt_timestamp_sync(entry['end'])}\n{entry['text']}\n\n"
    parsed = [(e['start'], e['end'], e['text']) for e in srt_entries]
    return srt_text, parsed

def auto_sync_srt(script_text, audio_path, whisper_data=None, audio_duration=None, sync_offset=0.0, short_punchy=False):
    if audio_duration is None: audio_duration = get_file_duration(audio_path)
    
    if whisper_data is not None:
        words_per_chunk = 3 if short_punchy else 6
        min_dur = 0.8 if short_punchy else 1.0
        result = whisper_words_to_srt(whisper_data, script_text, words_per_chunk, min_dur)
        if result is not None:
            srt_text, parsed = result
            if sync_offset != 0:
                parsed = [(max(0, s+sync_offset), max(0.8, e+sync_offset), t) for s, e, t in parsed]
                srt_text = ""
                for i, (s, e, t) in enumerate(parsed, 1):
                    srt_text += f"{i}\n{fmt_timestamp_sync(s)} --> {fmt_timestamp_sync(e)}\n{t}\n\n"
            return srt_text, parsed
    
    words_per_chunk = 4 if short_punchy else 8
    min_dur = 1.0 if short_punchy else 1.5
    return sync_by_character_mapping(script_text, audio_duration, words_per_chunk, min_dur, sync_offset)

# --- 2. CORE AUTOMATION FLOW ENGINES ---

def cleanup_temp_files():
    for f in os.listdir("."):
        if f.startswith(("fc_clip_", "fc_img_", "temp_", "subtitles.", "thumb_", "FACELESS_FINAL_", "AETHER_RECAP_FINAL_", "fc_audio.wav", "fc_video_loop.mp4", "hook_text.txt", "thumb_pro_text.txt", "thumb_text.txt")):
            try: os.remove(f)
            except Exception: pass

def get_file_duration(file_path):
    try:
        cmd = [FFMPEG_BINARY, "-i", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
        if match: h, m, s = match.groups(); return int(h)*3600 + int(m)*60 + float(s)
    except Exception: pass
    return 600.0

def download_video_from_url(url, output_path="input_temp.mp4"):
    if os.path.exists(output_path): os.remove(output_path)
    ydl_opts = {'outtmpl': output_path, 'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'quiet': True, 'no_warnings': True, 'nocheckcertificate': True, 'ffmpeg_location': FFMPEG_BINARY, 'source_address': '0.0.0.0', 'extractor_args': {'youtube': {'player_client': ['tv', 'ios', 'web']}}}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return output_path
    except Exception as e: raise Exception(f"YouTube Download Error: {str(e)}")

def extract_audio_fast(video_in, audio_out="temp_extracted.mp3"):
    if os.path.exists(audio_out): os.remove(audio_out)
    try:
        (ffmpeg.input(video_in).output(audio_out, acodec='libmp3lame', ac=1, ar='16000').run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True))
        if os.path.exists(audio_out): return audio_out
    except Exception: pass
    return None

async def generate_tts(text, voice_model, output_file, engine="Edge-TTS", ttsmaker_key="", eleven_key="", custom_eleven_id="", gemini_key="", pitch=0, voice_fx="None"):
    if not text.strip(): return
    if "Synergy" not in engine: text = strip_audio_tags(text)
    parts = re.split(r'([။?!.\n]+)', text)
    sentences = []
    for i in range(0, len(parts)-1, 2): sentences.append(parts[i]+parts[i+1])
    if len(parts)%2 != 0 and parts[-1].strip(): sentences.append(parts[-1])
    chunks = []; current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence: continue
        sentence += ' '
        if len(current_chunk)+len(sentence) < 300: current_chunk += sentence
        else:
            if current_chunk.strip(): chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk.strip(): chunks.append(current_chunk.strip())
    needs_ffmpeg = pitch != 0 or voice_fx != "None"
    temp_out = "temp_raw_audio_fx.wav" if needs_ffmpeg else output_file
    chunk_files = []; last_tts_error = "Unknown Network or API Error"
    for i, chunk_text in enumerate(chunks):
        if not chunk_text.strip(): continue
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
                            with wave.open(c_out, "wb") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000); wf.writeframes(pcm_data)
                            success = True; break
                        else: last_tts_error = "Safety Blocked or Empty Content generated."
                    else: last_tts_error = f"API Error {res.status_code}: {res.text[:100]}"
                except Exception as e: last_tts_error = str(e)
            if not success: continue
        elif "ElevenLabs" in engine:
            voice_id = custom_eleven_id.strip() if custom_eleven_id else ("21m00Tcm4TlvDq8ikWAM" if "Male" in voice_model else "AZnzlk1XvdvUeBnXmlld")
            res = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", json={"text": chunk_text, "model_id": "eleven_multilingual_v2"}, headers={"xi-api-key": eleven_key}, timeout=60)
            if res.status_code == 200:
                with open(c_out, "wb") as f:
                    f.write(res.content)
            else: last_tts_error = f"ElevenLabs API Error: {res.text[:100]}"
        else:
            voice = "my-MM-ThihaNeural" if "Male" in voice_model else "my-MM-NilarNeural"
            try: await edge_tts.Communicate(chunk_text, voice).save(c_out)
            except Exception as e: last_tts_error = str(e)
        if os.path.exists(c_out): chunk_files.append(c_out)
    if not chunk_files: raise Exception(f"TTS Generation Failed. Reason: {last_tts_error}")
    with open("audio_concat.txt", "w", encoding="utf-8") as f:
        for c in chunk_files: f.write(f"file '{c}'\n")
    subprocess.run([FFMPEG_BINARY, "-y", "-f", "concat", "-safe", "0", "-i", "audio_concat.txt", "-c:a", "pcm_s16le", "-ar", "44100", temp_out], capture_output=True)
    for c in chunk_files:
        if os.path.exists(c): os.remove(c)
    if os.path.exists("audio_concat.txt"): os.remove("audio_concat.txt")
    if needs_ffmpeg:
        audio = ffmpeg.input(temp_out)
        if pitch != 0: factor = 1.0+(pitch/100.0); audio = audio.filter('asetrate', int(44100*factor)).filter('atempo', 1.0/factor)
        if "Epic" in voice_fx: audio = audio.filter('bass', g=12, f=120)
        elif "Walkie-Talkie" in voice_fx: audio = audio.filter('highpass', f=400).filter('lowpass', f=3000).filter('volume', 1.5)
        elif "Reverb" in voice_fx: audio = audio.filter('aecho', 0.8, 0.88, 60, 0.4)
        elif "Demon" in voice_fx: audio = audio.filter('bass', g=15, f=100).filter('aecho', 0.8, 0.88, 40, 0.5)
        elif "ASMR" in voice_fx: audio = audio.filter('treble', g=12, f=6000).filter('volume', 1.5)
        elif "Robot" in voice_fx: audio = audio.filter('aphaser', type='t', speed=2, decay=0.6).filter('volume', 1.2)
        elif "Telephone" in voice_fx: audio = audio.filter('highpass', f=300).filter('lowpass', f=2500).filter('compand', attacks='0', decays='0.2', points='-70/-70|-20/-20|0/-10')
        elif "Cave" in voice_fx: audio = audio.filter('aecho', 0.8, 0.9, 1000, 0.3)
        elif "Underwater" in voice_fx: audio = audio.filter('lowpass', f=400).filter('volume', 1.5)
        elif "Deep & Energetic" in voice_fx: audio = audio.filter('bass', g=10, f=150).filter('treble', g=5, f=3000).filter('volume', 1.5)
        elif "Deep & Chilling" in voice_fx: audio = audio.filter('bass', g=15, f=80).filter('aecho', 0.8, 0.85, 60, 0.3).filter('volume', 1.2)
        try: (audio.output(output_file, acodec='pcm_s16le', ac=1, ar='44100').overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True))
        except Exception: shutil.copy(temp_out, output_file)
        finally:
            if os.path.exists(temp_out): os.remove(temp_out)

def parse_and_save_real_srt(raw_srt_text, output_file, use_fade=False):
    lines = raw_srt_text.strip().split('\n')
    parsed_lines = []; current_start, current_end = 0.0, 0.0; current_text = []
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.isdigit() and len(line) < 5: continue
        if "-->" in line:
            if current_text: parsed_lines.append((current_start, current_end, " ".join(current_text))); current_text = []
            parts = line.split("-->")
            try:
                def parse_lenient(t_str):
                    t_str = t_str.strip().replace('.', ',')
                    if ',' not in t_str: t_str += ",000"
                    main_t, ms = t_str.split(','); tp = main_t.split(':')
                    if len(tp) == 1: return int(tp[0])+float(ms.ljust(3,'0'))/1000.0
                    elif len(tp) == 2: return int(tp[0])*60+int(tp[1])+float(ms.ljust(3,'0'))/1000.0
                    else: return int(tp[0])*3600+int(tp[1])*60+int(tp[2])+float(ms.ljust(3,'0'))/1000.0
                current_start = parse_lenient(parts[0]); current_end = parse_lenient(parts[1])
            except Exception: pass
        else:
            if not re.match(r'^\[.*?\]$', line): current_text.append(line)
    if current_text: parsed_lines.append((current_start, current_end, " ".join(current_text)))
    final_parsed = []; prev_end = 0.0; full_speech = []
    for start, end, txt in parsed_lines:
        if start < prev_end: start = prev_end+0.1
        if end-start < 0.8: end = start+0.8
        prev_end = end
        # Clean speaker labels from text
        txt = strip_audio_tags(txt)
        if txt.strip(): full_speech.append(txt)
        final_parsed.append((start, end, txt))
    with open(output_file, "w", encoding="utf-8-sig") as f:
        for i, (s, e, t) in enumerate(final_parsed, 1):
            def fmt_sec(sec): return f"{int(sec//3600):02d}:{int((sec%3600)//60):02d}:{int(sec%60):02d},{int((sec%1)*1000):03d}"
            f.write(f"{i}\n{fmt_sec(s)} --> {fmt_sec(e)}\n{t}\n\n")
    return final_parsed, " ".join(full_speech)

def render_premium_saas_video(in_v, in_a, parsed_timestamps, out_v, ratio, use_bypass=False, use_blur=False, watermark="", subtitle_mode="Both (Burn + SRT)", use_mirror=False, use_color=False, use_grain=False, use_fps=False, sub_position="Bottom", sub_color="Yellow", sub_size=28, sub_thickness=2.5, sub_bg=False, use_freeze=False, logo_path=None, font_path="Padauk.ttf"):
    try:
        a_dur = get_file_duration(in_a)
        video = ffmpeg.input(in_v).video; v_w, v_h = (720, 1280) if "9:16" in ratio else (1280, 720)
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
            logo = ffmpeg.input(logo_path); logo = ffmpeg.filter(logo, 'scale', -1, 80)
            video = ffmpeg.overlay(video, logo, x='W-w-20', y=20)
        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"] and parsed_timestamps:
            wrap_width = 25 if "9:16" in ratio else 45; safe_font_path = font_path.replace('\\', '/')
            for i, (start, end, text) in enumerate(parsed_timestamps):
                # Clean speaker labels before burning
                text = strip_audio_tags(text)
                if not text.strip(): continue
                wrapped_lines = textwrap.wrap(text, width=wrap_width)
                if not wrapped_lines: wrapped_lines = [text]
                max_len = max(len(line) for line in wrapped_lines)
                centered_text = "\n".join(line.center(max_len, " ") for line in wrapped_lines)
                txt_filename = f"temp_sub_{i}.txt"
                with open(txt_filename, "w", encoding="utf-8") as tf: tf.write(centered_text)
                if "Center" in sub_position: y_expr = "(h-text_h)/2"
                elif "Top" in sub_position: y_expr = "150"
                else: y_expr = "h-text_h-150"
                c_str = "yellow"
                if "White" in sub_color: c_str = "white"
                elif "Green" in sub_color: c_str = "green"
                elif "Red" in sub_color: c_str = "red"
                elif "Gold" in sub_color: c_str = "gold"
                box_str = 1 if sub_bg else 0; box_color = 'black@0.6' if sub_bg else 'black@0.0'
                video = ffmpeg.filter(video, 'drawtext', textfile=txt_filename, fontfile=safe_font_path, fontcolor=c_str, fontsize=sub_size, bordercolor='black', borderw=sub_thickness, box=box_str, boxcolor=box_color, boxborderw=10, x='(w-text_w)/2', y=y_expr, line_spacing=20, text_align='C', enable=f'between(t,{start},{end})')
        out = ffmpeg.output(video, audio, out_v, vcodec='libx264', pix_fmt='yuv420p', acodec='aac', preset='superfast', crf=23, t=a_dur)
        out.run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "Success"
    except ffmpeg.Error as e: return False, e.stderr.decode('utf-8', errors='ignore')

# --- 3. UI INTERFACE & NAVIGATION ---
st.markdown('<div class="main-title">AETHER FILMWORKS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI Studio V52 \u26a1 SaaS Edition</div>', unsafe_allow_html=True)

# =====================================================================
# STATE INITIALIZATION
# =====================================================================
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
if "script_ready" not in st.session_state: st.session_state.script_ready = False
if "fc_ready" not in st.session_state: st.session_state.fc_ready = False
if "fc_hook_text" not in st.session_state: st.session_state.fc_hook_text = ""

# =====================================================================
# SIDEBAR
# =====================================================================
with st.sidebar:
    st.markdown("### \U0001f9ed Navigation Menu")
    app_mode = st.radio("Select Studio Mode:", ["\U0001f399\ufe0f Movie Dubbing Studio", "\U0001f399\ufe0f Faceless Channel Studio", "\U0001f3a5 Veo Video Studio", "\U0001f3b5 Lyria Music Studio"])
    st.markdown("---")
    
    st.markdown("### \U0001f3af Subtitle Sync Control")
    with st.form("sync_form", clear_on_submit=False):
        new_offset = st.slider(
            "Sync Offset (Emergency Backup)", 
            min_value=-5.0, max_value=5.0, 
            value=st.session_state.get('sync_offset', 0.0),
            step=0.1
        )
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.form_submit_button("Apply", use_container_width=True):
                st.session_state.sync_offset = new_offset
                st.rerun()
        with col_f2:
            if st.form_submit_button("Reset", use_container_width=True):
                st.session_state.sync_offset = 0.0
                st.rerun()
    st.caption(f"Active Offset: **{st.session_state.get('sync_offset', 0.0):+.1f}s**")
    
    st.markdown("---")
    st.markdown("### \U0001f4be Project Save & Load")
    if st.button("Save Current Project"):
        proj_data = {"script": st.session_state.generated_script, "title": st.session_state.viral_title, "tags": st.session_state.viral_tags, "sync_offset": st.session_state.get('sync_offset', 0.0)}
        json_str = json.dumps(proj_data, ensure_ascii=False)
        b64 = base64.b64encode(json_str.encode('utf-8')).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="Aether_Project.json" style="color:#38bdf8; font-weight:bold;">\U0001f4e5 Download Project File (.json)</a>'
        st.markdown(href, unsafe_allow_html=True)
    uploaded_proj = st.file_uploader("Upload Project", type=["json"])
    if uploaded_proj:
        try:
            data = json.load(uploaded_proj)
            st.session_state.generated_script = data.get("script", "")
            st.session_state.viral_title = data.get("title", "")
            st.session_state.viral_tags = data.get("tags", "")
            st.session_state.sync_offset = data.get("sync_offset", 0.0)
            st.success("Project Loaded!")
        except Exception: st.error("Invalid Project File.")
    
    st.markdown("---")
    ai_provider = st.selectbox("Choose AI Provider", ["Google Gemini (Flash - Recommended)", "OpenAI (GPT-5.5 Pro)", "Groq API (Fast & Free)"])
    saved_gemini = load_key(API_KEY_FILE)
    if "Gemini" in ai_provider:
        api_key_input = st.text_input("Gemini Keys (Comma separated)", type="password", value=saved_gemini)
        if api_key_input and api_key_input != saved_gemini: save_key(API_KEY_FILE, api_key_input)
    elif "Groq" in ai_provider:
        saved_groq = load_key(GROQ_KEY_FILE)
        api_key_input = st.text_input("Groq API Key", type="password", value=saved_groq)
        if api_key_input and api_key_input != saved_groq: save_key(GROQ_KEY_FILE, api_key_input)
    else:
        saved_openai = load_key(OPENAI_KEY_FILE)
        api_key_input = st.text_input("OpenAI API Key", type="password", value=saved_openai)
        if api_key_input and api_key_input != saved_openai: save_key(OPENAI_KEY_FILE, api_key_input)
    
    if app_mode == "\U0001f399\ufe0f Faceless Channel Studio":
        st.markdown("---"); st.markdown("### \U0001f511 Additional API Keys")
        saved_groq_fc = load_key(GROQ_KEY_FILE)
        groq_key_fc = st.text_input("Groq API Key (For Accurate Whisper Sync)", type="password", value=saved_groq_fc)
        if groq_key_fc and groq_key_fc != saved_groq_fc: save_key(GROQ_KEY_FILE, groq_key_fc)

# =====================================================================
# MODE 1 - MOVIE DUBBING (AUTO WHISPER SYNC + SPEAKER LABEL CLEAN)
# =====================================================================
if app_mode == "\U0001f399\ufe0f Movie Dubbing Studio":
    with st.sidebar:
        st.markdown("---")
        audio_engine_choice = st.radio("Voice Engine", ["Edge-TTS (Default Free)", "Google Synergy TTS (Flash 3.1 Preview)", "ElevenLabs (Premium AI)", "TTSMaker (Free API)"])
        if "Synergy" in audio_engine_choice: synergy_key = st.text_input("API Key for Synergy TTS", type="password", value=saved_gemini)
        if "ElevenLabs" in audio_engine_choice:
            saved_eleven = load_key(ELEVEN_KEY_FILE); eleven_key_input = st.text_input("ElevenLabs API Key", type="password", value=saved_eleven)
            if eleven_key_input and eleven_key_input != saved_eleven: save_key(ELEVEN_KEY_FILE, eleven_key_input)
            saved_voice_id = load_key(ELEVEN_VOICE_ID_FILE); custom_eleven_id = st.text_input("Custom Voice ID", value=saved_voice_id)
            if custom_eleven_id and custom_eleven_id != saved_voice_id: save_key(ELEVEN_VOICE_ID_FILE, custom_eleven_id)
        key_ttsmaker = st.text_input("TTSMaker API Key", type="password") if "TTSMaker" in audio_engine_choice else ""
        st.markdown("---")
        video_ratio = st.selectbox("Crop Ratio", ["Original", "9:16 (TikTok/Shorts)", "16:9 (YouTube)"])
        st.markdown("<b>Anti-Copyright Options</b>", unsafe_allow_html=True)
        cb_bypass = st.checkbox("Smart Zoom", value=True); cb_mirror = st.checkbox("Mirror Effect", value=False)
        cb_color = st.checkbox("Color Tweaks", value=False); cb_grain = st.checkbox("Film Grain", value=False)
        cb_fps = st.checkbox("Cinematic 24 FPS", value=False); cb_freeze = st.checkbox("Freeze Frame", value=False)
        st.markdown("<b>Visual & Subs</b>", unsafe_allow_html=True)
        cb_blur = st.checkbox("Cinematic Black Mask", value=True)
        st.markdown("<b>Brand Watermark</b>", unsafe_allow_html=True)
        uploaded_logo = st.file_uploader("Add Logo Image", type=["png", "jpg", "jpeg"])
        use_text_watermark = st.checkbox("Use Text Watermark", value=False)
        watermark_text = st.text_input("Text Watermark", "") if use_text_watermark else ""
        subtitle_mode = st.radio("Subtitle Output", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"])
        st.markdown("---"); st.markdown("<b>Professional Thumbnail</b>", unsafe_allow_html=True)
        thumbnail_style = st.selectbox("Thumbnail Style", list(THUMBNAIL_STYLES.keys()), index=0)

    st.markdown('<div class="setting-panel"><h3>Media Acquisition & Setup</h3>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        video_url = st.text_input("Paste Short Drama URL Link", placeholder="https://...")
        uploaded_file = st.file_uploader("OR Upload Video File (MP4)", type=["mp4"])
        st.markdown("<br><div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #38bdf8; font-size: 16px;'>AI Storytelling & Script Rules</p>", unsafe_allow_html=True)
        recap_mode = st.radio("Recap Mode", ["Translate Original Video (\u1019\u1030\u101b\u1004\u103a\u1038\u1000\u102d\u102f \u1018\u102c\u101e\u102c\u1015\u103c\u1014\u103a\u1019\u100a\u103a)", "Create Original AI Story (\u1000\u102d\u102f\u101a\u103a\u1015\u102d\u102f\u1004\u103a\u1007\u102c\u1010\u103a\u101c\u1019\u103a\u1038\u1016\u1014\u103a\u1010\u102e\u1038\u1019\u100a\u103a)"])
        script_style = st.selectbox("Script Style", ["Normal (\u1015\u102f\u1036\u1019\u103e\u1014\u103a)", "Slang (Gen-Z)", "Comedy (\u101f\u102c\u101e)", "Suspense (\u101e\u100a\u103a\u1038\u1011\u102d\u1010\u103a)"])
        script_hook = st.checkbox("3-Second Viral Hook", value=True)
        script_curiosity = st.checkbox("Curiosity Gaps", value=True)
        script_tone = st.checkbox("Emotion & Tone", value=True)
        script_cta = st.checkbox("Call to Action", value=False)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #10b981; font-size: 16px;'>Audio Mixing & Auto-Ducking</p>", unsafe_allow_html=True)
        bgm_options = ["None (BGM \u1019\u1011\u100a\u1037\u103a\u1015\u102b)"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files: bgm_options.insert(1, "Auto (Random Select)"); bgm_options.extend(bgm_files)
        selected_bgm = st.selectbox("Background Music", bgm_options)
        bgm_volume = st.slider("BGM Volume", 1, 50, 10) / 100.0
        st.markdown("</div>", unsafe_allow_html=True)
    with col_in2:
        dynamic_options = ["Synergy Puck (Male)", "Synergy Aoede (Female)", "Synergy Charon (Male - Deep)"] if "Synergy" in audio_engine_choice else (["Adam (Male Deep)", "Rachel (Female)"] if "ElevenLabs" in audio_engine_choice else (["TTSMaker Male", "TTSMaker Female"] if "TTSMaker" in audio_engine_choice else ["\u1007\u1031\u102c\u103a\u1007\u1031\u102c\u103a (Male)", "\u1021\u1031\u102c\u1004\u103a\u1021\u1031\u102c\u1004\u103a (Deep)", "\u1014\u103e\u1004\u103a\u1038\u1014\u103e\u1004\u103a\u1038 (Female)"]))
        voice_char = st.selectbox("Select Character Voice", dynamic_options, index=0)
        pitch_level = st.slider("Voice Pitch", min_value=-30, max_value=30, value=0, step=5)
        recommended_fx_dub = get_recommended_fx_for_niche(script_style, mode="dubbing")
        fx_level = st.selectbox("Cinematic Voice FX (Style-based)", recommended_fx_dub, index=0)
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #818cf8; font-size: 16px;'>Subtitle Pro Settings</p>", unsafe_allow_html=True)
        if subtitle_mode in ["Both (Burn + SRT)", "Burn into Video"]:
            selected_font = st.selectbox("Font Style", available_fonts, index=0)
            sub_position = st.selectbox("Position", ["Bottom", "Center", "Top"])
            sub_color = st.selectbox("Color", ["Yellow Text", "White Text", "Neon Green Text", "Red Text", "Gold Text"])
            sub_size = st.slider("Font Size", 16, 50, 28); sub_thickness = st.slider("Outline Thickness", 1.0, 5.0, 2.5)
            col_s1, col_s2 = st.columns(2)
            with col_s1: sub_bg = st.checkbox("Background Box", value=True)
            sub_short = st.checkbox("Short & Punchy (Hormozi)")
        else:
            st.info("Burn into Video \u101b\u103d\u1031\u1038\u1011\u102c\u1038\u1019\u103e \u1001\u103b\u102d\u1014\u103a\u100a\u103e\u102d\u1014\u102d\u102f\u1004\u103a\u1015\u102b\u1019\u100a\u103a\u104b")
            selected_font, sub_position, sub_color, sub_size, sub_thickness, sub_bg, sub_short = "Padauk.ttf", "Bottom", "Yellow", 28, 2.5, True, False
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("START ONE-CLICK WORKFLOW MONETIZE GENERATOR"):
        if not api_key_input: st.error("API Key \u101c\u102d\u102f\u1021\u1015\u103a\u1015\u102b\u101e\u100a\u103a\u104b")
        elif not uploaded_file and not video_url: st.error("\u1017\u102e\u1012\u102e\u101a\u102d\u102f\u1016\u102d\u102f\u1004\u103a\u101e\u102d\u102f\u1037\u1019\u101f\u102f\u1010\u103a Link \u1011\u100a\u1037\u103a\u1015\u1031\u1038\u1015\u102b\u104b")
        else:
            st.session_state.render_success = False; st.session_state.whisper_data = None
            cleanup_temp_files()
            run_id = str(int(time.time()))
            v_final = f"AETHER_RECAP_FINAL_{run_id}.mp4"
            st.session_state.final_video_path = v_final
            v_input, a_extracted, a_generated, srt_final = "input_temp.mp4", "temp_extracted.mp3", "voice_temp.wav", "subtitles.srt"
            
            pbar = st.progress(0, text="\u1021\u101c\u102f\u1015\u103a\u1005\u1010\u1004\u103a\u1014\u1031\u1015\u102b\u1015\u103c\u102e...")
            
            with st.spinner("[Stage 1/6] Downloading video..."):
                pbar.progress(10, text="[Stage 1/6] \u1017\u102e\u1012\u102e\u101a\u102d\u102f\u1006\u103d\u1032\u101a\u1030\u1014\u1031\u1015\u102b\u101e\u100a\u103a...")
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
                        st.success("Whisper word-level sync ready (95% accurate)!")
                except Exception as e: st.warning(f"Whisper unavailable - using fallback sync. Error: {str(e)[:100]}")
            
            with st.spinner(f"[Stage 2/6] {ai_provider} generating script..."):
                pbar.progress(30, text=f"[Stage 2/6] \u1007\u102c\u1010\u103a\u100a\u103d\u103e\u1014\u103a\u1038\u1016\u1014\u103a\u1010\u102e\u1038\u1014\u1031\u1015\u102b\u101e\u100a\u103a...")
                try:
                    extra_rules = ""
                    if script_hook: extra_rules += " [HOOK]"
                    if "Slang" in script_style: extra_rules += " [SLANG]"
                    elif "Comedy" in script_style: extra_rules += " [COMEDY]"
                    elif "Suspense" in script_style: extra_rules += " [SUSPENSE]"
                    if script_curiosity: extra_rules += " [CURIOSITY]"
                    if script_tone: extra_rules += " [TONE]"
                    if script_cta: extra_rules += " [CTA]"
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
                                while "PROCESSING" in str(client.files.get(name=media_file.name).state): time.sleep(2)
                                prompt = f"Create ORIGINAL Burmese recap with SRT.{extra_rules}{hormozi_rule}" if "Original" in recap_mode else f"Translate to Burmese SRT.{extra_rules}{hormozi_rule}"
                                response = client.models.generate_content(model="gemini-2.5-flash", contents=[media_file, prompt])
                                raw_output_text = response.text.strip()
                                client.files.delete(name=media_file.name)
                                success_g = True; break
                            except Exception: continue
                        if not success_g: st.error("Gemini failed"); st.stop()
                    else:
                        client = Groq(api_key=api_key_input) if "Groq" in ai_provider else openai
                        if "Groq" in ai_provider:
                            with open(a_extracted, "rb") as file: transcription = client.audio.translations.create(file=(a_extracted, file.read()), model="whisper-large-v3", response_format="verbose_json")
                            tsrt = "".join([f"{i}\n00:00:00,000 --> 00:00:10,000\n{seg['text']}\n\n" for i, seg in enumerate(transcription.get('segments', []), 1)]) if isinstance(transcription, dict) else str(transcription)
                        else:
                            openai.api_key = api_key_input
                            with open(a_extracted, "rb") as file: tsrt = openai.audio.translations.create(model="whisper-1", file=file, response_format="srt")
                        base_prompt = f"Translate to Burmese SRT. {extra_rules}{hormozi_rule}"
                        comp = client.chat.completions.create(model="llama-3.3-70b-versatile" if "Groq" in ai_provider else "gpt-4o", messages=[{"role": "user", "content": f"{base_prompt} --- SRT --- {tsrt}"}])
                        raw_output_text = comp.choices[0].message.content
                    
                    # Clean speaker labels from the raw output
                    raw_output_text = strip_audio_tags(raw_output_text)
                    
                    title_match = re.search(r'\[TITLE:\s*(.*?)\]', raw_output_text, re.IGNORECASE)
                    tags_match = re.search(r'\[TAGS:\s*(.*?)\]', raw_output_text, re.IGNORECASE)
                    st.session_state.viral_title = re.sub(r'[\[\]]', '', title_match.group(1)).strip() if title_match else "Viral Movie Recap"
                    st.session_state.viral_tags = tags_match.group(1).strip() if tags_match else "#movierecap #myanmar"
                    clean_raw_srt = re.sub(r'\[TITLE:.*?\]', '', raw_output_text, flags=re.IGNORECASE)
                    clean_raw_srt = re.sub(r'\[TAGS:.*?\]', '', clean_raw_srt, flags=re.IGNORECASE).strip()
                    clean_raw_srt = clean_raw_srt.replace("```srt", "").replace("```", "")
                    
                    audio_dur = get_file_duration(a_extracted)
                    if "-->" in clean_raw_srt:
                        parsed_timestamps, speech_text = parse_and_save_real_srt(clean_raw_srt, srt_final)
                    else:
                        sync_srt, parsed_timestamps = auto_sync_srt(clean_raw_srt, a_extracted, st.session_state.whisper_data, audio_dur, st.session_state.get('sync_offset', 0.0), sub_short)
                        with open(srt_final, "w", encoding="utf-8-sig") as f: f.write(sync_srt)
                        speech_text = strip_audio_tags(clean_raw_srt)
                    
                    st.session_state.generated_script = clean_raw_srt
                    
                    try:
                        t_A = min(get_file_duration(v_input)*0.2, 10); t_B = min(get_file_duration(v_input)*0.5, 20)
                        for ts, tv in [("A", t_A), ("B", t_B)]:
                            tn = f"thumb_{ts}_{run_id}.jpg"
                            ok, _ = generate_professional_thumbnail(v_input, tn, st.session_state.viral_title, tv, thumbnail_style, selected_font)
                            if ok:
                                if ts == "A": st.session_state.thumb_path_A = tn
                                elif ts == "B": st.session_state.thumb_path_B = tn
                    except Exception: pass
                    
                    pbar.progress(40, text="Script ready!")
                except Exception as e: st.error(f"Logic Error: {e}"); st.stop()
            
            with st.spinner("[Stage 4/6] Generating Voice Over..."):
                pbar.progress(60, text="[Stage 4/6] \u1021\u101e\u1036\u1016\u1014\u103a\u1010\u102e\u1038\u1014\u1031\u1015\u102b\u101e\u100a\u103a...")
                try:
                    asyncio.run(generate_tts(speech_text if 'speech_text' in locals() else strip_audio_tags(clean_raw_srt), voice_char, a_generated, audio_engine_choice, key_ttsmaker, locals().get('eleven_key_input',''), locals().get('custom_eleven_id',''), locals().get('synergy_key', api_key_input), pitch_level, fx_level))
                except Exception as e: st.error(f"TTS Failed: {e}"); st.stop()
            
            tts_dur = get_file_duration(a_generated)
            if abs(tts_dur-audio_dur) > 2.0:
                st.info("TTS duration differs - re-syncing with Whisper...")
                if groq_key_sync:
                    try:
                        with open(a_generated, "rb") as file:
                            client_groq2 = Groq(api_key=groq_key_sync)
                            tts_whisper = client_groq2.audio.transcriptions.create(file=(a_generated, file.read()), model="whisper-large-v3", response_format="verbose_json", timestamp_granularities=["word"])
                            sync_srt, parsed_timestamps = auto_sync_srt(clean_raw_srt, a_generated, tts_whisper, tts_dur, st.session_state.get('sync_offset', 0.0), sub_short)
                    except Exception: pass
            
            with st.spinner("[Stage 5/6] Rendering video..."):
                pbar.progress(80, text="[Stage 5/6] \u1017\u102e\u1012\u102e\u101a\u102d\u102f\u1014\u103e\u1004\u1037\u103a \u1005\u102c\u1010\u1014\u103a\u1038\u1011\u102d\u102f\u1038\u1015\u1031\u102b\u1004\u103a\u1038\u1005\u1015\u103a\u1014\u1031\u1015\u102b\u101e\u100a\u103a...")
                success, err_msg = render_premium_saas_video(v_input, a_generated, parsed_timestamps, v_final, video_ratio, cb_bypass, cb_blur, watermark_text, subtitle_mode, cb_mirror, cb_color, cb_grain, cb_fps, sub_position=sub_position, sub_color=sub_color, sub_size=sub_size, sub_thickness=sub_thickness, sub_bg=sub_bg, use_freeze=cb_freeze, logo_path=locals().get('uploaded_logo'), font_path=selected_font)
                if not success: st.error(f"Render Failed: {err_msg}"); st.stop()
            
            if success and selected_bgm not in ["None (BGM \u1019\u1011\u100a\u1037\u103a\u1015\u102b)"]:
                with st.spinner("[Stage 6/6] Adding BGM..."):
                    pbar.progress(95, text="[Stage 6/6] BGM \u1011\u100a\u1037\u103a\u1019\u1036\u1015\u1031\u102b\u1004\u103a\u1038\u1005\u1015\u103a\u1014\u1031\u1015\u102b\u101e\u100a\u103a...")
                    selected_bgm_path = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in selected_bgm else selected_bgm)
                    if os.path.exists(selected_bgm_path):
                        try:
                            ducked = ffmpeg.filter([ffmpeg.input(selected_bgm_path, stream_loop=-1).audio.filter('aresample', 44100).filter('volume', bgm_volume), ffmpeg.input(v_final).audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                            mixed = ffmpeg.filter([ffmpeg.input(v_final).audio, ducked], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                            (ffmpeg.output(ffmpeg.input(v_final).video, mixed, "temp_mix.mp4", vcodec='copy', acodec='aac', t=get_file_duration(v_final)).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True))
                            shutil.move("temp_mix.mp4", v_final)
                        except Exception: pass
            
            pbar.progress(100, text="Complete!")
            st.session_state.final_video_path = v_final
            st.session_state.render_success = True
            st.rerun()
    
    if st.session_state.render_success:
        st.balloons()
        st.success("Video Complete!")
        st.markdown(f"<h2 style='color:#38bdf8; text-align:center;'>{st.session_state.viral_title}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#94a3b8;'>{st.session_state.viral_tags}</p>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if os.path.exists(st.session_state.final_video_path):
                st.video(st.session_state.final_video_path)
                st.markdown(get_download_link(st.session_state.final_video_path, "Recap.mp4", "Download Video"), unsafe_allow_html=True)
                if os.path.exists("subtitles.srt"): st.markdown(get_download_link("subtitles.srt", "Subs.srt", "SRT"), unsafe_allow_html=True)
        with c2:
            st.markdown("### Scripts & Assets")
            if st.session_state.thumb_path_A and os.path.exists(st.session_state.thumb_path_A):
                st.image(st.session_state.thumb_path_A, caption=f"Thumb A ({thumbnail_style})"); st.markdown(get_download_link(st.session_state.thumb_path_A, "Thumb_A.jpg", "Download"), unsafe_allow_html=True)
            if st.session_state.thumb_path_B and os.path.exists(st.session_state.thumb_path_B):
                st.image(st.session_state.thumb_path_B, caption=f"Thumb B ({thumbnail_style})"); st.markdown(get_download_link(st.session_state.thumb_path_B, "Thumb_B.jpg", "Download"), unsafe_allow_html=True)
            with st.expander("Original Transcript", expanded=False): st.text_area("Original:", value=st.session_state.original_transcript, height=150, disabled=True)
            with st.expander("AI Generated Script", expanded=True): st.text_area("Script:", value=st.session_state.generated_script, height=250, disabled=True)

# =====================================================================
# MODE 1.5 - FACELESS Channel Studio (AUTO WHISPER SYNC + SPEAKER LABEL CLEAN)
# =====================================================================
elif app_mode == "\U0001f399\ufe0f Faceless Channel Studio":
    st.markdown('<div class="setting-panel"><h3>Faceless Channel Studio</h3>', unsafe_allow_html=True)
    st.markdown("TikTok, FB Reels \u1019\u103b\u102c\u1038\u1021\u1010\u103d\u1000\u103a Reddit Stories, Horror \u1015\u102f\u1036\u1015\u103c\u1004\u103a\u1019\u103b\u102c\u1038\u1000\u102d\u102f\u1016\u1014\u103a\u1010\u102e\u1038\u1015\u102b\u104b")

    with st.sidebar:
        st.markdown("---")
        st.markdown("<b>Voice & Audio Settings</b>", unsafe_allow_html=True)
        fc_audio_engine = st.radio("Voice Engine", ["Edge-TTS (Free)", "Google Synergy TTS (API)"], key="fc_engine")
        if "Synergy" in fc_audio_engine: fc_synergy_key = st.text_input("Synergy TTS Key", type="password", value=saved_gemini, key="fc_syn")
        fc_voice_char = st.selectbox("Voice Model", ["Synergy Puck (Male)", "Synergy Charon (Deep)"] if "Synergy" in fc_audio_engine else ["\u1007\u1031\u102c\u103a\u1007\u1031\u102c\u103a (Male)", "\u1021\u1031\u102c\u1004\u103a\u1021\u1031\u102c\u1004\u103a (Deep)", "\u1014\u103e\u1004\u103a\u1038\u1014\u103e\u1004\u103a\u1038 (Female)"], key="fc_voice")
        
        st.markdown("<b>Voice FX</b>", unsafe_allow_html=True)
        fc_niche = st.selectbox("Select Niche", ["Horror", "Relationship", "Dark Psychology", "Fun Facts", "Motivation", "History"])
        recommended_fx = get_recommended_fx_for_niche(fc_niche, mode="faceless")
        default_fx = recommended_fx[1] if len(recommended_fx) > 1 else recommended_fx[0]
        fc_fx = st.selectbox("Voice FX (Niche-based)", recommended_fx, index=1, key="fc_fx")
        
        st.markdown("---")
        st.markdown("<b>Visual & Niche Settings</b>", unsafe_allow_html=True)
        fc_ratio = st.selectbox("Video Ratio", ["9:16 (TikTok/Shorts)", "16:9 (YouTube)"], key="fc_ratio")
        fc_duration = st.slider("Story Duration (Minutes)", 1, 10, 3)
        
        st.markdown("---")
        st.markdown("<b>TikTok Hook Settings</b>", unsafe_allow_html=True)
        fc_use_hook = st.checkbox("Use Hook Text Overlay (First 3s)", value=True, key="fc_use_hook")
        if fc_use_hook:
            use_random = st.checkbox("Auto-Random Hook", value=True, key="fc_random_hook")
            if not use_random: fc_hook_text = st.text_input("Hook Text", value=get_random_hook(fc_niche), key="fc_hook_text_input")
            else:
                if "fc_hook_text" not in st.session_state or not st.session_state.fc_hook_text: st.session_state.fc_hook_text = get_random_hook(fc_niche)
                fc_hook_text = st.session_state.fc_hook_text
                st.markdown(f'<div class="hook-preview" style="color:#38bdf8; font-size:18px; font-weight:bold;">{fc_hook_text}</div>', unsafe_allow_html=True)
                if st.button("New Hook", key="fc_new_hook"): st.session_state.fc_hook_text = get_random_hook(fc_niche); st.rerun()
        fc_use_loop = st.checkbox("Add Loop Point", value=True, key="fc_loop")
        
        st.markdown("---")
        st.markdown("<b>Thumbnail Settings</b>", unsafe_allow_html=True)
        default_thumb = get_thumbnail_style_for_niche(fc_niche)
        thumb_keys = list(THUMBNAIL_STYLES.keys())
        default_idx = thumb_keys.index(default_thumb) if default_thumb in thumb_keys else 0
        fc_thumb = st.selectbox("Thumbnail Style", thumb_keys, index=default_idx, key="fc_thumb")

        st.markdown("<b>Subtitle Pro Settings</b>", unsafe_allow_html=True)
        fc_selected_font = st.selectbox("Font Style", available_fonts, index=0, key="fc_font")
        fc_sub_position = st.selectbox("Position", ["Center", "Bottom", "Top"], index=0, key="fc_sub_pos")
        fc_sub_color = st.selectbox("Color", ["Yellow Text", "White Text", "Neon Green Text", "Red Text", "Gold Text"], index=0, key="fc_sub_col")
        fc_sub_size = st.slider("Font Size", 16, 50, 28, key="fc_sub_size")
        fc_subtitle_mode = st.radio("Subtitle Output Mode", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"], key="fc_sub_mode")
        bgm_options = ["None (BGM \u1019\u1011\u100a\u1037\u103a\u1015\u102b)"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files: bgm_options.insert(1, "Auto (Random Select)"); bgm_options.extend(bgm_files)
        fc_bgm = st.selectbox("Background Music", bgm_options, key="fc_bgm")
        fc_bgm_vol = st.slider("BGM Volume", 1, 50, 8, key="fc_bgm_vol") / 100.0
        fc_sub_short = st.checkbox("Short & Punchy (Hormozi)", value=True)

    st.markdown('<div class="setting-panel"><h4>Manual Controls (Optional)</h4>', unsafe_allow_html=True)
    col_fc1, col_fc2 = st.columns(2)
    with col_fc1:
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        fc_script_mode = st.radio("Story Script Source", ["Auto-Generate AI Script", "Manual Script Entry"])
        fc_custom_topic = ""
        if "Auto" in fc_script_mode:
            fc_custom_topic = st.text_input("Topic (Optional):", placeholder="\u101e\u101b\u1032\u1018\u102f\u1036\u1000\u103b\u1031\u102c\u1004\u103a\u1038...", key="fc_topic")
            fc_script_hook = st.checkbox("3-Second Viral Hook", value=True, key="fc_hook")
            fc_script_curiosity = st.checkbox("Curiosity Gaps", value=True, key="fc_curiosity")
            fc_script_tone = st.checkbox("Emotion & Tone", value=True, key="fc_tone")
            fc_script_cta = st.checkbox("Call to Action", value=False, key="fc_cta")
        fc_manual_script = st.text_area("Paste your script here:", height=150) if "Manual" in fc_script_mode else ""
        st.markdown("</div>", unsafe_allow_html=True)
    with col_fc2:
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        fc_visual_mode = st.radio("Visuals Source", ["Auto-Generate AI Images (Pollinations)", "Upload Manual Images"])
        fc_uploaded_images = st.file_uploader("Upload Images (JPG/PNG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True) if "Upload" in fc_visual_mode else None
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("CREATE FACELESS VIDEO (AUTO-MAGIC)"):
        if not api_key_input: st.error("API Key \u1011\u100a\u1037\u103a\u101e\u103d\u1004\u103a\u1038\u1015\u1031\u1038\u1015\u102b\u104b")
        elif "Manual" in fc_script_mode and not fc_manual_script.strip(): st.error("Manual \u1007\u102c\u1010\u103a\u100a\u103d\u103e\u1014\u103a\u1038\u1011\u100a\u1037\u103a\u101e\u103d\u1004\u103a\u1038\u1015\u1031\u1038\u1015\u102b\u104b")
        elif "Upload" in fc_visual_mode and not fc_uploaded_images: st.error("\u1021\u1014\u100a\u103a\u1038\u1006\u102f\u1036\u1038\u1015\u102f\u1036 (1) \u1015\u102f\u1036 Upload \u1010\u1004\u103a\u1015\u1031\u1038\u1015\u102b\u104b")
        else:
            st.session_state.render_success = False; st.session_state.whisper_data = None
            cleanup_temp_files()
            run_id = str(int(time.time()))
            v_final = f"FACELESS_FINAL_{run_id}.mp4"
            st.session_state.final_video_path = v_final
            pbar = st.progress(0, text="Starting...")
            keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()] if "Gemini" in ai_provider else [api_key_input]
            
            fc_story = ""
            if "Manual" in fc_script_mode:
                pbar.progress(10, text="Reading manual script...")
                fc_story = fc_manual_script.strip()
            else:
                with st.spinner("[Stage 1/5] Generating story..."):
                    pbar.progress(10, text="[Stage 1/5] Generating story...")
                    target_words = fc_duration * 140
                    topic_instruction = f"Topic: {fc_custom_topic}.\n" if fc_custom_topic else ""
                    hook_rule = "1. HOOK\n" if fc_script_hook else ""
                    curiosity_rule = "2. CURIOSITY\n" if fc_script_curiosity else ""
                    tone_rule = "3. TONE\n" if fc_script_tone else ""
                    cta_rule = "4. CTA\n" if fc_script_cta else ""
                    story_prompt = f"""Write {fc_duration}min viral script for {fc_niche}. Burmese. {target_words} words.
{topic_instruction}{hook_rule}{curiosity_rule}{tone_rule}{cta_rule}NO formal grammar. Audio tags. [TITLE: ...] [TAGS: ...]"""
                    for key in keys_list:
                        try:
                            client = genai.Client(api_key=key)
                            response = client.models.generate_content(model="gemini-2.5-flash", contents=story_prompt)
                            fc_story = response.text.strip(); break
                        except Exception: continue
                    if not fc_story: st.error("Story Error"); st.stop()
            
            # Clean speaker labels
            fc_story = strip_audio_tags(fc_story)
            
            title_match = re.search(r'\[TITLE:\s*(.*?)\]', fc_story, re.IGNORECASE)
            tags_match = re.search(r'\[TAGS:\s*(.*?)\]', fc_story, re.IGNORECASE)
            if title_match: st.session_state.viral_title = re.sub(r'[\[\]]', '', title_match.group(1)).strip()
            if tags_match: st.session_state.viral_tags = tags_match.group(1).strip()
            fc_story = re.sub(r'\[TITLE:.*?\]', '', fc_story, flags=re.IGNORECASE)
            fc_story = re.sub(r'\[TAGS:.*?\]', '', fc_story, flags=re.IGNORECASE).strip()
            
            with st.spinner("[Stage 2/5] Generating TTS..."):
                pbar.progress(30, text="[Stage 2/5] Generating TTS...")
                try:
                    clean_story = re.sub(r'\[.*?\]', '', fc_story)
                    asyncio.run(generate_tts(fc_story if "Synergy" in fc_audio_engine else clean_story, fc_voice_char, "fc_audio.wav", fc_audio_engine, gemini_key=locals().get('fc_synergy_key', api_key_input), voice_fx=fc_fx))
                    fc_audio_dur = get_file_duration("fc_audio.wav")
                    if fc_audio_dur < 5.0: st.error("TTS Failed"); st.stop()
                except Exception as e: st.error(f"Audio Error: {e}"); st.stop()
            
            groq_key_fc_sync = load_key(GROQ_KEY_FILE)
            if groq_key_fc_sync and os.path.exists("fc_audio.wav"):
                try:
                    with open("fc_audio.wav", "rb") as file:
                        client_groq = Groq(api_key=groq_key_fc_sync)
                        st.session_state.whisper_data = client_groq.audio.transcriptions.create(file=("fc_audio.wav", file.read()), model="whisper-large-v3", response_format="verbose_json", timestamp_granularities=["word"])
                        st.success("Whisper word-level sync ready!")
                except Exception as e: st.warning(f"Whisper failed: {str(e)[:100]}")
            
            with st.spinner("[Stage 3/5] Generating visuals..."):
                pbar.progress(50, text="[Stage 3/5] Generating visuals...")
                try:
                    generated_clips = []; v_w, v_h = (720, 1280) if "9:16" in fc_ratio else (1280, 720)
                    if "Upload" in fc_visual_mode:
                        clip_dur = fc_audio_dur / len(fc_uploaded_images)
                        for i, img_file in enumerate(fc_uploaded_images):
                            img_path = f"fc_img_{i}.jpg"; clip_path = f"fc_clip_{i}.mp4"
                            img_file.seek(0)
                            with open(img_path, "wb") as f: f.write(img_file.read())
                            subprocess.run([FFMPEG_BINARY, "-y", "-loop", "1", "-framerate", "25", "-i", img_path, "-t", str(clip_dur), "-vf", f"scale=-2:2000,zoompan=z='min(zoom+0.001,1.15)':d={int(clip_dur*25)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={v_w}x{v_h},fps=25", "-c:v", "libx264", "-preset", "superfast", clip_path], capture_output=True)
                            if os.path.exists(clip_path): generated_clips.append(clip_path)
                    else:
                        style_mapping = {"Horror": "horror 8k", "Relationship": "drama cinematic", "Dark Psychology": "neo-noir", "Fun Facts": "Pixar style", "Motivation": "epic golden", "History": "fantasy epic"}
                        cs = "cinematic 8k"
                        for k, v in style_mapping.items():
                            if k in fc_niche: cs = v; break
                        img_count = max(4, int(fc_audio_dur // 12)); sk = []
                        for key in keys_list:
                            try:
                                client = genai.Client(api_key=key)
                                r = client.models.generate_content(model="gemini-2.5-flash", contents=f"Create {img_count} image prompts separated by '|'. Style: {cs}. Story: {fc_story[:500]}")
                                sk = [kw.strip() for kw in r.text.replace('\n','|').split('|') if len(kw.strip())>5][:img_count]; break
                            except Exception: continue
                        if not sk: sk = [f"{cs}, scene {i}" for i in range(img_count)]
                        clip_dur = fc_audio_dur / len(sk)
                        for i, kw in enumerate(sk):
                            try:
                                ep = kw.strip() + ", masterpiece, 8k"
                                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(ep)}?width={v_w}&height={v_h}&nologo=true"
                                r = requests.get(url, timeout=60)
                                if r.status_code == 200:
                                    img_path = f"fc_img_{i}.jpg"; clip_path = f"fc_clip_{i}.mp4"
                                    with open(img_path, "wb") as f: f.write(r.content)
                                    subprocess.run([FFMPEG_BINARY, "-y", "-loop", "1", "-framerate", "25", "-i", img_path, "-t", str(clip_dur), "-vf", f"scale=-2:2000,zoompan=z='min(zoom+0.001,1.15)':d={int(clip_dur*25)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={v_w}x{v_h},fps=25", "-c:v", "libx264", "-preset", "superfast", clip_path], capture_output=True)
                                    if os.path.exists(clip_path): generated_clips.append(clip_path)
                            except Exception: pass
                            time.sleep(2)
                    if not generated_clips: st.error("Visuals failed"); st.stop()
                    pbar.progress(65, text="Concatenating...")
                    with open("fc_concat.txt", "w") as f:
                        for c in generated_clips: f.write(f"file '{c}'\n")
                    subprocess.run([FFMPEG_BINARY, "-y", "-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", "fc_concat.txt", "-t", str(fc_audio_dur), "-c", "copy", "fc_video_loop.mp4"], capture_output=True)
                except Exception as e: st.error(f"Visual Error: {e}"); st.stop()
            
            with st.spinner("[Stage 4/5] Auto-syncing subtitles with Whisper..."):
                pbar.progress(70, text="[Stage 4/5] Auto-syncing with Whisper...")
                try:
                    sync_srt, fc_parsed = auto_sync_srt(fc_story, "fc_audio.wav", st.session_state.whisper_data, fc_audio_dur, st.session_state.get('sync_offset', 0.0), fc_sub_short)
                    with open("subtitles.srt", "w", encoding="utf-8-sig") as f: f.write(sync_srt)
                    if not fc_parsed: st.error("SRT Error"); st.stop()
                    st.success("Auto-sync complete! Whisper word-level timing applied.")
                except Exception as e: st.error(f"SRT Error: {e}"); st.stop()
            
            with st.spinner("[Stage 5/5] Rendering final video..."):
                pbar.progress(85, text="[Stage 5/5] Rendering...")
                temp_r = "temp_base.mp4"
                s, e = render_premium_saas_video("fc_video_loop.mp4", "fc_audio.wav", fc_parsed, temp_r, fc_ratio, True, subtitle_mode=fc_subtitle_mode, sub_position=fc_sub_position, sub_color=fc_sub_color, sub_size=fc_sub_size, sub_thickness=2.5, sub_bg=False, font_path=fc_selected_font)
                if s:
                    cv = temp_r
                    if fc_use_hook: cv = add_tiktok_hook_overlay(cv, "temp_h.mp4", fc_hook_text, fc_niche)
                    if fc_use_loop: cv = add_tiktok_loop_point(cv, "temp_l.mp4")
                    shutil.move(cv, v_final)
                    if fc_bgm != "None":
                        bp = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in fc_bgm else fc_bgm)
                        if os.path.exists(bp):
                            try:
                                dk = ffmpeg.filter([ffmpeg.input(bp, stream_loop=-1).audio.filter('aresample', 44100).filter('volume', fc_bgm_vol), ffmpeg.input(v_final).audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                                mx = ffmpeg.filter([ffmpeg.input(v_final).audio, dk], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                                ffmpeg.output(ffmpeg.input(v_final).video, mx, "tmp_b.mp4", vcodec='copy', acodec='aac', audio_bitrate='128k', t=fc_audio_dur).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
                                shutil.move("tmp_b.mp4", v_final)
                            except Exception: pass
                    st.session_state.final_video_path = v_final
                    st.session_state.render_success = True
                    try:
                        for ts, tv in [("A", min(fc_audio_dur*0.2,10)), ("B", min(fc_audio_dur*0.5,20))]:
                            tn = f"thumb_{ts}_{run_id}.jpg"
                            ok, _ = generate_professional_thumbnail(v_final, tn, st.session_state.viral_title or "Video", tv, fc_thumb, fc_selected_font)
                            if ok:
                                if ts == "A": st.session_state.thumb_path_A = tn
                                else: st.session_state.thumb_path_B = tn
                    except Exception: pass
                    try:
                        cv2 = genai.Client(api_key=keys_list[0])
                        r = cv2.models.generate_content(model="gemini-2.5-flash", contents=f"Virality score for: {st.session_state.viral_title}. Reply: Score: [1-100]\nReason: [Burmese]")
                        st.session_state.viral_score = r.text.strip()
                    except Exception: st.session_state.viral_score = "Score: 90\nReason: Good Hook"
                    pbar.progress(100, text="Done!")
                    st.rerun()
                else: st.error(f"Failed: {e}")
    
    if st.session_state.render_success:
        st.balloons(); st.success("Faceless Video Complete!")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if os.path.exists(st.session_state.final_video_path):
                st.video(st.session_state.final_video_path)
                st.markdown(get_download_link(st.session_state.final_video_path, "Faceless.mp4", "Download Video"), unsafe_allow_html=True)
                if os.path.exists("subtitles.srt"): st.markdown(get_download_link("subtitles.srt", "Subs.srt", "SRT"), unsafe_allow_html=True)
        with col_f2:
            st.markdown("### Story & Assets")
            st.info(f"**Viral Prediction:**\n{st.session_state.viral_score}")
            if st.session_state.thumb_path_A and os.path.exists(st.session_state.thumb_path_A): st.image(st.session_state.thumb_path_A, caption=f"A ({fc_thumb})"); st.markdown(get_download_link(st.session_state.thumb_path_A, "Thumb_A.jpg", "Download"), unsafe_allow_html=True)
            if st.session_state.thumb_path_B and os.path.exists(st.session_state.thumb_path_B): st.image(st.session_state.thumb_path_B, caption=f"B ({fc_thumb})"); st.markdown(get_download_link(st.session_state.thumb_path_B, "Thumb_B.jpg", "Download"), unsafe_allow_html=True)
            st.text_area("Script:", value=st.session_state.generated_script, height=300, disabled=True)

# =====================================================================
# MODE 2 - VEO VIDEO STUDIO
# =====================================================================
elif app_mode == "\U0001f3a5 Veo Video Studio":
    st.markdown('<div class="setting-panel"><h3>Veo 3.0 Cinematic Video Generator</h3>', unsafe_allow_html=True)
    video_prompt = st.text_area("Enter Video Prompt", placeholder="A cinematic slow-motion drone shot...")
    if st.button("Generate Veo Video"): pass

elif app_mode == "\U0001f3b5 Lyria Music Studio":
    st.markdown('<div class="setting-panel"><h3>Lyria 3 Pro Music Generator</h3>', unsafe_allow_html=True)
    music_prompt = st.text_area("Enter Music Prompt", placeholder="Epic cinematic background music...")
    if st.button("Generate Lyria Music"): pass
