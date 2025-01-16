import streamlit as st
import requests
import zipfile
import io
import tempfile
import os
from urllib.parse import urlparse

def is_valid_url(url):
    """Sprawdza czy podany string jest poprawnym URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_filename_from_url(url):
    """Generuje nazwę pliku na podstawie URL."""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        path = 'index'
    filename = path.replace('/', '_')
    return f"{parsed.netloc}_{filename}.html"

def download_pages(urls):
    """Pobiera strony i zwraca je jako dict {nazwa_pliku: zawartość}."""
    results = {}
    
    for url in urls:
        if not url.strip():
            continue
            
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        if not is_valid_url(url):
            st.error(f"Niepoprawny URL: {url}")
            continue
            
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            filename = get_filename_from_url(url)
            results[filename] = response.text
        except Exception as e:
            st.error(f"Błąd podczas pobierania {url}: {str(e)}")
            
    return results

def create_zip(pages):
    """Tworzy plik ZIP z pobranymi stronami."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in pages.items():
            zip_file.writestr(filename, content)
            
    return zip_buffer.getvalue()

# Konfiguracja strony
st.set_page_config(page_title="Pobieracz stron WWW", layout="wide")

# Interfejs użytkownika
st.title("Pobieracz stron WWW")
st.write("Wpisz adresy URL (każdy w osobnej linii):")

# Pole tekstowe na URLs
urls_text = st.text_area("", height=200)

# Przycisk do pobierania
if st.button("Pobierz strony"):
    if not urls_text.strip():
        st.error("Wprowadź co najmniej jeden URL")
    else:
        urls = urls_text.split('\n')
        
        with st.spinner("Pobieram strony..."):
            pages = download_pages(urls)
            
            if pages:
                zip_data = create_zip(pages)
                
                # Przygotowanie przycisku do pobrania
                st.download_button(
                    label="Pobierz ZIP",
                    data=zip_data,
                    file_name="strony.zip",
                    mime="application/zip"
                )
                st.success(f"Pobrano {len(pages)} stron!")
            else:
                st.error("Nie udało się pobrać żadnej strony.")