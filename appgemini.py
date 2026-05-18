```python
# =====================================================================
# 📌 AETHER FILMWORKS AI // STUDIO V51 (ULTIMATE MOBILE-SAFE VERSION)
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
import shutil

FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

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

# =====================================================================
# 📌 Theme & Styling
# =====================================================================
st.set_page_config(page_title="AETHER FILMWORKS AI // STUDIO V51", layout="wide")

st.markdown('''
    <style>
    .stApp { background: linear-gradient(135deg, #080510 0%, #0d0820 40%, #130b2e 100%) !important; color: #f0e6ff !important; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #080510 !important; border-right: 1px solid rgba(179, 71, 255, 0.2) !important; }
    h1, h2, h3, h4 { color: #00e5ff !important; font-family: 'Space Grotesk', sans-serif; font-weight: 800 !important; text-shadow: 0 0 15px rgba(0,229,255,0.2); }
    p, span, label, .stRadio label, .stCheckbox label, .stSelectbox label { color: #b8a9d4 !important; font-size: 14px; }
    .stTextInput input, div[data-baseweb="select"], .stTextArea textarea { background-color: #130b2e !important; color: #ffffff !important; border: 1px solid rgba(179, 71, 255, 0.3) !important; border-radius: 8px !important; }
    .setting-panel { background: #0d0820; border: 1px solid rgba(179, 71, 255, 0.15); border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 16px 48px rgba(0,0,0,0.6); }
    .stButton>button { background: linear-gradient(135deg, #b347ff 0%, #7c4dff 50%, #448aff 100%) !important; color: #ffffff !important; font-weight: 800 !important; font-size: 16px !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 15px !important; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0px 8px 30px rgba(179, 71, 255, 0.6); }
    </style>
''', unsafe_allow_html=True)

if "render_success" not in st.session_state: st.session_state.render_success = False
if "generated_script" not in st.session_state: st.session_state.generated_script = ""
if "original_transcript" not in st.session_state: st.session_state.original_transcript = ""

# =====================================================================
# 📌 Media & SRT Parser
# =====================================================================
def get_file_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path, cmd=FFMPEG_BINARY)
        stream = next((stream for stream in probe['streams'] if stream['codec_type'] in ['video', 'audio']), None)
        return float(stream['duration'])
    except: return 60.0

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

def parse_and_save_real_srt(raw_srt_text, output_file):
    clean_srt = raw_srt_text.replace("```srt", "").replace("```", "").strip()
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(clean_srt)
        
    parsed_lines = []
    full_speech = []
    matches = list(re.finditer(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', clean_srt))
    for i in range(len(matches)):
        start_str = matches[i].group(1).replace('.', ',')
        end_str = matches[i].group(2).replace('.', ',')
        text_start = matches[i].end()
        if i + 1 < len(matches):
            text_end = matches[i+1].start()
            block = clean_srt[text_start:text_end].strip()
            # SAFE LINE: Using chr(10) to avoid newline string literal errors on mobile copy
            block = re.sub(chr(10) + r'\d+$', '', block).strip()
        else:
            block = clean_srt[text_start:].strip()
        if block:
            try:
                def to_sec(t):
                    h, m, s_ms = t.split(':')
                    s, ms = s_ms.split(',')
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
                parsed_lines.append((to_sec(start_str), to_sec(end_str), block))
                full_speech.append(block)
            except Exception: pass

    if not parsed_lines:
        parsed_lines.append((0.0, 5.0, "[neutral] စာတန်းထိုး ဖော်မတ် မှားယွင်းနေပါသည်။"))
        full_speech.append("စာတန်းထိုး ဖော်မတ် မှားယွင်းနေပါသည်။")
    return parsed_lines, " ".join(full_speech)

# =====================================================================
# 📌 TTS & Auto-Sync 
# =====================================================================
async def generate_single_tts(text, voice_model, output_file, engine, ttsmaker_key="", eleven_key="", custom_eleven_id="", gemini_key=""):
    if not text.strip():
        (ffmpeg.input('anullsrc', f='lavfi', t=0.1).output(output_file, acodec='libmp3lame').run(cmd=FFMPEG_BINARY, overwrite_output=True, quiet=True))
        return

    if "Synergy" in engine:
        if not gemini_key: raise Exception("Gemini Synergy TTS API Key လိုအပ်ပါသည်။")
        keys_list = [k.strip() for k in gemini_key.split(",") if k.strip()]
        voice_name = "Puck" if "Puck" in voice_model else ("Charon" if "Charon" in voice_model else "Aoede")
        # SAFE LINE: Using chr(10) for newlines
        prompt_text = "You are a professional Burmese movie narrator. Read the following text naturally and expressively." + chr(10) + chr(10) + text
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "safetySettings": [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}}}
        }
        
        last_err = ""
        for retry in range(4):
            for current_key in keys_list:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={current_key}"
                res = requests.post(url, json=payload)
                if res.status_code == 200:
                    res_json = res.json()
                    try:
                        if res_json.get("candidates", [{}])[0].get("finishReason") == "SAFETY": raise Exception("Safety Error: AI မှ အသံထွက်ပေးရန် ငြင်းဆိုသည်။")
                        audio_b64 = res_json["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                        with wave.open(output_file, "wb") as wf:
                            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000); wf.writeframes(base64.b64decode(audio_b64))
                        return
                    except Exception as e: raise Exception(f"Parse Error: {e}")
                elif res.status_code == 429:
                    last_err = "API Skip: 429 (Quota Exceeded)"
                    continue
                elif res.status_code == 403:
                    last_err = "API Skip: 403 (Invalid Key)"
                    continue
                else:
                    last_err = f"API Error: {res.status_code}"
                    continue
            
            if "429" in last_err:
                time.sleep(15)
            else:
                time.sleep(3)
                
        raise Exception(f"ထည့်သွင်းထားသော Key များအားလုံး အလုပ်မလုပ်ပါ (သို့) Limit ကုန်သွားပါပြီ။ မှန်ကန်သော AI Studio Key များ ထပ်ထည့်ပေးပါ။ (Last state: {last_err})")

    else:
        voice = "my-MM-ThihaNeural" if "Male" in voice_model else "my-MM-NilarNeural"
        await edge_tts.Communicate(text, voice).save(output_file)

async def compile_synced_audio(parsed_timestamps, voice_char, final_audio_out, engine, ttsmaker_key, eleven_key, custom_id, gemini_key):
    temp_dir = "temp_audio_segments"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    concat_list_file = "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        current_time = 0.0
        for idx, (start_sec, end_sec, text) in enumerate(parsed_timestamps):
            target_duration = end_sec - start_sec
            raw_seg_file = os.path.join(temp_dir, f"raw_{idx}.wav")
            norm_seg_file = os.path.join(temp_dir, f"norm_{idx}.wav")
            final_seg_file = os.path.join(temp_dir, f"sync_{idx}.wav")
            gap = max(0, start_sec - current_time)
            if gap > 0.1:
                gap_file = os.path.join(temp_dir, f"gap_{idx}.wav")
                (ffmpeg.input('anullsrc', f='lavfi', t=gap).output(gap_file, acodec='pcm_s16le', ac=1, ar='24000').run(cmd=FFMPEG_BINARY, overwrite_output=True, quiet=True))
                # SAFE LINE
                f.write(f"file '{os.path.abspath(gap_file)}'{chr(10)}")
                current_time += gap
            await generate_single_tts(text, voice_char, raw_seg_file, engine, ttsmaker_key, eleven_key, custom_id, gemini_key)
            if "Synergy" in engine: time.sleep(4.5) 
            (ffmpeg.input(raw_seg_file).output(norm_seg_file, acodec='pcm_s16le', ac=1, ar='24000').run(cmd=FFMPEG_BINARY, overwrite_output=True, quiet=True))
            actual_duration = get_file_duration(norm_seg_file)
            if actual_duration > target_duration:
                speed_factor = min(actual_duration / target_duration, 1.25)
                (ffmpeg.input(norm_seg_file).filter('atempo', speed_factor).output(final_seg_file, acodec='pcm_s16le', ac=1, ar='24000').run(cmd=FFMPEG_BINARY, overwrite_output=True, quiet=True))
                final_dur = actual_duration / speed_factor
            elif actual_duration < target_duration - 0.2:
                pad_duration = target_duration - actual_duration
                pad_file = os.path.join(temp_dir, f"pad_{idx}.wav")
                (ffmpeg.input('anullsrc', f='lavfi', t=pad_duration).output(pad_file, acodec='pcm_s16le', ac=1, ar='24000').run(cmd=FFMPEG_BINARY, overwrite_output=True, quiet=True))
                with open("temp_pad_list.txt", "w", encoding="utf-8") as pf:
                    # SAFE LINE
                    pf.write(f"file '{os.path.abspath(norm_seg_file)}'{chr(10)}")
                    pf.write(f"file '{os.path.abspath(pad_file)}'{chr(10)}")
                (ffmpeg.input('temp_pad_list.txt', format='concat', safe=0).output(final_seg_file, acodec='pcm_s16le', ac=1, ar='24000').run(cmd=FFMPEG_BINARY, overwrite_output=True, quiet=True))
                final_dur = target_duration
            else:
                shutil.copy(norm_seg_file, final_seg_file)
                final_dur = actual_duration
            # SAFE LINE
            f.write(f"file '{os.path.abspath(final_seg_file)}'{chr(10)}")
            current_time += final_dur 
    try: (ffmpeg.input(concat_list_file, format='concat', safe=0).output(final_audio_out, acodec='libmp3lame', ar='44100').run(cmd=FFMPEG_BINARY, overwrite_output=True, quiet=True))
    except Exception as e: raise Exception(f"Concat Error: {e}")

# =====================================================================
# 📌 Video Rendering
# =====================================================================
def render_premium_saas_video(in_v, in_a, parsed_timestamps, out_v, ratio, use_bypass=False, use_blur=False, watermark="", subtitle_mode="Both (Burn + SRT)"):
    try:
        a_dur = get_file_duration(in_a); v_dur = get_file_duration(in_v); final_dur = max(a_dur, v_dur) 
        video = ffmpeg.input(in_v)
        if use_bypass:
            video = ffmpeg.filter(video, 'scale', '2*trunc(iw*1.08/2)', '2*trunc(ih*1.08/2)'); video = ffmpeg.filter(video, 'crop', 'iw/1.08', 'ih/1.08')
        if use_blur: video = ffmpeg.filter(video, 'drawbox', x=0, y='ih-90', w='iw', h=90, color='black@0.95', thickness='fill')
        if ratio == "9:16 (TikTok/Shorts)": video = ffmpeg.filter(video, 'crop', 'min(iw, ih*9/16)', 'ih')
        elif ratio == "16:9 (YouTube)": video = ffmpeg.filter(video, 'crop', 'iw', 'min(ih, iw*9/16)')
        if watermark: video = ffmpeg.filter(video, 'drawtext', text=watermark, x='w-tw-15', y='15', fontsize=26, fontcolor='white@0.4')
        if subtitle_mode in ["Burn into Video", "Both (Burn + SRT)"] and os.path.exists("subtitles.srt"):
            video = ffmpeg.filter(video, 'subtitles', 'subtitles.srt', force_style="FontSize=16,PrimaryColour=&H00FFFF&,Outline=2,Alignment=2")
        audio = ffmpeg.input(in_a).audio
        out = ffmpeg.output(video, audio, out_v, vcodec='libx264', acodec='aac', preset='ultrafast', t=final_dur)
        out.run(cmd=FFMPEG_BINARY, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return True, "Success"
    except ffmpeg.Error as e: return False, str(e)

# =====================================================================
# 📌 UI & Navigation
# =====================================================================
st.markdown('<h1 style="text-align:center; margin-bottom: 30px;">▲ AETHER FILMWORKS AI // STUDIO V51</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 Navigation Menu")
    app_mode = st.radio("Select Studio Mode:", ["🎙️ Movie Dubbing Studio", "🎥 Veo Video Studio", "🎵 Lyria Music Studio"])
    st.markdown("---")
    st.markdown("### 🔑 API Credentials")
    saved_gemini = load_key(API_KEY_FILE)
    api_key_input = st.text_input("Gemini / AI Studio Keys (Comma separated)", type="password", value=saved_gemini)
    if api_key_input and api_key_input != saved_gemini: save_key(API_KEY_FILE, api_key_input)
    st.caption("✨ AI Studio Key (AIzaSy...) ကို သုံးပါ။ ဇာတ်ညွှန်း၊ Veo နှင့် Lyria အတွက် လိုအပ်ပါသည်။")

# =====================================================================
# 📌 MODE 1 - MOVIE DUBBING
# =====================================================================
if app_mode == "🎙️ Movie Dubbing Studio":
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔊 Voice Engine")
        audio_engine_choice = st.radio("Select Voice Platform", ["Edge-TTS (Default Free)", "Google Synergy TTS (Flash 3.1)"])
        
        if "Synergy" in audio_engine_choice:
            st.caption("✨ AI Studio Key (AIzaSy...) များစွာကို ကော်မာခံ၍ ထည့်နိုင်သည်။")
            synergy_key = st.text_input("Enter Keys for Synergy TTS", type="password", value=saved_gemini)
        else:
            synergy_key = ""

        st.markdown("---")
        st.markdown("### 📐 Layout Settings")
        video_ratio = st.selectbox("Crop Ratio", ["Original", "9:16 (TikTok/Shorts)", "16:9 (YouTube)"])
        cb_bypass = st.checkbox("🔒 Copyright Bypass Mode", value=True)
        cb_blur = st.checkbox("👁️ Cinematic Black Mask", value=True)
        watermark_text = st.text_input("Text Watermark", "@Recapmaster")
        subtitle_mode = st.radio("Choose Subtitle Output", ["Both (Burn + SRT)", "Export SRT File Only", "Burn into Video"])

    st.markdown('<div class="setting-panel"><h3>📺 Media Acquisition & Setup</h3>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        video_url = st.text_input("🔗 Paste Short Drama URL Link", placeholder="https://...")
        uploaded_file = st.file_uploader("📥 OR Upload Video File (MP4)", type=["mp4"])
    with col_in2:
        if "Synergy" in audio_engine_choice: dynamic_options = ["Synergy Puck (Male)", "Synergy Aoede (Female)", "Synergy Charon (Male - Deep)"]
        else: dynamic_options = ["ဇော်ဇော် (Male Voice)", "နှင်းနှင်း (Female Voice)"]
        voice_char = st.selectbox("Select Character Voice", dynamic_options, index=0)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 START PRO SYNC DUBBING WORKFLOW"):
        if not api_key_input: st.error("⚠️ API Key အား ထည့်သွင်းပေးပါ ဆရာကြီး။")
        elif not uploaded_file and not video_url: st.error("⚠️ ဗီဒီယိုဖိုင် သို့မဟုတ် Link တစ်ခုခု ထည့်ပေးပါ။")
        else:
            v_input, a_extracted, a_generated, v_final, srt_final = "input_temp.mp4", "temp_extracted.mp3", "voice_temp_synced.mp3", "AETHER_RECAP_FINAL.mp4", "subtitles.srt"
            
            with st.spinner("⏳ [အဆင့် ၁/၆] ဗီဒီယို ဖိုင်အား စနစ်ထဲသို့ ဆွဲသွင်းနေပါသည်..."):
                if uploaded_file:
                    with open(v_input, "wb") as f: f.write(uploaded_file.read())
                else: download_video_from_url(video_url, v_input)
                extract_audio_fast(v_input, a_extracted)
            
            with st.spinner("⏳ [အဆင့် ၂/၆] Gemini ဖြင့် ဇာတ်ညွှန်း ရေးသားနေပါသည်..."):
                base_prompt = "You are a professional Burmese movie dubbing translator. Translate the SRT into natural spoken Burmese. DURATION CONTROL: Keep it SHORT to match the original audio duration. Output ONLY valid SRT format."
                try:
                    keys_list = [k.strip() for k in api_key_input.split(",") if k.strip()]
                    for key in keys_list:
                        genai.configure(api_key=key)
                        audio_file = genai.upload_file(path=a_extracted)
                        while audio_file.state.name == "PROCESSING": time.sleep(2); audio_file = genai.get_file(audio_file.name)
                        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
                        response = model.generate_content([audio_file, base_prompt])
                        st.session_state.generated_script = response.text.strip()
                        genai.delete_file(audio_file.name)
                        break
                    parsed_timestamps, _ = parse_and_save_real_srt(st.session_state.generated_script, srt_final)
                except Exception as e: st.error(f"Error: {e}"); st.stop()

            with st.spinner("⏳ [အဆင့် ၄/၆] AI Time-Sync Engine အား လည်ပတ်နေပါသည် (ဤအဆင့်သည် Limit မပြည့်စေရန် အချိန်အနည်းငယ် ယူပါမည်)..."):
                synergy_k = synergy_key if synergy_key else api_key_input
                asyncio.run(compile_synced_audio(parsed_timestamps, voice_char, a_generated, audio_engine_choice, "", "", "", synergy_k))

            with st.spinner("⏳ [အဆင့် ၅+၆] ဗီဒီယိုနှင့် စာတန်းထိုး ဖန်တီးနေပါသည်..."):
                success, err_msg = render_premium_saas_video(v_input, a_generated, parsed_timestamps, v_final, video_ratio, cb_bypass, cb_blur, watermark_text, subtitle_mode)
                if success:
                    st.balloons(); st.success("🎉 Pro Time-Synced ဗီဒီယို အောင်မြင်စွာ ထွက်လာပါပြီ!")
                    st.video("AETHER_RECAP_FINAL.mp4")
                    with open("AETHER_RECAP_FINAL.mp4", "rb") as vf: st.download_button("📥 Download Video", vf, "Aether_Recap_Synced.mp4")

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
