from typing import Any, Dict, Optional


def reduced_datum_value(mag: float,
                        filter: str,
                        error: float,
                        jd: float,
                        observer: Optional[str] = None,
                        facility: Optional[str] = None,
                        hjd: Optional[float] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "magnitude": mag,
        "filter": filter,
        "error": error,
        "jd": jd
    }

    if observer:
        result["observer"] = observer
    if facility:
        result["facility"] = facility
    if hjd:
        result["hjd"] = hjd

    return result


def reduced_datum_non_detection_value(limit: float,
                                      filter: str,
                                      jd: float,
                                      observer: Optional[str] = None,
                                      facility: Optional[str] = None,
                                      hjd: Optional[float] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "limit": limit,
        "filter": filter,
        "jd": jd
    }

    if observer:
        result["observer"] = observer
    if facility:
        result["facility"] = facility
    if hjd:
        result["hjd"] = hjd

    return result