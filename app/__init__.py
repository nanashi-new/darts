"""Application package for the Darts Rating EBCK desktop app."""

from app.build_info import load_build_info


_BUILD_INFO = load_build_info()

__version__ = _BUILD_INFO.version
__build_info__ = f"{_BUILD_INFO.packaging_mode}:{_BUILD_INFO.git_revision}"
__build_metadata__ = _BUILD_INFO
