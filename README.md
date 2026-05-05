# Blender REST API

A Flask-based REST API for Blender that allows sending Python commands to draw and manipulate 3D objects.

## Setup in Blender

1. Open Blender's **Text Editor** (or Script Editor)
2. Click **Open** → select `blender_rest_api.py` from this folder
3. Click the **Run Script** button ▶️

The server will start on port 8080 and run in a background thread.

## Usage Examples

### Execute arbitrary Python code
```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "import bpy; print(bpy.context.scene.objects)"}'
```

### Create a cube
```bash
curl -X POST http://localhost:8080/create_cube \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Set color on selected object
```bash
curl -X POST http://localhost:8080/set_color \
  -H "Content-Type: application/json" \
  -d '{"color": [0.2, 0.5, 1.0]}'
```

### List all objects in scene
```bash
curl http://localhost:8080/objects
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
