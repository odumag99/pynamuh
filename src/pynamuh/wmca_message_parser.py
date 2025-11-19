#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMCA 메시지 파싱 전담 모듈
Windows 메시지 lparam을 파싱하여 Python 객체로 변환
"""

from .structures.common import LoginBlock, OutDataBlock
from .wmca_logger import get_logger

logger = get_logger()


# ============================================================================
# WMCAMessageParser 클래스
# ============================================================================

class WMCAMessageParser:
    """WMCA 메시지 파싱 전담 클래스

    lparam → DTO 변환만 담당합니다.
    실제 파싱 로직은 각 DTO의 from_lparam/from_c_struct 메서드에 있습니다.
    """

    @staticmethod
    def parse_loginblock(lparam: int) -> LoginBlock:
        """CA_CONNECTED 메시지 파싱

        Args:
            lparam: LOGINBLOCK 구조체 포인터

        Returns:
            LoginBlock DTO
        """
        return LoginBlock.from_lparam(lparam)
    
    @staticmethod
    def parse_outdatablock(
        lparam: int, 
        is_receivemessage: bool = False, 
        is_receivesise: bool = False
    ) -> OutDataBlock:
        """CA_CONNECTED 메시지 파싱

        Args:
            lparam: OUTDATABLOCK 구조체 포인터

        Returns:
            OutDataBlock DTO
        """
        return OutDataBlock.from_lparam(lparam, is_receivemessage, is_receivesise)