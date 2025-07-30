from fastapi import FastAPI
from . import auth, chat, agent, analytics, feedback


class ModuleRegistry:
    """Central registry for managing HMVC modules"""
    
    def __init__(self):
        self.modules = {
            'auth': auth,
            'chat': chat,
            'agent': agent,
            'analytics': analytics,
            'feedback': feedback
        }
    
    def register_all_modules(self, app: FastAPI):
        """Register all modules with the FastAPI app"""
        for module_name, module in self.modules.items():
            app.include_router(module.router, tags=[module_name])
            print(f"Registered {module_name} module")
    
    def get_module(self, name: str):
        """Get a specific module by name"""
        return self.modules.get(name)
    
    def list_modules(self):
        """List all registered modules"""
        return list(self.modules.keys())


# Create singleton instance
module_registry = ModuleRegistry()