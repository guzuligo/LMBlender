"""Blender MCP Server - Model Context Protocol integration for Blender."""

import json
from urllib.request import urlopen, Request
from urllib.error import URLError

class BlenderMCP:
    """MCP server that exposes Blender operations via MCP protocol."""
    
    def __init__(self):
        self.base_url = "http://localhost:8080"
        
    def _call_blender_api(self, endpoint, data=None):
        """Call the Blender REST API and return parsed JSON response."""
        url = f"{self.base_url}/{endpoint}"
        
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
            with urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except URLError as e:
            return {"status": "error", "message": f"Connection failed: {str(e)}"}
    
    def execute_code(self, code):
        """Execute Python code in Blender context."""
        result = self._call_blender_api('execute', {'code': code})
        if result.get('status') == 'success':
            return {"result": result['result']}
        else:
            return {"error": result.get('message', 'Unknown error')}
    
    def get_objects(self):
        """Get list of all objects in the scene."""
        result = self._call_blender_api('objects')
        if isinstance(result, dict) and 'objects' in result:
            return {"objects": result['objects']}
        else:
            return {"error": "Failed to get objects"}
    
    def create_cube(self, name="Cube"):
        """Create a cube at origin."""
        result = self._call_blender_api('create_cube', {'name': name})
        if result.get('status') == 'success':
            return {"object_name": result['object_name']}
        else:
            return {"error": "Failed to create cube"}
    
    def create_sphere(self, name="Sphere"):
        """Create a sphere at origin."""
        result = self._call_blender_api('create_sphere', {'name': name})
        if result.get('status') == 'success':
            return {"object_name": result['object_name']}
        else:
            return {"error": "Failed to create sphere"}
    
    def set_color(self, r=1.0, g=0.5, b=0.2):
        """Set material color on selected object."""
        result = self._call_blender_api('set_color', {'color': [r, g, b]})
        if result.get('status') == 'success':
            return {"material": result['material']}
        else:
            return {"error": "Failed to set color"}

# Initialize the MCP server instance
blender_mcp = BlenderMCP()

def main():
    """Run the MCP server."""
    print("Starting Blender MCP Server...")
    
    # Example usage
    print("\nTesting execute_code:")
    result = blender_mcp.execute_code('import bpy; print("Hello from MCP!")')
    print(f"  Result: {result}")
    
    print("\nTesting get_objects:")
    result = blender_mcp.get_objects()
    print(f"  Result: {result}")
    
    print("\nTesting create_cube:")
    result = blender_mcp.create_cube("TestCube")
    print(f"  Result: {result}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
