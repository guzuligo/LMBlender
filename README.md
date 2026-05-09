# Connect Blender to LM Studio

A Model Context Protocol (MCP) server that connects LM Studio to Blender, allowing AI assistants powered by LM Studio to control Blender through natural language commands.

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

## LM Studio Integration

To connect Blender with LM Studio, you'll need to add a custom MCP server configuration. Here's how:

### Prerequisites

Before setting up the integration, install the required dependency:

```bash
pip install fastmcp
```

### Simple Setup

Copy the configuration below into your LM Studio MCP servers settings. Just replace the placeholder paths with your actual paths:

```json
"Blender": {
  "command": "/path/to/python",
  "args": [
    "/path/to/blender_mcp.py"
  ]
}
```

### What to Replace

| Placeholder | Replace with | Example |
|---|---|---|
| `/path/to/python` | Path to your Python executable | `/usr/bin/python3` |, or just use "python"
| `/path/to/blender_mcp.py` | Path to this file on your computer | Wherever you cloned this repo |

### How to Find Your Python Path

Open a terminal and run:
```bash
which python3
```
or if using a virtual environment:
```bash
source your_venv/bin/activate
which python
```

Then copy the path and paste it where `/path/to/python` appears above.

### How to Find Your blender_mcp.py Path

1. Open a file browser and navigate to where you cloned/downloaded this project
2. Right-click on `blender_mcp.py` and look for a "Copy path" or "Properties" option
3. Use that full path in the configuration above

## Notes

- The server runs in a thread so Blender stays responsive
- All code executes in Blender's `bpy` context
- Modify the script to add more endpoints as needed
