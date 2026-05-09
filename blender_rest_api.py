"""Blender REST API Addon - Uses standard library http.server.

Fixes: All bpy operations are now queued and executed on Blender's main thread
to prevent crashes caused by threading violations.
"""

import bpy
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import queue
import time

bl_info = {
    "name": "Blender REST API",
    "author": "User",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Sidebar (N-Panel) > REST API Tab",
    "description": "REST API for Blender to execute Python commands and manipulate objects.",
    "category": "3D View"
}

# Global queue for main-thread operation execution
_blender_op_queue = queue.Queue()
_queue_timer_registered = False


def _process_queue():
    """Process pending operations in the queue. Called from Blender's main thread."""
    processed = 0
    while not _blender_op_queue.empty():
        try:
            item = _blender_op_queue.get_nowait()
            if item is not None:
                item()
                _blender_op_queue.task_done()
                processed += 1
        except queue.Empty:
            break
    # Keep timer running if there are still items, otherwise stop
    if _blender_op_queue.empty() and processed > 0:
        _unregister_queue_timer()
        return None
    if not _blender_op_queue.empty():
        return 0.01  # Check again very shortly
    return None  # Stop timer


def _register_queue_timer():
    """Start the main-thread queue processor timer if not already running."""
    global _queue_timer_registered
    if _queue_timer_registered:
        return
    _queue_timer_registered = True
    bpy.app.timers.register(_process_queue, persistent=True, first_interval=0.01)


def _unregister_queue_timer():
    """Stop the queue processor timer."""
    global _queue_timer_registered
    _queue_timer_registered = False


def _queue_main_thread_op(func):
    """Queue a function to be executed on Blender's main thread.
    
    Args:
        func: A callable with no arguments that performs bpy operations.
    """
    _register_queue_timer()
    _blender_op_queue.put(func)


# Thread-safe response storage
_response_lock = threading.Lock()
_response_value = [None]  # Using list for mutability in closures


def _set_response(code, data):
    """Set the response value from the main thread.
    
    This is called by queued operations to pass results back to the HTTP handler.
    Only the latest response is kept - the caller should consume it immediately.
    """
    with _response_lock:
        _response_value[0] = (code, data)


def _get_response():
    """Get the current response value from the HTTP handler thread.
    
    Returns the (code, data) tuple set by a queued operation, or None if no
    response has been set yet.
    """
    with _response_lock:
        return _response_value[0]


def _clear_response():
    """Clear the stored response."""
    with _response_lock:
        _response_value[0] = None


class REST_API_Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress console spam

    def _send_json(self, data, status=200):
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data) if post_data else {}
        except Exception as e:
            self._send_json({"status": "error", "message": f"Invalid JSON: {str(e)}"}, 400)
            return

        if self.path == '/execute':
            self._handle_execute(data)
        elif self.path == '/create_cube':
            self._handle_create_cube(data)
        elif self.path == '/create_sphere':
            self._handle_create_sphere(data)
        elif self.path == '/set_color':
            self._handle_set_color(data)
        else:
            self._send_json({"status": "error", "message": "Not found"}, 404)

    def do_GET(self):
        if self.path == '/objects':
            self._handle_get_objects()
        elif self.path == '/health':
            self._send_json({"status": "ok", "message": "Blender REST API is running"})
        else:
            self._send_json({"status": "error", "message": "Not found"}, 404)

    def _wait_for_response(self, operation_func, timeout=30):
        """Queue an operation and wait for its response from Blender's main thread.
        
        Args:
            operation_func: A callable that will be executed on Blender's main thread.
                           It should call _set_response() with (code, data) when done.
            timeout: Maximum seconds to wait for the response.
        """
        _clear_response()
        _queue_main_thread_op(operation_func)
        
        # Poll for the response with a small delay to allow queue processing
        deadline = time.time() + timeout
        while time.time() < deadline:
            response = _get_response()
            if response is not None:
                code, data = response
                self._send_json(data, code)
                return
            time.sleep(0.05)  # Poll every 50ms
        
        self._send_json({"status": "error", "message": "Request timed out - Blender may be busy"}, 504)

    def _handle_execute(self, data):
        """Queue code execution on Blender's main thread."""
        code = data.get('code', '')

        def exec_op():
            try:
                exec_globals = {
                    'bpy': bpy,
                    'math': __import__('math'),
                    'random': __import__('random'),
                }
                exec(code, exec_globals)
                result = str(exec_globals.get('last_result', 'Code executed successfully'))
                _set_response(200, {"status": "success", "result": result})
            except Exception as e:
                _set_response(500, {"status": "error", "message": f"Execution error: {str(e)}"})

        self._wait_for_response(exec_op)

    def _handle_create_cube(self, data):
        """Queue cube creation on Blender's main thread."""
        name = data.get('name', 'Cube')

        def create_op():
            try:
                bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
                obj = bpy.context.active_object
                if obj:
                    obj.name = name
                _set_response(200, {"status": "success", "object_name": name})
            except Exception as e:
                _set_response(500, {"status": "error", "message": f"Create cube error: {str(e)}"})

        self._wait_for_response(create_op)

    def _handle_create_sphere(self, data):
        """Queue sphere creation on Blender's main thread."""
        name = data.get('name', 'Sphere')

        def create_op():
            try:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
                obj = bpy.context.active_object
                if obj:
                    obj.name = name
                _set_response(200, {"status": "success", "object_name": name})
            except Exception as e:
                _set_response(500, {"status": "error", "message": f"Create sphere error: {str(e)}"})

        self._wait_for_response(create_op)

    def _handle_set_color(self, data):
        """Queue color setting on Blender's main thread."""
        r, g, b = data.get('color', [1.0, 0.5, 0.2])

        def color_op():
            try:
                if bpy.context.active_object is None:
                    _set_response(400, {"status": "error", "message": "No object selected"})
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

                _set_response(200, {"status": "success", "material": mat_name})
            except Exception as e:
                _set_response(500, {"status": "error", "message": f"Set color error: {str(e)}"})

        self._wait_for_response(color_op)

    def _handle_get_objects(self):
        """Handle GET /objects - queue for thread safety."""
        def objects_op():
            try:
                objects = [obj.name for obj in bpy.context.scene.objects]
                _set_response(200, {"objects": objects})
            except Exception as e:
                _set_response(500, {"status": "error", "message": f"Get objects error: {str(e)}"})

        self._wait_for_response(objects_op)


class REST_API_Server:
    """Manages the HTTP server lifecycle. Not registered with Blender RNA."""
    server = None
    thread = None
    is_running = False
    
    @staticmethod
    def start(port=8080):
        if REST_API_Server.server and REST_API_Server.is_running:
            return
        
        REST_API_Server.server = HTTPServer(('0.0.0.0', port), REST_API_Handler)
        REST_API_Server.thread = threading.Thread(target=REST_API_Server.server.serve_forever, daemon=True)
        REST_API_Server.thread.start()
        REST_API_Server.is_running = True
        
    @staticmethod
    def stop():
        if REST_API_Server.server:
            REST_API_Server.server.shutdown()
            REST_API_Server.is_running = False
            REST_API_Server.server = None


class REST_API_Panel(bpy.types.Panel):
    bl_label = "REST API"
    bl_idname = "VIEW3D_PT_rest_api"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

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
        layout.label(text="- GET  /health")


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
    # Clean up the timer
    _unregister_queue_timer()


if __name__ == "__main__":
    register()