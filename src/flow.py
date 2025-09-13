#!/usr/bin/env python3
"""
Flow CLI - Personal Activity Tracking and Analysis Tool

A comprehensive CLI tool for screen tracking, AI analysis, and intelligent querying
of personal activity data using ChromaDB and local LLM integration.
"""

import asyncio
import logging
import os
import sys
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from lib.chroma_client import chroma_client
from lib.screen_detection import screen_detector
from ocr_processor import ocr_processor
from summary_service import SummaryService
from sprout_generator import SproutGenerator

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlowCLI:
    def __init__(self):
        self.summary_service = SummaryService()
        self.sprout_generator = SproutGenerator()
        self.verbose = False
        
    def setup_logging(self, verbose: bool):
        """Set up logging configuration."""
        self.verbose = verbose
        level = logging.DEBUG if verbose else logging.INFO
        logging.getLogger().setLevel(level)
        
        if verbose:
            logger.info("Verbose logging enabled")


# Global CLI instance
flow_cli = FlowCLI()


@click.group()
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--config', type=click.Path(), default='.flowrc', help='Path to configuration file')
@click.pass_context
def cli(ctx, verbose, config):
    """Flow CLI - Personal activity tracking and analysis tool."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    
    flow_cli.setup_logging(verbose)


@cli.command()
@click.argument('query', required=False)
@click.option('-c', '--context', help='Additional context for the conversation')
@click.pass_context
def ask(ctx, query, context):
    """Search and query your activity data."""
    if query:
        # Perform a search using the find command
        click.echo(f"🔍 Searching for: \"{query}\"")
        if context:
            click.echo(f"📝 Context: {context}")
        
        # Use the existing find functionality
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(find, [query])
        click.echo(result.output)
    else:
        click.echo("🤖 Flow Query Interface")
        click.echo("💡 Search your activity data using natural language")
        click.echo("")
        click.echo("Available commands:")
        click.echo("  flow find 'your search query'")
        click.echo("  flow summarize today")
        click.echo("  flow sprout --content 'your content'")
        click.echo("")
        click.echo("For AI-powered analysis, use Claude Desktop with MCP integration")


@cli.command()
@click.argument('query')
@click.option('-l', '--limit', default=10, help='Limit number of results')
@click.option('-t', '--type', 'search_type', default='all', 
              type=click.Choice(['screenshots', 'data/summaries', 'all']),
              help='Search type: screenshots, summaries, or all')
@click.option('-c', '--context', help='Additional context for search')
@click.option('--json', 'output_json', is_flag=True, help='Output results in JSON format')
@click.pass_context
def find(ctx, query, limit, search_type, context, output_json):
    """Search through your activity data using vector search."""
    async def _find():
        try:
            click.echo(f"🔍 Searching for: \"{query}\"")
            click.echo(f"📊 Limit: {limit}, Type: {search_type}")
            
            if context:
                click.echo(f"📝 Context: {context}")
            
            # Initialize ChromaDB client
            await chroma_client.init()
            
            # Perform search
            collection_name = "screen_history" if search_type == "all" else search_type
            results = await chroma_client.search(
                query=query,
                collection_name=collection_name,
                limit=limit
            )
            
            if output_json:
                import json
                click.echo(json.dumps([r.__dict__ for r in results], indent=2))
            else:
                formatted_results = chroma_client.format_search_results(results)
                click.echo(formatted_results)
                
        except Exception as error:
            click.echo(f"❌ Error: {error}")
            sys.exit(1)
    
    asyncio.run(_find())


@cli.command()
@click.argument('timeframe', required=False, default='today')
@click.option('-s', '--start', help='Start date (YYYY-MM-DD)')
@click.option('-e', '--end', help='End date (YYYY-MM-DD)')
@click.option('-g', '--granularity', type=click.Choice(['hourly', 'daily', 'monthly', 'yearly']),
              help='Summary granularity')
@click.option('--force', is_flag=True, help='Force regeneration of existing summaries')
@click.option('--catch-up', is_flag=True, help='Generate missing summaries (catch-up mode)')
@click.option('--list', 'list_summaries', is_flag=True, help='List existing summaries')
@click.option('--stats', is_flag=True, help='Show summary statistics')
@click.pass_context
def summarize(ctx, timeframe, start, end, granularity, force, catch_up, list_summaries, stats):
    """Generate summaries of your activity data."""
    async def _summarize():
        try:
            await flow_cli.summary_service.init()
            
            # Handle catch-up mode
            if catch_up:
                click.echo("📊 Running summary catch-up...")
                click.echo("💭 Generating missing hourly and daily summaries...")
                stats = await flow_cli.summary_service.ensure_summaries_up_to_date()
                
                click.echo("\n✅ Catch-up completed!")
                click.echo(f"📈 Generated {stats['hourly_generated']} hourly summaries")
                click.echo(f"📅 Generated {stats['daily_generated']} daily summaries")
                if stats['errors'] > 0:
                    click.echo(f"⚠️  {stats['errors']} errors occurred")
                click.echo(f"🕐 Last check: {stats['last_check']}")
                return
            
            if list_summaries:
                click.echo("📋 Existing Summaries:")
                click.echo("─" * 50)
                # TODO: Implement list functionality
                click.echo("Summary listing not yet implemented")
                return
            
            if stats:
                click.echo("📊 Summary Statistics:")
                click.echo("─" * 30)
                # TODO: Implement stats functionality
                click.echo("Summary statistics not yet implemented")
                return
            
            click.echo("📊 Generating activity summary...")
            click.echo(f"⏰ Timeframe: {timeframe}")
            
            if start and end:
                click.echo(f"📅 Custom range: {start} to {end}")
                # TODO: Implement custom range
                click.echo("Custom range summarization not yet implemented")
            elif timeframe == 'today':
                result = await flow_cli.summary_service.get_daily_summary()
                
                click.echo("\n✅ Summary generated successfully!")
                click.echo(f"📄 Date: {result.get('date', 'today')}")
                click.echo(f"💾 Cached: {'Yes' if result.get('cached', False) else 'No'}")
                click.echo(f"📊 Entries: {result.get('entry_count', 0)}")
                click.echo("\n📝 Summary:")
                click.echo("─" * 60)
                click.echo(result.get('summary', 'No summary available'))
                click.echo("─" * 60)
            else:
                click.echo(f"Timeframe '{timeframe}' not yet implemented")
                
        except Exception as error:
            click.echo(f"❌ Error: {error}")
            sys.exit(1)
    
    asyncio.run(_summarize())


@cli.command()
@click.option('-t', '--title', help='Page title')
@click.option('-d', '--description', help='Page description (auto-generated if not provided)')
@click.option('-c', '--content', help='Markdown content (or use --file)')
@click.option('-f', '--file', 'markdown_file', type=click.Path(exists=True), help='Markdown file to convert')
@click.option('-p', '--password', help='Optional password protection')
@click.option('--style', default='modern', type=click.Choice(['modern', 'minimal', 'dark']),
              help='CSS style theme')
@click.pass_context
def sprout(ctx, title, description, content, markdown_file, password, style):
    """Create shareable webpages from markdown content."""
    click.echo("🌱 Creating oasis webpage...")
    
    try:
        # Get content from file or parameter
        if markdown_file:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            click.echo(f"📄 Reading content from: {markdown_file}")
        elif content:
            click.echo("📝 Using provided content")
        else:
            click.echo("❌ Error: Either --content or --file must be provided")
            click.echo("💡 Use --help to see usage examples")
            return
        
        # Generate sprout
        result = flow_cli.sprout_generator.generate_sprout(
            content=content,
            title=title,
            description=description,
            style=style,
            password=password
        )
        
        if result['success']:
            click.echo("✅ Sprout created successfully!")
            click.echo(f"📄 Title: {result['title']}")
            click.echo(f"📝 Description: {result['description']}")
            click.echo(f"📁 File: {result['filename']}")
            click.echo(f"🌐 URL: {result['url']}")
            click.echo(f"📊 Size: {result['size']} bytes")
            
            if password:
                click.echo("🔒 Password protected")
        else:
            click.echo(f"❌ Error: {result['error']}")
            
    except Exception as error:
        click.echo(f"❌ Error creating sprout: {error}")
        sys.exit(1)


@cli.command()
@click.option('--list', 'list_sprouts', is_flag=True, help='List all generated sprouts')
@click.option('--open', 'open_sprout', help='Open a specific sprout by filename')
@click.pass_context
def sprouts(ctx, list_sprouts, open_sprout):
    """Manage generated sprout webpages."""
    if list_sprouts:
        try:
            sprout_list = flow_cli.sprout_generator.list_sprouts()
            
            if not sprout_list:
                click.echo("📝 No sprouts found.")
                click.echo("💡 Create your first sprout with: flow sprout --content 'Your markdown content'")
                return
            
            click.echo(f"📊 Found {len(sprout_list)} sprout(s):")
            click.echo("─" * 80)
            click.echo("Title".ljust(30) + "File".ljust(25) + "Size".ljust(10) + "Created")
            click.echo("─" * 80)
            
            for sprout in sprout_list:
                from datetime import datetime
                created = datetime.fromtimestamp(sprout['created']).strftime('%Y-%m-%d %H:%M')
                size_kb = f"{sprout['size'] // 1024}KB" if sprout['size'] > 1024 else f"{sprout['size']}B"
                
                click.echo(
                    sprout['title'][:29].ljust(30) +
                    sprout['filename'][:24].ljust(25) +
                    size_kb.ljust(10) +
                    created
                )
            
            click.echo("─" * 80)
            click.echo(f"💡 Open a sprout: flow sprouts --open FILENAME")
            
        except Exception as error:
            click.echo(f"❌ Error listing sprouts: {error}")
            sys.exit(1)
    
    elif open_sprout:
        try:
            import webbrowser
            from pathlib import Path
            
            sprout_dir = Path("data/sprouts")
            filepath = sprout_dir / open_sprout
            
            if not filepath.exists():
                click.echo(f"❌ Sprout not found: {open_sprout}")
                click.echo("💡 List available sprouts with: flow sprouts --list")
                return
            
            url = f"file://{filepath.absolute()}"
            webbrowser.open(url)
            click.echo(f"🌐 Opening sprout: {open_sprout}")
            click.echo(f"🔗 URL: {url}")
            
        except Exception as error:
            click.echo(f"❌ Error opening sprout: {error}")
            sys.exit(1)
    
    else:
        click.echo("🌱 Sprout Management")
        click.echo("💡 Use --list to see all sprouts")
        click.echo("💡 Use --open FILENAME to open a sprout")


@cli.command()
@click.option('--main-screen-only', is_flag=True, help='Record only the main screen')
@click.option('--ocr', is_flag=True, default=True, help='Use OCR mode (default)')
@click.pass_context
def start(ctx, main_screen_only, ocr):
    """Start interactive screen tracking and analysis."""
    async def _start():
        try:
            click.echo("🚀 Starting Flow interactive screen tracking...")
            
            # Detect available screens
            click.echo("🔍 Detecting available screens...")
            await screen_detector.detect_screens()
            screen_info = screen_detector.get_screen_info()
            
            click.echo(f"📺 Found {screen_info['screen_count']} screen(s):")
            for screen in screen_info['screens']:
                indicator = '⭐' if screen['is_main'] else '  '
                click.echo(f"  {indicator} {screen['index']}: {screen['name']} ({screen['resolution']})")
            
            if main_screen_only:
                main_screen = screen_detector.get_main_screen()
                click.echo(f"📺 Recording: Main screen only ({main_screen.name if main_screen else 'Unknown'})")
            else:
                click.echo("📺 Recording: All screens")
            
            click.echo("🤖 Mode: OCR" if ocr else "🤖 Mode: Claude AI")
            click.echo("\n📸 Screenshot Logging:")
            click.echo("  • Screenshots are being captured every 60 seconds")
            click.echo("  • OCR data is being saved to ChromaDB")
            click.echo("  • Use Ctrl+C to stop tracking")
            click.echo("\n💡 Make sure ChromaDB is running: flow chroma start")
            click.echo("─" * 60)
            
            # Set environment variables
            os.environ['MAIN_SCREEN_ONLY'] = str(main_screen_only).lower()
            os.environ['USE_OCR'] = str(ocr).lower()
            
            # Start the OCR processor
            await ocr_processor.start()
            
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping screen tracking...")
            await ocr_processor.stop()
        except Exception as error:
            click.echo(f"❌ Error: {error}")
            sys.exit(1)
    
    asyncio.run(_start())


@cli.group()
def chroma():
    """Manage ChromaDB server."""
    pass


@chroma.command('start')
@click.pass_context
def chroma_start(ctx):
    """Start ChromaDB server."""
    try:
        click.echo("🗄️  Starting ChromaDB server...")
        
        # Try to start ChromaDB server
        process = subprocess.Popen(
            ['chroma', 'run', '--host', 'localhost', '--port', '8000', '--path', 'data/chroma'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        click.echo("✅ ChromaDB started successfully")
        click.echo("📊 Server: http://localhost:8000")
        click.echo("💡 Use 'flow chroma stop' to stop the server")
        
    except FileNotFoundError:
        click.echo("❌ ChromaDB not found")
        click.echo("💡 Install ChromaDB: pip install chromadb")
        sys.exit(1)
    except Exception as error:
        click.echo(f"❌ Error starting ChromaDB: {error}")
        sys.exit(1)


@chroma.command('stop')
@click.pass_context
def chroma_stop(ctx):
    """Stop ChromaDB server."""
    try:
        click.echo("🛑 Stopping ChromaDB server...")
        
        # Try to stop ChromaDB (simplified - just inform user)
        click.echo("💡 Use Ctrl+C in the ChromaDB terminal to stop the server")
        
    except Exception as error:
        click.echo(f"❌ Error: {error}")
        sys.exit(1)


@chroma.command('status')
@click.pass_context
def chroma_status(ctx):
    """Check ChromaDB server status."""
    async def _status():
        try:
            await chroma_client.init()
            
            click.echo("✅ ChromaDB is running")
            click.echo("📊 Host: localhost:8000")
            click.echo("💚 Health: Healthy")
            
        except Exception as error:
            click.echo("❌ ChromaDB is not running")
            click.echo("💡 Start with: flow chroma start")
    
    asyncio.run(_status())


@chroma.command('count')
@click.pass_context
def chroma_count(ctx):
    """Count documents in ChromaDB collections."""
    async def _count():
        try:
            await chroma_client.init()
            
            click.echo("🔍 Checking ChromaDB document counts...")
            
            collections = await chroma_client.list_collections()
            click.echo(f"\n📊 Found {len(collections)} collection(s):")
            click.echo("─" * 60)
            
            total_count = 0
            
            for collection in collections:
                try:
                    stats = await chroma_client.get_collection_stats(collection['name'])
                    count = stats['count']
                    click.echo(f"📁 {collection['name']:<25}: {count} documents")
                    total_count += count
                except Exception as error:
                    click.echo(f"❌ {collection['name']:<25}: Error - {error}")
            
            click.echo("─" * 60)
            click.echo(f"📈 Total documents: {total_count}")
            
        except Exception as error:
            click.echo(f"❌ Error: {error}")
            sys.exit(1)
    
    asyncio.run(_count())


@cli.command()
@click.option('--chroma-only', is_flag=True, help='Stop only ChromaDB server')
@click.pass_context
def stop(ctx, chroma_only):
    """Stop screen tracking and ChromaDB server."""
    click.echo("🛑 Stopping Flow services...")
    
    if not chroma_only:
        click.echo("💡 Screen tracking is interactive - use Ctrl+C in the tracking window to stop")
        click.echo("   Or use --chroma-only to stop only ChromaDB")
    
    # Stop ChromaDB (simplified)
    click.echo("💡 Use Ctrl+C in the ChromaDB terminal to stop the server")


@cli.command()
@click.option('-s', '--service', help='Check specific service status')
@click.pass_context
def status(ctx, service):
    """Check status of Flow services."""
    click.echo("📊 Checking Flow service status...")
    click.echo("\n📊 Service Status:")
    click.echo("─" * 60)
    click.echo("Service".ljust(20) + "Status".ljust(10) + "Notes")
    click.echo("─" * 60)
    
    # Check ChromaDB
    async def _check_chroma():
        try:
            await chroma_client.init()
            return "✅ Running"
        except:
            return "❌ Stopped"
    
    chroma_status = asyncio.run(_check_chroma())
    click.echo("ChromaDB".ljust(20) + chroma_status.ljust(10) + "Vector database")
    
    click.echo("─" * 60)
    click.echo("💡 Start services with: flow start")


@cli.command()
@click.pass_context
def screens(ctx):
    """Detect and list available screens."""
    async def _screens():
        try:
            click.echo("🔍 Detecting available screens...")
            
            await screen_detector.detect_screens()
            screen_info = screen_detector.get_screen_info()
            
            click.echo(f"\n📺 Found {screen_info['screen_count']} screen(s):")
            click.echo("─" * 60)
            click.echo("Index".ljust(8) + "Name".ljust(20) + "Resolution".ljust(15) + "Status")
            click.echo("─" * 60)
            
            for screen in screen_info['screens']:
                status = "⭐ Main" if screen['is_main'] else "  Secondary"
                click.echo(
                    str(screen['index']).ljust(8) +
                    screen['name'].ljust(20) +
                    screen['resolution'].ljust(15) +
                    status
                )
            
            click.echo("─" * 60)
            
            if screen_info['main_screen']:
                main = screen_info['main_screen']
                click.echo(f"\n💡 Main screen: {main['name']} (Index: {main['index']})")
            
            click.echo("\n💡 Use --main-screen-only with flow start to record only the main screen")
            
        except Exception as error:
            click.echo(f"❌ Error: {error}")
            sys.exit(1)
    
    asyncio.run(_screens())


@cli.command()
@click.option('-p', '--port', default=3000, help='Port number')
@click.option('--public', is_flag=True, help='Make server publicly accessible via ngrok')
@click.pass_context
def serve(ctx, port, public):
    """Start MCP server for external client integration."""
    async def _serve():
        try:
            click.echo(f"🔌 Starting MCP HTTP Bridge on port {port}...")
            click.echo(f"🌐 Public access: {'Enabled via ngrok' if public else 'Local only'}")
            
            if public:
                # Start ngrok tunnel in background
                import subprocess
                ngrok_process = subprocess.Popen([
                    'ngrok', 'http', str(port), '--log=stdout'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait a moment for ngrok to start
                import time
                time.sleep(3)
                
                # Extract ngrok URL
                try:
                    result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        import json
                        tunnels = json.loads(result.stdout)
                        if tunnels.get('tunnels'):
                            public_url = tunnels['tunnels'][0]['public_url']
                            click.echo(f"🌍 Public URL: {public_url}")
                            
                            # Save URL to file for later reference
                            with open('mcp_public_url.txt', 'w') as f:
                                f.write(public_url)
                        else:
                            click.echo("⚠️  No ngrok tunnels found")
                    else:
                        click.echo("⚠️  Could not retrieve ngrok URL")
                except Exception as e:
                    click.echo(f"⚠️  Error getting ngrok URL: {e}")
            
            # Import and run the MCP HTTP bridge
            from mcp_http_bridge import MCPHttpBridge
            
            bridge = MCPHttpBridge(port=port)
            await bridge.run()
            
        except Exception as error:
            click.echo(f"❌ Error: {error}")
            sys.exit(1)
    
    asyncio.run(_serve())


@cli.command()
@click.option('-p', '--port', default=8080, help='Port number for sprout server')
@click.option('--public', is_flag=True, help='Make sprout server publicly accessible via ngrok')
@click.option('--open-browser', is_flag=True, help='Open browser after starting server')
@click.pass_context
def serve_sprouts(ctx, port, public, open_browser):
    """Start HTTP server to serve sprout webpages."""
    try:
        import http.server
        import socketserver
        import threading
        import subprocess
        import time
        from pathlib import Path
        
        sprout_dir = Path("data/sprouts")
        if not sprout_dir.exists():
            click.echo("❌ Sprout directory not found")
            click.echo("💡 Create sprouts with: flow sprout --content 'Your content'")
            return
        
        class SproutHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(sprout_dir), **kwargs)
            
            def log_message(self, format, *args):
                # Suppress default logging
                pass
        
        # Start HTTP server in background thread
        def start_server():
            with socketserver.TCPServer(("", port), SproutHandler) as httpd:
                httpd.serve_forever()
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        click.echo(f"🌱 Starting sprout server on port {port}...")
        click.echo(f"📁 Serving directory: {sprout_dir.absolute()}")
        
        # Wait for server to start
        time.sleep(1)
        
        local_url = f"http://localhost:{port}"
        public_url = None
        
        if public:
            click.echo("🌐 Starting ngrok tunnel...")
            try:
                # Start ngrok tunnel
                ngrok_process = subprocess.Popen([
                    'ngrok', 'http', str(port), '--log=stdout'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for ngrok to start
                time.sleep(3)
                
                # Get ngrok URL
                result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    import json
                    tunnels = json.loads(result.stdout)
                    if tunnels.get('tunnels'):
                        public_url = tunnels['tunnels'][0]['public_url']
                        click.echo(f"🌍 Public URL: {public_url}")
                        
                        # Save URL to file
                        with open('sprouts_public_url.txt', 'w') as f:
                            f.write(public_url)
                    else:
                        click.echo("⚠️  No ngrok tunnels found")
                else:
                    click.echo("⚠️  Could not retrieve ngrok URL")
                    
            except Exception as e:
                click.echo(f"⚠️  Error starting ngrok: {e}")
        
        click.echo(f"✅ Sprout server running!")
        click.echo(f"🏠 Local URL: {local_url}")
        if public_url:
            click.echo(f"🌍 Public URL: {public_url}")
        
        click.echo("\n📊 Available sprouts:")
        sprout_list = flow_cli.sprout_generator.list_sprouts()
        if sprout_list:
            for sprout in sprout_list[:5]:  # Show first 5
                sprout_url = f"{public_url or local_url}/{sprout['filename']}"
                click.echo(f"  • {sprout['title']}: {sprout_url}")
            if len(sprout_list) > 5:
                click.echo(f"  ... and {len(sprout_list) - 5} more")
        else:
            click.echo("  No sprouts found")
        
        if open_browser:
            import webbrowser
            webbrowser.open(public_url or local_url)
            click.echo("🌐 Opened browser")
        
        click.echo("\n💡 Press Ctrl+C to stop the server")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping sprout server...")
            
    except Exception as error:
        click.echo(f"❌ Error starting sprout server: {error}")
        sys.exit(1)


@cli.command()
@click.option('-f', '--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def vaporize(ctx, force):
    """Delete all Flow data (irreversible)."""
    click.echo("💥 Vaporizing all Flow data...")
    
    if not force:
        click.echo("⚠️  This will permanently delete ALL Flow data!")
        click.echo("   - Screenshots and analysis data")
        click.echo("   - All summaries (hourly, daily, monthly, yearly)")
        click.echo("   - ChromaDB collections and embeddings")
        click.echo("   - Configuration files and preferences")
        click.echo("   - Log files and temporary data")
        click.echo("")
        click.echo("💡 Use --force flag to proceed without confirmation")
        return
    
    # TODO: Implement vaporize functionality
    click.echo("Vaporize functionality not yet implemented in Python version")


if __name__ == "__main__":
    cli()
