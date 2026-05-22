# =====================================================================
# 📌 AETHER FILMWORKS AI // STUDIO V52 (FINAL PRODUCTION READY)
# =====================================================================

import streamlit as st
import google.generativeai as genai
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
    
    # ပြင်ဆင်ချက် ၁: Linux FFmpeg အတွက် utf-8-sig ဖြင့် သိမ်းခြင်း
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
        input_vid = ffmpeg.input(in_v)
        tts_audio = ffmpeg.input(in_a)
        
        # Hook 3-sec clip
        hook_video = input_vid.video.trim(start=20, end=23).setpts('PTS-STARTPTS')
        main_video = input_vid.video.setpts('PTS-STARTPTS')
        video = ffmpeg.concat(hook_video, main_video, v=1, a=0).node[0]
        
        # Features
        if use_bypass:
            video = ffmpeg.filter(video, 'scale', '2*trunc(iw*1.08/2)', '2*trunc(ih*1.08/2)')
            video = ffmpeg.filter(video, 'crop', 'iw/1.08', 'ih/1.08')
        video = ffmpeg.filter(video, 'scale', 'trunc(oh*a/2)*2', 1080, flags='bicubic')
        if use_blur: 
            video = ffmpeg.filter(video, 'drawbox', x=0, y='ih-90', w='iw', h=90, color='black@0.95', thickness='fill')
        if ratio == "9:16 (TikTok/Shorts)": 
            video = ffmpeg.filter(video, 'crop', 'min(iw, ih*9/16)', 'ih')
        elif ratio == "16:9 (YouTube)": 
            video = ffmpeg.filter(video, 'crop', 'iw', 'min(ih, iw*9/16)')
        if watermark: 
            video = ffmpeg.filter(video, 'drawtext', text=watermark, x='w-tw-15', y='15', fontsize=30, fontcolor='white@0.5')
        
        # SRT writing
        safe_srt_path_escaped = os.path.abspath("subtitles.srt").replace('\\', '/').replace(':', '\\:')
        with open("subtitles.srt", "w", encoding="utf-8-sig") as f:
            for i, (start, end, text) in enumerate(parsed_timestamps, start=1):
                def fmt_t(s): return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s-int(s))*1000):03d}"
                f.write(f"{i}\n{fmt_t(start+3)} --> {fmt_t(end+3)}\n{text}\n\n")

        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"]:
            video = ffmpeg.filter(video, 'subtitles', safe_srt_path_escaped, charenc='UTF-8', fontsdir='.', force_style="FontName=Pyidaungsu,FontSize=22,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2.5,Shadow=1,Alignment=2,MarginV=25")

        ffmpeg.output(video, tts_audio, out_v, vcodec='libx264', acodec='aac', preset='fast', crf=21).overwrite_output().run(cmd=FFMPEG_BINARY, quiet=True)
        return True, "Success"
    except Exception as e:
        return False, str(e)
# Helper function
def fmt_t(s): 
    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s-int(s))*1000):03d}"

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
        api_key_input = st.text_input("Gemini Keys (Comma separated)", type="password", value=saved_gemini, placeholder="Key1, Key2...")
        if api_key_input and api_key_input != saved_gemini: save_key(API_KEY_FILE, api_key_input)
    elif "Groq" in ai_provider:
        saved_groq = load_key(GROQ_KEY_FILE)
        api_key_input = st.text_input("Groq API Key", type="password", value=saved_groq)
        if api_key_input and api_key_input != saved_groq: save_key(GROQ_KEY_FILE, api_key_input)
    else:
        saved_openai = load_key(OPENAI_KEY_FILE)
        api_key_input = st.text_input("OpenAI API Key", type="password", value=saved_openai)
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
            synergy_key = st.text_input("Enter API Key for Synergy TTS", type="password", value=saved_gemini)

        if "ElevenLabs" in audio_engine_choice:
            saved_eleven = load_key(ELEVEN_KEY_FILE)
            eleven_key_input = st.text_input("ElevenLabs API Key", type="password", value=saved_eleven)
            if eleven_key_input and eleven_key_input != saved_eleven: save_key(ELEVEN_KEY_FILE, eleven_key_input)
            
            saved_voice_id = load_key(ELEVEN_VOICE_ID_FILE)
            custom_eleven_id = st.text_input("Custom Voice ID (Optional)", value=saved_voice_id, placeholder="e.g., pNInz6obbfdqI2CCOruU")
            if custom_eleven_id and custom_eleven_id != saved_voice_id: save_key(ELEVEN_VOICE_ID_FILE, custom_eleven_id)
        
        key_ttsmaker = st.text_input("TTSMaker API Key", type="password") if "TTSMaker" in audio_engine_choice else ""

        st.markdown("---")
        st.markdown("### 📐 4. Layout & Protection")
        video_ratio = st.selectbox("Crop Ratio", ["Original", "9:16 (TikTok/Shorts)", "16:9 (YouTube)"])
        cb_bypass = st.checkbox("🔒 Copyright Bypass Mode (Smart Zoom)", value=True)
        cb_blur = st.checkbox("👁️ Cinematic Black Mask (Hide Chinese Subs)", value=True)
        watermark_text = st.text_input("Text Watermark", "")

        st.markdown("---")
        st.markdown("### 📝 5. Subtitle Mode")
        subtitle_mode = st.radio("Choose Subtitle Output", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"])

    st.markdown('<div class="setting-panel"><h3>📺 Media Acquisition & Setup</h3>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns([1, 1])

    with col_in1:
        video_url = st.text_input("🔗 Paste Short Drama URL Link", placeholder="https://...")
        uploaded_file = st.file_uploader("📥 OR Upload Video File (MP4)", type=["mp4"])

    with col_in2:
        if "Synergy" in audio_engine_choice:
            dynamic_options = ["Synergy Puck (Male)", "Synergy Aoede (Female)", "Synergy Charon (Male - Deep)"]
        elif "ElevenLabs" in audio_engine_choice:
            dynamic_options = ["Adam (Male Deep)", "Rachel (Female)"]
        elif "TTSMaker" in audio_engine_choice:
            dynamic_options = ["TTSMaker Male (Voice 780)", "TTSMaker Female (Voice 781)"]
        else:
            dynamic_options = ["ဇော်ဇော် (Male Voice)", "အောင်အောင် (Male - Deep)", "နှင်းနှင်း (Female Voice)"]
            
        voice_char = st.selectbox("Select Character Voice", dynamic_options, index=0)
        
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 START ONE-CLICK WORKFLOW MONETIZE GENERATOR"):
        if not api_key_input: st.error("⚠️ API Key အား ထည့်သွင်းပေးပါ ဆရာကြီး။")
        elif not uploaded_file and not video_url: st.error("⚠️ ဗီဒီယိုဖိုင် သို့မဟုတ် Link တစ်ခုခု ထည့်ပေးပါ။")
        else:
            st.session_state.render_success = False
            st.session_state.original_transcript = ""
            st.session_state.generated_script = ""
            
            v_input, a_extracted, a_generated, v_final, srt_final = "input_temp.mp4", "temp_extracted.mp3", "voice_temp.wav", "AETHER_RECAP_FINAL.mp4", "subtitles.srt"

            with st.spinner("⏳ [အဆင့် ၁/၆] ဗီဒီယို ဖိုင်အား စနစ်ထဲသို့ ဆွဲသွင်းနေပါသည်..."):
                if uploaded_file:
                    with open(v_input, "wb") as f: f.write(uploaded_file.read())
                else: download_video_from_url(video_url, v_input)
                
                extracted_res = extract_audio_fast(v_input, a_extracted)
                if not extracted_res or not os.path.exists(a_extracted):
                    st.error("❌ ဗီဒီယိုထဲကနေ အသံဖိုင် ခွဲထုတ်လို့ မရပါဘူး။")
                    st.stop()

            with st.spinner(f"⏳ [အဆင့် ၂/၆] {ai_provider} ကိုအသုံးပြု၍ Audio Tags များပါဝင်သော ဇာတ်ညွှန်း ရေးသားနေပါသည်..."):
                try:
                    base_prompt = "You are an expert Myanmar (Burmese) TikTok movie recap narrator. I am providing you with an English SRT file translated from the original audio. Translate and adapt the text into highly engaging, natural spoken Burmese (မြန်မာစကားပြောဟန်). STRICT RULES: 1. SYNERGY AUDIO TAGS: You MUST include inline audio tags to direct the TTS voice. Use tags like [pause=0.5], [pause=1.0], [excited], [neutral], [whispers], [reluctantly] at the beginning of relevant sentences to add emotion and dramatic pacing. 2. NO ENGLISH TRANSLITERATION: Translate meanings naturally. 3. FORMAT: Keep the EXACT original SRT timecodes and indices. 4. Output ONLY the raw SRT format."

                    if "Gemini" in ai_provider:
                        keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                        success_gemini = False
                        last_err = ""
                        st.session_state.original_transcript = "[Gemini Model processed Audio directly.]"
                        
                        for idx, current_key in enumerate(keys_list):
                            try:
                                genai.configure(api_key=current_key)
                                audio_file = genai.upload_file(path=a_extracted)
                                while audio_file.state.name == "PROCESSING":
                                    time.sleep(2)
                                    audio_file = genai.get_file(audio_file.name)
                                
                               # အရင်က code လေးကို ဖျက်ပြီး အခုဟာနဲ့ အစားထိုးပါ
                                try:
                            model = genai.GenerativeModel('gemini-3.0-flash')
                        response = model.generate_content(prompt)
except:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt),
                                    safety_settings=[
                                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                                    ]
                                )
                                gemini_prompt = "Listen to the ENTIRE audio file from the absolute beginning to the very last second. Do NOT truncate, skip, or summarize the ending. You MUST generate a complete SRT subtitle file in natural spoken Burmese (မြန်မာစကားပြောဟန်) covering the WHOLE video duration until the very end. 🛑 STRICT RULES: 1. Include Synergy Audio Tags like [pause=0.5], [pause=1.0], [excited], [neutral], [whispers] to guide the voice naturally. 2. NO ENGLISH TRANSLITERATION. 3. Output ONLY valid SRT format."
                                response = model.generate_content([audio_file, gemini_prompt])
                                raw_output_text = response.text.strip()
                                genai.delete_file(audio_file.name)
                                success_gemini = True
                                break 
                            except Exception as e:
                                last_err = str(e)
                                if "429" in last_err or "quota" in last_err.lower() or "exhausted" in last_err.lower() or "limit" in last_err.lower():
                                    st.toast(f"⚠️ Key {idx+1} Limit ကုန်သွားပါပြီ။ နောက် Key ကို ပြောင်းလဲချိတ်ဆက်နေပါသည်...", icon="🔄")
                                    continue
                                else: break

                        if not success_gemini: raise Exception(f"Gemini API များကို အသုံးပြု၍မရပါ: {last_err}")

                    elif "Groq" in ai_provider:
                        client = Groq(api_key=api_key_input)
                        with open(a_extracted, "rb") as file:
                            transcription = client.audio.translations.create(file=(a_extracted, file.read()), model="whisper-large-v3", response_format="verbose_json")
                        
                        transcript_srt = ""
                        segments = getattr(transcription, 'segments', None)
                        if not segments and isinstance(transcription, dict): segments = transcription.get('segments')
                        if segments:
                            for i, seg in enumerate(segments, start=1):
                                start_t = seg.get('start', 0) if isinstance(seg, dict) else getattr(seg, 'start', 0)
                                end_t = seg.get('end', 0) if isinstance(seg, dict) else getattr(seg, 'end', 0)
                                text_seg = seg.get('text', '') if isinstance(seg, dict) else getattr(seg, 'text', '')
                                def fmt_t(s): return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d},{int((s-int(s))*1000):03d}"
                                transcript_srt += f"{i}\n{fmt_t(start_t)} --> {fmt_t(end_t)}\n{text_seg.strip()}\n\n"
                        else: transcript_srt = getattr(transcription, 'text', str(transcription))
                        
                        st.session_state.original_transcript = transcript_srt
                        completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "You are a professional Burmese movie recap narrator."}, {"role": "user", "content": f"{base_prompt} --- ORIGINAL SRT --- {transcript_srt}"}])
                        raw_output_text = completion.choices[0].message.content

                    else: # OpenAI
                        openai.api_key = api_key_input
                        with open(a_extracted, "rb") as file: transcription = openai.audio.translations.create(model="whisper-1", file=file, response_format="srt")
                        transcript_srt = transcription if isinstance(transcription, str) else transcription.text
                        st.session_state.original_transcript = transcript_srt
                        response = openai.chat.completions.create(model="gpt-5.5-pro" if "5.5" in ai_provider else "gpt-4o", messages=[{"role": "system", "content": "You are an expert Burmese content creator."}, {"role": "user", "content": f"{base_prompt} --- ORIGINAL SRT --- {transcript_srt}"}])
                        raw_output_text = response.choices[0].message.content
                    
                    parsed_timestamps, speech_text = parse_and_save_real_srt(raw_output_text, srt_final)
                    st.session_state.generated_script = raw_output_text
                except Exception as e: st.error(f"{ai_provider} Logic Error: {e}"); st.stop()

            with st.spinner(f"⏳ [အဆင့် ၄/၆] {audio_engine_choice} စနစ်ဖြင့် AI Voice Over ထုတ်လုပ်နေပါသည်..."):
                try:
                    custom_id = locals().get('custom_eleven_id', '')
                    final_gemini_key = locals().get('synergy_key', api_key_input)
                    asyncio.run(generate_tts(" ".join([t for _,_,t in parsed_timestamps]), voice_char, a_generated, engine=audio_engine_choice, ttsmaker_key=key_ttsmaker, eleven_key=locals().get('eleven_key_input', ''), custom_eleven_id=custom_id, gemini_key=final_gemini_key))
                except Exception as e:
                    st.error(f"အသံထုတ်လုပ်ခြင်း မအောင်မြင်ပါ: {e}")
                    st.stop()

            with st.spinner("⏳ [အဆင့် ၅+၆] ဗီဒီယိုနှင့် စာတန်းထိုးအား ရွေးချယ်ထားသော စနစ်အတိုင်း ဖန်တီးနေပါသည်..."):
                success, err_msg = render_premium_saas_video(v_input, a_generated, parsed_timestamps, v_final, video_ratio, cb_bypass, cb_blur, watermark_text, subtitle_mode)
                if success: st.session_state.render_success = True
                else: st.error(f"Rendering Sync Failure: {err_msg}")

    if st.session_state.render_success:
        st.balloons(); st.success(f"🎉 One-Click ဗီဒီယိုနှင့် စာတန်းထိုး အောင်မြင်စွာ ထွက်လာပါပြီ!")
        col_out1, col_out2 = st.columns([1, 1])
        with col_out1:
            if os.path.exists("AETHER_RECAP_FINAL.mp4"): 
                st.video("AETHER_RECAP_FINAL.mp4")
                st.markdown('<div class="setting-panel">', unsafe_allow_html=True)
                st.markdown("<h4>📥 Download Dashboard</h4>", unsafe_allow_html=True)
                with open("AETHER_RECAP_FINAL.mp4", "rb") as vf: 
                    st.download_button("📥 Download Recap Video (MP4)", vf, "Aether_Recap.mp4", key="final_v")
                if os.path.exists("subtitles.srt"):
                    with open("subtitles.srt", "rb") as sf: 
                        st.download_button("📥 Download Subtitles (.SRT)", sf, "Aether_Subs.srt", key="final_s")
                st.markdown('</div>', unsafe_allow_html=True)
                
        with col_out2:
            st.markdown('<div class="setting-panel"><h3>📝 Scripts Mini Window</h3>', unsafe_allow_html=True)
            with st.expander("👁️ Original English Transcript (မူရင်း)", expanded=True):
                st.text_area("Whisper မှ ခွဲထုတ်ပေးသော မူရင်းစာသား:", value=st.session_state.original_transcript, height=200, disabled=True)
            with st.expander("🇲🇲 Translated Burmese Script (မြန်မာပြန်)", expanded=True):
                st.text_area("AI မှ ပြန်လည်ရေးသားထားသော ဇာတ်ညွှန်း (Audio Tags များနှင့်အတူ):", value=st.session_state.generated_script, height=200, disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# 📌 MODE 2 - VEO VIDEO STUDIO
# =====================================================================
elif app_mode == "🎥 Veo Video Studio":
    st.markdown('<div class="setting-panel"><h3>🎥 Veo 2.0 Cinematic Video Generator</h3>', unsafe_allow_html=True)
    st.markdown("Movie Recap ဗီဒီယိုများအတွက် လိုအပ်သော B-Roll နှင့် နောက်ခံရုပ်သံဖိုင်များကို AI ဖြင့် အလွယ်တကူ ဖန်တီးပါ။")
    video_prompt = st.text_area("🎬 Enter Video Prompt", placeholder="e.g., A cinematic slow-motion drone shot of a futuristic cyberpunk city at night with neon lights...")
    if st.button("🚀 Generate Veo Video"):
        if not api_key_input: st.error("⚠️ AI Studio API Key လိုအပ်ပါသည်။")
        elif not video_prompt: st.error("⚠️ Video Prompt ရိုက်ထည့်ပေးပါ။")
        else:
            with st.spinner("🎥 Veo မှ ဗီဒီယို ဖန်တီးနေပါသည် (အချိန်အနည်းငယ် ကြာနိုင်ပါသည်)..."):
                try:
                    keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                    success = False
                    for key in keys_list:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/veo-2.0-preview:generateContent?key={key}"
                        payload = {"contents": [{"parts": [{"text": video_prompt}]}], "generationConfig": {"responseModalities": ["VIDEO"]}}
                        res = requests.post(url, json=payload)
                        if res.status_code == 200:
                            video_b64 = res.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                            with open("veo_output.mp4", "wb") as f: f.write(base64.b64decode(video_b64))
                            success = True
                            break
                    if success:
                        st.success("🎉 Veo ဗီဒီယို အောင်မြင်စွာ ထွက်လာပါပြီ!")
                        st.video("veo_output.mp4")
                        with open("veo_output.mp4", "rb") as f: st.download_button("📥 Download Video", f, "Veo_Generated.mp4")
                    else: st.error("❌ API Request Failed. Veo မော်ဒယ်အား ယခု Key ဖြင့် သုံး၍မရသေးပါ။")
                except Exception as e: st.error(f"Error: {e}")

# =====================================================================
# 📌 MODE 3 - LYRIA MUSIC STUDIO
# =====================================================================
elif app_mode == "🎵 Lyria Music Studio":
    st.markdown('<div class="setting-panel"><h3>🎵 Lyria 3 Pro Music Generator</h3>', unsafe_allow_html=True)
    st.markdown("Movie Recap ဗီဒီယိုများအတွက် ဇာတ်ဝင်ခန်းနှင့် လိုက်ဖက်မည့် နောက်ခံဂီတ (BGM) များကို AI ဖြင့် ဖန်တီးပါ။")
    music_prompt = st.text_area("🎧 Enter Music Prompt", placeholder="e.g., Epic cinematic orchestral background music for a suspenseful horror movie scene...")
    if st.button("🚀 Generate Lyria Music"):
        if not api_key_input: st.error("⚠️ AI Studio API Key လိုအပ်ပါသည်။")
        elif not music_prompt: st.error("⚠️ Music Prompt ရိုက်ထည့်ပေးပါ။")
        else:
            with st.spinner("🎵 Lyria 3 မှ (၃၀) စက္ကန့်စာ ဂီတ ဖန်တီးနေပါသည်..."):
                try:
                    keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                    success = False
                    for key in keys_list:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/lyria-3-pro-preview:generateContent?key={key}"
                        payload = {"contents": [{"parts": [{"text": music_prompt}]}], "generationConfig": {"responseModalities": ["AUDIO"]}}
                        res = requests.post(url, json=payload)
                        if res.status_code == 200:
                            audio_b64 = res.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                            with open("lyria_output.mp3", "wb") as f: f.write(base64.b64decode(audio_b64))
                            success = True
                            break
                    if success:
                        st.success("🎉 Lyria ဂီတ အောင်မြင်စွာ ထွက်လာပါပြီ!")
                        st.audio("lyria_output.mp3")
                        with open("lyria_output.mp3", "rb") as f: st.download_button("📥 Download Music", f, "Lyria_Generated.mp3")
                    else: st.error("❌ API Request Failed. Lyria မော်ဒယ်အား ယခု Key ဖြင့် သုံး၍မရသေးပါ။")
                except Exception as e: st.error(f"Error: {e}")

# =====================================================================
# 📌 MODE 4: TRANSLATION / TRANSCRIPT STUDIO (Whisper Timeline + Gemini Translation)
# =====================================================================
elif app_mode == "⚡ Translation/Transcript Studio":
    st.markdown('<h2 style="color:#00e5ff;">⚡ Translation & Subtitle Studio (AI Dual Engine)</h2>', unsafe_allow_html=True)
    st.markdown("Whisper AI ဖြင့် မီလီစက္ကန့်မလွဲ Timeline ယူ၍ Gemini 2.5 ဖြင့် အဓိပ္ပာယ်မှန်ကန်စွာ ဘာသာပြန်ဆိုခြင်း")

    st.markdown("### 📥 1. Video URL ထည့်ရန်")
    video_url = st.text_input("YouTube / FB / TikTok / Rednote URL ထည့်ပါ:")
    
    if "srt_path" not in st.session_state: st.session_state.srt_path = None
    if "title_suggestions" not in st.session_state: st.session_state.title_suggestions = []
    if "process_done" not in st.session_state: st.session_state.process_done = False

    if st.button("🚀 စတင်လုပ်ဆောင်မည်"):
        raw_keys = load_key(API_KEY_FILE)
        api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()] if raw_keys else []
        
        if not api_keys:
            st.error("⚠️ ကျေးဇူးပြု၍ ဘယ်ဘက် Menu တွင် Gemini API Key ကို အရင်ထည့်ပါ။")
        elif not video_url:
            st.error("⚠️ URL ထည့်သွင်းရန် လိုအပ်ပါသည်။")
        else:
            st.session_state.process_done = False
            st.session_state.title_suggestions = []
            
            with st.spinner("🔄 စနစ်နှစ်ခုစလုံး အလုပ်လုပ်နေပါသည်... (ကျေးဇူးပြု၍ စောင့်ပါ)"):
                error_logs = []
                try:
                    import whisper # Whisper library အား အသုံးပြုခြင်း
                    project_id = "project_" + str(int(time.time()))
                    
                    # 1. Download Audio ONLY ⚡
                    st.info("⬇️ ဗီဒီယိုမှ အသံလမ်းကြောင်းကို ရယူနေပါသည်...")
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f'{project_id}.%(ext)s',
                        'quiet': True,
                        'no_warnings': True,
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        }
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        downloaded_audio = ydl.prepare_filename(info)

                    # 2. Convert to Standard WAV for Whisper
                    wav_path = f"{project_id}.wav"
                    (
                        ffmpeg.input(downloaded_audio)
                        .output(wav_path, format='wav', acodec='pcm_s16le', ac=1, ar='16k')
                        .overwrite_output().run(quiet=True)
                    )
                    if os.path.exists(downloaded_audio): os.remove(downloaded_audio)

                    # 3. Whisper AI - CapCut ကဲ့သို့ မီလီစက္ကန့်မလွဲ Timeline ဖတ်ယူခြင်း 🎙️
                    st.info("🎙️ Whisper AI က ဗီဒီယိုအသံကို နားထောင်၍ တိကျသော Timeline ထုတ်ယူနေပါသည်...")
                    whisper_model = whisper.load_model("base") # ပေါ့ပါးမြန်ဆန်သော Base Model ကိုသုံးပါမည်
                    whisper_result = whisper_model.transcribe(wav_path, word_timestamps=False)
                    
                    # Whisper မှ ထွက်လာသော သန့်စင်ပြီးသား Timeline segments များ
                    segments = whisper_result.get("segments", [])
                    
                    # Gemini သို့ ပို့ရန် စက္ကန့်များနှင့် စာသားများအား ကျစ်လျစ်စွာ ပြင်ဆင်ခြင်း
                    whisper_json = []
                    for seg in segments:
                        whisper_json.append({
                            "start": round(seg["start"], 3),
                            "end": round(seg["end"], 3),
                            "text": seg["text"].strip()
                        })

                    # 4. Gemini 2.5 Flash - တိကျသော Timeline အတိုင်း မြန်မာဘာသာသို့ အနုပညာဆန်စွာ ပြန်ဆိုခြင်း 🤖
                    st.info("🤖 Gemini 2.5 Flash ဖြင့် မူရင်းအချိန်အတိုင်း မြန်မာဘာသာပြန်ဆိုနေပါသည်...")
                    response_json = None
                    
                    # Whisper မှရလာသော တိကျသည့် အချိန်အတုံးလေးများကို မပြောင်းလဲဘဲ text ကိုသာ မြန်မာပြန်ခိုင်းသည့် Prompt
                    prompt = f"""
                    You are an expert movie subtitle translator. You are given a JSON array of subtitles with precise timestamps.
                    Your tasks:
                    1. Generate 5 different viral, short, catchy video titles in Myanmar language.
                    2. Translate the "text" field of each item into natural, high-quality Myanmar (Burmese) language suitable for a TikTok movie recap. KEEP THE EXACT "start" AND "end" TIMESTAMPS UNCHANGED.
                    
                    Input Data:
                    {json.dumps(whisper_json, ensure_ascii=False)}
                    
                    Output MUST be ONLY a valid JSON object. Do not include ```json or any markdown formatting.
                    The output JSON structure MUST be exactly like this:
                    {{
                      "titles": ["ခေါင်းစဉ် ၁", "ခေါင်းစဉ် ၂", "ခေါင်းစဉ် ၃", "ခေါင်းစဉ် ၄", "ခေါင်းစဉ် ၅"],
                      "subtitles": [
                        {{"start": 0.038, "end": 0.988, "text": "မြန်မာဘာသာပြန်စာသား"}}
                      ]
                    }}
                    """
                    
                    for index, current_key in enumerate(api_keys):
                        try:
                            st.toast(f"🔑 Key ({index + 1}/{len(api_keys)}) ဖြင့် ကြိုးစားနေပါသည်...", icon="⏳")
                            genai.configure(api_key=current_key)
                            
                            # အရင်က code လေးကို ဖျက်ပြီး အခုဟာနဲ့ အစားထိုးပါ
try:
    model = genai.GenerativeModel('gemini-3.0-flash')
    response = model.generate_content(prompt)
except:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
                    
                            
                            raw_text = response.text.strip().replace("```json", "").replace("```", "")
                            response_json = json.loads(raw_text)
                            break 
                        except Exception as api_error:
                            error_logs.append(str(api_error))
                            continue
                    
                    if response_json is None:
                        st.error("🚨 Gemini API Key များ အဆင်မပြေပါ။")
                        raise Exception("Gemini Error")

                    st.session_state.title_suggestions = response_json.get("titles", [])
                    final_subtitles = response_json.get("subtitles", [])

                    # 5. မီလီစက္ကန့်မလွဲသော SRT ဖိုင်အဖြစ် ပြောင်းလဲထုတ်ယူခြင်း 🛠️
                    st.session_state.srt_path = f"{project_id}.srt"
                    with open(st.session_state.srt_path, "w", encoding="utf-8-sig") as f:
                        for i, sub in enumerate(final_subtitles):
                            def format_seconds(secs):
                                total_seconds = float(secs)
                                hours = int(total_seconds // 3600)
                                minutes = int((total_seconds % 3600) // 60)
                                seconds = int(total_seconds % 60)
                                milliseconds = int(round((total_seconds % 1) * 1000))
                                return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
                            
                            start_str = format_seconds(sub['start'])
                            end_str = format_seconds(sub['end'])
                            f.write(f"{i+1}\n{start_str} --> {end_str}\n{sub['text']}\n\n")

                    st.session_state.process_done = True
                    st.success("🎉 Whisper & Gemini ပူးပေါင်းမှု အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ လုပ်ဆောင်ချက် မှားယွင်းပါသည်- {str(e)}")
                finally:
                    if os.path.exists(wav_path): os.remove(wav_path)

    # ---------------------------------------------------------
    # 📺 UI OUTPUT AREA
    # ---------------------------------------------------------
    if st.session_state.process_done and st.session_state.srt_path and os.path.exists(st.session_state.srt_path):
        st.markdown("---")
        
        if st.session_state.title_suggestions:
            st.markdown("### 🏷️ TikTok Viral Title Suggestions (ခေါင်းစဉ် ၅ မျိုး)")
            for t_title in st.session_state.title_suggestions:
                st.code(f"{t_title}", language="text")

        st.markdown("### 📥 Download Subtitle")
        with open(st.session_state.srt_path, "rb") as f:
            st.download_button(label="📥 Download Subtitle (.srt ဖိုင်ရယူရန်)", data=f, file_name="MrZack_Whisper_Perfect.srt", mime="text/plain")
            st.caption("💡 **ပြီးပြည့်စုံသော နည်းလမ်း:** ယခုထွက်လာသော SRT သည် Whisper က ကွက်တိ နေရာချပေးထားပြီး Gemini က ဘာသာပြန်ပေးထားခြင်း ဖြစ်သဖြင့် CapCut PC ထဲသို့ သွင်းလိုက်ရုံဖြင့် အချိန်ကော စာသားပါ မလွဲမသွေ ကွက်တိကျနေပါလိမ့်မည်။")

        st.markdown("### 📝 Subtitle Preview")
        with open(st.session_state.srt_path, "r", encoding="utf-8") as f:
            st.text_area("SRT Preview", value="".join(f.readlines()[:20]), height=150)

# =====================================================================
# 📌 MODE 5: VIDEO DOWNLOADER HUB (Original Quality Multi-Platform Downloader)
# =====================================================================
elif app_mode == "📥 Video Downloader Hub":
    st.markdown('<h2 style="color:#00e5ff;">📥 Video Downloader Hub</h2>', unsafe_allow_html=True)
    st.markdown("YouTube, TikTok, Facebook, Rednote (小红书) စသည့် ဗီဒီယိုများကို မူရင်းအတိုင်း ဒေါင်းလုဒ်ဆွဲရန်")

    st.markdown("### 🔗 ဗီဒီယို Link ထည့်ရန်")
    dl_url = st.text_input("ဗီဒီယို URL ကို ဒီမှာ ထည့်ပါ (ဥပမာ- TikTok, YouTube, Rednote, FB):", key="hub_dl_url")
    
    # Session State ဖိုင်လမ်းကြောင်း သိမ်းဆည်းရန်
    if "hub_file_path" not in st.session_state: st.session_state.hub_file_path = None
    if "hub_file_name" not in st.session_state: st.session_state.hub_file_name = "downloaded_video.mp4"
    if "hub_done" not in st.session_state: st.session_state.hub_done = False

    if st.button("⬇️ ဗီဒီယို စစ်ဆေးပြီး ဒေါင်းလုဒ်ဆွဲမည်"):
        if not dl_url:
            st.error("⚠️ ကျေးဇူးပြု၍ ဗီဒီယို Link တစ်ခုခု အရင်ထည့်သွင်းပေးပါ။")
        else:
            st.session_state.hub_done = False
            with st.spinner("🔄 ဗီဒီယိုအား Platform မှ မူရင်းအတိုင်း ဖတ်ယူနေပါသည်... (ကျေးဇူးပြု၍ စောင့်ပါ)"):
                try:
                    # ဖိုင်နာမည် မထပ်စေရန် Time ID သုံးခြင်း
                    dl_project_id = "dl_" + str(int(time.time()))
                    
                    # 🚀 Multi-Platform & Original Quality အတွက် yt-dlp Options ချိန်ညှိခြင်း
                    ydl_hub_opts = {
                        # အကောင်းဆုံး Video ရော Audio ကိုပါ မူရင်းအတိုင်း ပေါင်းစပ်ထုတ်ယူရန် စနစ်
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': f'{dl_project_id}.%(ext)s',
                        'quiet': True,
                        'no_warnings': True,
                        # Rednote သို့မဟုတ် အချို့ တရုတ်ဆာဗာများအတွက် ပိတ်မကျသွားစေရန် Header ဖြည့်ခြင်း
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        }
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_hub_opts) as ydl:
                        # ဗီဒီယို အချက်အလက်များ ဖတ်ယူခြင်း
                        info_dict = ydl.extract_info(dl_url, download=True)
                        
                        # ဒေါင်းလုဒ်ပြီးသွားသော ဖိုင်လမ်းကြောင်းအား သိမ်းဆည်းခြင်း
                        st.session_state.hub_file_path = ydl.prepare_filename(info_dict)
                        
                        # ဗီဒီယို ခေါင်းစဉ်ကို ရယူပြီး ဖိုင်နာမည်အဖြစ် သတ်မှတ်ခြင်း (မရပါက Default သုံးမည်)
                        video_title = info_dict.get('title', 'downloaded_video')
                        # ဖိုင်နာမည်ထဲတွင် မပါသင့်သော သင်္ကေတများအား ဖယ်ရှားခြင်း
                        clean_title = "".join([c for c in video_title if c.isalpha() or c.isdigit() or c==' ']).strip()
                        st.session_state.hub_file_name = f"{clean_title or 'video'}.mp4"
                    
                    st.session_state.hub_done = True
                    st.toast("✅ ဗီဒီယိုကို ဆာဗာပေါ်သို့ အောင်မြင်စွာ ဆွဲယူပြီးပါပြီ။", icon="🚀")
                    st.rerun()

                except Exception as dl_err:
                    st.error(f"❌ ဗီဒီယို ဒေါင်းလုဒ်ဆွဲခြင်း မအောင်မြင်ပါ။ Link မှားနေခြင်း (သို့မဟုတ်) ပုဂ္ဂလိက ဗီဒီယို ဖြစ်နိုင်ပါသည်။")
                    with st.expander("🔍 အသေးစိတ် Error Details ကြည့်ရန်"):
                        st.write(str(dl_err))

    # ---------------------------------------------------------
    # 📺 DOWNLOAD BUTTON AREA (အလုပ်ပြီးပါက ချက်ချင်း ပေါ်လာမည့်နေရာ)
    # ---------------------------------------------------------
    if st.session_state.hub_done and st.session_state.hub_file_path and os.path.exists(st.session_state.hub_file_path):
        st.markdown("---")
        st.success("🎉 ဗီဒီယို အဆင်သင့်ဖြစ်ပါပြီ။ အောက်ပါခလုတ်ကို နှိပ်၍ ဖုန်း/ကွန်ပျူတာထဲသို့ သိမ်းဆည်းနိုင်ပါပြီ။")
        
        # ဗီဒီယို အစမ်းကြည့်ရှုရန် Player
        st.markdown("### 🎥 Video Preview")
        st.video(st.session_state.hub_file_path)
        
        # Local ထဲသို့ အပြီးသတ် ဒေါင်းလုဒ်ဆွဲမည့် ခလုတ်
        with open(st.session_state.hub_file_path, "rb") as file:
            st.download_button(
                label="📥 ကိုယ့်ဖုန်း/စက်ထဲသို့ ရယူရန် (Download Video)",
                data=file,
                file_name=st.session_state.hub_file_name,
                mime="video/mp4"
            )
