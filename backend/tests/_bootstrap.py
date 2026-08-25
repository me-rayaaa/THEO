import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent


def setup_backend_path():
    backend_path = str(BACKEND_DIR)

    if backend_path not in sys.path:
        sys.path.insert(
            0,
            backend_path
        )


setup_backend_path()