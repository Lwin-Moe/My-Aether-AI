# =====================================================================
# 📌 AETHER FILMWORKS AI // STUDIO V52 (PERFECT SYNC & IMAGE FETCH FIX)
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

# 👇 FIX: Prioritize system FFmpeg
if shutil.which("ffmpeg"):
    FFMPEG_BINARY = "ffmpeg"
else:
    FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

# 👇 FIX: Bulletproof Font Installation for Drawtext filter
local_font_path = "Padauk.ttf"
if not os.path.exists(local_font_path):
    try:
        import urllib.request
        urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/padauk/Padauk-Regular.ttf", local_font_path)
    except Exception:
        pass

# Force font cache update just in case
_fonts_dir = os.path.expanduser("~/.fonts")
os.makedirs(_fonts_dir, exist_ok=True)
_sys_font = os.path.join(_fonts_dir, "Padauk.ttf")
if not os.path.exists(_sys_font) and os.path.exists(local_font_path):
    try:
        shutil.copy(local_font_path, _sys_font)
        subprocess.run(["fc-cache", "-f", "-v"], capture_output=True)
    except Exception:
        pass

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

# --- 2. CORE AUTOMATION FLOW ENGINES ---
def cleanup_temp_files():
    for f in os.listdir("."):
        if f.startswith(("fc_clip_", "fc_img_", "raw_fc_clip_", "temp_", "subtitles.", "thumb_A_", "thumb_B_", "FACELESS_FINAL_", "AETHER_RECAP_FINAL_", "fc_audio.wav", "fc_video_loop.mp4")):
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
            payload = {"contents": [{"parts": [{"text": prompt_text}]}], "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": { "voiceConfig": { "prebuiltVoiceConfig": { "voiceName": voice_name } } }}}
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
                            success = True
                            break
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
                        return int(tp[0]) + float(ms.ljust(3, '0'))/1000.0
                    elif len(tp) == 2: 
                        return int(tp[0])*60 + int(tp[1]) + float(ms.ljust(3, '0'))/1000.0
                    else: 
                        return int(tp[0])*3600 + int(tp[1])*60 + int(tp[2]) + float(ms.ljust(3, '0'))/1000.0
                    
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
            def fmt(sec):
                return f"{int(sec//3600):02d}:{int((sec%3600)//60):02d}:{int(sec%60):02d},{int((sec%1)*1000):03d}"
            f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n{t}\n\n")
            
    return final_parsed, " ".join(full_speech)

def render_premium_saas_video(in_v, in_a, parsed_timestamps, out_v, ratio, use_bypass=False, use_blur=False, watermark="", subtitle_mode="Both (Burn + SRT)", use_mirror=False, use_color=False, use_grain=False, use_fps=False, sub_position="Bottom", sub_color="Yellow", sub_size=26, sub_thickness=2.5, sub_bg=False, use_freeze=False, logo_path=None):
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
            
            for i, (start, end, text) in enumerate(parsed_timestamps):
                wrapped_text = textwrap.fill(text, width=wrap_width)
                txt_filename = f"temp_sub_{i}.txt"
                with open(txt_filename, "w", encoding="utf-8") as tf:
                    tf.write(wrapped_text)
                
                if "Center" in sub_position: 
                    y_expr = "(h-text_h)/2"
                elif "Top" in sub_position: 
                    y_expr = "150"
                else: 
                    y_expr = "h-text_h-150"
                
                c_str = "yellow"
                if "White" in sub_color: c_str = "white"
               
