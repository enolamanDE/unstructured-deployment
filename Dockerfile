# ============================================
# Stage 1: Basis - Offizielles Unstructured Image
# ============================================
FROM downloads.unstructured.io/unstructured-io/unstructured:latest AS unstructured-base

# ============================================
# Stage 2: Anwendung - Streamlit Prototype
# ============================================
FROM unstructured-base AS app

USER root

# Streamlit und zusätzliche Dependencies installieren
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

# Erstelle optimise User und Gruppe (Alpine Linux kompatibel)
RUN addgroup -g 1000 optimise && \
    adduser -D -u 1000 -G optimise optimise && \
    mkdir -p test_files && \
    chown -R optimise:optimise /app/prototype

# Als optimise User ausführen
USER optimise

# Port für Streamlit
EXPOSE 8501

# Health Check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Umgebungsvariablen
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Anwendung starten
ENTRYPOINT ["streamlit", "run", "app_open_source_recovered.py", "--server.port=8501", "--server.address=0.0.0.0"]

