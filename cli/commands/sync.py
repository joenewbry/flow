"""Sync command - sync OCR files to ChromaDB."""

import json
from datetime import datetime
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from cli.display.components import print_header, print_success, print_error, format_number
from cli.display.colors import COLORS
from cli.services.health import HealthService
from cli.config import get_settings

console = Console()


def sync(
    force: bool = typer.Option(False, "--force", "-f", help="Re-sync all files"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be synced"),
    batch_size: int = typer.Option(100, "--batch-size", "-b", help="Batch size for syncing"),
):
    """Sync OCR files to ChromaDB."""
    print_header("Sync")

    health = HealthService()
    settings = get_settings()

    # Check ChromaDB is running
    chroma_check = health.check_chroma_server()
    if not chroma_check.running:
        print_error("ChromaDB server not running")
        console.print("  [dim]Start it with: chroma run --host localhost --port 8000[/dim]")
        console.print()
        return

    # Get file counts
    console.print("  Scanning OCR files...", end=" ")
    ocr_files = list(settings.ocr_data_path.glob("*.json")) if settings.ocr_data_path.exists() else []
    console.print(f"[bold]{format_number(len(ocr_files))}[/bold] found")

    # Connect to ChromaDB
    try:
        import chromadb
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )

        # Get or create collection
        try:
            collection = client.get_collection(name=settings.chroma_collection)
            existing_count = collection.count()
        except Exception:
            collection = client.create_collection(name=settings.chroma_collection)
            existing_count = 0

        console.print(f"  Checking ChromaDB...   [bold]{format_number(existing_count)}[/bold] indexed")

    except ImportError:
        print_error("ChromaDB package not installed")
        console.print("  [dim]Install with: pip install chromadb[/dim]")
        console.print()
        return
    except Exception as e:
        print_error(f"Failed to connect to ChromaDB: {e}")
        console.print()
        return

    # Get existing document IDs
    if force:
        to_sync = ocr_files
        console.print(f"  [dim]Force mode: re-syncing all files[/dim]")
    else:
        # Get IDs already in collection
        console.print("  Checking for missing documents...")
        existing_ids = set()

        if existing_count > 0:
            # Get all IDs in batches
            try:
                result = collection.get(include=[])
                existing_ids = set(result["ids"]) if result["ids"] else set()
            except Exception:
                pass

        # Find files not in collection
        to_sync = []
        for f in ocr_files:
            doc_id = f.stem  # Use filename without extension as ID
            if doc_id not in existing_ids:
                to_sync.append(f)

    if not to_sync:
        print_success("Already in sync!")
        console.print()
        return

    console.print()
    console.print(f"  Syncing [bold]{format_number(len(to_sync))}[/bold] documents...")

    if dry_run:
        console.print()
        console.print("  [dim]Dry run - no changes made[/dim]")
        console.print(f"  [dim]Would sync {len(to_sync)} files[/dim]")
        console.print()
        return

    # Sync in batches
    synced = 0
    errors = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("  Syncing...", total=len(to_sync))

        batch_ids = []
        batch_documents = []
        batch_metadatas = []

        for f in to_sync:
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)

                text = data.get("text", "")
                if not text:
                    progress.advance(task)
                    continue

                # Prepare document
                doc_id = f.stem
                timestamp_str = data.get("timestamp", "")

                # Parse timestamp
                try:
                    if timestamp_str:
                        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        timestamp = dt.timestamp()
                    else:
                        timestamp = f.stat().st_mtime
                        dt = datetime.fromtimestamp(timestamp)
                        timestamp_str = dt.isoformat()
                except Exception:
                    timestamp = f.stat().st_mtime
                    timestamp_str = datetime.fromtimestamp(timestamp).isoformat()

                metadata = {
                    "timestamp": timestamp,
                    "timestamp_iso": timestamp_str,
                    "screen_name": data.get("screen_name", "unknown"),
                    "word_count": data.get("word_count", len(text.split())),
                    "text_length": len(text),
                    "data_type": "ocr",
                }

                batch_ids.append(doc_id)
                batch_documents.append(text)
                batch_metadatas.append(metadata)

                # Add batch when full
                if len(batch_ids) >= batch_size:
                    try:
                        collection.add(
                            ids=batch_ids,
                            documents=batch_documents,
                            metadatas=batch_metadatas,
                        )
                        synced += len(batch_ids)
                    except Exception as e:
                        errors += len(batch_ids)

                    batch_ids = []
                    batch_documents = []
                    batch_metadatas = []

            except Exception as e:
                errors += 1

            progress.advance(task)

        # Add remaining batch
        if batch_ids:
            try:
                collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                )
                synced += len(batch_ids)
            except Exception:
                errors += len(batch_ids)

    console.print()
    if errors > 0:
        console.print(f"  [{COLORS['success']}]✓[/] Synced {format_number(synced)} documents")
        console.print(f"  [{COLORS['error']}]✗[/] {format_number(errors)} errors")
    else:
        print_success(f"Sync complete. {format_number(synced)} documents added.")

    console.print()
