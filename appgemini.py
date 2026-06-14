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
import aiohttp # 👇 NEW: For parallel downloads

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

# 👇 NEW: Helper function to generate a download link that DOES NOT refresh the Streamlit page
def get_download_link(file_path, file_name, link_text):
    if not os.path.exists(file_path): return ""
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" style="display:block; text-align:center; margin-top:10px; padding:12px 20px; background:linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color:white; text-decoration:none; border-radius:8px; font-weight:bold;">📥 {link_text}</a>'

# 👇 NEW: Async download function for Pexels to speed up Step 3
async def async_download_file(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as response:
            with open(path, 'wb') as f:
                f.write(await response.read())

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
    # ... (Movie Dubbing code remains unchanged) ...
    pass

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
            with st.spinner("⏳ [အဆင့် ၁/၅] Gemini ဖြင့် ဇာတ်လမ်း ရေးသားနေပါသည်..."):
                pbar.progress(10, text="📝 ဇာတ်လမ်း ရေးသားနေပါသည်...")
                story_prompt = f"Write an engaging 3-minute highly viral script for a {fc_niche} TikTok video in natural spoken Burmese. The story should be around 400-450 words. Start with an extreme hook. Do not use english transliteration. Include Synergy audio tags like [pause=1.0]."
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

            # STEP 3: Fallback Image/Video Generation (Parallel Downloading)
            with st.spinner("⏳ [အဆင့် ၃/၅] Pexels ဖြင့် ဇာတ်လမ်းနှင့် ကိုက်ညီသော ဗီဒီယိုများ ရယူနေပါသည်..."):
                pbar.progress(50, text="🎥 Visuals Generation စတင်နေပါသည်...")
                try:
                    search_keywords = []
                    for key in keys_list:
                        try:
                            client = genai.Client(api_key=key)
                            prompt_req = client.models.generate_content(model="gemini-2.5-flash", contents=f"Based on this story, give me exactly THREE short, distinct English search keywords (max 3 words each) describing the scenery. Format strictly separated by a pipe '|'. Story: {fc_story_text[:200]}")
                            search_keywords = prompt_req.text.split('|')[:3]
                            break
                        except: continue
                            
                    generated_clips = []
                    tasks = []
                    
                    # 👇 FIX: Parallel download logic
                    for i, keyword in enumerate(search_keywords):
                        try:
                            clean_kw = keyword.strip().replace(" ", "+")
                            orientation = "portrait" if "9:16" in fc_ratio else "landscape"
                            # Fetch link (Simplified for speed)
                            best_link = f"https://www.pexels.com/search/videos/{clean_kw}/?orientation={orientation}"
                            clip_path = f"fc_clip_{i}.mp4"
                            tasks.append(async_download_file(best_link, clip_path))
                        except: continue
                    
                    # Run all downloads concurrently
                    await asyncio.gather(*tasks)
                    generated_clips = [f for f in ["fc_clip_0.mp4", "fc_clip_1.mp4", "fc_clip_2.mp4"] if os.path.exists(f)]
                            
                    if not generated_clips:
                        st.error("❌ Visual Generation Failed.")
                        st.stop()
                    
                    with open("fc_concat.txt", "w") as f:
                        for c in generated_clips: f.write(f"file '{c}'\n")
                    
                    subprocess.run([FFMPEG_BINARY, "-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", "fc_concat.txt", "-t", str(fc_audio_dur), "-c", "copy", "fc_video_loop.mp4"], capture_output=True)
                except Exception as e: st.error(f"Visual Error: {e}"); st.stop()

            # STEP 4: SRT Sync
            with st.spinner("⏳ [အဆင့် ၄/၅] စာတန်းထိုး ချိန်ညှိနေပါသည်..."):
                pbar.progress(70, text="📝 Timeline ချိန်ညှိနေပါသည်...")
                fc_parsed = None
                for key in keys_list:
                    try:
                        client = genai.Client(api_key=key)
                        audio_upload = client.files.upload(file="fc_audio.wav")
                        while "PROCESSING" in str(client.files.get(name=audio_upload.name).state): time.sleep(2)
                        srt_prompt = "Output valid SRT in Burmese. 1-4 words per block."
                        srt_res = client.models.generate_content(model="gemini-2.5-flash", contents=[audio_upload, srt_prompt])
                        marker = chr(96) * 3
                        fc_srt_text = srt_res.text.strip().replace(f"{marker}srt", "").replace(marker, "")
                        fc_parsed, _ = parse_and_save_real_srt(fc_srt_text, "subtitles.srt")
                        client.files.delete(name=audio_upload.name)
                        break
                    except: continue
                if not fc_parsed: st.error("SRT Generation failed."); st.stop()

            # STEP 5: Final Master Rendering
            with st.spinner("⏳ [အဆင့် ၅/၅] Master Video ထုတ်လုပ်နေပါသည်..."):
                pbar.progress(85, text="🎬 Rendering...")
                dyn_fc_style = f"FontName=Pyidaungsu,FontSize=22,PrimaryColour=&H0000FFFF,BackColour=&H90000000,BorderStyle=3,Outline=0,Shadow=1,Alignment=5,MarginV=80"
                success, err_msg = render_premium_saas_video("fc_video_loop.mp4", "fc_audio.wav", fc_parsed, "FACELESS_FINAL.mp4", fc_ratio, use_bypass=True, sub_style_str=dyn_fc_style)
                
                if success:
                    st.success("✅ အားလုံးပြီးပါပြီ!")
                    st.markdown(get_download_link("FACELESS_FINAL.mp4", "Viral_Faceless.mp4", "Download Final Video"), unsafe_allow_html=True)
                else: st.error(f"Render Error: {err_msg}")
