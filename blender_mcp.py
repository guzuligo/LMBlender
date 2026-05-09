"""Blender MCP Server - Model Context Protocol integration for Blender."""

from fastmcp import FastMCP
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import time

# Create the MCP server instance
mcp = FastMCP("blender")

# Default timeout in seconds for API requests
API_TIMEOUT = 15


def _call_blender_api(endpoint: str, data: dict = None, timeout: int = API_TIMEOUT) -> dict:
    """Call the Blender REST API and return parsed JSON response.
    
    Args:
        endpoint: API endpoint path (without leading slash)
        data: Optional dictionary to send as JSON body
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with parsed JSON response, or error dict on failure
    """
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
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        # Handle HTTP error responses (4xx, 5xx)
        error_body = {"status": "error", "message": f"HTTP {e.code}: {e.reason}"}
        try:
            error_body = json.loads(e.read().decode('utf-8'))
        except Exception:
            pass
        return error_body
    except URLError as e:
        return {"status": "error", "message": f"Connection failed: {e.reason}"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON response from Blender"}
    except TimeoutError:
        return {"status": "error", "message": f"Request timed out after {timeout} seconds"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


@mcp.tool()
def blenderAPI_execute_code(code: str) -> dict:
    """Execute arbitrary Python code in Blender's context.
    
    This allows you to run any Blender Python API commands. The code is executed 
    with access to bpy module and standard library modules (math, random).
    
    Args:
        code: Python code string to execute in Blender context
        
    Returns:
        dict with 'result' on success, or 'error' on failure
        
    Example:
        # Create a cube at origin
        blenderAPI_execute_code('import bpy; bpy.ops.mesh.primitive_cube_add()')
        
        # Get all objects in scene
        result = blenderAPI_execute_code('print([obj.name for obj in bpy.context.scene.objects])')
    """
    result = _call_blender_api('execute', {'code': code})
    if result.get('status') == 'success':
        return {"result": result.get('result', '')}
    else:
        return {"error": result.get('message', 'Unknown error: execution failed')}


@mcp.tool()
def blenderAPI_get_objects() -> dict:
    """Get list of all objects in the current Blender scene.
    
    Returns:
        dict with 'objects' key containing list of object names, or 'error' on failure
        
    Example:
        result = blenderAPI_get_objects()
        print(result['objects'])  # ['Camera', 'Light', 'Cube']
    """
    result = _call_blender_api('objects')
    if isinstance(result, dict) and result.get('status') == 'success' and 'objects' in result:
        return {"objects": result['objects']}
    else:
        return {"error": result.get('message', 'Failed to get objects from Blender')}


@mcp.tool()
def blenderAPI_create_cube(name: str = "Cube") -> dict:
    """Create a cube at origin (0, 0, 0).
    
    Args:
        name: Name for the new cube object (default: "Cube")
        
    Returns:
        dict with 'object_name' on success, or 'error' on failure
        
    Example:
        result = blenderAPI_create_cube("MyCube")
        print(result['object_name'])  # "MyCube"
    """
    result = _call_blender_api('create_cube', {'name': name})
    if isinstance(result, dict) and result.get('status') == 'success':
        return {"object_name": result.get('object_name', name)}
    else:
        return {"error": result.get('message', 'Failed to create cube')}


@mcp.tool()
def blenderAPI_create_sphere(name: str = "Sphere") -> dict:
    """Create a sphere at origin (0, 0, 0).
    
    Args:
        name: Name for the new sphere object (default: "Sphere")
        
    Returns:
        dict with 'object_name' on success, or 'error' on failure
        
    Example:
        result = blenderAPI_create_sphere("MySphere")
        print(result['object_name'])  # "MySphere"
    """
    result = _call_blender_api('create_sphere', {'name': name})
    if isinstance(result, dict) and result.get('status') == 'success':
        return {"object_name": result.get('object_name', name)}
    else:
        return {"error": result.get('message', 'Failed to create sphere')}


@mcp.tool()
def blenderAPI_set_color(r: float = 1.0, g: float = 0.5, b: float = 0.2, name: str = "Object") -> dict:
    """Set material color on the currently selected object in Blender.
    
    Args:
        r: Red component (0.0-1.0), defaults to 1.0
        g: Green component (0.0-1.0), defaults to 0.5
        b: Blue component (0.0-1.0), defaults to 0.2
        name: Display name for the object (used in response only)
        
    Returns:
        dict with 'material' name on success, or 'error' on failure
        
    Example:
        # Set selected object to blue color
        result = blenderAPI_set_color(0.0, 0.5, 1.0)
        print(result['material'])  # "Cube_Material"
    """
    result = _call_blender_api('set_color', {'color': [r, g, b]})
    if isinstance(result, dict) and result.get('status') == 'success':
        return {"material": result.get('material', f"{name}_Material")}
    else:
        return {"error": result.get('message', 'Failed to set color')}


if __name__ == "__main__":
    mcp.run()