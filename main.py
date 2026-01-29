import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from playwright.async_api import async_playwright

app = FastAPI(title="Screenshot Service")

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


class ScreenshotRequest(BaseModel):
    url: HttpUrl


class ScreenshotResponse(BaseModel):
    screenshot_url: str


@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Serve the homepage with API instructions and a screenshot form."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Screenshot Service</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: #f5f5f5;
            color: #333;
        }
        h1 { color: #2c3e50; }
        h2 { color: #34495e; margin-top: 2rem; }
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }
        code { font-family: 'Monaco', 'Consolas', monospace; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        input[type="url"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        input[type="url"]:focus {
            outline: none;
            border-color: #3498db;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
        }
        button:hover { background: #2980b9; }
        button:disabled { background: #bdc3c7; cursor: not-allowed; }
        #result {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 4px;
            display: none;
        }
        #result.success { background: #d4edda; color: #155724; display: block; }
        #result.error { background: #f8d7da; color: #721c24; display: block; }
        #result a { color: inherit; font-weight: 600; }
    </style>
</head>
<body>
    <h1>Screenshot Service</h1>

    <div class="card">
        <h2>Try It Out</h2>
        <form id="screenshot-form">
            <div class="form-group">
                <label for="url">Enter a URL to capture:</label>
                <input type="url" id="url" name="url" placeholder="https://example.com" required>
            </div>
            <button type="submit" id="submit-btn">Take Screenshot</button>
        </form>
        <div id="result"></div>
    </div>

    <div class="card">
        <h2>API Usage</h2>
        <p>Send a POST request to <code>/screenshot</code> with a JSON body containing the URL:</p>
        <pre><code>curl -X POST http://localhost:8080/screenshot \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com"}'</code></pre>

        <h3>Request</h3>
        <pre><code>POST /screenshot
Content-Type: application/json

{
  "url": "https://example.com"
}</code></pre>

        <h3>Response</h3>
        <pre><code>{
  "screenshot_url": "/screenshots/abc123.png"
}</code></pre>

        <p>The returned <code>screenshot_url</code> can be accessed directly to view or download the image.</p>
    </div>

    <div class="card">
        <h2>Authentication</h2>
        <p>If your Sprite is configured with <strong>authenticated access</strong>, include your Sprite token in the request header:</p>
        <pre><code>curl -X POST https://your-sprite.spriteos.dev/screenshot \\
  -H "Authorization: Bearer $SPRITE" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com"}'</code></pre>
        <p>If your Sprite is <strong>public</strong>, no authorization header is needed.</p>
    </div>

    <script>
        const form = document.getElementById('screenshot-form');
        const urlInput = document.getElementById('url');
        const submitBtn = document.getElementById('submit-btn');
        const result = document.getElementById('result');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            submitBtn.disabled = true;
            submitBtn.textContent = 'Capturing...';
            result.className = '';
            result.style.display = 'none';

            try {
                const response = await fetch('/screenshot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: urlInput.value })
                });

                const data = await response.json();

                if (response.ok) {
                    const fullUrl = window.location.origin + data.screenshot_url;
                    result.innerHTML = `Screenshot captured! <a href="${data.screenshot_url}" target="_blank">${fullUrl}</a>`;
                    result.className = 'success';
                    result.style.display = 'block';
                } else {
                    result.textContent = 'Error: ' + (data.detail || 'Failed to capture screenshot');
                    result.className = 'error';
                    result.style.display = 'block';
                }
            } catch (err) {
                result.textContent = 'Error: ' + err.message;
                result.className = 'error';
                result.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Take Screenshot';
            }
        });
    </script>
</body>
</html>"""


@app.post("/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(request: ScreenshotRequest):
    """Take a screenshot of the given URL and return a link to the image."""
    filename = f"{uuid.uuid4()}.png"
    filepath = SCREENSHOTS_DIR / filename

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.goto(str(request.url), timeout=30000)
            await page.screenshot(path=str(filepath))
            await browser.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to capture screenshot: {e}")

    return ScreenshotResponse(screenshot_url=f"/screenshots/{filename}")


@app.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    """Serve a saved screenshot."""
    filepath = SCREENSHOTS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(filepath, media_type="image/png")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
