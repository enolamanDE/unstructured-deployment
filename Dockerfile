# ============================================
# Basis: Offizielles Unstructured Image
# (Enthält bereits unstructured mit allen Dependencies)
# ============================================
FROM downloads.unstructured.io/unstructured-io/unstructured:latest

# Arbeitsverzeichnis für Anwendung
WORKDIR /app/prototype

# Anwendungs-Code kopieren
COPY app_open_source_recovered.py .
COPY pptx_helpers.py .

# Test-Dateien Verzeichnis erstellen
RUN mkdir -p test_files logs

# Wechsle zu notebook-user
USER notebook-user

# Installiere Streamlit und Dependencies als notebook-user
RUN python3 -m pip install --user --no-cache-dir \
    streamlit==1.28.0 \
    plotly==5.17.0 \
    pandas==2.1.1

# Port für Streamlit
EXPOSE 8501


# Umgebungsvariablen
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Anwendung starten
ENTRYPOINT ["streamlit", "run", "app_open_source_recovered.py", "--server.port=8501", "--server.address=0.0.0.0"]

