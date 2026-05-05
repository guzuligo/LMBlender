"""Blender REST API Addon - Allows controlling Blender via HTTP requests."""

import bpy
from flask import Flask, request, jsonify
import threading
from werkzeug.serving import make_server

bl_info = {
    "name": "Blender REST API",
    "author": "User",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Sidebar (N-Panel) > REST API Tab",
    "description": "REST API for Blender to execute Python commands and manipulate objects.",
    "category": "3D View"
}

class REST_API_Server:
    """Manages the Flask server lifecycle."""
    server = None
    is_running = False
    
    @staticmethod
    def start():
        if cls.server and cls.is_running:
            return
        
        app = Flask(__name__)
        
        # --- Routes ---
        @app.route('/execute', methods=['POST'])
        def execute():
            data = request.get_json()
            if not data or 'code' not in data:
                return jsonify({"error": "Missing 'code' field"}), 400
            
            try:
                exec_globals = {
                    'bpy': bpy,
                    'math': __import__('math'),
                    'random': __import__('random'),
                }
                exec(data['code'], exec_globals)
                return jsonify({"status": "success", "result": str(exec_globals.get('last_result', 'Code executed'))})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @app.route('/objects', methods=['GET'])
        def get_objects():
            objects = [obj.name for obj in bpy.context.scene.objects]
            return jsonify({"objects": objects})

        @app.route('/create_cube', methods=['POST'])
        def create_cube():
            data = request.get_json() or {}
            name = data.get('name', 'Cube')
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
            obj = bpy.context.active_object
            if obj:
                obj.name = name
            return jsonify({"status": "success", "object_name": name})

        @app.route('/create_sphere', methods=['POST'])
        def create_sphere():
            data = request.get_json() or {}
            name = data.get('name', 'Sphere')
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
            obj = bpy.context.active_object
            if obj:
                obj.name = name
            return jsonify({"status": "success", "object_name": name})

        @app.route('/set_color', methods=['POST'])
        def set_color():
            data = request.get_json() or {}
            r, g, b = data.get('color', [1.0, 0.5, 0.2])
            
            if not bpy.context.active_object:
                return jsonify({"status": "error", "message": "No object selected"}), 400
            
            obj = bpy.context.active_object
            mat_name = f"{obj.name}_Material"
            
            if obj.data.materials:
                mat = obj.data.materials[0]
            else:
                mat = bpy.data.materials.new(name=mat_name)
                obj.data.materials.append(mat)
                
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
            
            return jsonify({"status": "success", "material": mat_name})

        cls.server = make_server('0.0.0.0', 8080, app)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.is_running = True
        
    @staticmethod
    def stop():
        if cls.server:
            cls.server.shutdown()
            cls.is_running = False

class REST_API_Panel(bpy.types.Panel):
    bl_label = "REST API"
    bl_idname = "VIEW3D_PT_rest_api"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOL_PROPS'  # Sidebar (N-Panel)

    def draw(self, context):
        layout = self.layout
        
        if not REST_API_Server.is_running:
            layout.operator("rest_api.start_server")
        else:
            layout.label(text="Status: Running", icon='PLAY')
            layout.operator("rest_api.stop_server")
            
        layout.separator()
        layout.label(text="Endpoints:")
        layout.label(text="- POST /execute (code)")
        layout.label(text="- GET  /objects")
        layout.label(text="- POST /create_cube")
        layout.label(text="- POST /create_sphere")
        layout.label(text="- POST /set_color")

class REST_API_Start(bpy.types.Operator):
    bl_idname = "rest_api.start_server"
    bl_label = "Start Server"
    
    def execute(self, context):
        REST_API_Server.start()
        self.report({'INFO'}, "REST API server started on port 8080")
        return {'FINISHED'}

class REST_API_Stop(bpy.types.Operator):
    bl_idname = "rest_api.stop_server"
    bl_label = "Stop Server"
    
    def execute(self, context):
        REST_API_Server.stop()
        self.report({'INFO'}, "REST API server stopped")
        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
