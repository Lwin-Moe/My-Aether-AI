# =====================================================================
# 📌 AETHER FILMWORKS AI // STUDIO V52 (FINAL PRODUCTION READY)
# =====================================================================

import streamlit as st
from google import genai 
import os
import asyncio
import edge_tts
import ffmpeg
import yt_dlp
import time
import imageio_ffmpeg
from datetime import timedelta
import requests
import re
from groq import Groq
import openai
import base64
import wave
import subprocess
import json
import datetime
import random
import shutil
import textwrap 
import urllib.parse 
import concurrent.futures 

# 👇 FIX: Prioritize system FFmpeg (which supports Burmese Text Shaping) over imageio_ffmpeg
if shutil.which("ffmpeg"):
    FFMPEG_BINARY = "ffmpeg"
else:
    FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

# --- Key Save Files ---
API_KEY_FILE = "saved_api_key.txt"
ELEVEN_KEY_FILE = "saved_eleven_key.txt"
GROQ_KEY_FILE = "saved_groq_key.txt"
OPENAI_KEY_FILE = "saved_openai_key.txt"
ELEVEN_VOICE_ID_FILE = "saved_eleven_voice_id.txt"
PEXELS_KEY_FILE = "saved_pexels_key.txt" 

def load_key(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f: return f.read().strip()
    return ""

def save_key(file_path, key):
    with open(file_path, "w", encoding="utf-8") as f: f.write(key)

def get_download_link(file_path, file_name, link_text):
    if not os.path.exists(file_path): return ""
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" style="display:block; text-align:center; margin-top:10px; padding:12px 20px; background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color:white; text-decoration:none; border-radius:8px; font-weight:bold;">📥 {link_text}</a>'

# --- 1. THEME & STYLING (PREMIUM PRO UI) ---
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
    </style>
''', unsafe_allow_html=True)

if "render_success" not in st.session_state: st.session_state.render_success = False
if "generated_script" not in st.session_state: st.session_state.generated_script = ""
if "original_transcript" not in st.session_state: st.session_state.original_transcript = ""
if "viral_title" not in st.session_state: st.session_state.viral_title = ""
if "viral_tags" not in st.session_state: st.session_state.viral_tags = ""
if "thumb_path" not in st.session_state: st.session_state.thumb_path = None

# --- 2. CORE AUTOMATION FLOW ENGINES ---
def get_file_duration(file_path):
    try:
        cmd = [FFMPEG_BINARY, "-i", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except: pass
    return 600.0 

def download_video_from_url(url, output_path="input_temp.mp4"):
    if os.path.exists(output_path): os.remove(output_path)
    ydl_opts = {
        'outtmpl': output_path, 
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 
        'quiet': True, 'no_warnings': True, 'nocheckcertificate': True,
        'ffmpeg_location': FFMPEG_BINARY, 'source_address': '0.0.0.0', 
        'extractor_args': {'youtube': {'player_client': ['tv', 'ios', 'web']}}, 
        'http_headers': { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36' }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return output_path
    except Exception as e: raise Exception(f"YouTube Download Error: {str(e)}")

def extract_audio_fast(video_in, audio_out="temp_extracted.mp3"):
    if os.path.exists(audio_out): os.remove(audio_out)
    try:
        (ffmpeg.input(video_in).output(audio_out, acodec='libmp3lame', ac=1, ar='16000')
         .run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True))
        if os.path.exists(audio_out): return audio_out
    except: pass
    try:
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_extracted', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'quiet': True, 'nocheckcertificate': True, 'source_address': '0.0.0.0', 'extractor_args': {'youtube': {'player_client': ['tv', 'ios', 'web']}}, 'ffmpeg_location': FFMPEG_BINARY}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.extract_info(video_in, download=True)
        return audio_out
    except: return None

async def generate_tts(text, voice_model, output_file, engine="Edge-TTS (Default Free)", ttsmaker_key="", eleven_key="", custom_eleven_id="", gemini_key="", pitch=0, voice_fx="None (Standard Voice)"):
    if not text.strip(): return
    needs_ffmpeg = pitch != 0 or voice_fx != "None (Standard Voice)"
    temp_out = "temp_raw_audio_fx.wav" if needs_ffmpeg else output_file

    if "Synergy" in engine:
        if not gemini_key: raise Exception("Gemini API Key လိုအပ်ပါသည်။")
        keys_list = [k.strip() for k in gemini_key.split(",") if k.strip()]
        voice_name = "Puck" if "Puck" in voice_model else ("Charon" if "Charon" in voice_model else "Aoede")
        prompt_text = "You are a professional Burmese movie narrator. Read the following text naturally. " + text
        payload = {"contents": [{"parts": [{"text": prompt_text}]}], "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": { "voiceConfig": { "prebuiltVoiceConfig": { "voiceName": voice_name } } }}}
        
        last_err = ""
        for idx, current_key in enumerate(keys_list):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={current_key}"
            try:
                res = requests.post(url, json=payload, timeout=300)
                if res.status_code == 200:
                    candidate = res.json().get("candidates", [{}])[0]
                    if candidate.get("finishReason") == "SAFETY": raise Exception("Safety Error")
                    pcm_data = base64.b64decode(candidate["content"]["parts"][0]["inlineData"]["data"])
                    with wave.open(temp_out, "wb") as wf:
                        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000); wf.writeframes(pcm_data)
                    break
                elif res.status_code == 429:
                    last_err = "Limit Reached"
                    continue
                else:
                    last_err = res.text
                    continue
            except Exception as e: 
                last_err = str(e); continue
        if not os.path.exists(temp_out): raise Exception(f"Keys Exhausted. {last_err}")
    elif "ElevenLabs" in engine:
        voice_id = custom_eleven_id.strip() if custom_eleven_id else ("21m00Tcm4TlvDq8ikWAM" if "Male" in voice_model else "AZnzlk1XvdvUeBnXmlld")
        res = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", json={"text": text, "model_id": "eleven_multilingual_v2"}, headers={"xi-api-key": eleven_key}, timeout=300)
        if res.status_code == 200:
            with open(temp_out, "wb") as f: f.write(res.content)
    elif "TTSMaker" in engine:
        voice_id = 781 if "Female" in voice_model else 780
        res = requests.post("https://api.ttsmaker.com/v1/create-tts-order", json={"tts_api_key": ttsmaker_key, "tts_text": text, "voice_id": voice_id, "audio_format": "mp3"}, timeout=300).json()
        if res.get("status") == "success":
            with open(temp_out, "wb") as f: f.write(requests.get(res["audio_file_url"]).content)
    else:
        voice = "my-MM-ThihaNeural" if "Male" in voice_model else "my-MM-NilarNeural"
        await edge_tts.Communicate(text, voice).save(temp_out)

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
        try: (audio.output(output_file, acodec='pcm_s16le', ac=1, ar='44100').overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True))
        except: import shutil; shutil.copy(temp_out, output_file)
        finally:
            if os.path.exists(temp_out): os.remove(temp_out)

def parse_and_save_real_srt(raw_srt_text, output_file, use_fade=False):
    marker = chr(96) * 3
    clean_srt = raw_srt_text.replace(f"{marker}srt", "").replace(marker, "").strip()
    with open(output_file, "w", encoding="utf-8-sig") as f: f.write(clean_srt)
    parsed_lines = []
    full_speech = []
    matches = list(re.finditer(r'(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})', clean_srt))
    for i in range(len(matches)):
        start_str = matches[i].group(1).replace('.', ',')
        end_str = matches[i].group(2).replace('.', ',')
        text_start = matches[i].end()
        if i + 1 < len(matches):
            block = clean_srt[text_start:matches[i+1].start()].strip()
            lines = block.split('\n')
            if len(lines) > 0 and lines[-1].strip().isdigit(): lines.pop()
            block = " ".join(lines)
        else: block = clean_srt[text_start:].strip().replace('\n', ' ')
        if block:
            try:
                def to_sec(t):
                    h, m, s_ms = t.split(':'); s, ms = s_ms.split(',')
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms.ljust(3, '0'))/1000.0
                text_content = block.strip()
                if use_fade: text_content = "{\\fad(250,250)}" + text_content
                parsed_lines.append((to_sec(start_str), to_sec(end_str), text_content))
                full_speech.append(block.strip())
            except: pass
    if not parsed_lines:
        text_only = re.sub(r'^\d+\s*$', '', clean_srt, flags=re.MULTILINE).strip()
        if text_only:
             parsed_lines.append((0.0, min(10.0, len(text_only)*0.1), text_only))
             full_speech.append(text_only)
        else:
             parsed_lines.append((0.0, 10.0, "[pause=1.0] စာတန်းထိုး အပြောင်းအလဲလုပ်နေပါသည်။"))
             full_speech.append("[pause=1.0] စာတန်းထိုး အပြောင်းအလဲလုပ်နေပါသည်။")
    return parsed_lines, " ".join(full_speech)

def render_premium_saas_video(in_v, in_a, parsed_timestamps, out_v, ratio, use_bypass=False, use_blur=False, watermark="", subtitle_mode="Both (Burn + SRT)", use_mirror=False, use_color=False, use_grain=False, use_fps=False, sub_style_str="", use_freeze=False, logo_path=None):
    try:
        a_dur = get_file_duration(in_a)
        v_max_dur = get_file_duration(in_v)
        safe_srt_path = os.path.abspath("subtitles.srt").replace('\\', '/')
        safe_srt_path_escaped = safe_srt_path.replace(':', '\\:')
        
        with open("subtitles.srt", "w", encoding="utf-8-sig") as f:
            for i, (start, end, text) in enumerate(parsed_timestamps, start=1):
                if start >= v_max_dur: continue
                safe_end = min(end, v_max_dur)
                def fmt_t(s): return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s-int(s))*1000):03d}"
                clean_text = re.sub(r'\[.*?\]', '', text)
                clean_text = re.sub(r'\{.*?\}', '', clean_text).strip()
                f.write(f"{i}\n{fmt_t(start)} --> {fmt_t(safe_end)}\n{clean_text}\n\n")
        
        video = ffmpeg.input(in_v).video
        if use_bypass: video = ffmpeg.filter(video, 'scale', '2*trunc(iw*1.08/2)', '2*trunc(ih*1.08/2)').filter('crop', 'iw/1.08', 'ih/1.08')
        if use_mirror: video = ffmpeg.filter(video, 'hflip')
        if use_color: video = ffmpeg.filter(video, 'eq', brightness=0.02, contrast=1.05, saturation=1.1)
        if use_grain: video = ffmpeg.filter(video, 'noise', alls=2, allf='t+u')
        if use_fps: video = ffmpeg.filter(video, 'fps', fps=24, round='near')
        if use_freeze: video = ffmpeg.filter(video, 'minterpolate', fps=12, mi_mode='dup')
        
        video = ffmpeg.filter(video, 'scale', 'trunc(oh*a/2)*2', 1080, flags='bicubic')
        audio = ffmpeg.input(in_a).audio
        
        if v_max_dur > 1.0 and a_dur > 0:
            speed_factor = a_dur / (v_max_dur - 0.5)
            if 0.5 <= speed_factor <= 2.0: audio = ffmpeg.filter(audio, 'atempo', speed_factor)
        
        if use_blur: video = ffmpeg.filter(video, 'drawbox', x=0, y='ih-90', w='iw', h=90, color='black@0.95', thickness='fill')
        if ratio == "9:16 (TikTok/Shorts)": video = ffmpeg.filter(video, 'crop', 'min(iw, ih*9/16)', 'ih')
        elif ratio == "16:9 (YouTube)": video = ffmpeg.filter(video, 'crop', 'iw', 'min(ih, iw*9/16)')
        
        if watermark: video = ffmpeg.filter(video, 'drawtext', text=watermark, x='w-tw-15', y='15', fontsize=30, fontcolor='white@0.5')
        
        if logo_path and os.path.exists(logo_path):
            logo = ffmpeg.input(logo_path)
            logo = ffmpeg.filter(logo, 'scale', -1, 80)
            video = ffmpeg.overlay(video, logo, x='W-w-20', y=20)

        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"] and os.path.exists("subtitles.srt"):
            video = ffmpeg.filter(video, 'subtitles', safe_srt_path_escaped, charenc='UTF-8', fontsdir='.', force_style=sub_style_str)

        out = ffmpeg.output(video, audio, out_v, vcodec='libx264', acodec='aac', preset='fast', crf=21, t=v_max_dur)
        out.run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "Success"
    except ffmpeg.Error as e: return False, str(e)

# --- 3. UI INTERFACE & NAVIGATION ---
st.markdown('<div class="main-title">AETHER FILMWORKS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI Studio V52 ⚡ Premium Edition</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 Navigation Menu")
    app_mode = st.radio("Select Studio Mode:", ["🎙️ Movie Dubbing Studio", "🎙️ Faceless Channel Studio", "🎥 Veo Video Studio", "🎵 Lyria Music Studio","⚡ Translation/Transcript Studio","📥 Video Downloader Hub",])
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
    
    if app_mode == "🎙️ Faceless Channel Studio":
        st.markdown("---")
        st.markdown("### 🔑 Pexels API Key (Optional)")
        saved_pexels = load_key(PEXELS_KEY_FILE)
        pexels_key_input = st.text_input("Pexels API Key (Free API for HQ Videos)", type="password", value=saved_pexels)
        if pexels_key_input and pexels_key_input != saved_pexels: save_key(PEXELS_KEY_FILE, pexels_key_input)

# =====================================================================
# 📌 MODE 1 - MOVIE DUBBING
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
        cb_thumb_text = st.checkbox("🖼️ Add Viral Title to Thumbnail", value=True)
        
        st.markdown("<b>©️ Brand Watermark</b>", unsafe_allow_html=True)
        uploaded_logo = st.file_uploader("🖼️ Add Logo Image (Top Right)", type=["png", "jpg", "jpeg"])
        use_text_watermark = st.checkbox("✍️ Use Text Watermark instead", value=False)
        watermark_text = st.text_input("Text Watermark", "") if use_text_watermark else ""
        
        subtitle_mode = st.radio("Subtitle Output", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"])

    st.markdown('<div class="setting-panel"><h3>📺 Media Acquisition & Setup</h3>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns([1, 1])

    with col_in1:
        video_url = st.text_input("🔗 Paste Short Drama URL Link", placeholder="https://...")
        uploaded_file = st.file_uploader("📥 OR Upload Video File (MP4)", type=["mp4"])
        
        st.markdown("<br><div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #38bdf8; font-size: 16px;'>✍️ AI Storytelling & Script Rules</p>", unsafe_allow_html=True)
        recap_mode = st.radio("🎬 Recap Mode", ["Translate Original Video (မူရင်းကို ဘာသာပြန်မည်)", "Create Original AI Story (ကိုယ်ပိုင် ဇာတ်လမ်းဖန်တီးမည်)"])
        script_style = st.selectbox("🎭 Script Style (ဇာတ်ညွှန်း ပုံစံ)", ["Normal (ပုံမှန် အညွှန်း)", "Slang (လူငယ်သုံး/Gen-Z)", "Comedy (ဟာသပြောင်ချော်ချော်)", "Suspense (သည်းထိတ်ရင်ဖို)"])
        script_hook = st.checkbox("🪝 3-Second Viral Hook (အစချီ ဆွဲဆောင်မည်)", value=True)
        script_curiosity = st.checkbox("🤯 Curiosity Gaps (စိတ်ဝင်စားမှု အရှိန်တင်မည်)", value=True)
        script_tone = st.checkbox("🎭 Emotion & Tone (ဇာတ်ကောင်စရိုက် သွင်းမည်)", value=True)
        script_cta = st.checkbox("💬 Call to Action (Comment ခေါ်မည်)", value=False)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #10b981; font-size: 16px;'>🎵 Audio Mixing & Auto-Ducking</p>", unsafe_allow_html=True)
        bgm_options = ["None (BGM မထည့်ပါ)"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files:
            bgm_options.insert(1, "🤖 Auto (Random Select)")
            bgm_options.extend(bgm_files)
        selected_bgm = st.selectbox("🎼 Background Music", bgm_options)
        bgm_volume = st.slider("🔊 BGM Volume", 1, 50, 10) / 100.0
        st.markdown("</div>", unsafe_allow_html=True)

    with col_in2:
        dynamic_options = ["Synergy Puck (Male)", "Synergy Aoede (Female)", "Synergy Charon (Male - Deep)"] if "Synergy" in audio_engine_choice else (["Adam (Male Deep)", "Rachel (Female)"] if "ElevenLabs" in audio_engine_choice else (["TTSMaker Male", "TTSMaker Female"] if "TTSMaker" in audio_engine_choice else ["ဇော်ဇော် (Male)", "အောင်အောင် (Deep)", "နှင်းနှင်း (Female)"]))
        voice_char = st.selectbox("Select Character Voice", dynamic_options, index=0)
        pitch_level = st.slider("🎙️ Voice Pitch (Frequency Adjust)", min_value=-30, max_value=30, value=0, step=5)
        fx_level = st.selectbox("🎧 Cinematic Voice FX", ["None", "🎙️ Epic Trailer Voice", "📻 Walkie-Talkie", "🏛️ Cinematic Reverb", "👹 Demon / Monster", "🤫 ASMR / Whisper"])
        
        st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: bold; color: #818cf8; font-size: 16px;'>📝 Subtitle Pro Settings</p>", unsafe_allow_html=True)
        if subtitle_mode in ["Both (Burn + SRT)", "Burn into Video"]:
            sub_position = st.selectbox("📍 Position", ["Bottom", "Center", "Top"])
            sub_color = st.selectbox("🎨 Color", ["Yellow Text + Black Outline", "White Text + Black Outline", "Neon Green Text + Black Outline"])
            sub_font = st.selectbox("🅰️ Font Family", ["Pyidaungsu", "NotoSans-Bold", "Myanmar3_2018", "Padauk"])
            sub_size = st.slider("🔠 Font Size", 16, 40, 22)
            sub_thickness = st.slider("✒️ Outline Thickness", 1.0, 5.0, 2.5)
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                sub_bg = st.checkbox("🔲 Background Box")
                sub_short = st.checkbox("✂️ Short & Punchy (Hormozi)")
            with col_s2:
                sub_fade = st.checkbox("✨ Cinematic Fades")
        else:
            st.info("💡 Burn into Video ရွေးထားမှ ချိန်ညှိနိုင်ပါမည်။")
            sub_position, sub_color, sub_font, sub_size, sub_thickness, sub_bg, sub_short, sub_fade = "Bottom", "Yellow", "Pyidaungsu", 22, 2.5, False, False, False
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 START ONE-CLICK WORKFLOW MONETIZE GENERATOR"):
        if not api_key_input: st.error("⚠️ API Key လိုအပ်ပါသည်။")
        elif not uploaded_file and not video_url: st.error("⚠️ ဗီဒီယိုဖိုင် သို့မဟုတ် Link ထည့်ပေးပါ။")
        else:
            st.session_state.render_success = False
            st.session_state.original_transcript = ""
            st.session_state.generated_script = ""
            v_input, a_extracted, a_generated, v_final, srt_final = "input_temp.mp4", "temp_extracted.mp3", "voice_temp.wav", "AETHER_RECAP_FINAL.mp4", "subtitles.srt"

            pbar = st.progress(0, text="🚀 အလုပ်စတင်နေပါပြီ...")

            with st.spinner("⏳ [အဆင့် ၁/၆] ဗီဒီယို ဖိုင်အား စနစ်ထဲသို့ ဆွဲသွင်းနေပါသည်..."):
                pbar.progress(10, text="📥 [အဆင့် ၁/၆] ဗီဒီယို ဆွဲယူနေပါသည်...")
                try:
                    if uploaded_file:
                        with open(v_input, "wb") as f: f.write(uploaded_file.read())
                    else: 
                        download_video_from_url(video_url, v_input)
                except Exception as dl_err:
                    st.error(str(dl_err)); st.stop()
                
                extracted_res = extract_audio_fast(v_input, a_extracted)
                if not extracted_res or not os.path.exists(a_extracted):
                    st.error("❌ အသံဖိုင် ခွဲထုတ်မရပါ။"); st.stop()

            with st.spinner(f"⏳ [အဆင့် ၂/၆] {ai_provider} ဖြင့် ဇာတ်ညွှန်း၊ Title နှင့် Thumbnail ထုတ်လုပ်နေပါသည်..."):
                pbar.progress(30, text=f"🤖 [အဆင့် ၂/၆] ဇာတ်ညွှန်း၊ Title နှင့် Hashtags ဖန်တီးနေပါသည်...")
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
                    hormozi_rule = " [HORMOZI]: Split the subtitles into chunks of 3-5 words max." if sub_short else ""

                    if "Gemini" in ai_provider:
                        keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                        success_gemini = False; last_err = ""
                        st.session_state.original_transcript = "[Gemini processed media directly.]"
                        
                        for idx, current_key in enumerate(keys_list):
                            try:
                                client = genai.Client(api_key=current_key)
                                
                                target_file = v_input if "Original" in recap_mode else a_extracted
                                media_file = client.files.upload(file=target_file)
                                
                                while "PROCESSING" in str(client.files.get(name=media_file.name).state):
                                    time.sleep(2)
                                
                                if "Original" in recap_mode:
                                    gemini_prompt = f"Watch the provided video carefully. Invent a completely ORIGINAL, highly engaging storytelling recap in Burmese. Do NOT just translate. STRICT RULES: 1. Include Synergy Audio Tags like [pause=1.0], [excited]. 2. NO ENGLISH TRANSLITERATION. 3. Output ONLY valid SRT format synced to the scenes.{extra_rules}{hormozi_rule}"
                                else:
                                    gemini_prompt = f"Listen to the audio. Translate and adapt the text into highly engaging, natural spoken Burmese. STRICT RULES: 1. Include Synergy Audio Tags like [pause=1.0], [excited]. 2. NO ENGLISH TRANSLITERATION. 3. Output ONLY valid SRT format matching original timestamps.{extra_rules}{hormozi_rule}"
                                
                                response = client.models.generate_content(model="gemini-2.5-flash", contents=[media_file, gemini_prompt])
                                marker = chr(96) * 3
                                raw_output_text = response.text.strip().replace(f"{marker}srt", "").replace(marker, "")
                                client.files.delete(name=media_file.name)
                                success_gemini = True
                                break 
                            except Exception as e:
                                last_err = str(e)
                                if any(err in last_err.lower() for err in ["429", "503", "unavailable", "quota", "exhausted", "limit"]): continue
                                else: continue

                        if not success_gemini: raise Exception(f"Gemini API Error: {last_err}")

                    else: # Groq / OpenAI Fallback
                        if "Original" in recap_mode: st.warning("⚠️ Original Story Mode ကို Gemini ဖြင့်သာ သုံးနိုင်ပါသည်။ Translate Mode သို့ ပြောင်းလဲလုပ်ဆောင်ပါမည်။")
                        client = Groq(api_key=api_key_input) if "Groq" in ai_provider else openai
                        if "Groq" in ai_provider:
                            with open(a_extracted, "rb") as file: transcription = client.audio.translations.create(file=(a_extracted, file.read()), model="whisper-large-v3", response_format="verbose_json")
                            tsrt = "".join([f"{i}\n00:00:00,000 --> 00:00:10,000\n{seg['text']}\n\n" for i, seg in enumerate(transcription.get('segments', []), 1)]) if isinstance(transcription, dict) else str(transcription)
                        else:
                            openai.api_key = api_key_input
                            with open(a_extracted, "rb") as file: tsrt = openai.audio.translations.create(model="whisper-1", file=file, response_format="srt")
                        
                        st.session_state.original_transcript = tsrt
                        base_prompt = f"Translate and adapt the English SRT into engaging Burmese. Add audio tags. Output valid SRT format. {extra_rules}{hormozi_rule}"
                        comp = client.chat.completions.create(model="llama-3.3-70b-versatile" if "Groq" in ai_provider else ("gpt-5.5-pro" if "5.5" in ai_provider else "gpt-4o"), messages=[{"role": "user", "content": f"{base_prompt} --- SRT --- {tsrt}"}])
                        raw_output_text = comp.choices[0].message.content

                    title_match = re.search(r'\[TITLE:\s*(.*?)\]', raw_output_text)
                    tags_match = re.search(r'\[TAGS:\s*(.*?)\]', raw_output_text)
                    st.session_state.viral_title = title_match.group(1).strip() if title_match else "Viral Movie Recap"
                    st.session_state.viral_tags = tags_match.group(1).strip() if tags_match else "#movierecap #myanmar"
                    
                    clean_raw_srt = re.sub(r'\[TITLE:.*?\]', '', raw_output_text)
                    clean_raw_srt = re.sub(r'\[TAGS:.*?\]', '', clean_raw_srt)
                    
                    parsed_timestamps, speech_text = parse_and_save_real_srt(clean_raw_srt, srt_final, use_fade=sub_fade)
                    st.session_state.generated_script = clean_raw_srt
                    
                    try:
                        thumb_time = min(get_file_duration(v_input)/3, 15)
                        font_path = "Pyidaungsu.ttf"
                        
                        try:
                            stream = ffmpeg.input(v_input, ss=thumb_time)
                            if cb_thumb_text:
                                wrapped_title = textwrap.fill(st.session_state.viral_title, width=25)
                                with open("thumb_text.txt", "w", encoding="utf-8") as tf:
                                    tf.write(wrapped_title)
                                if os.path.exists(font_path):
                                    stream = ffmpeg.filter(stream.video, 'drawtext', textfile='thumb_text.txt', fontfile=font_path, fontcolor='white', fontsize=65, x='(w-text_w)/2', y='h-text_h-100', box=1, boxcolor='red@0.9', boxborderw=20, borderw=3, bordercolor='black', line_spacing=15)
                            ffmpeg.output(stream, "auto_thumb.jpg", vframes=1).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
                        except:
                            ffmpeg.input(v_input, ss=thumb_time).output("auto_thumb.jpg", vframes=1).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
                        st.session_state.thumb_path = "auto_thumb.jpg"
                    except: pass

                except Exception as e: st.error(f"Logic Error: {e}"); st.stop()

            with st.spinner(f"⏳ [အဆင့် ၄/၆] AI Voice Over ထုတ်လုပ်နေပါသည်..."):
                pbar.progress(60, text="🎙️ [အဆင့် ၄/၆] အသံသရုပ်ဆောင် ဖန်တီးနေပါသည်...")
                try:
                    raw_speech = " ".join([t for _,_,t in parsed_timestamps])
                    clean_speech = re.sub(r'\{.*?\}', '', raw_speech)
                    asyncio.run(generate_tts(clean_speech, voice_char, a_generated, engine=audio_engine_choice, ttsmaker_key=key_ttsmaker, eleven_key=locals().get('eleven_key_input', ''), custom_eleven_id=locals().get('custom_eleven_id', ''), gemini_key=locals().get('synergy_key', api_key_input), pitch=pitch_level, voice_fx=fx_level))
                except Exception as e: st.error(f"အသံထုတ်လုပ်ခြင်း မအောင်မြင်ပါ: {e}"); st.stop()

            with st.spinner("⏳ [အဆင့် ၅/၆] ဗီဒီယိုနှင့် စာတန်းထိုး ပေါင်းစပ်နေပါသည်..."):
                pbar.progress(80, text="🎬 [အဆင့် ၅/၆] ဗီဒီယိုနှင့် စာတန်းထိုး ပေါင်းစပ်နေပါသည်...")
                align_val = 2 if "Bottom" in sub_position else (5 if "Center" in sub_position else 8)
                prim_c = "&H0000FFFF" if "Yellow" in sub_color else ("&H00FFFFFF" if "White" in sub_color else "&H0000FF00")
                dyn_style = f"FontName={sub_font.split()[0]},FontSize={sub_size},PrimaryColour={prim_c},BackColour={'&H80000000' if sub_bg else '&H00000000'},BorderStyle={3 if sub_bg else 1},Outline={0 if sub_bg else sub_thickness},Alignment={align_val},MarginV=60"
                
                logo_file_path = None
                if uploaded_logo and not use_text_watermark:
                    logo_file_path = "temp_logo.png"
                    with open(logo_file_path, "wb") as f: f.write(uploaded_logo.read())

                success, err_msg = render_premium_saas_video(v_input, a_generated, parsed_timestamps, v_final, video_ratio, cb_bypass, cb_blur, watermark_text, subtitle_mode, cb_mirror, cb_color, cb_grain, cb_fps, dyn_style, cb_freeze, logo_file_path)
                if not success: st.error(f"Sync Failure: {err_msg}")

            if success and selected_bgm not in ["None (BGM မထည့်ပါ)"]:
                with st.spinner("⏳ [အဆင့် ၆/၆] Auto-Ducking ဖြင့် BGM ထပ်မံပေါင်းစပ်နေပါသည်..."):
                    pbar.progress(95, text="🎵 [အဆင့် ၆/၆] Auto-Ducking စနစ်ဖြင့် BGM အသံကစားနေပါသည်...")
                    selected_bgm_path = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in selected_bgm else selected_bgm)
                    if os.path.exists(selected_bgm_path):
                        try:
                            temp_final = "temp_with_bgm.mp4"
                            v_dur = get_file_duration(v_final)
                            in_video = ffmpeg.input(v_final)
                            in_bgm = ffmpeg.input(selected_bgm_path, stream_loop=-1)
                            
                            bgm_audio = in_bgm.audio.filter('aresample', 44100).filter('volume', bgm_volume)
                            voice_audio = in_video.audio
                            ducked_bgm = ffmpeg.filter([bgm_audio, voice_audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                            mixed_audio = ffmpeg.filter([voice_audio, ducked_bgm], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                            
                            (ffmpeg.output(in_video.video, mixed_audio, temp_final, vcodec='copy', acodec='aac', t=v_dur).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True))
                            import shutil; shutil.move(temp_final, v_final)
                        except: pass
            
            pbar.progress(100, text="✅ အားလုံး ပြီးစီးပါပြီ!")
            if success: st.session_state.render_success = True

    if st.session_state.render_success:
        st.balloons(); st.success(f"🎉 One-Click ဗီဒီယို အောင်မြင်စွာ ထွက်လာပါပြီ!")
        
        st.markdown(f"<h2 style='color:#38bdf8; text-align:center;'>🔥 {st.session_state.viral_title}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#94a3b8;'>{st.session_state.viral_tags}</p>", unsafe_allow_html=True)
        
        col_out1, col_out2 = st.columns([1, 1])
        with col_out1:
            if os.path.exists("AETHER_RECAP_FINAL.mp4"): 
                st.video("AETHER_RECAP_FINAL.mp4")
                st.markdown('<div class="setting-panel"><h4>📥 Download Dashboard</h4>', unsafe_allow_html=True)
                st.markdown(get_download_link("AETHER_RECAP_FINAL.mp4", "Aether_Recap.mp4", "Download Recap Video (MP4)"), unsafe_allow_html=True)
                if os.path.exists("subtitles.srt"):
                    st.markdown(get_download_link("subtitles.srt", "Aether_Subs.srt", "Download Subtitles (.SRT)"), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
        with col_out2:
            st.markdown('<div class="setting-panel"><h3>📝 Scripts & Assets</h3>', unsafe_allow_html=True)
            if st.session_state.thumb_path and os.path.exists(st.session_state.thumb_path):
                st.image(st.session_state.thumb_path, caption="Auto-Generated Thumbnail", use_column_width=True)
                st.markdown(get_download_link(st.session_state.thumb_path, "Thumb.jpg", "Download Thumbnail"), unsafe_allow_html=True)
            with st.expander("👁️ Original Transcript", expanded=False):
                st.text_area("မူရင်းစာသား:", value=st.session_state.original_transcript, height=150, disabled=True)
            with st.expander("🇲🇲 AI Generated Script", expanded=True):
                st.text_area("AI မှ ရေးသားထားသော ဇာတ်ညွှန်း:", value=st.session_state.generated_script, height=250, disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# 📌 MODE 1.5 - FACELESS CHANNEL STUDIO (NEW!)
# =====================================================================
elif app_mode == "🎙️ Faceless Channel Studio":
    st.markdown('<div class="setting-panel"><h3>👻 Fully-Automated Faceless Channel Studio</h3>', unsafe_allow_html=True)
    st.markdown("TikTok, FB Reels များအတွက် Reddit Stories, Horror ပုံပြင်များကို AI ဖြင့် အလိုအလျောက် ဗီဒီယိုဖန်တီးပါ။")

    with st.sidebar:
        st.markdown("---")
        st.markdown("<b>🎙️ Voice & Audio Settings</b>", unsafe_allow_html=True)
        fc_audio_engine = st.radio("Voice Engine", ["Edge-TTS (Free)", "Google Synergy TTS (API)"], key="fc_engine")
        if "Synergy" in fc_audio_engine: fc_synergy_key = st.text_input("Synergy TTS Key", type="password", value=saved_gemini, key="fc_syn")
        fc_voice_char = st.selectbox("Voice Model", ["Synergy Puck (Male)", "Synergy Charon (Deep)"] if "Synergy" in fc_audio_engine else ["ဇော်ဇော် (Male)", "အောင်အောင် (Deep)", "နှင်းနှင်း (Female)"], key="fc_voice")
        fc_fx = st.selectbox("Voice FX (Effect)", ["None", "👹 Demon / Horror", "🤫 ASMR / Whisper", "🎙️ Epic Trailer"], key="fc_fx")
        
        st.markdown("---")
        st.markdown("<b>🎨 Visual & Niche Settings</b>", unsafe_allow_html=True)
        fc_niche = st.selectbox("Select Niche", ["👻 Horror / Creepypasta", "💔 Reddit Relationship Drama", "🧠 Dark Psychology", "💡 Fun Facts / Trivia"])
        fc_ratio = st.selectbox("Video Ratio", ["9:16 (TikTok/Shorts)", "16:9 (YouTube)", "Original"], key="fc_ratio")
        
        fc_duration = st.slider("⏱️ Story Duration (Minutes)", 1, 10, 3)
        st.caption("💡 Subtitles များသည် Viral ဖြစ်စေရန် (Alex Hormozi Style) အလယ်တည့်တည့်တွင် အကြီးကြီး အော်တိုချိန်ညှိပေးထားပါသည်။")

        bgm_options = ["None (BGM မထည့်ပါ)"]
        bgm_files = [f for f in os.listdir("bgm_tracks") if f.endswith(".mp3")] if os.path.exists("bgm_tracks") else []
        if bgm_files:
            bgm_options.insert(1, "🤖 Auto (Random Select)")
            bgm_options.extend(bgm_files)
        fc_bgm = st.selectbox("🎼 Background Music", bgm_options, key="fc_bgm")
        fc_bgm_vol = st.slider("🔊 BGM Volume", 1, 50, 8, key="fc_bgm_vol") / 100.0

    if st.button("🚀 CREATE FACELESS VIDEO (AUTO-MAGIC)"):
        if not api_key_input: st.error("⚠️ Google Gemini API Key ထည့်သွင်းပေးပါ။ (Sidebar တွင်ထည့်ပါ)")
        else:
            st.session_state.render_success = False
            pbar = st.progress(0, text="🚀 အလိုအလျောက် ဖန်တီးမှု စတင်နေပါပြီ...")
            keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]

            # STEP 1: Generate Story
            with st.spinner(f"⏳ [အဆင့် ၁/၅] Gemini ဖြင့် {fc_duration} မိနစ်စာ ဇာတ်လမ်း ရေးသားနေပါသည်..."):
                pbar.progress(10, text="📝 ဇာတ်လမ်း ရေးသားနေပါသည်...")
                
                target_words = fc_duration * 140
                story_prompt = f"Write an engaging {fc_duration}-minute highly viral script for a {fc_niche} TikTok video in natural spoken Burmese. The story should be around {target_words} words. Start with an extreme hook. Do not use english transliteration. Include Synergy audio tags like [pause=1.0]."
                
                fc_story_text = ""
                last_err = ""
                for key in keys_list:
                    try:
                        client = genai.Client(api_key=key)
                        response = client.models.generate_content(model="gemini-2.5-flash", contents=story_prompt)
                        fc_story_text = response.text.strip()
                        break
                    except Exception as e:
                        last_err = str(e)
                        continue
                if not fc_story_text:
                    st.error(f"Story Error: Key အားလုံး Limit ပြည့်နေပါသည်။ {last_err}")
                    st.stop()

            # STEP 2: Generate Audio
            with st.spinner("⏳ [အဆင့် ၂/၅] AI သရုပ်ဆောင်ဖြင့် အသံဖန်တီးနေပါသည်..."):
                pbar.progress(30, text="🎙️ အသံဖန်တီးနေပါသည်...")
                try:
                    clean_story = re.sub(r'\[.*?\]', '', fc_story_text) 
                    asyncio.run(generate_tts(fc_story_text if "Synergy" in fc_audio_engine else clean_story, fc_voice_char, "fc_audio.wav", engine=fc_audio_engine, gemini_key=locals().get('fc_synergy_key', api_key_input), voice_fx=fc_fx))
                    fc_audio_dur = get_file_duration("fc_audio.wav")
                except Exception as e: st.error(f"Audio Error: {e}"); st.stop()

            # STEP 3: Fallback Image/Video Generation (Parallel Downloading + Normalization)
            with st.spinner("⏳ [အဆင့် ၃/၅] Pexels ဖြင့် ဇာတ်လမ်းနှင့် ကိုက်ညီသော ဗီဒီယိုများ ရယူနေပါသည်..."):
                pbar.progress(50, text="🎥 Visuals Generation စတင်နေပါသည်...")
                try:
                    search_keywords = []
                    last_err = ""
                    for key in keys_list:
                        try:
                            client = genai.Client(api_key=key)
                            prompt_req = client.models.generate_content(model="gemini-2.5-flash", contents=f"Based on this story, give me exactly THREE short, distinct English search keywords (max 3 words each) describing the scenery. Avoid any violent, gory, or explicitly scary words. Format strictly separated by a pipe '|'. Story: {fc_story_text[:200]}")
                            search_keywords = prompt_req.text.split('|')[:3]
                            break
                        except Exception as e:
                            last_err = str(e)
                            continue
                            
                    if not search_keywords:
                        st.error(f"Keyword Error: Key အားလုံး Limit ပြည့်နေပါသည်။ {last_err}")
                        st.stop()
                    
                    generated_clips = []
                    pexels_api_key = locals().get('pexels_key_input', '').strip()
                    
                    step3_start_time = time.time()
                    total_clips = len(search_keywords)
                    
                    # 👇 FIX: Parallel downloading & normalization to completely remove FFmpeg bottlenecks
                    def fetch_pexels_clip(kw, idx):
                        try:
                            clean_kw = kw.strip().replace(" ", "+")
                            orientation = "portrait" if "9:16" in fc_ratio else "landscape"
                            best_link = None
                            
                            if pexels_api_key:
                                headers = {"Authorization": pexels_api_key}
                                pexels_url = f"https://api.pexels.com/videos/search?query={clean_kw}&orientation={orientation}&per_page=1"
                                res = requests.get(pexels_url, headers=headers, timeout=30)
                                if res.status_code == 200 and res.json().get('videos'):
                                    video_files = res.json()['videos'][0]['video_files']
                                    sd_links = [vf['link'] for vf in video_files if vf['quality'] == 'sd']
                                    best_link = sd_links[0] if sd_links else video_files[0]['link']
                            else:
                                search_url = f"https://www.pexels.com/search/videos/{clean_kw}/?orientation={orientation}"
                                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                                html_res = requests.get(search_url, headers=headers, timeout=30)
                                match = re.search(r'https://player.vimeo.com/external/[^\s"\'<>]+', html_res.text)
                                if match:
                                    best_link = match.group(0)
                            
                            if best_link:
                                raw_path = f"raw_fc_clip_{idx}.mp4"
                                vid_res = requests.get(best_link, stream=True, timeout=60)
                                if vid_res.status_code == 200:
                                    with open(raw_path, "wb") as f:
                                        for chunk in vid_res.iter_content(chunk_size=1024 * 1024): 
                                            if chunk: f.write(chunk)
                                    
                                    # Normalize video immediately (Forces all clips to have same fps, size, and codec for safe concat)
                                    clip_path = f"fc_clip_{idx}.mp4"
                                    scale_filter = "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280" if "9:16" in fc_ratio else ("scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720" if "16:9" in fc_ratio else "scale=720:-2")
                                    subprocess.run([FFMPEG_BINARY, "-y", "-i", raw_path, "-vf", f"{scale_filter},fps=25,format=yuv420p", "-c:v", "libx264", "-preset", "superfast", "-crf", "26", "-an", clip_path], capture_output=True)
                                    
                                    if os.path.exists(raw_path): os.remove(raw_path) # cleanup
                                    return clip_path
                        except: pass
                        return None

                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        futures = [executor.submit(fetch_pexels_clip, kw, i) for i, kw in enumerate(search_keywords)]
                        completed = 0
                        for future in concurrent.futures.as_completed(futures):
                            completed += 1
                            elapsed_time = int(time.time() - step3_start_time)
                            pbar.progress(50 + (completed * 5), text=f"🎥 Pexels ဗီဒီယို ဆွဲယူနေပါသည် (Clip {completed}/{total_clips}) ... [ကြာချိန်: {elapsed_time} စက္ကန့်]")
                    
                    generated_clips = [f"fc_clip_{i}.mp4" for i in range(total_clips) if os.path.exists(f"fc_clip_{i}.mp4")]
                    
                    if not generated_clips:
                        st.error("❌ Visual Generation Failed. Pexels မှ ဗီဒီယို ရှာမတွေ့ပါ။ ကျေးဇူးပြု၍ Sidebar တွင် Pexels API Key ထည့်ပေးပါ။ (https://www.pexels.com/api/)")
                        st.stop()
                    
                    pbar.progress(65, text="🎞️ ဗီဒီယိုများကို ပေါင်းစပ်နေပါသည်...")
                    with open("fc_concat.txt", "w") as f:
                        for c in generated_clips: f.write(f"file '{c}'\n")
                    
                    subprocess.run([FFMPEG_BINARY, "-y", "-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", "fc_concat.txt", "-t", str(fc_audio_dur), "-c", "copy", "fc_video_loop.mp4"], capture_output=True)
                except Exception as e: st.error(f"Visual Error: {e}"); st.stop()

            # STEP 4: SRT Sync
            with st.spinner("⏳ [အဆင့် ၄/၅] စာတန်းထိုးများကို Alex Hormozi ပုံစံ ချိန်ညှိနေပါသည်..."):
                pbar.progress(70, text="📝 Timeline ချိန်ညှိနေပါသည်...")
                fc_parsed = None
                last_err = ""
                for key in keys_list:
                    try:
                        client = genai.Client(api_key=key)
                        audio_upload = client.files.upload(file="fc_audio.wav")
                        while "PROCESSING" in str(client.files.get(name=audio_upload.name).state): time.sleep(2)
                        
                        srt_prompt = "Listen to the audio. Output ONLY a valid SRT file in Burmese. CRITICAL RULE: Each subtitle block MUST contain ONLY 1 to 4 words maximum (fast-paced TikTok style). Ensure timestamps are precise. No markdown."
                        srt_res = client.models.generate_content(model="gemini-2.5-flash", contents=[audio_upload, srt_prompt])
                        
                        marker = chr(96) * 3
                        fc_srt_text = srt_res.text.strip().replace(f"{marker}srt", "").replace(marker, "")
                        
                        fc_parsed, _ = parse_and_save_real_srt(fc_srt_text, "subtitles.srt")
                        client.files.delete(name=audio_upload.name)
                        break
                    except Exception as e:
                        last_err = str(e)
                        continue
                        
                if not fc_parsed:
                    st.error(f"SRT Error: Key အားလုံး Limit ပြည့်နေပါသည်။ {last_err}")
                    st.stop()

            # STEP 5: Final Master Rendering
            with st.spinner("⏳ [အဆင့် ၅/၅] အားလုံးကိုပေါင်းစပ်ပြီး Master Video ထုတ်လုပ်နေပါသည်..."):
                pbar.progress(85, text="🎬 Master Rendering အလုပ်လုပ်နေပါသည်...")
                try:
                    dyn_fc_style = f"FontName=Pyidaungsu,FontSize=22,PrimaryColour=&H0000FFFF,BackColour=&H90000000,BorderStyle=3,Outline=0,Shadow=1,Alignment=5,MarginV=80"
                    
                    success, err_msg = render_premium_saas_video("fc_video_loop.mp4", "fc_audio.wav", fc_parsed, "FACELESS_FINAL.mp4", fc_ratio, use_bypass=True, sub_style_str=dyn_fc_style)
                    
                    if success and fc_bgm not in ["None (BGM မထည့်ပါ)"]:
                        bgm_path = os.path.join("bgm_tracks", random.choice(bgm_files) if "Auto" in fc_bgm else fc_bgm)
                        if os.path.exists(bgm_path):
                            try:
                                ducked = ffmpeg.filter([ffmpeg.input(bgm_path, stream_loop=-1).audio.filter('aresample', 44100).filter('volume', fc_bgm_vol), ffmpeg.input("FACELESS_FINAL.mp4").audio], 'sidechaincompress', threshold=0.04, ratio=4, attack=50, release=300)
                                mixed = ffmpeg.filter([ffmpeg.input("FACELESS_FINAL.mp4").audio, ducked], 'amix', inputs=2, duration='first').filter('volume', 2.0)
                                ffmpeg.output(ffmpeg.input("FACELESS_FINAL.mp4").video, mixed, "temp_faceless.mp4", vcodec='copy', acodec='aac', t=fc_audio_dur).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
                                shutil.move("temp_faceless.mp4", "FACELESS_FINAL.mp4")
                            except: pass
                            
                    pbar.progress(100, text="✅ အားလုံး ပြီးစီးပါပြီ!")
                    st.balloons()
                    st.success("🎉 Faceless Video ထုတ်လုပ်မှု အောင်မြင်စွာ ပြီးစီးပါပြီ!")
                    
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        st.video("FACELESS_FINAL.mp4")
                        st.markdown(get_download_link("FACELESS_FINAL.mp4", "Viral_Faceless.mp4", "Download Final Video (No Refresh)"), unsafe_allow_html=True)
                    with col_f2:
                        st.markdown("### 📝 Generated Story")
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
    if st.button("⬇️ ဗီဒီယို စစ်ဆေးပြီး ဒေါင်းလုဒ်ဆွဲမည်"): pass
