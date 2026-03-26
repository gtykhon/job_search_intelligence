import re
from typing import Any, Dict, List

try:
    import ftfy  # type: ignore
except Exception:  # pragma: no cover
    ftfy = None  # fallback


def fix_mojibake(text: str) -> str:
    """Repair common UTF-8→cp1252/latin-1 mojibake and map known sequences.

    - Prefer ftfy if available.
    - Otherwise, try cp1252->utf-8, then latin-1->utf-8.
    - Replace specific legacy sequences we've observed in data.
    """
    if not isinstance(text, str):
        return text

    # Use ftfy if installed
    if ftfy is not None:
        try:
            text = ftfy.fix_text(text)
        except Exception:
            pass

    # Fast path: only try if suspicious bytes are present
    if any(ch in text for ch in ('\u00f0', '\u00e2', '\ufffd', 'ð', 'â', '')):
        for enc in ('cp1252', 'latin-1'):
            try:
                text = text.encode(enc, 'strict').decode('utf-8', 'strict')
                break
            except Exception:
                continue

    # Known partial sequences (map to codepoints)
    replacements: Dict[str, str] = {
        'ðŸ“ˆ': '\U0001F4C8',  # 📈
        'ðŸŽª': '\U0001F3AA',  # 🎪
        'ðŸ“Š': '\U0001F4CA',  # 📊
        'ðŸ’ª': '\U0001F4AA',  # 💪
        'ðŸ‘”': '\U0001F454',  # 👔
        'ðŸ¤': '\U0001F91D',  # 🤝
        'ðŸ¢': '\U0001F3C6',  # 🏆
        'ðŸ­': '\U0001F3E2',  # 🏢
        'ðŸ’¡': '\U0001F4A1',  # 💡
        'ðŸ‘¥': '\U0001F465',  # 👥
        'ðŸŒ':  '\U0001F30D',  # 🌍 (fallback for partial)
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


def sanitize_obj(obj: Any) -> Any:
    """Recursively fix mojibake in dict/list/str values."""
    if isinstance(obj, dict):
        return {sanitize_obj(k): sanitize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_obj(x) for x in obj]
    if isinstance(obj, str):
        return fix_mojibake(obj)
    return obj


class AsciiLogFilter:
    """Logging filter that strips non-ASCII (keeps logs readable on cp1252 consoles)."""

    def filter(self, record) -> bool:  # pragma: no cover
        try:
            msg = str(record.getMessage())
            # Drop emoji/non-ASCII to avoid mojibake in Windows console
            safe = msg.encode('ascii', 'ignore').decode('ascii', 'ignore')
            record.msg = safe
            record.args = ()
        except Exception:
            pass
        return True


def install_ascii_logging_filter(logger) -> None:  # pragma: no cover
    try:
        # Avoid duplicating filters
        if not any(isinstance(f, AsciiLogFilter) for f in getattr(logger, 'filters', [])):
            logger.addFilter(AsciiLogFilter())
    except Exception:
        pass

