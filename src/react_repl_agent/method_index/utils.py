import re
from typing import Optional

from .doc_utils import get_signature


def extract_method_name_from_type_error(error: TypeError) -> Optional[str]:
    """Extract method name from TypeError message."""
    msg = error.args[0]
    match = re.match(r"^([^\W0-9]\w*)\(", msg)
    if match:
        return match.group(1)
    return None


def extract_method_signature_from_type_error(
    error: TypeError, context: dict
) -> Optional[str]:
    """Extract method signature from TypeError message."""
    method_name = extract_method_name_from_type_error(error)
    if method_name and method_name in context:
        return get_signature(context[method_name])
    return None
