import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, HttpUrl, Field
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

SCREENSHOT_MAX_AGE_MINUTES = 30


async def cleanup_old_screenshots():
    """Background task that deletes screenshots older than SCREENSHOT_MAX_AGE_MINUTES."""
    while True:
        await asyncio.sleep(60)  # Check every minute
        cutoff = datetime.now() - timedelta(minutes=SCREENSHOT_MAX_AGE_MINUTES)
        for file in SCREENSHOTS_DIR.glob("*.png"):
            try:
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    file.unlink()
            except OSError:
                pass  # File may have been deleted already


@asynccontextmanager
async def lifespan(app):
    """Start background cleanup task on startup."""
    task = asyncio.create_task(cleanup_old_screenshots())
    yield
    task.cancel()


app = FastAPI(title="Screenshot Service", lifespan=lifespan)


class ScreenshotRequest(BaseModel):
    url: HttpUrl  # HttpUrl validates scheme is http or https
    width: int = Field(default=1280, ge=320, le=3840)
    height: int = Field(default=720, ge=200, le=2160)


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
        input[type="url"]:focus, input[type="number"]:focus {
            outline: none;
            border-color: #3498db;
        }
        input[type="number"] {
            width: 100px;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        .inline-group {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        .inline-group .form-group {
            margin-bottom: 0;
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
            <div class="form-group">
                <label>Viewport size:</label>
                <div class="inline-group">
                    <div class="form-group">
                        <input type="number" id="width" name="width" value="1280" min="320" max="3840">
                    </div>
                    <span>x</span>
                    <div class="form-group">
                        <input type="number" id="height" name="height" value="720" min="200" max="2160">
                    </div>
                </div>
            </div>
            <button type="submit" id="submit-btn">Take Screenshot</button>
        </form>
        <div id="result"></div>
    </div>

    <div class="card">
        <h2>API Usage</h2>
        <p>Send a POST request to <code>/screenshot</code> with a JSON body containing the URL and optional viewport dimensions:</p>
        <pre><code>curl -X POST http://localhost:8080/screenshot \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "width": 1280, "height": 720}'</code></pre>

        <h3>Request</h3>
        <pre><code>POST /screenshot
Content-Type: application/json

{
  "url": "https://example.com",
  "width": 1280,
  "height": 720
}</code></pre>

        <h3>Parameters</h3>
        <ul>
            <li><code>url</code> (required) - The webpage URL to capture</li>
            <li><code>width</code> (optional) - Viewport width in pixels (320-3840, default: 1280)</li>
            <li><code>height</code> (optional) - Viewport height in pixels (200-2160, default: 720)</li>
        </ul>

        <h3>Response</h3>
        <pre><code>{
  "screenshot_url": "/screenshots/abc123.png"
}</code></pre>

        <p>The returned <code>screenshot_url</code> can be accessed directly to view or download the image.</p>
        <p><strong>Note:</strong> Screenshots are automatically deleted after 30 minutes.</p>
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
        const widthInput = document.getElementById('width');
        const heightInput = document.getElementById('height');
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
                    body: JSON.stringify({
                        url: urlInput.value,
                        width: parseInt(widthInput.value),
                        height: parseInt(heightInput.value)
                    })
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
            page = await browser.new_page(viewport={"width": request.width, "height": request.height})
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
