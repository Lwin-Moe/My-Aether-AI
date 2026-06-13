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

# --- 1. THEME & STYLING (PREMIUM PRO UI) ---
st.set_page_config(page_title="AETHER STUDIO V52", layout="wide", page_icon="🎬")

st.markdown('''
    <style>
    /* Import Premium Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Montserrat:wght@500;700;800;900&display=swap');

    /* Base App Styling */
    .stApp { 
        background-color: #0b0f19 !important; 
        background-image: radial-gradient(circle at top, #161b2e 0%, #0b0f19 60%) !important;
        color: #cbd5e1 !important; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { 
        background-color: #0d111c !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important; 
    }
    
    /* Typography */
    h1, h2, h3, h4 { 
        font-family: 'Montserrat', sans-serif !important; 
        color: #f8fafc !important; 
        font-weight: 700 !important;
    }
    p, span, label, .stRadio label, .stCheckbox label, .stSelectbox label { 
        color: #94a3b8 !important; 
        font-size: 14px; 
    }
    
    /* Main Cinematic Title */
    .main-title {
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-size: 3.5rem !important;
        font-weight: 900;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 20px;
        margin-bottom: 5px;
        letter-spacing: -1px;
        text-shadow: 0px 10px 30px rgba(129, 140, 248, 0.2);
    }
    .sub-title {
        text-align: center;
        color: #64748b;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 40px;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

    /* Input Fields & Dropdowns */
    .stTextInput input, div[data-baseweb="select"], .stTextArea textarea { 
        background-color: #151b2b !important; 
        color: #f1f5f9 !important; 
        border: 1px solid #334155 !important; 
        border-radius: 8px !important; 
        transition: all 0.3s ease;
    }
    .stTextInput input:focus, div[data-baseweb="select"]:focus-within, .stTextArea textarea:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 0 1px rgba(129, 140, 248, 0.5) !important;
    }
    
    /* Custom Panel / Card Design */
    .setting-panel { 
        background: #111624; 
        border: 1px solid rgba(255, 255, 255, 0.05); 
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 24px; 
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); 
    }
    
    /* Primary CTA Button */
    .stButton>button { 
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important; 
        color: #ffffff !important; 
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important; 
        font-size: 16px !important; 
        letter-spacing: 0.5px;
        border-radius: 8px !important; 
        border: none !important; 
        width: 100%; 
        padding: 16px !important; 
        transition: all 0.3s ease !important; 
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
    }
    .stButton>button:hover { 
        transform: translateY(-3px); 
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5); 
    }
    
    /* Expander / Accordion */
    .streamlit-expanderHeader {
        background-color: #151b2b !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
    }
    
    /* Subtitle Styling Box */
    .sub-box {
        background-color: #1a2235;
        border: 1px solid rgba(129, 140, 248, 0.3);
        border-radius: 8px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 10px;
    }
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

async def generate_tts(text, voice_model, output_file, engine="Edge-TTS (Default Free)", ttsmaker_key="", eleven_key="", custom_eleven_id="", gemini_key="", pitch=0, voice_fx="None (Standard Voice)"):
    if not text.strip(): return
    
    needs_ffmpeg = pitch != 0 or voice_fx != "None (Standard Voice)"
    temp_out = "temp_raw_audio_fx.wav" if needs_ffmpeg else output_file

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
                # 👇 FIX: Added timeout=300 (5 minutes) to prevent infinite hangs
                res = requests.post(url, json=payload, timeout=300)
                if res.status_code == 200:
                    candidate = res.json().get("candidates", [{}])[0]
                    if candidate.get("finishReason") == "SAFETY":
                        raise Exception("Safety Error: AI မှ အသံထွက်ပေးရန် ငြင်းဆိုလိုက်ပါသည်။")
                    
                    audio_b64 = candidate["content"]["parts"][0]["inlineData"]["data"]
                    pcm_data = base64.b64decode(audio_b64)
                    with wave.open(temp_out, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(pcm_data)
                    break
                elif res.status_code == 429:
                    last_err = f"Key {current_key[-4:]} ၏ တစ်နေ့စာ Limit ပြည့်သွားပါပြီ။"
                    continue
                else:
                    last_err = f"Gemini API Error ({res.status_code}): {res.text}"
                    continue
            except Exception as e: 
                last_err = str(e)
                continue
                
        if not os.path.exists(temp_out):
            raise Exception(f"ထည့်သွင်းထားသော Key များအားလုံး Limit ပြည့်သွားပါပြီ။ Key အသစ် ထပ်ထည့်ပါ။ နောက်ဆုံး Error: {last_err}")

    elif "ElevenLabs" in engine:
        if not eleven_key: raise Exception("ElevenLabs API Key လိုအပ်ပါသည်။")
        voice_id = custom_eleven_id.strip() if custom_eleven_id else ("21m00Tcm4TlvDq8ikWAM" if "Male" in voice_model else "AZnzlk1XvdvUeBnXmlld")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = { "Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": eleven_key }
        payload = { "text": text, "model_id": "eleven_multilingual_v2", "voice_settings": { "stability": 0.45, "similarity_boost": 0.75 } }
        # 👇 FIX: Added timeout
        res = requests.post(url, json=payload, headers=headers, timeout=300)
        if res.status_code == 200:
            with open(temp_out, "wb") as f: f.write(res.content)
        else: raise Exception(f"ElevenLabs API Error: {res.text}")
            
    elif "TTSMaker" in engine:
        if not ttsmaker_key: raise Exception("TTSMaker API Key လိုအပ်ပါသည်။")
        voice_id = 781 if "Female" in voice_model else 780
        url = "https://api.ttsmaker.com/v1/create-tts-order"
        payload = { "tts_api_key": ttsmaker_key, "tts_text": text, "voice_id": voice_id, "audio_format": "mp3" }
        # 👇 FIX: Added timeout
        res = requests.post(url, json=payload, timeout=300).json()
        if res.get("status") == "success":
            audio_data = requests.get(res["audio_file_url"]).content
            with open(temp_out, "wb") as f: f.write(audio_data)
        else: raise Exception(f"TTSMaker API Error: {res}")

    else:
        voice = "my-MM-ThihaNeural" if "Male" in voice_model else "my-MM-NilarNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(temp_out)

    if needs_ffmpeg:
        audio = ffmpeg.input(temp_out)
        if pitch != 0:
            factor = 1.0 + (pitch / 100.0) 
            new_sr = int(44100 * factor)
            atempo_val = 1.0 / factor
            audio = audio.filter('asetrate', new_sr).filter('atempo', atempo_val)
        if "Epic" in voice_fx: audio = audio.filter('bass', g=12, f=120)
        elif "Walkie-Talkie" in voice_fx: audio = audio.filter('highpass', f=400).filter('lowpass', f=3000).filter('volume', 1.5)
        elif "Reverb" in voice_fx: audio = audio.filter('aecho', 0.8, 0.88, 60, 0.4)
        elif "Demon" in voice_fx: audio = audio.filter('bass', g=15, f=100).filter('aecho', 0.8, 0.88, 40, 0.5)
        elif "ASMR" in voice_fx: audio = audio.filter('treble', g=12, f=6000).filter('volume', 1.5)
        try:
            (audio.output(output_file, acodec='pcm_s16le', ac=1, ar='44100').overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True))
        except Exception as e:
            import shutil
            shutil.copy(temp_out, output_file)
        finally:
            if os.path.exists(temp_out): os.remove(temp_out)

def parse_and_save_real_srt(raw_srt_text, output_file, use_fade=False):
    clean_srt = raw_srt_text.replace('```srt', '').replace('
```', '').strip()
    with open(output_file, "w", encoding="utf-8-sig") as f: f.write(clean_srt)
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
            if len(lines) > 0 and lines[-1].strip().isdigit(): lines.pop()
            block = " ".join(lines)
        else: block = clean_srt[text_start:].strip().replace('\n', ' ')
        if block:
            try:
                def to_sec(t):
                    h, m, s_ms = t.split(':')
                    s, ms = s_ms.split(',')
                    ms = ms.ljust(3, '0')
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
                text_content = block.strip()
                if use_fade: text_content = "{\\fad(250,250)}" + text_content
                parsed_lines.append((to_sec(start_str), to_sec(end_str), text_content))
                full_speech.append(block.strip())
            except: pass
    return parsed_lines, " ".join(full_speech)

def render_premium_saas_video(in_v, in_a, parsed_timestamps, out_v, ratio, use_bypass=False, use_blur=False, watermark="", subtitle_mode="Both (Burn + SRT)", use_mirror=False, use_color=False, use_grain=False, use_fps=False, sub_style_str="FontName=Pyidaungsu,FontSize=22,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2.5,Shadow=1,Alignment=2,MarginV=25"):
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
                f.write(f"{i}\n{fmt_t(start)} --> {fmt_t(safe_end)}\n{text}\n\n")
        video = ffmpeg.input(in_v).video
        if use_bypass: video = ffmpeg.filter(video, 'scale', '2*trunc(iw*1.08/2)', '2*trunc(ih*1.08/2)').filter('crop', 'iw/1.08', 'ih/1.08')
        if use_mirror: video = ffmpeg.filter(video, 'hflip')
        if use_color: video = ffmpeg.filter(video, 'eq', brightness=0.02, contrast=1.05, saturation=1.1)
        if use_grain: video = ffmpeg.filter(video, 'noise', alls=2, allf='t+u')
        if use_fps: video = ffmpeg.filter(video, 'fps', fps=24, round='near')
        video = ffmpeg.filter(video, 'scale', 'trunc(oh*a/2)*2', 1080, flags='bicubic')
        audio = ffmpeg.input(in_a).audio
        if v_max_dur > 1.0 and a_dur > 0:
            speed_factor = a_dur / (v_max_dur - 0.5)
            if 0.5 <= speed_factor <= 2.0: audio = ffmpeg.filter(audio, 'atempo', speed_factor)
        if use_blur: video = ffmpeg.filter(video, 'drawbox', x=0, y='ih-90', w='iw', h=90, color='black@0.95', thickness='fill')
        if ratio == "9:16 (TikTok/Shorts)": video = ffmpeg.filter(video, 'crop', 'min(iw, ih*9/16)', 'ih')
        elif ratio == "16:9 (YouTube)": video = ffmpeg.filter(video, 'crop', 'iw', 'min(ih, iw*9/16)')
        if watermark: video = ffmpeg.filter(video, 'drawtext', text=watermark, x='w-tw-15', y='15', fontsize=30, fontcolor='white@0.5')
        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"] and os.path.exists("subtitles.srt"):
            video = ffmpeg.filter(video, 'subtitles', safe_srt_path_escaped, charenc='UTF-8', fontsdir='.', force_style=sub_style_str)
        out = ffmpeg.output(video, audio, out_v, vcodec='libx264', acodec='aac', preset='fast', crf=21, t=v_max_dur)
        out.run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "Success"
    except ffmpeg.Error as e: return False, str(e)

# --- 3. UI INTERFACE ---
st.markdown('<div class="main-title">AETHER FILMWORKS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI Studio V52 ⚡ Premium Edition</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 Navigation Menu")
    app_mode = st.radio("Select Studio Mode:", ["🎙️ Movie Dubbing Studio", "🎥 Veo Video Studio", "🎵 Lyria Music Studio","⚡ Translation/Transcript Studio","📥 Video Downloader Hub",])
    st.markdown("---")
    ai_provider = st.selectbox("Choose AI Provider", ["Google Gemini (Flash - Recommended)", "OpenAI (GPT-5.5 Pro)", "Groq API (Fast & Free)"])
    api_key_input = st.text_input("API Keys", type="password", value=load_key(API_KEY_FILE))
    if api_key_input: save_key(API_KEY_FILE, api_key_input)

# =====================================================================
# 📌 MODE 1 - MOVIE DUBBING
# =====================================================================
if app_mode == "🎙️ Movie Dubbing Studio":
    with st.sidebar:
        audio_engine_choice = st.radio("Voice Platform", ["Edge-TTS (Default Free)", "Google Synergy TTS (Flash 3.1 Preview)", "ElevenLabs (Premium AI)", "TTSMaker (Free API)"])
        video_ratio = st.selectbox("Crop Ratio", ["Original", "9:16 (TikTok/Shorts)", "16:9 (YouTube)"])
        cb_bypass = st.checkbox("🔍 Smart Zoom", value=True)
        cb_mirror = st.checkbox("🪞 Mirror Effect", value=False)
        cb_color = st.checkbox("🎨 Color Tweaks", value=False)
        cb_grain = st.checkbox("🎞️ Subtle Film Grain", value=False)
        cb_fps = st.checkbox("🎬 Cinematic 24 FPS", value=False)
        cb_blur = st.checkbox("👁️ Cinematic Black Mask", value=True)
        watermark_text = st.text_input("Text Watermark", "")
        subtitle_mode = st.radio("Choose Subtitle Output", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"])

    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        video_url = st.text_input("🔗 Paste URL", placeholder="https://...")
        uploaded_file = st.file_uploader("📥 Upload Video", type=["mp4"])
    with col_in2:
        voice_char = st.selectbox("Select Character Voice", ["Synergy Puck (Male)", "Synergy Aoede (Female)", "Synergy Charon (Male - Deep)"])
        pitch_level = st.slider("🎙️ Voice Pitch", -30, 30, 0, 5)
        fx_level = st.selectbox("🎧 Voice FX", ["None (Standard Voice)", "🎙️ Epic Trailer Voice", "📻 Walkie-Talkie", "🏛️ Cinematic Reverb", "👹 Demon / Monster", "🤫 ASMR / Whisper"])
        
        with st.container():
            st.markdown("<div class='sub-box'>", unsafe_allow_html=True)
            st.markdown("<b>📝 Subtitle Pro Settings</b>", unsafe_allow_html=True)
            sub_position = st.selectbox("📍 Position", ["Bottom", "Center", "Top"])
            sub_color = st.selectbox("🎨 Color", ["Yellow", "White", "Neon Green"])
            sub_font = st.selectbox("🅰️ Font", ["Pyidaungsu", "MyanmarText", "Padauk"])
            sub_size = st.slider("🔠 Size", 16, 40, 22)
            sub_thickness = st.slider("✒️ Outline", 1.0, 5.0, 2.5, 0.5)
            sub_bg = st.checkbox("🔲 Background Box")
            sub_short = st.checkbox("✂️ Short & Punchy (Hormozi)")
            sub_fade = st.checkbox("✨ Cinematic Fades")
            st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🚀 START WORKFLOW"):
        v_input, a_extracted, a_generated, v_final, srt_final = "input_temp.mp4", "temp_extracted.mp3", "voice_temp.wav", "AETHER_RECAP_FINAL.mp4", "subtitles.srt"
        if uploaded_file:
            with open(v_input, "wb") as f: f.write(uploaded_file.read())
        else: download_video_from_url(video_url, v_input)
        
        extract_audio_fast(v_input, a_extracted)
        
        hormozi_rule = " 5. SHORT & PUNCHY (ALEX HORMOZI STYLE): Split subtitles into 3-5 words max." if sub_short else ""
        client = genai.Client(api_key=api_key_input)
        audio_file = client.files.upload(file=a_extracted)
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[audio_file, f"Generate Burmese SRT.{hormozi_rule}"])
        raw_text = response.text.strip().replace('```srt', '').replace('```', '')
        
        parsed_timestamps, speech_text = parse_and_save_real_srt(raw_text, srt_final, use_fade=sub_fade)
        
        # 👇 FIX: Removed ASS tags from text before sending to TTS engine
        raw_speech_text = " ".join([t for _,_,t in parsed_timestamps])
        clean_speech_text = re.sub(r'\{.*?\}', '', raw_speech_text)
        
        asyncio.run(generate_tts(clean_speech_text, voice_char, a_generated, engine=audio_engine_choice, gemini_key=api_key_input, pitch=pitch_level, voice_fx=fx_level))
        
        align_val = 2 if "Bottom" in sub_position else (5 if "Center" in sub_position else 8)
        prim_c = "&H0000FFFF" if "Yellow" in sub_color else ("&H00FFFFFF" if "White" in sub_color else "&H0000FF00")
        dyn_style = f"FontName={sub_font},FontSize={sub_size},PrimaryColour={prim_c},BackColour={'&H80000000' if sub_bg else '&H00000000'},Outline={0 if sub_bg else sub_thickness},Alignment={align_val},MarginV=60"
        
        render_premium_saas_video(v_input, a_generated, parsed_timestamps, v_final, video_ratio, cb_bypass, cb_blur, watermark_text, subtitle_mode, cb_mirror, cb_color, cb_grain, cb_fps, dyn_style)
        st.success("🎉 Done!")
        st.video(v_final)

# --- Other modes (Veo/Lyria/Translation/Downloader) remain unchanged ---
elif app_mode == "🎥 Veo Video Studio": pass
elif app_mode == "🎵 Lyria Music Studio": pass
elif app_mode == "⚡ Translation/Transcript Studio": pass
elif app_mode == "📥 Video Downloader Hub": pass
