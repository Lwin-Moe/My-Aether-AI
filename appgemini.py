# =====================================================================
# 📌 AETHER FILMWORKS AI // STUDIO V52 (FINAL PRODUCTION READY)
# =====================================================================

import streamlit as st
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

FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

# --- Key Save Files ---
API_KEY_FILE = "saved_api_key.txt"
ELEVEN_KEY_FILE = "saved_eleven_key.txt"
GROQ_KEY_FILE = "saved_groq_key.txt"
OPENAI_KEY_FILE = "saved_openai_key.txt"
ELEVEN_VOICE_ID_FILE = "saved_eleven_voice_id.txt"

def load_key(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f: return f.read().strip()
    return ""

def save_key(file_path, key):
    with open(file_path, "w", encoding="utf-8") as f: f.write(key)

# --- 1. THEME & STYLING ---
st.set_page_config(page_title="AETHER FILMWORKS AI // STUDIO V52", layout="wide")

st.markdown('''
    <style>
    .stApp { background: linear-gradient(135deg, #080510 0%, #0d0820 40%, #130b2e 100%) !important; color: #f0e6ff !important; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #080510 !important; border-right: 1px solid rgba(179, 71, 255, 0.2) !important; }
    h1, h2, h3, h4 { color: #00e5ff !important; font-family: 'Space Grotesk', sans-serif; font-weight: 800 !important; text-shadow: 0 0 15px rgba(0,229,255,0.2); }
    p, span, label, .stRadio label, .stCheckbox label, .stSelectbox label { color: #b8a9d4 !important; font-size: 14px; }
    .stTextInput input, div[data-baseweb="select"] { background-color: #130b2e !important; color: #ffffff !important; border: 1px solid rgba(179, 71, 255, 0.3) !important; border-radius: 8px !important; }
    .stTextArea textarea { background-color: #1a1038 !important; color: #00e5ff !important; border: 1px solid rgba(179, 71, 255, 0.5) !important; font-family: 'JetBrains Mono', monospace; line-height: 1.6; }
    .setting-panel { background: #0d0820; border: 1px solid rgba(179, 71, 255, 0.15); border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 16px 48px rgba(0,0,0,0.6); }
    .stButton>button { background: linear-gradient(135deg, #b347ff 0%, #7c4dff 50%, #448aff 100%) !important; color: #ffffff !important; font-weight: 800 !important; font-size: 16px !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 15px !important; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0px 8px 30px rgba(179, 71, 255, 0.6); }
    </style>
''', unsafe_allow_html=True)

if "render_success" not in st.session_state: st.session_state.render_success = False
if "generated_script" not in st.session_state: st.session_state.generated_script = ""
if "original_transcript" not in st.session_state: st.session_state.original_transcript = ""

# --- 2. CORE AUTOMATION FLOW ENGINES ---

def get_file_duration(file_path):
    try:
        cmd = [FFMPEG_BINARY, "-i", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        pass
    return 600.0 

def download_video_from_url(url, output_path="input_temp.mp4"):
    if os.path.exists(output_path): os.remove(output_path)
    ydl_opts = {'outtmpl': output_path, 'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return output_path
    except Exception: raise Exception("ဗီဒီယိုအား ဒေါင်းလုဒ်ဆွဲ၍ မရပါ။")

def extract_audio_fast(video_in, audio_out="temp_extracted.mp3"):
    if os.path.exists(audio_out): os.remove(audio_out)
    try:
        (ffmpeg.input(video_in).output(audio_out, acodec='libmp3lame', ac=1, ar='16000')
         .run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True))
        if os.path.exists(audio_out): return audio_out
    except: pass
    try:
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_extracted', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'quiet': True, 'ffmpeg_location': FFMPEG_BINARY}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.extract_info(video_in, download=True)
        return audio_out
    except: return None

async def generate_tts(text, voice_model, output_file, engine="Edge-TTS (Default Free)", ttsmaker_key="", eleven_key="", custom_eleven_id="", gemini_key=""):
    if not text.strip(): return

    if "Synergy" in engine:
        if not gemini_key: raise Exception("Gemini Synergy TTS အား အသုံးပြုရန် API Key လိုအပ်ပါသည်။")
        keys_list = [k.strip() for k in gemini_key.split(",") if k.strip()]
        
        voice_name = "Puck" if "Puck" in voice_model else ("Charon" if "Charon" in voice_model else "Aoede")
        prompt_text = "You are a professional Burmese movie narrator. Read the following text naturally and expressively. " + text
        
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": { "voiceConfig": { "prebuiltVoiceConfig": { "voiceName": voice_name } } }
            }
        }
        
        last_err = ""
        for idx, current_key in enumerate(keys_list):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={current_key}"
            try:
                res = requests.post(url, json=payload)
                if res.status_code == 200:
                    candidate = res.json().get("candidates", [{}])[0]
                    if candidate.get("finishReason") == "SAFETY":
                        raise Exception("Safety Error: AI မှ အသံထွက်ပေးရန် ငြင်းဆိုလိုက်ပါသည်။")
                    
                    audio_b64 = candidate["content"]["parts"][0]["inlineData"]["data"]
                    pcm_data = base64.b64decode(audio_b64)
                    with wave.open(output_file, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(pcm_data)
                    return
                elif res.status_code == 429:
                    last_err = f"Key {current_key[-4:]} ၏ တစ်နေ့စာ Limit ပြည့်သွားပါပြီ။"
                    continue
                else:
                    last_err = f"Gemini API Error ({res.status_code}): {res.text}"
                    continue
            except Exception as e: 
                last_err = str(e)
                continue
                
        raise Exception(f"ထည့်သွင်းထားသော Key များအားလုံး Limit ပြည့်သွားပါပြီ။ Key အသစ် ထပ်ထည့်ပါ။ နောက်ဆုံး Error: {last_err}")

    elif "ElevenLabs" in engine:
        if not eleven_key: raise Exception("ElevenLabs API Key လိုအပ်ပါသည်။")
        voice_id = custom_eleven_id.strip() if custom_eleven_id else ("21m00Tcm4TlvDq8ikWAM" if "Male" in voice_model else "AZnzlk1XvdvUeBnXmlld")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = { "Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": eleven_key }
        payload = { "text": text, "model_id": "eleven_multilingual_v2", "voice_settings": { "stability": 0.45, "similarity_boost": 0.75 } }
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            with open(output_file, "wb") as f: f.write(res.content)
            return
        else: raise Exception(f"ElevenLabs API Error: {res.text}")
            
    elif "TTSMaker" in engine:
        if not ttsmaker_key: raise Exception("TTSMaker API Key လိုအပ်ပါသည်။")
        voice_id = 781 if "Female" in voice_model else 780
        url = "https://api.ttsmaker.com/v1/create-tts-order"
        payload = { "tts_api_key": ttsmaker_key, "tts_text": text, "voice_id": voice_id, "audio_format": "mp3" }
        res = requests.post(url, json=payload).json()
        if res.get("status") == "success":
            audio_data = requests.get(res["audio_file_url"]).content
            with open(output_file, "wb") as f: f.write(audio_data)
            return
        else: raise Exception(f"TTSMaker API Error: {res}")

    else:
        voice = "my-MM-ThihaNeural" if "Male" in voice_model else "my-MM-NilarNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)

def parse_and_save_real_srt(raw_srt_text, output_file):
    clean_srt = raw_srt_text.replace("```srt", "").replace("```", "").strip()
    
    with open(output_file, "w", encoding="utf-8-sig") as f: 
        f.write(clean_srt)
        
    parsed_lines = []
    full_speech = []
    matches = list(re.finditer(r'(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})', clean_srt))
    
    for i in range(len(matches)):
        start_str = matches[i].group(1).replace('.', ',')
        end_str = matches[i].group(2).replace('.', ',')
        text_start = matches[i].end()
        
        if i + 1 < len(matches):
            text_end = matches[i+1].start()
            block = clean_srt[text_start:text_end].strip()
            lines = block.split('\n')
            if len(lines) > 0 and lines[-1].strip().isdigit():
                lines.pop()
            block = " ".join(lines)
        else:
            block = clean_srt[text_start:].strip().replace('\n', ' ')
            
        if block:
            try:
                def to_sec(t):
                    h, m, s_ms = t.split(':')
                    s, ms = s_ms.split(',')
                    ms = ms.ljust(3, '0')
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
                parsed_lines.append((to_sec(start_str), to_sec(end_str), block.strip()))
                full_speech.append(block.strip())
            except: pass
            
    if not parsed_lines:
        text_only = re.sub(r'^\d+\s*$', '', clean_srt, flags=re.MULTILINE)
        text_only = text_only.strip()
        if text_only:
             parsed_lines.append((0.0, min(10.0, len(text_only)*0.1), text_only))
             full_speech.append(text_only)
        else:
             parsed_lines.append((0.0, 10.0, "[pause=1.0] စာတန်းထိုး အပြောင်းအလဲလုပ်နေပါသည်။"))
             full_speech.append("[pause=1.0] စာတန်းထိုး အပြောင်းအလဲလုပ်နေပါသည်။")
        
    return parsed_lines, " ".join(full_speech)

def render_premium_saas_video(in_v, in_a, parsed_timestamps, out_v, ratio, use_bypass=False, use_blur=False, watermark="", subtitle_mode="Both (Burn + SRT)"):
    try:
        a_dur = get_file_duration(in_a)
        v_max_dur = get_file_duration(in_v)
        
        safe_srt_path = os.path.abspath("subtitles.srt").replace('\\', '/')
        safe_srt_path_escaped = safe_srt_path.replace(':', '\\:')
        
        with open("subtitles.srt", "w", encoding="utf-8-sig") as f:
            for i, (start, end, text) in enumerate(parsed_timestamps, start=1):
                if start >= v_max_dur: continue
                safe_end = min(end, v_max_dur)
                def fmt_t(s): 
                    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s-int(s))*1000):03d}"
                f.write(f"{i}\n{fmt_t(start)} --> {fmt_t(safe_end)}\n{text}\n\n")
        
        video = ffmpeg.input(in_v).video
        if use_bypass:
            video = ffmpeg.filter(video, 'scale', '2*trunc(iw*1.08/2)', '2*trunc(ih*1.08/2)')
            video = ffmpeg.filter(video, 'crop', 'iw/1.08', 'ih/1.08')
        
        video = ffmpeg.filter(video, 'scale', 'trunc(oh*a/2)*2', 1080, flags='bicubic')
        audio = ffmpeg.input(in_a).audio
        
        if v_max_dur > 1.0 and a_dur > 0:
            target_a_dur = v_max_dur - 0.5
            speed_factor = a_dur / target_a_dur
            if 0.5 <= speed_factor <= 2.0:
                audio = ffmpeg.filter(audio, 'atempo', speed_factor)
        
        if use_blur: 
            video = ffmpeg.filter(video, 'drawbox', x=0, y='ih-90', w='iw', h=90, color='black@0.95', thickness='fill')
            
        if ratio == "9:16 (TikTok/Shorts)": 
            video = ffmpeg.filter(video, 'crop', 'min(iw, ih*9/16)', 'ih')
        elif ratio == "16:9 (YouTube)": 
            video = ffmpeg.filter(video, 'crop', 'iw', 'min(ih, iw*9/16)')
        
        try:
            if watermark: 
                video = ffmpeg.filter(video, 'drawtext', text=watermark, x='w-tw-15', y='15', fontsize=30, fontcolor='white@0.5')
        except: pass
        
        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"] and os.path.exists("subtitles.srt"):
            video = ffmpeg.filter(video, 'subtitles', safe_srt_path_escaped, charenc='UTF-8', fontsdir='.', force_style="FontName=Pyidaungsu,FontSize=22,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2.5,Shadow=1,Alignment=2,MarginV=25")

        out = ffmpeg.output(video, audio, out_v, vcodec='libx264', acodec='aac', preset='fast', crf=21, t=v_max_dur)
        out.run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "Success"
    except ffmpeg.Error as e: 
        return False, e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)

# --- 3. UI INTERFACE & NAVIGATION ---
st.markdown('<h1 style="text-align:center; margin-bottom: 30px;">▲ AETHER FILMWORKS AI // STUDIO V52</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 Navigation Menu")
    app_mode = st.radio("Select Studio Mode:", ["🎙️ Movie Dubbing Studio", "🎥 Veo Video Studio", "🎵 Lyria Music Studio","⚡ Translation/Transcript Studio","📥 Video Downloader Hub",])
    st.markdown("---")
    st.markdown("### 🧠 1. Select AI Core Engine")
    ai_provider = st.selectbox("Choose AI Provider", ["Google Gemini (Flash - Recommended)", "OpenAI (GPT-5.5 Pro)", "Groq API (Fast & Free)"])
    
    st.markdown("### 🔑 2. API Credentials")
    saved_gemini = load_key(API_KEY_FILE)
    if "Gemini" in ai_provider:
        api_key_input = st.text_input("Gemini Keys (Comma separated)", value=saved_gemini, placeholder="Key1, Key2...")
        if api_key_input and api_key_input != saved_gemini: save_key(API_KEY_FILE, api_key_input)
    elif "Groq" in ai_provider:
        saved_groq = load_key(GROQ_KEY_FILE)
        api_key_input = st.text_input("Groq API Key", value=saved_groq)
        if api_key_input and api_key_input != saved_groq: save_key(GROQ_KEY_FILE, api_key_input)
    else:
        saved_openai = load_key(OPENAI_KEY_FILE)
        api_key_input = st.text_input("OpenAI API Key", value=saved_openai)
        if api_key_input and api_key_input != saved_openai: save_key(OPENAI_KEY_FILE, api_key_input)

# =====================================================================
# 📌 MODE 1 - MOVIE DUBBING
# =====================================================================
if app_mode == "🎙️ Movie Dubbing Studio":
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔊 3. Voice Engine Platform")
        audio_engine_choice = st.radio("Select Voice Platform", [
            "Edge-TTS (Default Free)", 
            "Google Synergy TTS (Flash 3.1 Preview)", 
            "ElevenLabs (Premium AI)",
            "TTSMaker (Free API)"
        ])
        
        if "Synergy" in audio_engine_choice:
            st.caption("✨ Using your Gemini API Key for Synergy Speech synthesis.")
            synergy_key = st.text_input("Enter API Key for Synergy TTS", value=saved_gemini)

        if "ElevenLabs" in audio_engine_choice:
            saved_eleven = load_key(ELEVEN_KEY_FILE)
            eleven_key_input = st.text_input("ElevenLabs API Key", value=saved_eleven)
            if eleven_key_input and eleven_key_input != saved_eleven: save_key(ELEVEN_KEY_FILE, eleven_key_input)
            
            saved_voice_id = load_key(ELEVEN_VOICE_ID_FILE)
            custom_eleven_id = st.text_input("Custom Voice ID (Optional)", value=saved_voice_id, placeholder="e.g., pNInz6obbfdqI2CCOruU")
            if custom_eleven_id and custom_eleven_id != saved_voice_id: save_key(ELEVEN_VOICE_ID_FILE, custom_eleven_id)
