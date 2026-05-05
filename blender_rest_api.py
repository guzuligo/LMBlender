"""blender_rest_api.py - REST API for Blender"""

import json
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store results of last execution
last_result = None


def execute_blender_code(code):
    """Execute Python code in Blender's context."""
    global last_result
    try:
        # Create a namespace with Blender's bpy module and common utilities
        exec_globals = {
            'bpy': __import__('bpy'),
            'math': __import__('math'),
            'random': __import__('random'),
            'last_result': None,
        }

        # Execute the code
        exec(code, exec_globals)

        # Return any result from last_result assignment or stdout capture
        return {
            "status": "success",
            "result": str(exec_globals.get('last_result', 'Code executed'))
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.route('/execute', methods=['POST'])
def execute():
    """Execute arbitrary Python code in Blender."""
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({"error": "Missing 'code' field"}), 400

        result = execute_blender_code(data['code'])
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/objects', methods=['GET'])
def get_objects():
    """List all objects in the scene."""
    import bpy
    objects = [obj.name for obj in bpy.context.scene.objects]
    return jsonify({"objects": objects})


@app.route('/create_cube', methods=['POST'])
def create_cube():
    """Create a cube at origin."""
    import bpy

    data = request.get_json() or {}
    name = data.get('name', 'Cube')

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object
    if obj:
        obj.name = name

    return jsonify({"status": "success", "object_name": name})


@app.route('/create_sphere', methods=['POST'])
def create_sphere():
    """Create a sphere."""
    import bpy

    data = request.get_json() or {}
    name = data.get('name', 'Sphere')

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    obj = bpy.context.active_object
    if obj:
        obj.name = name

    return jsonify({"status": "success", "object_name": name})


@app.route('/set_color', methods=['POST'])
def set_color():
    """Set material color on selected object."""
    import bpy

    data = request.get_json() or {}
    r, g, b = data.get('color', [1.0, 0.5, 0.2])

    if not bpy.context.active_object:
        return jsonify({"status": "error", "message": "No object selected"}), 400

    obj = bpy.context.active_object
    mat_name = f"{obj.name}_Material"

    # Create or get material
    if obj.data.materials:
        mat = obj.data.materials[0]
    else:
        mat = bpy.data.materials.new(name=mat_name)
        obj.data.materials.append(mat)

    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)

    return jsonify({"status": "success", "material": mat_name})


def start_server(port=8080):
    """Start the Flask server in a thread."""
    app.run(host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    # For testing outside Blender
    print("Starting REST API on http://localhost:8080")
    start_server()
