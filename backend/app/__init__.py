"""
Interactive Estimation System Backend
------------------------------------
A FastAPI backend for an interactive service estimation system.
"""

import warnings

# Filter out PydanticSchemaJson warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/object/apply:.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*tag:yaml.org,2002:python/.*", category=UserWarning)

__version__ = "0.1.0"
