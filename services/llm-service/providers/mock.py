from __future__ import annotations

from config.prompts import detect_topic

_MOCK_RESPONSES: dict[str, str] = {
    "greeting": (
        "Chao con! Minh la LumiEdu, gia su Toan lop 6 cua con. "
        "Hom nay con muon hoc ve chu de gi nao?"
    ),
    "empty": (
        "Con dang gap bai nao? "
        "Minh se goi y tung buoc de con tu giai nhe!"
    ),
    "phan_so": (
        "Con dang lam bai ve phan so phai khong? Rat tot! "
        "Buoc dau tien, con thu xac dinh tu so va mau so cua cac phan so trong bai. "
        "Sau do minh se cung tim mau so chung nhe!"
    ),
    "so_thap_phan": (
        "Bai so thap phan nay thu vi day! "
        "Con thu nhin xem so thap phan nay co bao nhieu chu so sau dau phay? "
        "Tu do minh se cung chuyen doi nhe!"
    ),
    "so_nguyen": (
        "So nguyen la chu de quan trong! "
        "Con thu ve truc so ra giay va danh dau cac so nguyen trong bai. "
        "Nhu vay minh se de hinh dung hon! Con thu di nhe?"
    ),
    "hinh_hoc": (
        "Bai hinh hoc nay thu vi day! "
        "Con thu ve hinh ra giay truoc nhe. "
        "Sau do xac dinh cac yeu to da biet nhu do dai canh, goc. "
        "Minh se goi y buoc tiep theo!"
    ),
    "phep_tinh": (
        "Bai phep tinh nay can can than! "
        "Con nho thu tu thuc hien phep tinh khong? "
        "Nhan chia truoc, cong tru sau, va ngoac don lam truoc nhat. "
        "Con thu ap dung xem nhe!"
    ),
    "ti_so": (
        "Bai ti so va ti le thuc! "
        "Con thu doc ky de bai va xac dinh hai dai luong can lap ti so. "
        "Sau do minh se cung tim cach giai nhe!"
    ),
    "default": (
        "Minh hieu cau hoi cua con roi! "
        "Thu voi buoc 1: doc ky de bai va xac dinh xem de dang hoi gi nhe. "
        "Sau do noi cho minh cach con se bat dau?"
    ),
}


class MockProvider:
    @staticmethod
    def respond(transcript: str) -> str:
        if not transcript.strip():
            return _MOCK_RESPONSES["empty"]

        lower = transcript.lower()
        if any(kw in lower for kw in ["chao", "xin chao", "hello", "hi"]):
            return _MOCK_RESPONSES["greeting"]

        topic = detect_topic(transcript)
        if topic and topic in _MOCK_RESPONSES:
            return _MOCK_RESPONSES[topic]

        return _MOCK_RESPONSES["default"]
