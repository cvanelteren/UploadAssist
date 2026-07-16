"""UploadAssist public API."""

from ._version import __version__
from .deps import collect, get_deps

__all__ = ["__version__", "collect", "get_deps"]
