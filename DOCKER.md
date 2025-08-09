# Docker Overview

This document provides an overview of the Docker setup for the Maharashtra Holidays MCP server.

## Base Image

The server uses Python 3.9-slim as its base image to maintain a small footprint while providing all necessary Python functionality.

## Container Structure

```
/app/
  ├── my_mcp_server.py    # Main MCP server script
  └── cache/              # Directory for storing holiday data cache
```

## Environment Variables

The container accepts the following environment variables:
- `CACHE_DIR`: Directory for storing holiday data (default: /app/cache)
- `REFRESH_INTERVAL`: Cache refresh interval in hours (default: 24)

## Docker Commands

Build the image:
```bash
docker build -t shubhammh/maharashtra-holiday-mcp .
```

Run the container:
```bash
docker run -i --rm shubhammh/maharashtra-holiday-mcp
```

Run with custom cache directory:
```bash
docker run -i --rm \
  -v /path/to/cache:/app/cache \
  -e CACHE_DIR=/app/cache \
  shubhammh/maharashtra-holiday-mcp
```

## Security Considerations

- Uses minimal base image to reduce attack surface
- Runs as non-root user for security
- Only exposes necessary files and directories
- No sensitive information stored in the container

## Performance

The container is optimized for:
- Fast startup time
- Minimal memory footprint
- Efficient caching of holiday data
- Quick response times for queries

## Maintenance

Regular updates:
1. Base image updates for security patches
2. Python package updates
3. Cache cleanup for old holiday data

## Build and Deploy

The image is automatically built and deployed to Docker Hub when changes are pushed to the main branch.
