"""Blender REST API Addon - Uses standard library http.server."""

import bpy
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json

bl_info = {
    "name": "Blender REST API",
    "author": "User",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Sidebar (N-Panel) > REST API Tab",
    "description": "REST API for Blender to execute Python commands and manipulate objects.",
    "category": "3D View"
}

class REST_API_Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress console spam

    def _send_json(self, data):
        response = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data) if post_data else {}
        except Exception as e:
            self.send_error(400, "Invalid JSON")
            return

        if self.path == '/execute':
            try:
                exec_globals = {
                    'bpy': bpy,
                    'math': __import__('math'),
                    'random': __import__('random'),
                }
                exec(data.get('code', ''), exec_globals)
                result = str(exec_globals.get('last_result', 'Code executed'))
            except Exception as e:
                self.send_error(500, str(e))
                return
            self._send_json({"status": "success", "result": result})

        elif self.path == '/create_cube':
            name = data.get('name', 'Cube')
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
            obj = bpy.context.active_object
            if obj:
                obj.name = name
            self._send_json({"status": "success", "object_name": name})

        elif self.path == '/create_sphere':
            name = data.get('name', 'Sphere')
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
            obj = bpy.context.active_object
            if obj:
                obj.name = name
            self._send_json({"status": "success", "object_name": name})

        elif self.path == '/set_color':
            r, g, b = data.get('color', [1.0, 0.5, 0.2])
            
            if not bpy.context.active_object:
                self.send_error(400, "No object selected")
                return
            
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
            
            self._send_json({"status": "success", "material": mat_name})

        else:
            self.send_error(404, "Not found")

    def do_GET(self):
        if self.path == '/objects':
            objects = [obj.name for obj in bpy.context.scene.objects]
            self._send_json({"objects": objects})
        else:
            self.send_error(404, "Not found")

class REST_API_Server:
    """Manages the HTTP server lifecycle. Not registered with Blender RNA."""
    server = None
    thread = None
    is_running = False
    
    @staticmethod
    def start():
        if cls.server and cls.is_running:
            return
        
        cls.server = HTTPServer(('0.0.0.0', 8080), REST_API_Handler)
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
    bl_region_type = 'UI'  # Fixed for Blender 5.1+ compatibility

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

# Only register Blender types (Panel and Operators)
classes = (
    REST_API_Panel,
    REST_API_Start,
    REST_API_Stop,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
