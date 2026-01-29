# ScreenShot

A simple web service that captures screenshots of any webpage via API. Built with FastAPI and Playwright.

## Features

- REST API for capturing webpage screenshots
- Configurable viewport dimensions (default: 1280x720)
- Web interface for interactive testing
- Runs as a managed service on Sprite

## Installation

Run the install script on a [Sprite](https://sprites.dev/):

```bash
curl -fsSL https://raw.githubusercontent.com/symkat/ScreenShot/main/install.sh | bash
```

This will:
1. Clone the repository
2. Install Python dependencies
3. Install Playwright and Chromium
4. Register and start the screenshot service

The service will be available at `http://localhost:8080`.

## Authentication

When accessing your Sprite via its authenticated URL, you must include an authorization header with your Sprite token:

```bash
-H "Authorization: Bearer $SPRITE"
```

If your Sprite is configured with public access, no authentication header is required.

## API Reference

### Take Screenshot

Capture a screenshot of a webpage.

**Endpoint:** `POST /screenshot`

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | - | The webpage URL to capture |
| `width` | integer | No | 1280 | Viewport width (320-3840) |
| `height` | integer | No | 720 | Viewport height (200-2160) |

**Request:**

```http
POST /screenshot
Content-Type: application/json

{
  "url": "https://example.com",
  "width": 1280,
  "height": 720
}
```

**Example (public Sprite):**

```bash
curl -X POST http://localhost:8080/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "width": 1920, "height": 1080}'
```

**Example (authenticated Sprite):**

```bash
curl -X POST https://your-sprite.spriteos.dev/screenshot \
  -H "Authorization: Bearer $SPRITE" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "width": 1920, "height": 1080}'
```

**Response:**

```json
{
  "screenshot_url": "/screenshots/abc123.png"
}
```

### Get Screenshot

Retrieve a previously captured screenshot.

**Endpoint:** `GET /screenshots/{filename}`

**Example:**

```bash
curl http://localhost:8080/screenshots/abc123.png --output screenshot.png
```

**Response:** PNG image file

## Web Interface

Visit `http://localhost:8080` in your browser for an interactive form to capture screenshots.

---

Built on [Sprites](https://sprites.dev/) with Claude Code.
