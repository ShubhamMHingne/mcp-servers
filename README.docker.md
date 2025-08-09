# Maharashtra Holidays MCP Docker Image

This Docker image provides a Model Context Protocol (MCP) server for accessing Maharashtra state holiday information. It automatically fetches and caches holiday data from the MMRDA website.

## Quick Start

1. Pull and run the image:
```bash
docker pull shubhammh/maharashtra-holiday-mcp
docker run -i --rm shubhammh/maharashtra-holiday-mcp
```

2. Add to your VS Code configuration (`.vscode/mcp.json`):
```json
{
    "servers": {
        "maharashtra-holidays": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "shubhammh/maharashtra-holiday-mcp"
            ],
            "type": "stdio"
        }
    }
}
```

## Available Functions

- `fetch_holidays(year: Optional[int], force_refresh: bool = False)`
- `find_holidays(year: Optional[int], query: Optional[str], month: Optional[int])`
- `is_holiday(date: str)`
- `export(format: str = "ics", year: Optional[int] = None)`

## Technical Details

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
