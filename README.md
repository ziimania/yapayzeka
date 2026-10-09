# Kod Asistanı (NVIDIA API + Streamlit)

Sol menüden NVIDIA API anahtarınızı girip istediğiniz modelle kod yazdırın.

## Yayına alma (Streamlit Community Cloud)
1. Bu klasörün içeriğini yeni bir GitHub deposuna yükleyin (app.py, requirements.txt, .gitignore).
2. share.streamlit.io adresine GitHub ile girin > Create app > depoyu seçin > Main file: `app.py` > Deploy.
3. (Önerilir) Uygulama > Settings > Secrets bölümüne şunu ekleyin:
       APP_PASSWORD = "kendi-sifreniz"
   Böylece uygulamayı yalnızca siz açabilirsiniz.

## Anahtar nerede tutulur?
- Varsayılan: Anahtarı her açılışta sol menüye yapıştırırsınız. Hiçbir yere kaydedilmez.
- Kolaylık için Secrets'a `NVIDIA_API_KEY = "nvapi-..."` da yazabilirsiniz.
  DİKKAT: Bunu yaparsanız mutlaka APP_PASSWORD de koyun. Yoksa linki bilen herkes sizin anahtarınızı kullanır.
- Anahtarı asla GitHub'a (kod dosyalarına) yazmayın.

## Yerelde çalıştırma
    pip install -r requirements.txt
    streamlit run app.py
