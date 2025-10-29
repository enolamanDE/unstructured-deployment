# ============================================
# Basis: Offizielles Unstructured Image
# (Enthält bereits unstructured mit allen Dependencies)
# ============================================
FROM downloads.unstructured.io/unstructured-io/unstructured:latest

# Wechsle zu root für Installation
USER root

# Nur Streamlit und Visualisierungs-Dependencies installieren
RUN pip install --no-cache-dir \
    streamlit==1.28.0 \
    plotly==5.17.0 \
    pandas==2.1.1 \
    && rm -rf /root/.cache/pip

# Arbeitsverzeichnis für Anwendung
WORKDIR /app/prototype

# Anwendungs-Code kopieren
COPY app_open_source_recovered.py .
COPY pptx_helpers.py .

# Test-Dateien Verzeichnis erstellen und Berechtigungen setzen
RUN mkdir -p test_files logs && \
    chown -R notebook-user:notebook-user /app/prototype

# Zurück zum notebook-user (Standard-User im Base-Image)
USER notebook-user

# Port für Streamlit
EXPOSE 8501


# Umgebungsvariablen
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Anwendung starten
ENTRYPOINT ["streamlit", "run", "app_open_source_recovered.py", "--server.port=8501", "--server.address=0.0.0.0"]

