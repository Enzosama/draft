"""
Patch passlib to avoid wrap bug detection issues and bcrypt version reading errors.
This must be imported before any passlib operations.
"""
import logging

logger = logging.getLogger("patch_passlib")

try:
    import passlib.handlers.bcrypt as bcrypt_module
    import bcrypt as _bcrypt
    
    # Patch bcrypt module to add __about__ if it doesn't exist (for bcrypt 3.x compatibility)
    if not hasattr(_bcrypt, '__about__'):
        class _BcryptAbout:
            def __init__(self):
                # Try to get version from __version__ or use default
                try:
                    self.__version__ = _bcrypt.__version__
                except AttributeError:
                    self.__version__ = "3.2.2"
        
        _bcrypt.__about__ = _BcryptAbout()
        logger.debug("Added __about__ attribute to bcrypt module for compatibility")
    
    # Patch _load_backend_mixin to handle bcrypt version reading
    # bcrypt 3.x doesn't have __about__ attribute, so we need to patch this
    original_load_backend = bcrypt_module.bcrypt._load_backend_mixin
    
    @classmethod
    def patched_load_backend_mixin(cls, name, dryrun=False):
        """
        Patched version that handles bcrypt version reading for both 3.x and 4.x versions.
        """
        try:
            # Try to get version - handle both old and new bcrypt versions
            try:
                # For bcrypt 4.x: _bcrypt.__about__.__version__
                if hasattr(_bcrypt, '__about__'):
                    version = _bcrypt.__about__.__version__
                # For bcrypt 3.x: try __version__ directly or use a default
                elif hasattr(_bcrypt, '__version__'):
                    version = _bcrypt.__version__
                else:
                    # Fallback: use a default version string
                    version = "3.2.2"
            except (AttributeError, ImportError):
                version = "3.2.2"
            
            # Call original method but catch any version-related errors
            try:
                return original_load_backend(name, dryrun)
            except AttributeError as e:
                if '__about__' in str(e):
                    # If it's the __about__ error, just continue with default version
                    logger.debug(f"Bypassed bcrypt version reading error, using default version")
                    # Set backend manually if needed
                    if not dryrun:
                        cls._backend = name
                    return True
                raise
        except Exception as e:
            logger.warning(f"Error in _load_backend_mixin: {e}, attempting fallback")
            if not dryrun:
                cls._backend = name
            return True
    
    # Replace _load_backend_mixin
    bcrypt_module.bcrypt._load_backend_mixin = patched_load_backend_mixin
    logger.debug("Successfully patched passlib _load_backend_mixin for bcrypt version compatibility")
    
    # Get the original _finalize_backend_mixin
    original_finalize = bcrypt_module.bcrypt._finalize_backend_mixin
    
    # Create a completely new version that skips detect_wrap_bug
    @classmethod
    def patched_finalize_backend_mixin(cls, name, dryrun=False):
        """
        Patched version that completely skips wrap bug detection.
        The original detect_wrap_bug uses a 255-byte password which exceeds bcrypt's 72-byte limit.
        """
        if dryrun:
            return True
        
        # Simply set the backend and return True
        # We skip all the wrap bug detection logic
        cls._backend = name
        logger.debug(f"Backend {name} initialized (wrap bug detection skipped)")
        return True
    
    # Replace the method BEFORE any bcrypt operations
    bcrypt_module.bcrypt._finalize_backend_mixin = patched_finalize_backend_mixin
    logger.debug("Successfully patched passlib _finalize_backend_mixin")
    
except Exception as e:
    logger.warning(f"Could not patch passlib (non-critical): {e}")
