#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMCA Common Structures and DTOs

C Structures paired with their corresponding Pydantic Models for better readability
"""
from abc import ABC
import ctypes
from ctypes import Structure, POINTER
from typing import ClassVar, Optional, List, Type, Union, Tuple
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from .parser_info import get_parser_info
from ..wmca_logger import logger

# ============================================================================
# 1. AccountInfo
# ============================================================================

class CAccountInfo(Structure):
    """C 구조체: ACCOUNTINFO (계좌 정보)
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

@dataclass
class AccountInfo:
    """계좌 정보 DTO"""
    szAccountNo: str         # 계좌번호
    szAccountName: str       # 계좌명
    act_pdt_cdz3: str        # 상품코드
    amn_tab_cdz4: str        # 관리점코드
    expr_datez8: str         # 계좌만료일
    granted: str             # 미결제주문 권한여부 (G:가능)

    @classmethod
    def from_c_struct(cls, c_struct: CAccountInfo) -> 'AccountInfo':
        """C 구조체로부터 파싱

        Args:
            c_struct: CAccountInfo C 구조체

        Returns:
            AccountInfo DTO
        """
        return cls(
            szAccountNo=c_struct.szAccountNo.decode('cp949', errors='ignore').strip(),
            szAccountName=c_struct.szAccountName.decode('cp949', errors='ignore').strip(),
            act_pdt_cdz3=c_struct.act_pdt_cdz3.decode('cp949', errors='ignore').strip(),
            amn_tab_cdz4=c_struct.amn_tab_cdz4.decode('cp949', errors='ignore').strip(),
            expr_datez8=c_struct.expr_datez8.decode('cp949', errors='ignore').strip(),
            granted=c_struct.granted.decode('cp949', errors='ignore').strip(),
        )

# ============================================================================
# 2. LoginInfo
# ============================================================================

class CLoginInfo(Structure):
    """C 구조체: LOGININFO (로그인 정보)
    """
    _fields_ = [
        ("szDate", ctypes.c_char * 14),           # 접속시간 (14자리)
        ("szServerName", ctypes.c_char * 15),     # 서버명
        ("szUserID", ctypes.c_char * 8),          # 사용자ID
        ("szAccountCount", ctypes.c_char * 3),    # 계좌수 (3자리)
        ("accountlist", CAccountInfo * 999),      # 계좌 리스트 (최대 999개)
    ]


@dataclass
class LoginInfo:
    """로그인 정보 DTO"""
    szDate: str              # 접속시간 (14자리)
    szServerName: str        # 서버명
    szUserID: str            # 사용자ID
    szAccountCount: str      # 계좌수 (3자리 문자열)
    accountlist: List[AccountInfo]  # 계좌 리스트

    @classmethod
    def from_c_struct(cls, c_struct: CLoginInfo) -> 'LoginInfo':
        """C 구조체로부터 파싱

        Args:
            c_struct: CLoginInfo C 구조체

        Returns:
            LoginInfo DTO
        """
        # 계좌수 파싱
        szAccountCount = c_struct.szAccountCount.decode('cp949', errors='ignore').strip()
        account_count = int(szAccountCount) if szAccountCount and szAccountCount.isdigit() else 0

        logger.debug(f"접속시간: {c_struct.szDate.decode('cp949', errors='ignore').strip()}")
        logger.debug(f"서버명: {c_struct.szServerName.decode('cp949', errors='ignore').strip()}")
        logger.debug(f"사용자ID: {c_struct.szUserID.decode('cp949', errors='ignore').strip()}")
        logger.debug(f"계좌수: {account_count}")

        # 계좌 목록 파싱
        accountlist = []
        for i in range(min(account_count, 999)):
            acc = AccountInfo.from_c_struct(c_struct.accountlist[i])
            if acc.szAccountNo:  # 계좌번호가 있는 경우만
                accountlist.append(acc)
                logger.debug(f"계좌[{i+1}]: {acc.szAccountNo} - {acc.szAccountName}")

        return cls(
            szDate=c_struct.szDate.decode('cp949', errors='ignore').strip(),
            szServerName=c_struct.szServerName.decode('cp949', errors='ignore').strip(),
            szUserID=c_struct.szUserID.decode('cp949', errors='ignore').strip(),
            szAccountCount=szAccountCount,
            accountlist=accountlist
        )



# ============================================================================
# 3. LoginBlock
# ============================================================================

class CLoginBlock(Structure):
    """C 구조체: LOGINBLOCK (로그인 블록)

    크기: 8 bytes
    """
    _fields_ = [
        ("TrIndex", ctypes.c_int),                # 트랜잭션 인덱스
        ("pLoginInfo", POINTER(CLoginInfo)),      # 로그인 정보 포인터
    ]


@dataclass
class LoginBlock:
    """로그인 블록 DTO"""
    TrIndex: int                       # 트랜잭션 인덱스
    pLoginInfo: Optional[LoginInfo]    # 로그인 정보 (NULL일 수 있음)

    @classmethod
    def from_lparam(cls, lparam: int) -> 'LoginBlock':
        """lparam으로부터 파싱

        Args:
            lparam: LOGINBLOCK 구조체 포인터

        Returns:
            LoginBlock DTO

        CRITICAL: lparam이 가리키는 메모리는 이 메서드가 반환된 후 DLL이 해제합니다.
        따라서 즉시 파싱하고 Python 객체로 복사해야 합니다.
        """
        logger.debug("LoginBlock 파싱 시작 (즉시)")

        if not lparam:
            logger.error("lparam이 NULL")
            raise ValueError("lparam이 NULL입니다")

        try:
            c_block = ctypes.cast(lparam, POINTER(CLoginBlock)).contents
            TrIndex = c_block.TrIndex
            logger.debug(f"LoginBlock.TrIndex = {TrIndex}")

            if not c_block.pLoginInfo:
                logger.error("pLoginInfo가 NULL")
                raise ValueError("pLoginInfo가 NULL입니다")
            
            pLoginInfo = LoginInfo.from_c_struct(c_block.pLoginInfo.contents)

            return cls(
                TrIndex=TrIndex,
                pLoginInfo=pLoginInfo
            )

        except Exception as e:
            logger.error("LoginBlock 파싱 오류: %s", e, exc_info=True)
            raise

# ============================================================================
# szData 공통 클래스
# ============================================================================

@dataclass
class OutBlock:
    """
    OutBlock 기본 클래스 (Python dataclass)

    모든 szData OutBlock은 이 클래스를 상속받아야 합니다.
    - Python dataclass: 단순하고 빠른 데이터 컨테이너
    - C_STRUCT: 각 서브클래스에서 Structure 타입 지정 (ClassVar)
    - from_c_struct(): Structure → Python 객체 변환 (공통 구현)
    """

    @classmethod
    def from_c_struct(cls, c_struct: Structure) -> 'OutBlock':
        """
        C 구조체 → Python 객체 변환

        공통 변환 로직:
        1. dataclass 필드 목록 조회 (__dataclass_fields__)
        2. 각 필드에 대응하는 C 구조체 필드 읽기 (필드명 동일)
        3. bytes → str 변환 (cp949 디코딩, 공백 제거)
        4. dataclass 인스턴스 생성

        Returns:
            OutBlock: 파싱된 데이터 객체

        Example:
            >>> c_struct = Tc8201OutBlockCStruct(...)
            >>> outblock = Tc8201OutBlock.from_c_struct(c_struct)
            >>> print(outblock.dpsit_amtz16)  # "1000000"
        """
        logger.debug("OutBlock 파싱 시작. cls=%s", cls.__name__)
        parsed_data = {}

        # dataclass 필드 순회 (속성 바이트 필드는 자동으로 제외됨)
        if hasattr(cls, '__dataclass_fields__'):
            field_names = cls.__dataclass_fields__.keys()
        else:
            # dataclass가 아닌 경우 (하위 호환성)
            raise TypeError(f"{cls.__name__}은 @dataclass로 정의되어야 합니다")

        for field_name in field_names:
            try:
                c_value = getattr(c_struct, field_name)
            except AttributeError:
                logger.warning(f"C 구조체에 필드 없음: {field_name}")
                continue

            # bytes → str 변환 (cp949 디코딩, 공백 제거)
            if isinstance(c_value, bytes):
                str_value = c_value.decode('cp949', errors='ignore').strip()
            else:
                str_value = str(c_value).strip()

            parsed_data[field_name] = str_value

        result = cls(**parsed_data)
        logger.debug("OutBlock 파싱 완료. result: %s", result)
        return result



# ============================================================================
# 4. MessageHeader
# ============================================================================

class CMsgHeader(Structure):
    """C 구조체: MSGHEADER (메시지 헤더)

    서버 메시지용 구조체
    """
    _fields_ = [
        ("msg_cd", ctypes.c_char * 5),      # 메시지 코드 (00000: 정상, 기타: 오류)
        ("user_msg", ctypes.c_char * 80),   # 사용자 메시지
    ]

@dataclass
class MsgHeader(OutBlock):
    """메시지 헤더 DTO"""
    msg_cd: str          # 메시지 코드 (00000: 정상, 기타: 오류)
    user_msg: str        # 사용자 메시지


# ============================================================================
# 5. Received
# ============================================================================

class CReceived(Structure):
    """C 구조체: RECEIVED (수신 데이터)

    TR 조회 결과 또는 실시간 데이터
    """
    _fields_ = [
        ("szBlockName", POINTER(ctypes.c_char_p)),   # 블록 이름 포인터
        ("szData", POINTER(ctypes.c_char)),        # 데이터 포인터
        ("nLen", ctypes.c_int),             # 데이터 길이
    ]

@dataclass
class Received:
    """TR 수신 데이터 DTO

    szData의 3가지 상태:
        1. 파싱 전: bytes (원시 바이너리)
        2. 단일 레코드 파싱 후: OutBlock (예: Tc8201OutBlock)
        3. 반복 레코드 파싱 후: List[OutBlock] (예: List[Tc8201OutBlock1])

    Example:
        >>> # from_c_struct()가 자동으로 파싱
        >>> received = Received.from_c_struct(c_struct, auto_parse=True)
        >>>
        >>> # c8201OutBlock (단일 레코드)
        >>> if received.szBlockName == "c8201OutBlock":
        ...     account: Tc8201OutBlock = received.szData
        ...     print(f"예수금: {account.dpsit_amtz16}")
        >>>
        >>> # c8201OutBlock1 (반복 레코드)
        >>> elif received.szBlockName == "c8201OutBlock1":
        ...     stocks: List[Tc8201OutBlock1] = received.szData
        ...     for stock in stocks:
        ...         print(f"{stock.issue_namez40}: {stock.jan_qtyz16}주")
    """
    szBlockName: str                                    # 블록 이름
    szData: Union[OutBlock, List[OutBlock], bytes]     # 파싱된 데이터 또는 bytes
    nLen: int                                           # 데이터 길이

    @classmethod
    def from_c_struct(
        cls,
        c_struct: CReceived,
        is_receivemessage: bool = False,
        is_receivesise: bool = False,
        auto_parse: bool = True
    ) -> 'Received':
        """C 구조체로부터 Received 생성

        Args:
            c_struct: CReceived C 구조체
            auto_parse: True면 szBlockName에 따라 자동 파싱

        Returns:
            Received[T]: 파싱된 데이터 또는 bytes

        Example:
            >>> # 자동 파싱 (기본값)
            >>> received = Received.from_c_struct(c_struct)
            >>> # szData는 이미 C8201Received 또는 List[...] 타입
            >>>
            >>> # 파싱 안 함 (bytes 그대로)
            >>> received = Received.from_c_struct(c_struct, auto_parse=False)
            >>> # szData는 bytes
        """
        if is_receivesise:
            # ca_receivesise는 szBlockName 파싱 시 특수 케이스 -> szBlockName이 가리키는 char 배열에 '\0'이 없어 앞 글자 2개만 추출해야 함.
            szBlockName = ctypes.string_at(c_struct.szBlockName, 2)\
                .decode('cp949', errors='ignore').strip() if c_struct.szBlockName else ""
            szData_bytes = ctypes.string_at(c_struct.szData[3:c_struct.nLen]) if c_struct.szData else b""
        else:
            szBlockName = ctypes.string_at(c_struct.szBlockName)\
                .decode('cp949', errors='ignore').strip() if c_struct.szBlockName else ""
            szData_bytes = ctypes.string_at(c_struct.szData, c_struct.nLen) if c_struct.szData else b""
        
        nLen = c_struct.nLen
        logger.debug("Received.from_c_struct(szBlockName=%s, szData_bytes=%s, nLen=%d, auto_parse=%s)", szBlockName, szData_bytes, nLen, auto_parse)
        if not auto_parse:
            # 파싱 안 함 (bytes 그대로 반환)
            return cls(
                szBlockName=szBlockName,
                szData=szData_bytes,
                nLen=nLen
            )
        else:
            # ca_receivemessage는 특수 케이스 -> szData를 MsgHeader로 파싱
            if is_receivemessage:
                szData = MsgHeader.from_c_struct(ctypes.cast(c_struct.szData, POINTER(CMsgHeader)).contents)
                logger.debug("Received 파싱 완료. type(szData)=%s", type(szData).__name__)
                return cls(
                    szBlockName=szBlockName,
                    szData=szData,
                    nLen=nLen
                )

            # szBlockName에 따라 자동 파싱
            return cls._auto_parse(szBlockName, szData_bytes, nLen, is_receivemessage)

    @classmethod
    def _auto_parse(cls, block_name: str, data_bytes: bytes, nLen: int, is_receivemessage: bool = False) -> 'Received':
        """블록 이름에 따라 자동 파싱

        Args:
            block_name: szBlockName (예: "c8201OutBlock")
            data_bytes: szData (bytes)
            nLen: 데이터 길이

        Returns:
            Received[T]: 파싱된 데이터를 담은 Received 인스턴스
        """
        # 파서 정보 조회
        if is_receivemessage:
            parser_info = (CMsgHeader, MsgHeader, False)
        else:
            try:
                parser_info = get_parser_info(block_name)
            except ValueError:
                logger.debug("파서 미등록: %s, bytes로 반환. nLen=%d, szData=%s", block_name, nLen, data_bytes)
                parser_info = None

        if not parser_info:
            # parser_info가 None인 경우 → bytes 그대로
            return cls(
                szBlockName=block_name,
                szData=data_bytes,
                nLen=nLen
            )

        struct_class, model_class, is_array = parser_info

        if is_array:
            # 반복 레코드 파싱
            parsed_data = cls._parse_array_internal(
                data_bytes, nLen, struct_class, model_class
            )
        else:
            # 단일 레코드 파싱
            parsed_data = cls._parse_single_internal(
                data_bytes, struct_class, model_class
            )
        logger.debug("Received _auto_parse 완료. type(szData)=%s", type(parsed_data).__name__)

        return cls(
            szBlockName=block_name,
            szData=parsed_data,  # T or List[T]
            nLen=nLen
        )


    @staticmethod
    def _parse_single_internal(
        data_bytes: bytes,
        struct_class: Type[Structure],
        model_class: Type['OutBlock']
    ) -> 'OutBlock':
        """단일 레코드 내부 파싱 로직

        Args:
            data_bytes: 원시 바이너리 데이터
            struct_class: Structure 클래스
            model_class: OutBlock 서브클래스

        Returns:
            OutBlock 인스턴스
        """
        struct_size = ctypes.sizeof(struct_class)

        if len(data_bytes) < struct_size:
            raise ValueError(
                f"데이터 크기 부족: len={len(data_bytes)}, "
                f"required={struct_size} (struct={struct_class.__name__})"
            )

        # bytes → Structure
        c_struct = struct_class.from_buffer_copy(data_bytes[:struct_size])

        # Structure → OutBlock (OutBlock.from_c_struct 공통 메서드 사용)
        parsed_model = model_class.from_c_struct(c_struct)

        return parsed_model

    @staticmethod
    def _parse_array_internal(
        data_bytes: bytes,
        nLen: int,
        struct_class: Type[Structure],
        model_class: Type['OutBlock']
    ) -> List['OutBlock']:
        """반복 레코드 내부 파싱 로직

        Args:
            data_bytes: 원시 바이너리 데이터
            nLen: 데이터 길이
            struct_class: Structure 클래스
            model_class: OutBlock 서브클래스

        Returns:
            List[OutBlock]: 파싱된 모델 리스트
        """
        struct_size = ctypes.sizeof(struct_class)

        if struct_size == 0:
            raise ValueError(f"구조체 크기가 0: {struct_class.__name__}")

        # 반복 횟수 계산 (C++ 예제와 동일)
        occurs_count = nLen // struct_size

        logger.debug(
            f"parse_array_internal: struct={struct_class.__name__}, "
            f"struct_size={struct_size}, nLen={nLen}, "
            f"occurs_count={occurs_count}"
        )

        if occurs_count == 0:
            logger.warning(f"반복 레코드 없음 (nLen={nLen} < struct_size={struct_size})")
            return []

        # 배열 파싱
        parsed_list = []
        offset = 0

        for i in range(occurs_count):
            # bytes 슬라이스 → Structure
            record_bytes = data_bytes[offset:offset + struct_size]
            c_struct = struct_class.from_buffer_copy(record_bytes)

            # Structure → OutBlock (OutBlock.from_c_struct 공통 메서드 사용)
            parsed_model = model_class.from_c_struct(c_struct)
            parsed_list.append(parsed_model)

            offset += struct_size

        return parsed_list

# ============================================================================
# 6. OutDataBlock
# ============================================================================

class COutDataBlock(Structure):
    """C 구조체: OUTDATABLOCK (출력 데이터 블록)

    TR 조회 응답 블록
    """
    _fields_ = [
        ("TrIndex", ctypes.c_int),          # 트랜잭션 인덱스
        ("pData", POINTER(CReceived)),      # 데이터 포인터
    ]


@dataclass
class OutDataBlock:
    """TR 출력 데이터 블록 DTO"""
    TrIndex: int                        # 트랜잭션 인덱스
    pData: Optional[Received]           # 수신 데이터 (NULL일 수 있음)

    @classmethod
    def from_lparam(cls, lparam: int, is_receivemessage: bool = False, is_receivesise: bool = False) -> 'OutDataBlock':
        """lparam으로부터 파싱

        Args:
            lparam: OUTDATABLOCK 구조체 포인터
            ca_receivemessage: CA_RECEIVEMESSAGE 메시지 여부

        Returns:
            OutDataBlock DTO
        """
        logger.debug("OutDataBlock 파싱 시작. lparam=%s, is_receivemessage=%s", lparam, is_receivemessage)

        if not lparam:
            logger.error("lparam이 NULL")
            raise ValueError("lparam이 NULL입니다")

        c_block = ctypes.cast(lparam, POINTER(COutDataBlock)).contents
        TrIndex = c_block.TrIndex
        logger.debug(f"OutDataBlock.TrIndex = {TrIndex}")
        pData = None

        if c_block.pData:
            pData = Received.from_c_struct(c_block.pData.contents, is_receivemessage, is_receivesise)
            logger.debug("OutDataBlock 파싱 완료. lparam=%s, TrIndex=%d", lparam, TrIndex)
        
        return cls(
            TrIndex=TrIndex,
            pData=pData
        )




# ============================================================================
# query() szInput 공통 클래스
# ============================================================================

class InBlock(BaseModel, ABC):
    """
    szInput InBlock은 이 클래스를 상속받아야 합니다.
    - Pydantic BaseModel: 자동 타입 변환 및 검증
    - C_STRUCT: 각 서브클래스에서 Structure 타입 지정 (ClassVar)
    - to_c_struct(): Python 객체 → Structure 변환
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Structure 타입 허용
        str_strip_whitespace=True,     # 문자열 앞뒤 공백 자동 제거
        validate_assignment=True,      # 할당 시에도 검증
    )

    # 각 서브클래스에서 정의해야 할 C 구조체 타입
    C_STRUCT: ClassVar[Type[Structure]]

    def to_c_struct(self) -> Structure:
        """
        Python 객체 → Structure 변환

        공통 변환 로직:
        1. C_STRUCT 인스턴스 생성
        2. 구조체 전체를 공백문자(0x20)로 초기화 (FAQ.pdf 페이지 3)
        3. 각 필드를 cp949로 인코딩하여 C 구조체에 설정

        ⚠️ CRITICAL (FAQ.pdf):
        - InBlock은 반드시 공백문자(0x20)로 초기화
        - null(0x00) 초기화 시 서버에서 정상 처리 안 되는 경우 발생

        Returns:
            Structure: C 구조체 객체 (wmcaQuery에 ctypes.byref()로 전달)

        Example:
            >>> input_data = C8201Input(pswd_noz44="...", bnc_bse_cdz1="1")
            >>> c_struct = input_data.to_c_struct()
            >>> wmcaQuery(hwnd, 1, "c8201", ctypes.byref(c_struct),
            ...           ctypes.sizeof(c_struct), 1)
        """
        struct = self.C_STRUCT()

        # FAQ.pdf 페이지 3: InBlock을 공백문자(0x20)로 초기화
        ctypes.memset(ctypes.addressof(struct), 0x20, ctypes.sizeof(struct))

        # Pydantic v3 호환: model_dump() 사용
        for field_name, value in self.model_dump().items():
            # str → bytes (cp949 인코딩) → C 구조체 필드에 할당
            if isinstance(value, str):
                encoded_value = value.encode('cp949')
            elif isinstance(value, int):
                encoded_value = str(value).encode('cp949')
            elif isinstance(value, float):
                encoded_value = str(value).encode('cp949')
            else:
                encoded_value = str(value).encode('cp949')

            setattr(struct, field_name, encoded_value)

        return struct
