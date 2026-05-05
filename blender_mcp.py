"""Blender MCP Server - Model Context Protocol integration for Blender."""

from fastmcp import FastMCP
import json
from urllib.request import urlopen, Request
from urllib.error import URLError
import time

# Create the MCP server instance
mcp = FastMCP("blender")

@mcp.tool()
def execute_code(code: str) -> dict:
    """Execute Python code in Blender context."""
    result = _call_blender_api('execute', {'code': code})
    if result.get('status') == 'success':
        return {"result": result['result']}
    else:
        return {"error": result.get('message', 'Unknown error')}

@mcp.tool()
def get_objects() -> dict:
    """Get list of all objects in the scene."""
    result = _call_blender_api('objects')
    if isinstance(result, dict) and 'objects' in result:
        return {"objects": result['objects']}
    else:
        return {"error": "Failed to get objects"}

@mcp.tool()
def create_cube(name: str = "Cube") -> dict:
    """Create a cube at origin."""
    time.sleep(0.1)  # Small delay to ensure Blender is ready
    result = _call_blender_api('create_cube', {'name': name})
    if isinstance(result, dict):
        return {"object_name": name}
    else:
        return {"error": "Failed to create cube"}

@mcp.tool()
def create_sphere(name: str = "Sphere") -> dict:
    """Create a sphere at origin."""
    time.sleep(0.1)
    result = _call_blender_api('create_sphere', {'name': name})
    if isinstance(result, dict):
        return {"object_name": name}
    else:
        return {"error": "Failed to create sphere"}

@mcp.tool()
def set_color(r: float = 1.0, g: float = 0.5, b: float = 0.2) -> dict:
    """Set material color on selected object."""
    time.sleep(0.1)
    result = _call_blender_api('set_color', {'color': [r, g, b]})
    if isinstance(result, dict):
        return {"material": f"{name}_Material"}
    else:
        return {"error": "Failed to set color"}

def _call_blender_api(endpoint: str, data=None) -> dict:
    """Call the Blender REST API and return parsed JSON response."""
    url = f"http://localhost:8080/{endpoint}"
    
    if data is not None:
        req = Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
    else:
        req = Request(url)
        
    try:
        with urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}

if __name__ == "__main__":
    mcp.run()
