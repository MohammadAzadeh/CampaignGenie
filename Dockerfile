FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # let “import pages.*” resolve no matter where we start the app
    PYTHONPATH="/app"

WORKDIR /app

# ─── System-level libs required by pyarrow/LanceDB ────────────
#RUN apt-get update && apt-get install -y --no-install-recommends \
#        build-essential gcc git libgomp1 \
#    && rm -rf /var/lib/apt/lists/*

# ─── Python deps (layer-cached) ───────────────────────────────
COPY requirements.txt .
# RUN python -m pip install --upgrade pip setuptools wheel \
#    && pip install -r requirements.txt

RUN python -m pip install -r requirements.txt

#RUN python -m pip install --upgrade pip
#RUN python -m pip install streamlit
#RUN python -m pip install openai
#RUN python -m pip install TinyDB
#RUN python -m pip install agno
#RUN python -m pip install sqlalchemy
#RUN python -m pip install fastapi[standard]
#RUN python -m pip install lancedb
#RUN python -m pip install pydantic-ai==0.3.3


COPY . .

EXPOSE 8501

# ─── Entry-point ──────────────────────────────────────────────
# `-m app.ui` runs the file *as a module* so imports work
CMD ["streamlit", "run", "-m", "app.ui", \
     "--server.port=8501", "--server.address=0.0.0.0"]
