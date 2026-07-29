import os
import json
import uuid
import requests
from tools._shared import TIMEOUT, domain, err

def search_apartments(location: str = "", min_price: int = 0, max_price: int = 100000000, room_type: str = "phong_tro") -> dict:
    """
    Tìm kiếm nhà trọ hoặc căn hộ cho thuê thực tế bằng cách dùng Tavily Search API 
    (tìm trên các trang bất động sản).
    """
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return {"status": "error", "message": "Missing TAVILY_API_KEY env var để tìm dữ liệu thực."}
        
    room_str = room_type.replace("_", " ")
    price_str = f"giá từ {min_price//1000000} đến {max_price//1000000} triệu"
    
    query = f"Cho thuê {room_str} tại {location} {price_str} mới nhất"
    
    try:
        body = {
            "query": query, 
            "topic": "general", 
            "max_results": 5, 
            "search_depth": "advanced"
        }
        response = requests.post(
            "https://api.tavily.com/search",
            json=body,
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for i, item in enumerate(data.get("results", [])):
            # Tạo ID giả từ URL để dùng cho get_apartment_details
            apt_id = f"APT-REAL-{uuid.uuid4().hex[:6].upper()}"
            results.append({
                "id": apt_id,
                "title": item.get("title"),
                "location": location,
                "price_estimate": price_str,
                "room_type": room_type,
                "summary": item.get("content"),
                "url": item.get("url"), # Lưu URL để get_details
                "source": domain(item.get("url", ""))
            })
            
        return {
            "status": "success",
            "total_results": len(results),
            "query": query,
            "results": results
        }
    except Exception as exc:
        return err("search_apartments", exc)


def get_apartment_details(apartment_id: str) -> dict:
    """
    Trong thực tế, khi có URL của phòng trọ, ta dùng thư viện requests/BeautifulSoup để cào (scrape) 
    chi tiết diện tích, sđt chủ nhà. Ở đây ta trả về hướng dẫn để Agent biết URL.
    (Do Agent không truyền URL mà truyền ID, ta cần map ID -> URL. Để đơn giản, 
    nếu là APT-REAL, báo Agent dùng fetch để đọc trực tiếp URL từ kết quả trước).
    """
    return {
        "status": "info",
        "message": f"Dữ liệu đang được lấy từ web thực tế. Hãy dùng công cụ `fetch` để đọc chi tiết từ URL của phòng có ID {apartment_id} từ kết quả tìm kiếm trước đó, hoặc giải thích tổng quan dựa vào summary."
    }

def book_viewing(apartment_id: str, customer_name: str, phone_number: str, viewing_time: str) -> dict:
    """
    Đặt lịch hẹn đến xem nhà trọ/căn hộ.
    """
    booking_id = f"BK-{uuid.uuid4().hex[:6].upper()}"
    
    return {
        "status": "success",
        "message": "Ghi nhận yêu cầu đặt lịch hệ thống (Mô phỏng)!",
        "booking_info": {
            "booking_id": booking_id,
            "apartment_id": apartment_id,
            "customer_name": customer_name,
            "phone_number": phone_number,
            "viewing_time": viewing_time,
            "note": "Hệ thống sẽ liên hệ chủ nhà thực tế qua SĐT trên web và gửi lại SMS xác nhận cho bạn."
        }
    }
