# Maharashtra Holidays MCP Server

A Model Context Protocol (MCP) server that provides holiday information for Maharashtra state. The server fetches and caches holiday data from the MMRDA (Mumbai Metropolitan Region Development Authority) website.

## Features

- Fetch and cache holiday data for a specific year
- Search holidays by name, month, or date range
- Check if a specific date is a holiday
- Export holidays in ICS or JSON format
- Auto-refreshing cache to ensure up-to-date holiday information

## Installation

You can use this MCP server in two ways:

### 1. Using Docker

```bash
# Pull the image
docker pull shubhammh/maharashtra-holiday-mcp

# Run the container
docker run -i --rm shubhammh/maharashtra-holiday-mcp
```

### 2. Using Python

```bash
# Install the required package
pip install fastmcp

# Run the server using the python script
python my_mcp_server.py
```

## Configuration

Add the following configuration to your `.vscode/mcp.json` file:

```json
{
  "servers": {
    "maharashtra-holidays": {
      "type": "stdio",
      "command": "python",
      "args": ["path/to/my_mcp_server.py"],
      "env": {},
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

## Usage

The server provides the following functions:

1. `fetch_holidays(year: Optional[int], force_refresh: bool = False)` - Fetch and cache holidays
2. `find_holidays(year: Optional[int], query: Optional[str], month: Optional[int], range_start: Optional[str], range_end: Optional[str])` - Search holidays
3. `is_holiday(date: str)` - Check if a date is a holiday
4. `export(year: Optional[int], format: str = "ics")` - Export holidays

## Data Source

Holiday data is sourced from the [MMRDA Public Holidays page](https://mmrda.maharashtra.gov.in/public-holidays).

## License

MIT License
