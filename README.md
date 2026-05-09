# Blender REST API Addon

A Flask-based REST API for Blender packaged as a standard addon. Allows sending Python commands to draw and manipulate 3D objects via HTTP requests.

## Installation in Blender

1. Open Blender → **Edit > Preferences > Add-ons**
2. Click **Install...**
3. Select `blender_rest_api.py`
4. Enable the addon (check the box)

The REST API tab will appear in the 3D Viewport sidebar (N-Panel).

## Usage

### Start Server
Open the Sidebar (press `N`) → Look for "REST API" tab → Click **Start Server**

Or run from Text Editor:
```python
import bpy
bpy.utils.register_module(__name__)
bpy.ops.rest_api.start_server()
```

### Test it
```bash
curl http://localhost:8080/objects
# Should return: {"objects": ["Camera", "Light", ...]}
```

## API Endpoints

| Method | Endpoint       | Description                  |
|--------|----------------|------------------------------|
| POST   | /execute       | Execute arbitrary Python code |
| GET    | /objects       | List all scene objects      |
| POST   | /create_cube   | Create a cube               |
| POST   | /create_sphere | Create a sphere             |
| POST   | /set_color     | Set material color           |

## Notes

- The server runs in a thread so Blender stays responsive
- All code executes in Blender's `bpy` context
- Modify the script to add more endpoints as needed
