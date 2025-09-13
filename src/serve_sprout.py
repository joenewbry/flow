#!/usr/bin/env python3
"""
Standalone oasis server for serving Flow-generated webpages
Can be used with ngrok for public access
"""

import http.server
import socketserver
import subprocess
import threading
import time
import json
import sys
import webbrowser
from pathlib import Path
from typing import Optional

import click


class SproutHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for serving oasis files with proper MIME types"""
    
    def __init__(self, *args, oasis_dir="data/oasis", **kwargs):
        self.oasis_dir = oasis_dir
        super().__init__(*args, directory=oasis_dir, **kwargs)
    
    def log_message(self, format, *args):
        """Override to provide custom logging"""
        timestamp = self.log_date_time_string()
        click.echo(f"📊 {timestamp} - {format % args}")
    
    def end_headers(self):
        """Add custom headers for better sprout serving"""
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


class SproutServer:
    def __init__(self, port: int = 8080, oasis_dir: str = "data/oasis"):
        self.port = port
        self.oasis_dir = Path(oasis_dir)
        self.server = None
        self.server_thread = None
        self.ngrok_process = None
        self.public_url = None
    
    def start_server(self):
        """Start the HTTP server"""
        if not self.oasis_dir.exists():
            raise FileNotFoundError(f"Oasis directory not found: {self.oasis_dir}")
        
        # Create server with custom handler
        def create_handler(*args, **kwargs):
            return SproutHandler(*args, oasis_dir=str(self.oasis_dir), **kwargs)
        
        self.server = socketserver.TCPServer(("", self.port), create_handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(1)
        return f"http://localhost:{self.port}"
    
    def start_ngrok(self) -> Optional[str]:
        """Start ngrok tunnel and return public URL"""
        try:
            # Start ngrok tunnel
            self.ngrok_process = subprocess.Popen([
                'ngrok', 'http', str(self.port), '--log=stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for ngrok to start
            time.sleep(3)
            
            # Get ngrok URL from API
            result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                tunnels_data = json.loads(result.stdout)
                if tunnels_data.get('tunnels'):
                    self.public_url = tunnels_data['tunnels'][0]['public_url']
                    
                    # Save URL to file for later reference
                    with open('sprouts_public_url.txt', 'w') as f:
                        f.write(self.public_url)
                    
                    return self.public_url
            
            return None
            
        except Exception as e:
            click.echo(f"⚠️  Error starting ngrok: {e}")
            return None
    
    def list_oasis(self) -> list:
        """List all oasis files in the directory"""
        oasis = []
        for filepath in self.oasis_dir.glob("*.html"):
            stat = filepath.stat()
            # Extract title from filename
            title = filepath.stem
            if '_' in title:
                title = title.split('_', 1)[1].replace('-', ' ').title()
            
            oasis.append({
                'filename': filepath.name,
                'title': title,
                'path': str(filepath),
                'size': stat.st_size,
                'created': stat.st_mtime
            })
        
        return sorted(oasis, key=lambda x: x['created'], reverse=True)
    
    def stop(self):
        """Stop the server and ngrok"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.ngrok_process:
            self.ngrok_process.terminate()
        
        # Clean up URL files
        for file in ['sprouts_public_url.txt']:
            try:
                Path(file).unlink()
            except FileNotFoundError:
                pass


@click.command()
@click.option('-p', '--port', default=8080, help='Port number for oasis server')
@click.option('--public', is_flag=True, help='Make server publicly accessible via ngrok')
@click.option('--open-browser', is_flag=True, help='Open browser after starting server')
@click.option('-q', '--quiet', is_flag=True, help='Suppress server logs')
def serve_oasis(port, public, open_browser, quiet):
    """Start HTTP server to serve Flow oasis webpages."""
    
    try:
        server = SproutServer(port=port)
        
        click.echo(f"🌱 Starting oasis server on port {port}...")
        click.echo(f"📁 Serving directory: {server.oasis_dir.absolute()}")
        
        # Start HTTP server
        local_url = server.start_server()
        click.echo(f"✅ Server started!")
        
        # Start ngrok if requested
        public_url = None
        if public:
            click.echo("🌐 Starting ngrok tunnel...")
            public_url = server.start_ngrok()
            if public_url:
                click.echo(f"🌍 Public URL: {public_url}")
            else:
                click.echo("⚠️  Could not start ngrok tunnel")
        
        click.echo(f"🏠 Local URL: {local_url}")
        
        # List available oasis
        oasis = server.list_oasis()
        click.echo(f"\n📊 Available oasis ({len(oasis)}):")
        
        if oasis:
            base_url = public_url or local_url
            for i, sprout in enumerate(oasis[:10]):  # Show first 10
                sprout_url = f"{base_url}/{sprout['filename']}"
                size_kb = f"{sprout['size'] // 1024}KB" if sprout['size'] > 1024 else f"{sprout['size']}B"
                click.echo(f"  {i+1}. {sprout['title']} ({size_kb})")
                click.echo(f"     {sprout_url}")
            
            if len(oasis) > 10:
                click.echo(f"     ... and {len(oasis) - 10} more")
        else:
            click.echo("  No oasis found")
            click.echo("  💡 Create oasis with: python oasis_generator.py markdown_file.md")
        
        # Open browser if requested
        if open_browser:
            webbrowser.open(public_url or local_url)
            click.echo("🌐 Opened browser")
        
        click.echo("\n💡 Server controls:")
        click.echo("   • Press Ctrl+C to stop the server")
        click.echo("   • Visit the URLs above to view your oasis")
        if public_url:
            click.echo("   • Share the public URL with others")
        
        if not quiet:
            click.echo("\n📝 Access logs:")
        
        try:
            # Keep main thread alive and show logs
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping oasis server...")
            server.stop()
            click.echo("✅ Server stopped")
            
    except FileNotFoundError as e:
        click.echo(f"❌ {e}")
        click.echo("💡 Create oasis with: python oasis_generator.py your_file.md")
        sys.exit(1)
    except Exception as error:
        click.echo(f"❌ Error starting oasis server: {error}")
        sys.exit(1)


@click.command()
def list_ngrok_tunnels():
    """List active ngrok tunnels"""
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            tunnels_data = json.loads(result.stdout)
            tunnels = tunnels_data.get('tunnels', [])
            
            if tunnels:
                click.echo("🌐 Active ngrok tunnels:")
                for tunnel in tunnels:
                    click.echo(f"  • {tunnel['public_url']} → {tunnel['config']['addr']}")
            else:
                click.echo("No active ngrok tunnels")
        else:
            click.echo("❌ Could not connect to ngrok (is it running?)")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@click.group()
def cli():
    """Flow Sprout Server - Serve your markdown-generated webpages"""
    pass


cli.add_command(serve_oasis, name='serve')
cli.add_command(list_ngrok_tunnels, name='tunnels')


if __name__ == "__main__":
    cli()
