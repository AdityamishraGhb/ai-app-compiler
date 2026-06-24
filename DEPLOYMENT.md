# Deployment Guide

The AI Application Compiler backend is optimized for quick deployment on modern PaaS providers. 

## 🏆 Recommended Platform: Render

**Render** is highly recommended because it natively supports Python, detects `pyproject.toml` / `requirements.txt`, and we have included a ready-to-use `render.yaml` configuration file.

## 🚀 Exact Deployment Steps (Render)

1. **Push to GitHub**: Make sure your latest code (including `render.yaml`) is pushed to your GitHub repository.
2. **Connect to Render**:
   - Log into [Render](https://render.com/).
   - Click **New** -> **Blueprint**.
   - Connect your GitHub repository.
3. **Configure the Service**:
   - Render will automatically detect the `render.yaml` file.
   - It will prompt you to provide the `GEMINI_API_KEY` environment variable.
4. **Deploy**:
   - Click **Apply**.
   - Render will build the environment using `pip install -e .` and start the server using Uvicorn.

## 🔑 Required Environment Variables

You must configure the following environment variables in your deployment dashboard:

| Variable | Description | Example |
|---|---|---|
| `GEMINI_API_KEY` | **(Required)** Your Google Gemini API Key | `AIzaSy...` |
| `GEMINI_MODEL` | (Optional) Model name to use | `gemini-2.5-flash` |
| `PYTHON_VERSION` | (Optional) Python version | `3.10.11` |

## 🏥 Health Check & API Docs

Once deployed, your application will be available at a public URL (e.g., `https://ai-app-compiler-xxxxx.onrender.com`).

* **Health Check URL**: `https://<your-app-url>/health` (Used by the platform to verify the server is running)
* **API Documentation**: `https://<your-app-url>/docs` (Interactive Swagger UI)

## 🏗 Alternative Platform: Railway

If you prefer Railway, the repository includes a `Procfile` and `runtime.txt`.
1. Create a New Project on Railway from your GitHub repo.
2. Add the `GEMINI_API_KEY` in the Variables tab.
3. Railway's Nixpacks builder will automatically detect Python and start the app using the `Procfile`.
