import streamlit as st
from openai import OpenAI

BASE_URL = "https://integrate.api.nvidia.com/v1"

# Başlangıç model listesi. "Modelleri listele" butonu güncel listeyi NVIDIA'dan çeker.
DEFAULT_MODELS = [
    "qwen/qwen3-coder-480b-a35b-instruct",
    "deepseek-ai/deepseek-v4-flash",
    "deepseek-ai/deepseek-v4-pro",
    "nvidia/nemotron-3-super-120b-a12b",
]

# Sohbet/kod için uygun olmayan modelleri listeden ayıklamak için
EXCLUDE = ("embed", "rerank", "retriev", "guard", "safety", "reward", "parse", "ocr",
           "clip", "vila", "cosmos", "riva", "tts", "asr", "stable-diffusion", "flux",
           "sdxl", "paligemma", "neva", "fuyu", "kosmos", "deplot", "nvclip", "bge",
           "arctic-embed", "nv-embed", "synthetic", "topic-control", "content-safety")

DEFAULT_SYSTEM = (
    "Sen deneyimli bir yazılım geliştiricisin. Kullanıcının isteğine göre temiz, çalışan ve "
    "iyi yorumlanmış kod yaz. Kodu her zaman uygun dil etiketiyle bir kod bloğu içinde ver. "
    "Kısa ve net açıklama ekle. Kullanıcı Türkçe yazıyorsa Türkçe yanıt ver."
)

st.set_page_config(page_title="Kod Asistanı (NVIDIA)", page_icon="💻", layout="wide")

# ---------- İsteğe bağlı şifre koruması ----------
# Streamlit Cloud > Settings > Secrets içine APP_PASSWORD = "sifreniz" yazarsanız
# uygulama şifre sormadan açılmaz.
app_password = st.secrets.get("APP_PASSWORD", "") if hasattr(st, "secrets") else ""
if app_password:
    if not st.session_state.get("auth_ok"):
        st.title("🔒 Giriş")
        pw = st.text_input("Uygulama şifresi", type="password")
        if st.button("Giriş yap"):
            if pw == app_password:
                st.session_state.auth_ok = True
                st.rerun()
            else:
                st.error("Şifre yanlış.")
        st.stop()

# ---------- Oturum durumu ----------
st.session_state.setdefault("messages", [])
st.session_state.setdefault("models", DEFAULT_MODELS)

# ---------- Kenar çubuğu ----------
with st.sidebar:
    st.header("⚙️ Ayarlar")

    # Anahtar yalnızca bu oturumda bellekte tutulur, hiçbir yere kaydedilmez.
    secret_key = st.secrets.get("NVIDIA_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input(
        "NVIDIA API Anahtarı",
        type="password",
        value=secret_key,
        placeholder="nvapi-...",
        help="build.nvidia.com/settings/api-keys adresinden alabilirsiniz.",
    )

    if st.button("🔄 Modelleri listele", disabled=not api_key):
        try:
            client = OpenAI(base_url=BASE_URL, api_key=api_key)
            all_ids = sorted(m.id for m in client.models.list().data)
            ids = [i for i in all_ids if not any(x in i.lower() for x in EXCLUDE)]
            ids = [m for m in DEFAULT_MODELS if m in ids] + [i for i in ids if i not in DEFAULT_MODELS]
            if ids:
                st.session_state.models = ids
                st.success(f"{len(ids)} sohbet modeli bulundu (toplam {len(all_ids)} kayıt).")
            missing = [m for m in DEFAULT_MODELS if m not in all_ids]
            if missing:
                st.warning("Önerilen şu modeller listede yok: " + ", ".join(missing))
        except Exception as e:
            st.error(f"Liste alınamadı: {e}")

    model = st.selectbox("Model", st.session_state.models, index=0)
    custom_model = st.text_input("veya model adını elle yazın", placeholder="örn: org/model-adi")
    if custom_model.strip():
        model = custom_model.strip()

    temperature = st.slider("Sıcaklık (yaratıcılık)", 0.0, 1.5, 0.3, 0.1)
    max_tokens = st.slider("Maksimum çıktı uzunluğu", 256, 16384, 4096, 256)
    system_prompt = st.text_area("Sistem talimatı", DEFAULT_SYSTEM, height=160)

    if st.button("🗑️ Sohbeti temizle"):
        st.session_state.messages = []
        st.rerun()

# ---------- Ana ekran ----------
st.title("💻 Kod Asistanı")
st.caption(f"Model: `{model}`")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Ne yazmamı istersiniz? (örn: Python ile CSV'yi Excel'e çeviren bir betik)")

if prompt:
    if not api_key:
        st.warning("Önce sol taraftan NVIDIA API anahtarınızı girin.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        try:
            client = OpenAI(base_url=BASE_URL, api_key=api_key)
            msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages
            stream = client.chat.completions.create(
                model=model,
                messages=msgs,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full += delta.content
                    placeholder.markdown(full + "▌")
            placeholder.markdown(full)
        except Exception as e:
            msg = str(e)
            if "429" in msg:
                st.error("Hız sınırına takıldınız (429). Biraz bekleyip tekrar deneyin ya da başka bir model seçin.")
            elif "401" in msg or "403" in msg:
                st.error("API anahtarı geçersiz veya yetkisiz. Anahtarı kontrol edin.")
            elif "404" in msg:
                st.error(f"404: `{model}` bu hesapta sohbet için kullanılamıyor (eskimiş, kapalı ya da sohbet modeli değil). "
                         "Listeden başka bir model deneyin.")
            else:
                st.error("Hata oluştu.")
            st.code(msg)  # NVIDIA'nın döndürdüğü asıl hata metni
            # Başarısız isteği geçmişten çıkar (üst üste 'selam' birikmesin)
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()

        if full:
            st.session_state.messages.append({"role": "assistant", "content": full})

# ---------- Son yanıtı indir ----------
last = next((m for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None)
if last:
    st.download_button("⬇️ Son yanıtı .md olarak indir", last["content"], file_name="yanit.md")
