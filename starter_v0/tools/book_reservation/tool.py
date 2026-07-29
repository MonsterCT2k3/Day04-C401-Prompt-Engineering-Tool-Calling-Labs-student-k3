from __future__ import annotations

import uuid
from typing import Any


def book_reservation(place_name: str = "", when: str = "", party_size: int = 2, confirmed: bool = False) -> dict[str, Any]:
    """Reserve a table/slot at a place found via place_search. Simulated booking (no real backend) — only commits when confirmed=True."""
    if not place_name or not when:
        return {
            "tool": "book_reservation",
            "status": "missing_info",
            "message": "Cần tên địa điểm và thời gian (ngày giờ) để đặt chỗ.",
        }
    if not confirmed:
        return {
            "tool": "book_reservation",
            "status": "needs_confirmation",
            "place_name": place_name,
            "when": when,
            "party_size": party_size,
            "message": "Chỉ xác nhận đặt chỗ sau khi người dùng đồng ý (yes_no).",
        }
    return {
        "tool": "book_reservation",
        "status": "reserved",
        "place_name": place_name,
        "when": when,
        "party_size": party_size,
        "confirmation_code": f"RES-{uuid.uuid4().hex[:6].upper()}",
        "message": "Đây là booking mô phỏng cho demo — chưa kết nối hệ thống đặt chỗ thật.",
    }
