from ctypes import Structure, c_char
from dataclasses import dataclass

from ..common import OutBlock


class CTj8OutBlock(Structure):
    _fields_ = [
        ("code", c_char * 6), # 종목코드
        ("_code", c_char * 1),
        ("time", c_char * 8), # 시간
        ("_time", c_char * 1),
        ("sign", c_char * 1), # 등락부호
        ("_sign", c_char * 1),
        ("change", c_char * 6), # 등락폭
        ("_change", c_char * 1),
        ("price", c_char * 7), # 현재가
        ("_price", c_char * 1),
        ("chrate", c_char * 5), # 등락률
        ("_chrate", c_char * 1),
        ("high", c_char * 7), # 고가
        ("_high", c_char * 1),
        ("low", c_char * 7), # 저가
        ("_low", c_char * 1),
        ("offer", c_char * 7), # 매도호가
        ("_offer", c_char * 1),
        ("bid", c_char * 7), # 매수호가
        ("_bid", c_char * 1),
        ("volume", c_char * 9), # 거래량
        ("_volume", c_char * 1),
        ("volrate", c_char * 6), # 거래량전일비
        ("_volrate", c_char * 1),
        ("movolume", c_char * 8), # 변동거래량
        ("_movolume", c_char * 1),
        ("value", c_char * 9), # 거래대금
        ("_value", c_char * 1),
        ("open", c_char * 7), # 시가
        ("_open", c_char * 1),
        ("avgprice", c_char * 7), # 가중평균가
        ("_avgprice", c_char * 1),
        ("janggubun", c_char * 1), # 장구분
        ("_janggubun", c_char * 1),
    ]

@dataclass
class Tj8OutBlock(OutBlock):
    """코스피/코스닥 체결 시세(j8) 데이터 블록
    Attributes:
        code: 종목코드
        time: 시간
        sign: 등락부호
        change: 등락폭
        price: 현재가
        chrate: 등락률
        high: 고가
        low: 저가
        offer: 매도호가
        bid: 매수호가
        volume: 거래량
        volrate: 거래량전일비
        movolume: 변동거래량
        value: 거래대금
        open: 시가
        avgprice: 가중평균가
        janggubun: 장구분
    """
    code: str
    time: str
    sign: str
    change: str
    price: str
    chrate: str
    high: str
    low: str
    offer: str
    bid: str
    volume: str
    volrate: str
    movolume: str
    value: str
    open: str
    avgprice: str
    janggubun: str


__all__ = [
    "CTj8OutBlock",
    "Tj8OutBlock",
]