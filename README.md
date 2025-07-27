# CampaignGenie

> Your all‑in‑one agent‑powered toolkit for generating and managing multi‑channel marketing campaigns with the ease of a
> chat.

---

## ✨ Features

* **Streamlit UI** – instant, shareable interface for creating and analysing campaigns.
* **Agent‑UI (optional)** – React front‑end for an autonomous GPT‑based agent.
* **Embeddings DB** – LanceDB + PyArrow for lightning‑fast vector search.
* **Docker‑first** – reproducible builds for dev, CI and production.

---

## 📦 Requirements

| Tool              | Version | Notes                          |
|-------------------|---------|--------------------------------|
| Python            | 3.11.x  | Only needed for non‑Docker use |
| Docker Engine     | ≥ 24    | Works on Linux/macOS/Windows   |
| Docker Compose v2 | ≥ 2.21  | Included with Docker Desktop   |

---

## 🚀 Quick Start

### 1. Run with Docker (recommended)

```bash
# 1) clone & enter the repo
 git clone https://github.com/<you>/campaigngenie.git
 cd campaigngenie

# 2) add your secrets
 cp .env.example .env                # then edit .env

# 3) build & launch Streamlit
 docker compose up --build

# 4) open the app
 open http://localhost:8501           # macOS
 # or simply paste the URL in your browser
```

The first build installs all Python wheels and can take a minute;<br>subsequent launches are instantaneous thanks to
Docker layer caching.

#### What’s running?

| Container       | Port | Purpose                 |
|-----------------|------|-------------------------|
| `campaigngenie` | 8501 | Streamlit UI (`app.ui`) |
| `mongodb`       | 27017| MongoDB Database        |

---

### 2. Run on bare metal (no Docker)

```bash
# create virtualenv
python3 -m venv .venv && source .venv/bin/activate

# install deps
pip install -r requirements.txt

# export your Metis key
export METIS_API_KEY="sk‑..."

# launch Streamlit
python -m streamlit run -m app.ui
```

#### 2.1 To enable crawling Crawl4AI
```bash
pip install crawl4ai
sudo apt-get install libavif16
playwright install
```

---

## 🛠 Development Workflow with Docker

```bash
# rebuild after changing requirements.txt or Dockerfile
docker compose build

# start containers in the background
docker compose up -d

# view logs (follow)
docker compose logs -f

# hot‑reload Streamlit after code edits is automatic 🎉
```

### Live‑mount your source code

`docker-compose.yml` mounts the project directory into `/app` inside the container. Any file save locally triggers
Streamlit’s autoreload.

### Interactive debugging / REPL

```bash
# open a shell in the running container
docker compose exec campaigngenie bash
python -m ipdb -m app.ui   # example
```
