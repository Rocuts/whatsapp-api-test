from importlib import util as _importlib_util
from pathlib import Path as _Path

_MODULE_PATH = _Path(__file__).parent / "agentes-ia" / "whatsapp-webhook" / "main.py"
_SPEC = _importlib_util.spec_from_file_location("whatsapp_webhook_main", _MODULE_PATH)
_MODULE = _importlib_util.module_from_spec(_SPEC)
if _SPEC and _SPEC.loader:
    _SPEC.loader.exec_module(_MODULE)
else:
    raise ImportError(f"Unable to load module from {_MODULE_PATH}")

app = getattr(_MODULE, "app")
