#!/usr/bin/env python3
"""
Sprout generator for creating shareable webpages from markdown
Generates HTML/CSS webpages from markdown content with Flow branding
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import markdown
from markdown.extensions import codehilite, tables, toc, fenced_code, attr_list
import click


class SproutGenerator:
    def __init__(self, sprout_dir: str = "data/sprouts"):
        self.sprout_dir = Path(sprout_dir)
        self.sprout_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure markdown with extensions for better rendering
        self.md = markdown.Markdown(extensions=[
            'codehilite',
            'tables', 
            'toc',
            'fenced_code',
            'attr_list',
            'def_list',
            'footnotes',
            'md_in_html'
        ])
    
    def generate_sprout(self, 
                       content: str,
                       title: Optional[str] = None,
                       description: Optional[str] = None,
                       style: str = "modern",
                       password: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a sprout webpage from markdown content
        
        Args:
            content: Markdown content to convert
            title: Optional page title (auto-generated if not provided)
            description: Optional page description
            style: CSS style theme ('modern', 'minimal', 'dark')
            password: Optional password protection
            
        Returns:
            Dictionary with sprout generation results
        """
        try:
            # Generate title if not provided
            if not title:
                title = self._generate_title_from_content(content)
            
            # Generate description if not provided
            if not description:
                description = self._generate_description_from_content(content)
            
            # Convert markdown to HTML
            html_content = self.md.convert(content)
            
            # Generate complete HTML page
            html_page = self._generate_html_page(
                title=title,
                description=description,
                content=html_content,
                style=style,
                password=password
            )
            
            # Save the sprout file
            filename = self._save_sprout(title, html_page)
            filepath = self.sprout_dir / filename
            
            return {
                'success': True,
                'filename': filename,
                'title': title,
                'description': description,
                'path': str(filepath),
                'url': f"file://{filepath.absolute()}",
                'size': filepath.stat().st_size if filepath.exists() else 0
            }
            
        except Exception as error:
            return {
                'success': False,
                'error': str(error),
                'filename': None,
                'title': title,
                'description': description
            }
    
    def _generate_title_from_content(self, content: str) -> str:
        """Extract or generate a title from markdown content"""
        # Look for first H1 header
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Look for first H2 header
        h2_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
        if h2_match:
            return h2_match.group(1).strip()
        
        # Use first non-empty line
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if lines:
            # Remove markdown formatting from first line
            first_line = re.sub(r'[#*`_\[\]()]', '', lines[0]).strip()
            if len(first_line) > 50:
                first_line = first_line[:47] + "..."
            return first_line or "Generated Content"
        
        return "Generated Content"
    
    def _generate_description_from_content(self, content: str) -> str:
        """Generate a description from markdown content"""
        # Remove headers and markdown formatting
        clean_content = re.sub(r'^#+\s+.+$', '', content, flags=re.MULTILINE)
        clean_content = re.sub(r'[*_`\[\]()]', '', clean_content)
        clean_content = re.sub(r'\n+', ' ', clean_content).strip()
        
        # Take first 150 characters
        if len(clean_content) > 150:
            description = clean_content[:147] + "..."
        else:
            description = clean_content or "Generated webpage content"
        
        return description
    
    def _generate_html_page(self, 
                          title: str,
                          description: str,
                          content: str,
                          style: str,
                          password: Optional[str] = None) -> str:
        """Generate complete HTML page with styles and footer"""
        
        css = self._get_css(style)
        footer_html = self._get_footer_html()
        password_html = self._get_password_html() if password else ""
        password_js = self._get_password_js(password) if password else ""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)}</title>
    <meta name="description" content="{self._escape_html(description)}">
    <meta name="generator" content="Flow CLI">
    <style>
        {css}
    </style>
</head>
<body>
    {password_html}
    <div class="container" id="content">
        <header>
            <h1 class="page-title">{self._escape_html(title)}</h1>
            <p class="page-description">{self._escape_html(description)}</p>
            <div class="meta">
                <span class="generated-date">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</span>
            </div>
        </header>
        <main class="content">
            {content}
        </main>
        {footer_html}
    </div>
    <script>
        {password_js}
    </script>
</body>
</html>"""

    def _get_css(self, style: str) -> str:
        """Get CSS styles for different themes"""
        styles = {
            'modern': '''
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 1rem;
                }
                
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
                    overflow: hidden;
                }
                
                header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                    text-align: center;
                }
                
                .page-title {
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .page-description {
                    font-size: 1.2rem;
                    opacity: 0.9;
                    font-weight: 300;
                    margin-bottom: 1rem;
                }
                
                .meta {
                    opacity: 0.8;
                    font-size: 0.9rem;
                }
                
                .content {
                    padding: 2rem;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    color: #2c3e50;
                    margin: 1.5rem 0 1rem 0;
                    font-weight: 600;
                }
                
                h1 { font-size: 2.2rem; }
                h2 { font-size: 1.8rem; }
                h3 { font-size: 1.5rem; }
                h4 { font-size: 1.3rem; }
                
                p {
                    margin-bottom: 1.2rem;
                    text-align: justify;
                }
                
                code {
                    background: #f8f9fa;
                    padding: 0.2rem 0.4rem;
                    border-radius: 4px;
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
                    font-size: 0.9em;
                    color: #e83e8c;
                }
                
                pre {
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 1rem;
                    overflow-x: auto;
                    margin: 1.5rem 0;
                }
                
                pre code {
                    background: none;
                    padding: 0;
                    color: #495057;
                }
                
                blockquote {
                    border-left: 4px solid #667eea;
                    margin: 1.5rem 0;
                    padding: 1rem 1.5rem;
                    background: #f8f9ff;
                    font-style: italic;
                    color: #495057;
                }
                
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1.5rem 0;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    overflow: hidden;
                }
                
                th, td {
                    padding: 0.75rem;
                    text-align: left;
                    border-bottom: 1px solid #dee2e6;
                }
                
                th {
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #495057;
                }
                
                tr:hover {
                    background: #f8f9fa;
                }
                
                a {
                    color: #667eea;
                    text-decoration: none;
                    border-bottom: 1px solid transparent;
                    transition: border-color 0.2s;
                }
                
                a:hover {
                    border-bottom-color: #667eea;
                }
                
                ul, ol {
                    margin: 1rem 0;
                    padding-left: 1.5rem;
                }
                
                li {
                    margin-bottom: 0.5rem;
                }
                
                .footer {
                    background: #f8f9fa;
                    padding: 2rem;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                }
                
                .footer-ascii {
                    font-family: monospace;
                    font-size: 0.7rem;
                    line-height: 1.2;
                    white-space: pre;
                    color: #6c757d;
                    margin: 1rem 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .footer-wave {
                    text-align: left;
                }
                
                .footer-palm {
                    text-align: right;
                }
                
                .footer-text {
                    color: #6c757d;
                    font-size: 0.9rem;
                }
                
                .footer-text a {
                    color: #667eea;
                    font-weight: 500;
                }
                
                @media (max-width: 768px) {
                    body { padding: 0.5rem; }
                    .container { border-radius: 8px; }
                    header { padding: 1.5rem; }
                    .page-title { font-size: 2rem; }
                    .content { padding: 1.5rem; }
                    .footer { padding: 1.5rem; }
                    .footer-ascii { 
                        flex-direction: column; 
                        gap: 1rem;
                        font-size: 0.6rem;
                    }
                }
            ''',
            
            'minimal': '''
                body {
                    font-family: Georgia, 'Times New Roman', serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 2rem;
                    background: #fefefe;
                }
                
                .page-title {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 0.5rem;
                    margin-bottom: 0.5rem;
                }
                
                .page-description {
                    color: #7f8c8d;
                    font-style: italic;
                    margin-bottom: 1rem;
                }
                
                .meta {
                    color: #95a5a6;
                    font-size: 0.9rem;
                    margin-bottom: 2rem;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    color: #2c3e50;
                    margin-top: 2rem;
                    margin-bottom: 1rem;
                }
                
                p { margin-bottom: 1rem; }
                
                code {
                    background: #f0f0f0;
                    padding: 0.2rem 0.4rem;
                    border-radius: 3px;
                    font-family: monospace;
                }
                
                pre {
                    background: #f8f8f8;
                    border-left: 4px solid #3498db;
                    padding: 1rem;
                    overflow-x: auto;
                    margin: 1.5rem 0;
                }
                
                blockquote {
                    border-left: 4px solid #bdc3c7;
                    margin: 1.5rem 0;
                    padding: 0 1.5rem;
                    color: #7f8c8d;
                    font-style: italic;
                }
                
                a {
                    color: #3498db;
                    text-decoration: none;
                }
                
                a:hover {
                    text-decoration: underline;
                }
                
                .footer {
                    margin-top: 3rem;
                    padding-top: 2rem;
                    border-top: 1px solid #bdc3c7;
                    text-align: center;
                }
                
                .footer-ascii {
                    font-family: monospace;
                    font-size: 0.7rem;
                    line-height: 1.2;
                    white-space: pre;
                    color: #95a5a6;
                    margin: 1rem 0;
                    display: flex;
                    justify-content: space-between;
                }
                
                .footer-text {
                    color: #7f8c8d;
                    font-size: 0.9rem;
                }
            ''',
            
            'dark': '''
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #e0e0e0;
                    background: #0d1117;
                    margin: 0;
                    padding: 2rem;
                }
                
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    background: #161b22;
                    border-radius: 8px;
                    border: 1px solid #30363d;
                    overflow: hidden;
                }
                
                header {
                    background: #21262d;
                    border-bottom: 1px solid #30363d;
                    padding: 2rem;
                    text-align: center;
                }
                
                .page-title {
                    color: #f0f6fc;
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                }
                
                .page-description {
                    color: #8b949e;
                    font-size: 1.2rem;
                    margin-bottom: 1rem;
                }
                
                .meta {
                    color: #6e7681;
                    font-size: 0.9rem;
                }
                
                .content {
                    padding: 2rem;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    color: #f0f6fc;
                    margin: 1.5rem 0 1rem 0;
                    border-bottom: 1px solid #30363d;
                    padding-bottom: 0.5rem;
                }
                
                p { margin-bottom: 1rem; }
                
                code {
                    background: #1c2128;
                    color: #f85149;
                    padding: 0.2rem 0.4rem;
                    border-radius: 4px;
                    font-family: 'SF Mono', Monaco, monospace;
                }
                
                pre {
                    background: #0d1117;
                    border: 1px solid #30363d;
                    border-radius: 6px;
                    padding: 1rem;
                    overflow-x: auto;
                    margin: 1.5rem 0;
                }
                
                pre code {
                    background: none;
                    color: #e6edf3;
                }
                
                blockquote {
                    border-left: 4px solid #fd7e14;
                    margin: 1.5rem 0;
                    padding: 0 1.5rem;
                    color: #8b949e;
                }
                
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1.5rem 0;
                    border: 1px solid #30363d;
                    border-radius: 6px;
                    overflow: hidden;
                }
                
                th, td {
                    padding: 0.75rem;
                    text-align: left;
                    border-bottom: 1px solid #30363d;
                }
                
                th {
                    background: #21262d;
                    color: #f0f6fc;
                    font-weight: 600;
                }
                
                a {
                    color: #58a6ff;
                    text-decoration: none;
                }
                
                a:hover {
                    text-decoration: underline;
                }
                
                .footer {
                    background: #0d1117;
                    border-top: 1px solid #30363d;
                    padding: 2rem;
                    text-align: center;
                }
                
                .footer-ascii {
                    font-family: monospace;
                    font-size: 0.7rem;
                    line-height: 1.2;
                    white-space: pre;
                    color: #6e7681;
                    margin: 1rem 0;
                    display: flex;
                    justify-content: space-between;
                }
                
                .footer-text {
                    color: #8b949e;
                    font-size: 0.9rem;
                }
                
                .footer-text a {
                    color: #58a6ff;
                }
            '''
        }
        
        return styles.get(style, styles['modern'])
    
    def _get_footer_html(self) -> str:
        """Generate footer with ASCII art"""
        return '''
        <footer class="footer">
            <div class="footer-ascii">
                <div class="footer-wave">
   ~~~~~
 ~~     ~~
~         ~
 ~~     ~~
   ~~~~~</div>
                <div class="footer-palm">
      ^^^
     ^^^^^
    ^^^^^^^
   ^^^^^^^^^
      |||
      |||
      |||</div>
            </div>
            <div class="footer-text">
                <p>Generated with ❤️ by <a href="https://github.com/your-username/flow" target="_blank">Flow CLI</a></p>
                <p>Personal activity tracking and analysis tool</p>
            </div>
        </footer>
        '''
    
    def _get_password_html(self) -> str:
        """Generate password protection overlay"""
        return '''
        <div class="password-container" id="passwordContainer">
            <div class="password-box">
                <h2>🔒 Password Required</h2>
                <p>This content is password protected.</p>
                <div class="password-input-group">
                    <input type="password" id="passwordInput" placeholder="Enter password">
                    <button onclick="checkPassword()">Access</button>
                </div>
                <div id="error" class="error" style="display: none;">Incorrect password</div>
            </div>
        </div>
        '''
    
    def _get_password_js(self, password: str) -> str:
        """Generate password protection JavaScript"""
        escaped_password = self._escape_html(password)
        return f'''
        function checkPassword() {{
            const input = document.getElementById('passwordInput');
            const error = document.getElementById('error');
            const container = document.getElementById('passwordContainer');
            
            if (input.value === '{escaped_password}') {{
                container.style.display = 'none';
                document.getElementById('content').style.display = 'block';
            }} else {{
                error.style.display = 'block';
                input.value = '';
                input.focus();
            }}
        }}
        
        document.getElementById('passwordInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                checkPassword();
            }}
        }});
        
        // Hide content by default if password protected
        document.getElementById('content').style.display = 'none';
        document.getElementById('passwordInput').focus();
        '''
    
    def _save_sprout(self, title: str, html_content: str) -> str:
        """Save sprout to file and return filename"""
        timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')[:-3] + 'Z'
        safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip()
        safe_title = re.sub(r'\s+', '-', safe_title).lower()
        safe_title = safe_title[:50]  # Limit length
        
        filename = f"{timestamp}_{safe_title}.html"
        filepath = self.sprout_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def list_sprouts(self) -> list:
        """List all generated sprouts"""
        sprouts = []
        for filepath in self.sprout_dir.glob("*.html"):
            stat = filepath.stat()
            # Extract title from filename
            title = filepath.stem
            if '_' in title:
                title = title.split('_', 1)[1].replace('-', ' ').title()
            
            sprouts.append({
                'filename': filepath.name,
                'title': title,
                'path': str(filepath),
                'size': stat.st_size,
                'created': stat.st_mtime,
                'url': f"file://{filepath.absolute()}"
            })
        
        return sorted(sprouts, key=lambda x: x['created'], reverse=True)


# CLI interface for testing
@click.command()
@click.option('-t', '--title', help='Page title')
@click.option('-d', '--description', help='Page description')
@click.option('-s', '--style', default='modern', 
              type=click.Choice(['modern', 'minimal', 'dark']),
              help='Style theme')
@click.option('-p', '--password', help='Password protection')
@click.option('-o', '--output-dir', default='data/sprouts', help='Output directory')
@click.argument('markdown_file', type=click.Path(exists=True))
def generate_sprout_cli(title, description, style, password, output_dir, markdown_file):
    """Generate a sprout webpage from a markdown file"""
    
    generator = SproutGenerator(output_dir)
    
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate sprout
    result = generator.generate_sprout(
        content=content,
        title=title,
        description=description,
        style=style,
        password=password
    )
    
    if result['success']:
        click.echo(f"✅ Sprout created successfully!")
        click.echo(f"📄 Title: {result['title']}")
        click.echo(f"📁 File: {result['filename']}")
        click.echo(f"🌐 URL: {result['url']}")
        click.echo(f"📊 Size: {result['size']} bytes")
    else:
        click.echo(f"❌ Error: {result['error']}")


if __name__ == "__main__":
    generate_sprout_cli()
