# Flow Website Builder

Static file server for serving sharable webpages created from Flow search results and markdown content.

## Quick Start

```bash
python server.py --port 8084
```

Your pages will be available at:
- List all pages: `http://localhost:8084/`
- Specific page: `http://localhost:8084/page/[page-name]`

## Creating Pages

Use the Flow MCP tools in Claude Desktop:

```
"Create a webpage called 'team-update' with title 'Weekly Team Update' 
and this content: [your markdown here]"
```

## Directory Structure

```
website-builder/
├── server.py           # Static file server
├── pages/              # Generated HTML pages
├── static/
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript
│   └── assets/        # Images, videos, etc.
└── templates/         # HTML templates
```

## Sharing Pages

### Local Access
```bash
python server.py --port 8084
# Access at http://localhost:8084/page/your-page
```

### Public Sharing via Ngrok
```bash
# Terminal 1
python server.py --port 8084

# Terminal 2
ngrok http 8084
# Share the ngrok URL: https://abc123.ngrok.io/page/your-page
```

## Features

- **Markdown Support**: Full markdown rendering with code highlighting
- **Responsive Design**: Works on desktop and mobile
- **Dark/Light Theme**: Automatic theme detection
- **Easy Sharing**: Simple URLs for all pages
- **Static Assets**: Support for images, videos, and other media

## Page Management

List pages:
```
Use list-webpages tool in Claude Desktop
```

Delete a page:
```
Use delete-webpage tool with the page name
```

Get page URL:
```
Use get-webpage-url tool with the page name and optional ngrok URL
```


