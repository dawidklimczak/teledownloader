import streamlit as st
import requests
import zipfile
import io
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
import unicodedata

def is_valid_url(url):
    """Sprawdza czy podany string jest poprawnym URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def sanitize_filename(title):
    """Upraszcza tekst do bezpiecznej nazwy pliku."""
    # Usuń polskie znaki
    title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('ASCII')
    # Zamień spacje i inne znaki specjalne na podkreślenia
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '_', title)
    # Przytnij długość
    return title[:50].lower().strip('_')

def get_page_title(html_content, url):
    """Wyciąga tytuł strony z HTML."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else None
        if title:
            return sanitize_filename(title)
    except:
        pass
    # Jeśli nie udało się pobrać tytułu, użyj domyślnej nazwy z URL
    parsed = urlparse(url)
    return f"{parsed.netloc}_{parsed.path.strip('/').replace('/', '_') or 'index'}"

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
            
            # Generuj nazwę pliku na podstawie tytułu strony
            filename = get_page_title(response.text, url) + '.html'
            results[filename] = response.text
            
            # Wyświetl informację o pobranej stronie
            st.info(f"Pobrano: {url} → {filename}")
            
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