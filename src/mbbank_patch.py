"""Patch for MBBank library to fix thread event loop issues"""
import asyncio
import functools

import mbbank


def set_event_loop_in_thread(func):
    """Decorator to set event loop in thread"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Try to get the current event loop, if it fails, create a new one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in thread function: {e}")
            raise
    return wrapper

# Apply the patch
def apply_patches():
    """Apply patches to MBBank library"""
    try:
        from mbbank.wasm_helper import wasm_encrypt
        from mbbank.wasm_helper import GO
        
        # Store original methods
        original_wasm_encrypt = wasm_encrypt
        original_GO_init = GO.__init__
        
        # Patch GO.__init__ to handle event loop creation
        @functools.wraps(original_GO_init)
        def patched_GO_init(self, *args, **kwargs):
            try:
                # Try to get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                return original_GO_init(self, *args, **kwargs)
            except Exception as e:
                print(f"Error in GO.__init__: {e}")
                raise
                
        # Apply the patches
        GO.__init__ = patched_GO_init
        mbbank.wasm_helper.wasm_encrypt = set_event_loop_in_thread(original_wasm_encrypt)
        
        print("MBBank library successfully patched!")
        return True
    except Exception as e:
        print(f"Failed to patch MBBank library: {e}")
        return False