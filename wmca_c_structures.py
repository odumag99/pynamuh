#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMCA C 구조체 정의
NH투자증권 WMCA DLL이 사용하는 C 구조체들을 ctypes로 정의
"""

import ctypes
from ctypes import POINTER


# ============================================================================
# 로그인 관련 구조체
# ============================================================================

class CAccountInfo(ctypes.Structure):
    """C 구조체: ACCOUNTINFO (계좌 정보)

    크기: 256 bytes
    """
    _fields_ = [
        ("szAccountNo", ctypes.c_char * 11),      # 계좌번호
        ("szAccountName", ctypes.c_char * 40),    # 계좌명
        ("act_pdt_cdz3", ctypes.c_char * 3),      # 상품코드
        ("amn_tab_cdz4", ctypes.c_char * 4),      # 관리점코드
        ("expr_datez8", ctypes.c_char * 8),       # 계좌만료일
        ("granted", ctypes.c_char),               # 미결제주문 권한여부 (G:가능)
        ("filler", ctypes.c_char * 189),          # filler
    ]


class CLoginInfo(ctypes.Structure):
    """C 구조체: LOGININFO (로그인 정보)

    크기: 255,784 bytes
    """
    _fields_ = [
        ("szDate", ctypes.c_char * 14),           # 접속시간 (14자리)
        ("szServerName", ctypes.c_char * 15),     # 서버명
        ("szUserID", ctypes.c_char * 8),          # 사용자ID
        ("szAccountCount", ctypes.c_char * 3),    # 계좌수 (3자리)
        ("accountlist", CAccountInfo * 999),      # 계좌 리스트 (최대 999개)
    ]


class CLoginBlock(ctypes.Structure):
    """C 구조체: LOGINBLOCK (로그인 블록)

    크기: 8 bytes
    """
    _fields_ = [
        ("TrIndex", ctypes.c_int),                # 트랜잭션 인덱스
        ("pLoginInfo", POINTER(CLoginInfo)),      # 로그인 정보 포인터
    ]


# ============================================================================
# 메시지 관련 구조체
# ============================================================================

class CMsgHeader(ctypes.Structure):
    """C 구조체: MSGHEADER (메시지 헤더)

    서버 메시지용 구조체
    """
    _fields_ = [
        ("msg_cd", ctypes.c_char * 5),      # 메시지 코드 (00000: 정상, 기타: 오류)
        ("user_msg", ctypes.c_char * 80),   # 사용자 메시지
    ]


# ============================================================================
# TR 데이터 관련 구조체
# ============================================================================

class CReceived(ctypes.Structure):
    """C 구조체: RECEIVED (수신 데이터)

    TR 조회 결과 또는 실시간 데이터
    """
    _fields_ = [
        ("szBlockName", POINTER(ctypes.c_char_p)),   # 블록 이름 포인터
        ("szData", POINTER(ctypes.c_char)),        # 데이터 포인터
        ("nLen", ctypes.c_int),             # 데이터 길이
    ]


class COutDataBlock(ctypes.Structure):
    """C 구조체: OUTDATABLOCK (출력 데이터 블록)

    TR 조회 응답 블록
    """
    _fields_ = [
        ("TrIndex", ctypes.c_int),          # 트랜잭션 인덱스
        ("pData", POINTER(CReceived)),      # 데이터 포인터
    ]
