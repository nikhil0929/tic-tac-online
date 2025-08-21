from sqlalchemy.orm import DeclarativeBase
import sys
import importlib
import pathlib
from .base import Base

# Automatically import all model files
models_dir = pathlib.Path(__file__).parent
for model_file in models_dir.glob("*.py"):
    if model_file.name not in ["__init__.py", "base.py"]:
        module_name = model_file.stem  # Remove .py extension
        importlib.import_module(f".{module_name}", package=__name__)

# Get all classes that inherit from Base

__all__ = ['Base']
# Use a list to avoid dictionary iteration issues
module_dict = globals().copy()
for name, obj in module_dict.items():
    if (isinstance(obj, type) and
        issubclass(obj, DeclarativeBase) and
        obj != DeclarativeBase and
            obj != Base):
        __all__.append(name)
