# my_mcp_server.py
from fastmcp import FastMCP

# Create server with a friendly name
mcp = FastMCP(name="My First MCP Server")

# Expose a simple tool
@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integers and returns the result."""
    return a + b

if __name__ == "__main__":
    # Run over stdio transport so MCP hosts/clients can connect
    mcp.run(transport="stdio")
