import asyncio
from blender_mcp import mcp

async def main():
    # Test execute_code with a simple print statement
    result = await mcp.call_tool('blenderAPI_execute_code', {'code': 'print("Hello from MCP!")'})
    print(f"execute_code result: {result}")
    
    # Test create_cube
    result = await mcp.call_tool('blenderAPI_create_cube', {'name': 'TestCube'})
    print(f"create_cube result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
