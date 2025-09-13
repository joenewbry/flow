#!/bin/bash
# Start ChromaDB server using Docker
# This script follows the official ChromaDB documentation

set -e

# Default configuration
CHROMA_PORT=${CHROMA_PORT:-8000}
CHROMA_HOST=${CHROMA_HOST:-localhost}
CHROMA_DATA_DIR=${CHROMA_DATA_DIR:-./chroma}

# Create data directory if it doesn't exist
mkdir -p "$CHROMA_DATA_DIR"

echo "Starting ChromaDB server..."
echo "Port: $CHROMA_PORT"
echo "Host: $CHROMA_HOST"
echo "Data directory: $CHROMA_DATA_DIR"

# Start ChromaDB using Docker
docker run -d \
  --name chroma-server \
  -p $CHROMA_PORT:8000 \
  -v "$(pwd)/$CHROMA_DATA_DIR:/chroma/chroma" \
  chromadb/chroma:latest \
  --host 0.0.0.0 \
  --port 8000

echo "ChromaDB server started successfully!"
echo "Server URL: http://$CHROMA_HOST:$CHROMA_PORT"
echo "To stop the server: docker stop chroma-server"
echo "To remove the container: docker rm chroma-server"
