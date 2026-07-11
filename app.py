import streamlit as st
import google.generativeai as genai
from groq import Groq
from datetime import datetime
from io import StringIO

# Configure page
st.set_page_config(
    page_title="பர்சனல் ஏஐ ஜோதிடர்",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SYSTEM PROMPT - VEDIC & KP ASTROLOGY
# ============================================================================
SYSTEM_PROMPT = """நீ 30 வருடங்களுக்கு மேல் அனுபவம் வாய்ந்த, பாரம்பரிய தமிழ் வேதி ஜோதிட (Vedic Astrology) மற்றும் கேபி ஜோதிட (KP Astrology - Krishnamurti Paddhati) மாபெரும் நிபுணர். உன்னிடம் ஜாதகர் தனது முழு ஜாதக விவரங்கள் அடங்கிய கோப்பையும், தற்போதைய கோச்சார (Transit) நேரத்தையும் வழங்கி கேள்வி கேட்கிறார்.

[விதிமுறைகள் & பலன் சொல்லும் முறை]:
1. அணுகுமுறை: ஒரு தேர்ந்த தமிழ் ஜோசியர் எப்படி கனிவாகவும், பக்குவமாகவும், அதே சமயம் உண்மையை மறைக்காமல் நேர்மையாகவும் பேசுவாரோ, அதே போன்ற தமிழ் நடையில் பதில் அளிக்க வேண்டும் (உதாரணமாக: "வணக்கம் அன்பரே...", "உங்களுடைய தசா புத்தி அமைப்பின்படி...", "கவலை வேண்டாம்...").
2. தசா புத்தி ஆய்வு: ஜாதகரின் 5 நிலை தசா புத்திகளை (மகா தசா -> புத்தி -> அந்தரம் -> சூட்சுமம் -> பிராண தசா) தற்போதைய நேரத்தோடு ஒப்பிட்டு, தற்போதைய பிராண தசா சாதகமாக உள்ளதா என்று பார்க்க வேண்டும். தசா புத்தி மாறும் தேதிகளைக் குறிப்பிட்டு, எப்போது மாற்றம் நடக்கும் என்று துல்லியமாகச்ச் சொல்ல வேண்டும்.
3. வேதிக + கேபி கலவை: 
   - பொதுவான கேள்விகள் மற்றும் தசா பலன்களுக்கு 'வேதி ஜோதிட' முறையையும் (ராசி, லக்னம், கிரக பார்வை, 10-ஆம் அதிபதி நிலை), 
   - துல்லியமான 'ஆம்/இல்லை' மற்றும் 'காரிய சித்தி' போன்ற கேள்விகளுக்கு 'கேபி (KP) ஜோதிட' முறையையும் (பாவ தொடர்புகள், கிரகங்களின் நட்சத்திர நாதன் (Starlord), உப-நட்சத்திர நாதன் (Sublord) தொடர்புகள்) பயன்படுத்த வேண்டும்.
4. கோச்சாரம் (Transit): தற்போதை��� கோச்சார கிரக நிலைகளை, ஜாதகரின் பிறப்பு ராசி மற்றும் லக்னத்திற்கு ஒப்பிட்டு (உதாரணமாக: ஏழரை சனி, அஷ்டமத்து சனி, குரு பார்வை, ராகு-கேது பெயர்ச்சி தாக்கம்) இன்றைய நாள் அல்லது தற்போதைய காலம் எப்படி இருக்கும் என்று கணிக்க வேண்டும்.
5. பரிகாரம்: தேவையற்ற பயத்தை ஏற்படுத்தாமல், எளிய ஆன்மீக அல்லது எளிய வாழ்வியல் வழிகாட்டுதல்/பரிகாரங்களை (எந்த தெய்வத்தை வழிபட வேண்டும், என்ன தானம் செய்யலாம்) கூற வேண்டும்.

உன் பதில்கள் எப்போதும் ஜாதக விவரங்களை கொண்டு பாஷ்யம் செய்ய வேண்டும், மற்றும் தற்போதைய கோச்சார (Transit) நேரத்தை கருத்தில் கொண்டு பதில் அளிக்க வேண்டும்."""

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "horoscope_data" not in st.session_state:
    st.session_state.horoscope_data = None
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = None
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = None
if "api_provider" not in st.session_state:
    st.session_state.api_provider = "Groq"  # Default to Groq
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
if "model_used" not in st.session_state:
    st.session_state.model_used = None

# ============================================================================
# SIDEBAR - API KEY & FILE UPLOAD
# ============================================================================
with st.sidebar:
    st.title("⚙️ கட்டமைப்பு")
    
    # API Provider Selection
    st.subheader("🔌 API வழங்குநர் தேர்வு")
    api_provider = st.radio(
        "எந்த API ஐ பயன்படுத்த வேண்டும்?",
        options=["Groq", "Gemini"],
        help="Groq: விரைவு & இலவசம் | Gemini: Google AI"
    )
    st.session_state.api_provider = api_provider
    
    st.divider()
    
    # Groq API Key input
    if api_provider == "Groq" or True:  # Show both options
        groq_key_input = st.text_input(
            "Groq API Key (விரைவான & இலவசம்)",
            type="password",
            placeholder="gsk_..."
        )
        if groq_key_input:
            st.session_state.groq_api_key = groq_key_input
    
    st.divider()
    
    # Gemini API Key input
    gemini_key_input = st.text_input(
        "Gemini API Key (விருப்பம்)",
        type="password",
        placeholder="AIzaSy..."
    )
    if gemini_key_input:
        st.session_state.gemini_api_key = gemini_key_input
    
    st.divider()
    
    # File uploader
    uploaded_file = st.file_uploader(
        "உங்கள் ஜாதக டெக்ஸ்ட் (.txt) ஃபைலை அப்லோட் செய்யவும்",
        type=["txt"]
    )
    
    if uploaded_file is not None:
        try:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            horoscope_content = stringio.read()
            st.session_state.horoscope_data = horoscope_content
            st.session_state.file_uploaded = True
            st.success("✅ ஜாதக ஃபைல் சுமாரான வகையில் அப்லோட் ஆனது")
        except Exception as e:
            st.error(f"❌ ஃபைல் படிப்பு பிழை: {str(e)}")
            st.session_state.file_uploaded = False
    
    st.divider()
    
    # Session info
    st.subheader("📊 சத்ர தகவல்கள்")
    
    if st.session_state.groq_api_key:
        st.info("✅ Groq Key: வழங்கப்பட்டுவிட்டது", icon="⚡")
    else:
        st.warning("⚠️ Groq Key: வழங்க வேண்டியுள்ளது", icon="⚡")
    
    if st.session_state.gemini_api_key:
        st.info("✅ Gemini Key: வழங்கப்பட்டுவிட்டது", icon="🔐")
    else:
        st.caption("ℹ️ Gemini Key: விருப்பம் (Groq மாற்று)", icon="🔐")
    
    if st.session_state.horoscope_data:
        st.info(f"✅ ஜாதக ஃபைல்: அப்லோட்டாகியுள்ளது ({len(st.session_state.horoscope_data)} bytes)", icon="📄")
    else:
        st.warning("⚠️ ஜாதக ஃபைல்: வழங்க வேண்டியுள்ளது", icon="📄")
    
    if st.session_state.model_used:
        st.info(f"🤖 பயன்படுத்தப்பட்ட மாதிரி: {st.session_state.model_used}", icon="✨")
    
    st.divider()
    
    # Privacy notice
    st.caption(
        "🔒 **100% பிரைவசி**: பிரவுசர் டேபை க்ளோஸ் செய்தால் உங்கள் டேட்டா சர்வரில் இருந்து அழிந்துவிடும்."
    )

# ============================================================================
# MAIN AREA - TITLE & DISCLAIMER
# ============================================================================
st.title("🔮 பர்சனல் ஏஐ ஜோதிடர் (Vedic & KP)")
st.subheader("100% பிரைவசி: பிரவுசர் டேபை க்ளோஸ் செய்தால் உங்கள் டேட்டா சர்வரில் இருந்து அழிந்துவிடும்।")

st.divider()

# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================
# Display existing messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Check if both API key and horoscope data are available
has_api_key = st.session_state.groq_api_key or st.session_state.gemini_api_key
has_horoscope = st.session_state.horoscope_data

if not has_api_key or not has_horoscope:
    if not has_api_key:
        st.info(
            "🔓 **API Key தேவை**: தயவுசெய்து பக்க பட்டையில் Groq அல்லது Gemini API Key ஐ வழங்கவும்.",
            icon="ℹ️"
        )
    if not has_horoscope:
        st.info(
            "📄 **ஜாதக ஃபைல் தேவை**: தயவுசெய்து உங்கள் ஜாதக .txt ஃபைலை அப்லோட் செய்யவும்.",
            icon="ℹ️"
        )
else:
    st.success("✅ **நீங்கள் கேள்வி கேட்க தயாராக உள்ளீர்கள்!**", icon="🟢")

# ============================================================================
# CHAT INPUT & RESPONSE GENERATION
# ============================================================================
user_input = st.chat_input(
    "உங்கள் ஜோதிட கேள்வியை இங்கே கேட்கவும்... 🔮",
    disabled=not (has_api_key and has_horoscope)
)

if user_input:
    # Add user message to session state
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)
    
    # Generate AI response
    try:
        # Get current time with live timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare the context with horoscope data and transit time
        context = f"""
[ஜாதக விவரங்கள்]:
{st.session_state.horoscope_data}

[தற்போதைய கோச்சார (Transit) நேரம்]:
{current_time}

[ஜாதகரின் கேள்வி]:
{user_input}
"""
        
        full_prompt = f"{SYSTEM_PROMPT}\n\n{context}"
        
        assistant_response = None
        model_used = None
        
        # Try Groq first if key is available
        if st.session_state.groq_api_key:
            try:
                groq_client = Groq(api_key=st.session_state.groq_api_key)
                
                groq_models = [
                    "mixtral-8x7b-32768",
                    "llama-3.1-70b-versatile",
                    "llama-3.1-8b-instant"
                ]
                
                for groq_model in groq_models:
                    try:
                        chat_completion = groq_client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system",
                                    "content": SYSTEM_PROMPT
                                },
                                {
                                    "role": "user",
                                    "content": context
                                }
                            ],
                            model=groq_model,
                            max_tokens=2048,
                            temperature=0.7,
                        )
                        assistant_response = chat_completion.choices[0].message.content
                        model_used = f"Groq ({groq_model})"
                        st.session_state.model_used = model_used
                        break
                    except:
                        continue
                
                if assistant_response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(assistant_response)
                    
                    st.caption(f"🕐 **கோச்சார நேரம்**: {current_time} | 🤖 **{model_used}** | ⚡ விரைவு")
            except Exception as groq_error:
                groq_error_str = str(groq_error)
                if "API key" in groq_error_str or "authentication" in groq_error_str.lower():
                    st.warning("⚠️ Groq API Key பிழை - Gemini க்கு மாறுகிறது...")
                else:
                    st.warning(f"⚠️ Groq பிழை - Gemini க்கு மாறுகிறது...")
                assistant_response = None
        
        # Fallback to Gemini if Groq failed or not provided
        if not assistant_response and st.session_state.gemini_api_key:
            try:
                genai.configure(api_key=st.session_state.gemini_api_key)
                
                models_to_try = [
                    "gemini-1.5-flash",
                    "gemini-1.5-flash-latest",
                    "gemini-pro",
                    "gemini-1.0-pro"
                ]
                
                for model_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(model_name)
                        
                        response = model.generate_content(
                            full_prompt,
                            generation_config=genai.types.GenerationConfig(
                                max_output_tokens=2048,
                                temperature=0.7,
                            )
                        )
                        
                        assistant_response = response.text
                        model_used = f"Gemini ({model_name})"
                        st.session_state.model_used = model_used
                        break
                    except:
                        continue
                
                if assistant_response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(assistant_response)
                    
                    st.caption(f"🕐 **கோச்சார நேரம்**: {current_time} | 🤖 **{model_used}**")
            except Exception as gemini_error:
                pass
        
        # If still no response
        if not assistant_response:
            error_message = "❌ **பிழை**: எந்த API யும் பதிலளிக்கவில்லை. தயவுசெய்து: 1) API Keys சரியாக உள்ளதா சரிபார்க்கவும் 2) Groq: https://console.groq.com 3) Gemini: https://ai.google.dev"
            st.error(error_message)
            
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })
    
    except Exception as e:
        error_str = str(e)
        
        if "API key" in error_str or "authentication" in error_str.lower():
            error_message = "❌ **API Key பிழை**: உங்கள் API Key தவறாக உள்ளது. தயவுசெய்து சரியான Key ஐ வழங்கவும்."
        elif "quota" in error_str.lower() or "rate limit" in error_str.lower():
            error_message = "⏳ **Quota பிழை**: API வரம்பு அடிக்கப்பட்டுவிட்டது. சிறிது நேரம் பிறகு முயற்சி செய்யவும்."
        elif "429" in error_str:
            error_message = "⏳ **கோரிக்கை மிக அதிகம்**: சிறிது நேரம் பிறகு மீண்டும் முயற்சி செய்யவும்."
        else:
            error_message = f"❌ **பிழை**: {error_str[:150]}"
        
        st.error(error_message)
        
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_message
            })

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
---
**📌 குறிப்பு**: 
- இந்த பயன்பாடு 100% பிரவுசர்-அடிப்படையாக இயங்கும். சர்வரில் எந்த தரவும் சேமிக்கப்படாது.
- பிரவுசர் டேபை க்ளோஸ் செய்தால் அனைத்து உரையாடல்களும் சுத்தமாக அழிந்துவிடும்.

**API Keys பெறுதல்:**
- **Groq** (விரைவு & இலவசம்): https://console.groq.com
- **Gemini** (Google AI): https://ai.google.dev

**🔮 வாழ்க தமிழ் ஜோதிடம்!**
""")
