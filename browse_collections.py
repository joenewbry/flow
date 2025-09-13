#!/usr/bin/env python3
"""
Simple script to browse Chroma collections
"""

import asyncio
import sys
from pathlib import Path

# Add src to path to import chroma_client
sys.path.append(str(Path(__file__).parent / "src"))

from lib.chroma_client import chroma_client

async def browse_collections():
    """Browse and display all Chroma collections with their document counts."""
    try:
        print("🔍 Connecting to ChromaDB...")
        await chroma_client.init()
        
        print("📊 Fetching collections...")
        collections = await chroma_client.list_collections()
        
        if not collections:
            print("❌ No collections found in ChromaDB")
            return
        
        print(f"\n📁 Found {len(collections)} collection(s):")
        print("─" * 60)
        
        total_count = 0
        
        for collection in collections:
            try:
                stats = await chroma_client.get_collection_stats(collection['name'])
                count = stats['count']
                metadata = stats.get('metadata', {})
                description = metadata.get('description', 'No description')
                
                print(f"📁 {collection['name']:<25}: {count} documents")
                print(f"   Description: {description}")
                print()
                
                total_count += count
            except Exception as error:
                print(f"❌ {collection['name']:<25}: Error - {error}")
        
        print("─" * 60)
        print(f"📈 Total documents across all collections: {total_count}")
        
    except Exception as error:
        print(f"❌ Error: {error}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(browse_collections()))
