#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMCA DLL 저수준 클라이언트
DLL 함수 호출, Windows 메시지 처리, 응답을 Python 객체로 변환
"""

import os
import sys
import win32gui
import win32con
import ctypes
from ctypes import c_char_p, c_int, c_char, WINFUNCTYPE
from ctypes.wintypes import HWND, UINT, WPARAM, LPARAM, DWORD
from typing import Generator, Optional, Any, Literal, Tuple
from pathlib import Path
from enum import IntEnum
import queue

from .wmca_logger import logger
from .wmca_message_parser import WMCAMessageParser
from .structures.common import InBlock

# Windows 프로시저 콜백 타입 정의
WNDPROC = WINFUNCTYPE(ctypes.c_long, HWND, UINT, WPARAM, LPARAM)

# Windows API
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


# MSG 구조체
class MSG(ctypes.Structure):
    _fields_ = [
        ("hWnd", HWND),
        ("message", UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", ctypes.wintypes.DWORD),
        ("pt", ctypes.wintypes.POINT),
    ]


# Windows 환경 확인
if sys.platform != "win32":
    raise OSError("이 모듈은 Windows 환경에서만 실행 가능합니다.")


# ============================================================================
# 응답 메시지 상수 (SDK.pdf 페이지 11)
# ============================================================================

# WMCA 이벤트 메시지 (샘플 코드 참고)
CA_WMCAEVENT = win32con.WM_USER + 8400  # 중요! wparam에 실제 메시지 타입이 들어있음


class WMCAMessage(IntEnum):
    """WMCA 응답 메시지 종류"""

    CA_CONNECTED = win32con.WM_USER + 110  # 로그인 성공
    CA_DISCONNECTED = win32con.WM_USER + 120  # 연결 해제
    CA_SOCKETERROR = win32con.WM_USER + 130  # 통신 오류
    CA_RECEIVEDATA = win32con.WM_USER + 210  # TR 결과 수신
    CA_RECEIVESISE = win32con.WM_USER + 220  # 실시간 시세 수신
    CA_RECEIVEMESSAGE = win32con.WM_USER + 230  # 상태 메시지
    CA_RECEIVECOMPLETE = win32con.WM_USER + 240  # 처리 완료
    CA_RECEIVEERROR = win32con.WM_USER + 250  # 처리 실패


# ============================================================================
# WMCAAgent - DLL 저수준 클라이언트
# ============================================================================


class WMCAAgent:
    """
    WMCA DLL 저수준 클라이언트

    주요 기능:
    - DLL 함수 호출
    - Windows 메시지 루프 처리
    - 응답 메시지를 Python 객체로 변환
    """

    def __init__(self, dll_path: Optional[str] = None):
        """
        WMCAAgent 초기화

        Args:
            dll_path: wmca.dll 경로 (None이면 자동 탐색)

        Note:
            - 서버 주소와 포트는 DLL 내장 설정(wmca.ini) 사용
            - 실제 초기화는 __enter__에서 수행됨
        """

        # DLL 경로 자동 탐색
        if dll_path is None:
            try:
                dll_path = self._find_dll_path()
            except FileNotFoundError as e:
                logger.critical("wmca.dll 경로를 찾지 못 함: %s", e)
                raise
        self.dll_path = dll_path

        # DLL 관련 변수
        self.dll = None
        self.initialized = False  # 초기화 상태 플래그

        # DLL 함수 포인터들
        self._init_function_pointers()

        # Windows 메시지 처리용
        self.hwnd = None
        self.wnd_class_name = None  # 윈도우 클래스 이름
        self.wnd_class_atom = None  # 윈도우 클래스 등록 식별자
        self.message_thread = None
        self.message_queue = queue.Queue()

        # DLL 로드 (함수 포인터만 설정)
        self._load_dll()

    def _find_dll_path(self) -> str:
        """wmca.dll 경로 자동 탐색"""
        script_dir = Path(__file__).parent
        wmca_dll_path = script_dir / "dll" / "wmca.dll"

        if wmca_dll_path.exists():
            return str(wmca_dll_path)

        raise FileNotFoundError(
            f"wmca.dll을 찾을 수 없습니다.\n"
            f"NH투자증권 OpenAPI 라이브러리를 다운받은 후 DLL 파일을 {wmca_dll_path} 경로에 배치해주세요."
        )

    def _init_function_pointers(self):
        """DLL 함수 포인터 초기화"""
        self.wmca_load = None
        self.wmca_free = None
        self.wmca_set_server = None
        self.wmca_set_port = None
        self.wmca_is_connected = None
        self.wmca_connect = None
        self.wmca_disconnect = None
        self.wmca_query = None
        self.wmca_attach = None
        self.wmca_detach = None
        self.wmca_set_account_index_pwd = None

    def _load_dll(self):
        """DLL 로드 및 함수 포인터 설정

        Reference:
            - WmcaIntf.h (23-42줄): 모든 함수의 typedef 정의
            - SDK.pdf: 함수 프로토타입 상세 설명

        Note:
            모든 WMCA 함수는 __stdcall 규약 사용 → ctypes.WinDLL 사용
        """
        try:
            dll_abs_path = os.path.abspath(self.dll_path)
            dll_dir = os.path.dirname(dll_abs_path)
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

            self.dll = ctypes.WinDLL(dll_abs_path)
            logger.debug(f"DLL 로드됨: {dll_abs_path}")
        except OSError as e:
            raise OSError(f"{self.dll_path} 로드 실패: {e}")

        try:
            # ================================================================
            # 1. 함수 포인터 획득
            # ================================================================
            self.wmca_load = self.dll.wmcaLoad
            self.wmca_free = self.dll.wmcaFree
            self.wmca_set_server = self.dll.wmcaSetServer
            self.wmca_set_port = self.dll.wmcaSetPort
            self.wmca_is_connected = self.dll.wmcaIsConnected
            self.wmca_connect = self.dll.wmcaConnect
            self.wmca_disconnect = self.dll.wmcaDisconnect
            self.wmca_query = self.dll.wmcaQuery
            self.wmca_attach = self.dll.wmcaAttach
            self.wmca_detach = self.dll.wmcaDetach
            self.wmca_set_account_index_pwd = self.dll.wmcaSetAccountIndexPwd

            # ================================================================
            # 2. 함수 시그니처 설정 (WmcaIntf.h typedef 기준)
            # ================================================================

            # BOOL wmcaLoad()
            self.wmca_load.argtypes = []
            self.wmca_load.restype = ctypes.c_bool

            # BOOL wmcaFree()
            self.wmca_free.argtypes = []
            self.wmca_free.restype = ctypes.c_bool

            # BOOL wmcaSetServer(const char* szServer)
            self.wmca_set_server.argtypes = [c_char_p]
            self.wmca_set_server.restype = ctypes.c_bool

            # BOOL wmcaSetPort(const int nPort)
            self.wmca_set_port.argtypes = [c_int]
            self.wmca_set_port.restype = ctypes.c_bool

            # BOOL wmcaIsConnected()
            self.wmca_is_connected.argtypes = []
            self.wmca_is_connected.restype = ctypes.c_bool

            # BOOL wmcaConnect(HWND hWnd, DWORD dwMsg, char cMediaType, char cUserType,
            #                  const char* pszID, const char* pszPassword, const char* pszSignPassword)
            self.wmca_connect.argtypes = [HWND, DWORD, c_char, c_char, c_char_p, c_char_p, c_char_p]
            self.wmca_connect.restype = ctypes.c_bool

            # BOOL wmcaDisconnect()
            self.wmca_disconnect.argtypes = []
            self.wmca_disconnect.restype = ctypes.c_bool

            # BOOL wmcaQuery(HWND hWnd, int nTransactionID, const char* pszTrCode,
            #                const char* pszInputData, int nInputDataSize, int nAccountIndex)
            self.wmca_query.argtypes = [HWND, c_int, c_char_p, c_char_p, c_int, c_int]
            self.wmca_query.restype = ctypes.c_bool

            # BOOL wmcaAttach(HWND hWnd, const char* pszSiseName, const char* pszInputCode,
            #                 int nInputCodeSize, int nInputCodeTotalSize)
            self.wmca_attach.argtypes = [HWND, c_char_p, c_char_p, c_int, c_int]
            self.wmca_attach.restype = ctypes.c_bool

            # BOOL wmcaDetach(HWND hWnd, const char* pszSiseName, const char* pszInputCode,
            #                 int nInputCodeSize, int nInputCodeTotalSize)
            self.wmca_detach.argtypes = [HWND, c_char_p, c_char_p, c_int, c_int]
            self.wmca_detach.restype = ctypes.c_bool

            # BOOL wmcaSetAccountIndexPwd(const char* pszHashOut, int nAccountIndex, const char* pszPassword)
            self.wmca_set_account_index_pwd.argtypes = [c_char_p, c_int, c_char_p]
            self.wmca_set_account_index_pwd.restype = ctypes.c_bool

            logger.debug("모든 DLL 함수 시그니처 설정 완료")
        except AttributeError as e:
            raise AttributeError(f"함수 포인터 설정 실패: {e}")

    # ========================================================================
    # Windows 메시지 처리
    # ========================================================================

    def _create_message_window(self):
        """메시지 수신용 숨김 윈도우 생성"""
        # 윈도우 프로시저를 WNDPROC 타입으로 변환 (중요!)
        self._wnd_proc_callback = WNDPROC(self._wnd_proc)

        # 윈도우 클래스 등록 (인스턴스마다 고유한 이름 사용)
        import time

        self.wnd_class_name = f"WMCA_WINDOW_{id(self)}_{int(time.time() * 1000)}"

        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc_callback  # 변환된 콜백 사용
        wc.lpszClassName = self.wnd_class_name
        wc.hInstance = win32gui.GetModuleHandle(None)

        try:
            self.wnd_class_atom = win32gui.RegisterClass(wc)
            logger.debug(
                f"윈도우 클래스 등록 성공: name={self.wnd_class_name}, atom={self.wnd_class_atom}"
            )
        except Exception as e:
            logger.error(f"윈도우 클래스 등록 실패: {e}")
            raise

        # 숨김 윈도우 생성
        self.hwnd = win32gui.CreateWindow(
            wc.lpszClassName, "WMCA Message Window", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
        )
        logger.debug(f"CreateWindow 완료: hwnd={self.hwnd}")

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Windows 메시지 프로시저 (콜백)"""
        # CA_WMCAEVENT 메시지만 처리 (샘플 코드 방식)
        if msg == CA_WMCAEVENT:
            try:
                # WMCA 이벤트 처리로 위임
                self._handle_wmca_event(wparam, lparam)
            except Exception as e:
                logger.error(f"메시지 처리 오류: {e}", exc_info=True)

            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _handle_wmca_event(self, wparam: int, lparam: int):
        """
        WMCA 이벤트 처리

        Args:
            wparam: 메시지 타입 (WMCAMessage enum 값)
            lparam: 데이터 포인터 (C 구조체 주소)

        CRITICAL: lparam이 가리키는 메모리는 이 함수가 반환된 후 DLL이 해제합니다.
        따라서 lparam을 즉시 파싱해서 Python 객체로 변환한 후 큐에 저장해야 합니다.
        """
        # wparam을 WMCAMessage IntEnum으로 변환
        try:
            msg_type = WMCAMessage(wparam)
        except ValueError:
            logger.warning(f"알 수 없는 메시지 타입: wparam={wparam}")
            return

        logger.debug(
            "CA_WMCAEVENT 수신: msg_type=%s (%s), lparam=%s", msg_type.name, msg_type.value, lparam
        )

        # 메시지 타입에 따라 파싱 (WMCAMessageParser 사용)
        parsed_dto = None

        if msg_type == WMCAMessage.CA_DISCONNECTED:
            parsed_dto = None
        elif msg_type == WMCAMessage.CA_CONNECTED:
            parsed_dto = WMCAMessageParser.parse_loginblock(lparam)
        elif msg_type == WMCAMessage.CA_RECEIVEMESSAGE:
            parsed_dto = WMCAMessageParser.parse_outdatablock(lparam, is_receivemessage=True)
        elif msg_type == WMCAMessage.CA_RECEIVEDATA or msg_type == WMCAMessage.CA_RECEIVECOMPLETE:
            parsed_dto = WMCAMessageParser.parse_outdatablock(lparam)
        elif msg_type == WMCAMessage.CA_RECEIVESISE:
            parsed_dto = WMCAMessageParser.parse_outdatablock(lparam, is_receivesise=True)
        else:
            logger.warning("처리되지 않은 메시지 타입: %s", msg_type.name)
            parsed_dto = WMCAMessageParser.parse_outdatablock(lparam)

        # 파싱된 데이터를 큐에 추가
        self.message_queue.put((msg_type, parsed_dto))

    def _start_message_loop(self):
        """메시지 윈도우 생성 (메인 스레드에서 실행)"""
        if self.hwnd is None:
            self._create_message_window()
            logger.debug(f"메시지 윈도우 생성 완료: hwnd={self.hwnd}")

    def receive_events(
        self, timeout: Optional[float] = None
    ) -> Generator[Tuple[WMCAMessage, Any], None, None]:
        """
        Windows 메시지 큐에서 이벤트를 수신하는 Generator

        Args:
            timeout: 최대 대기 시간 (초). None이면 무한 대기

        Yields:
            Tuple[WMCAMessage, Any]: (메시지 타입, 파싱된 데이터)

        Example:
            >>> # timeout 있는 경우
            >>> for msg_type, data in agent.receive_events(timeout=10.0):
            ...     if msg_type == WMCAMessage.CA_CONNECTED:
            ...         print(f"로그인 성공: {data.pLoginInfo.szUserID}")
            ...         break
            ...
            >>> # 무한 대기 (timeout=None)
            >>> for msg_type, data in agent.receive_events():
            ...     if msg_type == WMCAMessage.CA_RECEIVESISE:
            ...         print(f"실시간 시세 수신: {data}")
            ...     # break 없이 계속 수신

        Note:
            - Windows 메시지 펌핑을 자동으로 처리
            - timeout이 None이면 무한 루프 (사용자가 명시적으로 break 해야 함)
            - timeout 지정 시 시간 초과 시 StopIteration 발생
            - 각 메시지는 이미 파싱된 Python 객체로 반환됨
        """
        import time

        start_time = time.time()

        while True:
            # timeout 체크 (timeout이 None이면 무한 루프)
            if timeout is not None and time.time() - start_time >= timeout:
                logger.debug("receive_events: timeout 종료")
                break

            # Windows 메시지 펌핑 (DLL이 메시지를 보내면 _wnd_proc 호출됨)
            msg = MSG()
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE=1
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            # 큐에서 파싱된 메시지 확인
            try:
                msg_type, parsed_data = self.message_queue.get_nowait()
                logger.debug(
                    f"receive_events: 메시지 수신 - type={msg_type.name}, data={type(parsed_data).__name__}"
                )
                yield (msg_type, parsed_data)
            except queue.Empty:
                pass

            time.sleep(0.01)  # 10ms 대기

    # ========================================================================
    # DLL 함수 호출 (저수준)
    # ========================================================================

    def connect(
        self,
        szID: str,
        szPW: str,
        szCertPW: str,
        MediaType: Literal["P", "T"] = "T",
        UserType: Literal["1", "W"] = "W",
    ) -> bool:
        """
        서버 연결 요청 (wmcaConnect)

        Args:
            szID: 사용자 ID (QV 또는 Namuh 온라인 약정 및 OpenAPI 서비스 이용 등록 필요)
            szPW: 사용자 ID 비밀번호
            szCertPW: 공인인증서 비밀번호
            MediaType: 매체유형 ('P': QV계좌, 'T': Namuh계좌)
            UserType: 사용자유형 ('1': QV계좌, 'W': Namuh계좌)

        Returns:
            bool: wmcaConnect 호출 성공 여부 (응답은 receive_events()로 수신)

        Note:
            - 이 함수는 요청만 전송합니다
            - 실제 로그인 결과는 receive_events()로 수신해야 합니다
            - CA_CONNECTED: 로그인 성공
            - CA_DISCONNECTED: 로그인 실패
            - WMCAClient.connect()는 이 함수와 receive_events()를 조합하여 사용

        Example:
            >>> # 저수준 사용 (권장하지 않음)
            >>> agent.connect(szID="id", szPW="pw", szCertPW="cert")
            >>> for msg_type, data in agent.receive_events():
            ...     if msg_type == WMCAMessage.CA_CONNECTED:
            ...         print("로그인 성공!")
            ...         break
            >>>
            >>> # 고수준 사용 (권장)
            >>> client = WMCAClient()
            >>> login_info = client.connect(...)  # 내부적으로 receive_events 사용
        """
        if not self.initialized:
            raise RuntimeError(
                "Agent가 초기화되지 않았습니다. with 문으로 사용하거나 initialize()를 먼저 호출하세요."
            )

        logger.info(f"로그인 요청 전송: ID={szID}, MediaType={MediaType}, UserType={UserType}")

        # 서버 연결 호출 (요청만 전송)
        id_bytes = szID.encode("utf-8")
        pw_bytes = szPW.encode("utf-8")
        cert_pw_bytes = szCertPW.encode("utf-8")

        result = self.wmca_connect(
            self.hwnd,
            CA_WMCAEVENT,
            ord(MediaType),  # 'P' 또는 'T'를 정수로 변환
            ord(UserType),  # '1' 또는 'W'를 정수로 변환
            id_bytes,
            pw_bytes,
            cert_pw_bytes,
        )

        if result:
            logger.debug("wmcaConnect() 호출 성공 - 응답은 receive_events()로 수신")
        else:
            logger.error("wmcaConnect() 호출 실패")

        return bool(result)

    def disconnect(self) -> bool:
        """서버 연결 해제 (로그아웃)"""

        result = self.wmca_disconnect()
        return bool(result)

    def get_account_hash_password(self, account_index: int, password: str) -> str:
        """
        계좌 비밀번호를 44자 해시값으로 변환

        Args:
            account_index: 계좌 인덱스 (1부터 시작)
            password: 평문 비밀번호 (실제로는 이미 인증서 비밀번호로 암호화된 값)

        Returns:
            str: 44자 해시 문자열 (cp949 인코딩)

        Reference:
            - SDK.pdf 페이지 10: wmcaSetAccountIndexPwd() 함수
            - api/SAMPLES/VC++/WMCALOADERDlg.cpp:620

        Example:
            >>> hash_pwd = client.get_account_hash_password(1, "계좌비밀번호")
            >>> len(hash_pwd)
            44
            >>> # 이 해시값을 InBlock의 pswd_noz44 필드에 설정

        Note:
            - wmcaSetAccountIndexPwd()가 반환하는 해시는 ASCII/cp949 텍스트 (바이너리 아님)
            - C 예제에서도 char 배열에 직접 복사하므로 텍스트 문자열로 안전
        """
        # 44바이트 버퍼 생성 (공백으로 초기화)
        hash_buffer = ctypes.create_string_buffer(44)

        # 평문 비밀번호를 cp949로 인코딩
        password_bytes = password.encode("cp949")

        # DLL 함수 호출
        result = self.wmca_set_account_index_pwd(hash_buffer, account_index, password_bytes)

        if not result:
            raise RuntimeError(f"계좌 비밀번호 해시 생성 실패 (account_index={account_index})")

        # bytes → str (cp949 디코딩)
        # 해시는 ASCII/cp949 호환 텍스트이므로 안전하게 디코딩 가능
        hash_str = hash_buffer.value.decode("cp949")

        # 길이 검증
        if len(hash_str) != 44:
            raise ValueError(
                f"예상치 못한 해시 길이: {len(hash_str)}자 (예상: 44자)\n" f"해시값: '{hash_str}'"
            )

        return hash_str

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        if self.dll is None:
            return False
        try:
            result = self.wmca_is_connected()
            return bool(result)
        except Exception:
            return False

    def query(self, nTRID: int, szTRCode: str, szInput: InBlock, nAccountIndex: int = 0) -> bool:
        """
        TR(Transaction) 조회 요청 전송 (wmcaQuery)

        Args:
            nTRID: Transaction ID (TrIndex, 응답 구분용)
            szTRCode: 서비스 코드 (5자리, 예: "c1101", "c8201")
            szInput: TR 입력 데이터 (InBlock 기반 Pydantic 모델)
            nAccountIndex: 계좌 인덱스 (0: 계좌번호 불필요, 1~: 로그인 시 받은 계좌 순서)

        Returns:
            bool: wmcaQuery 호출 성공 여부 (응답은 receive_events()로 수신)

        Note:
            - 이 함수는 요청만 전송합니다
            - 실제 응답은 receive_events()로 수신해야 합니다
            - CA_RECEIVEDATA: TR 블록 데이터 (여러 개 가능)
            - CA_RECEIVECOMPLETE: 모든 블록 수신 완료
            - CA_RECEIVEERROR: TR 처리 실패
            - WMCAClient.query()는 이 함수와 receive_events()를 조합하여 사용

        Example:
            >>> # 저수준 사용 (권장하지 않음)
            >>> tr_index = agent.get_next_tr_index()
            >>> agent.query(tr_index, "c8201", input_data, nAccountIndex=1)
            >>> for msg_type, data in agent.receive_events():
            ...     if getattr(data, 'TrIndex', None) == tr_index:
            ...         if msg_type == WMCAMessage.CA_RECEIVECOMPLETE:
            ...             break
            >>>
            >>> # 고수준 사용 (권장)
            >>> client = WMCAClient()
            >>> blocks = client.query(...)  # 내부적으로 receive_events 사용
        """
        logger.info(
            f"TR 조회 요청 전송: TrCode={szTRCode}, TrIndex={nTRID}, AccountIndex={nAccountIndex}"
        )

        # InputBlock을 C 구조체로 변환
        c_struct = szInput.to_c_struct()
        input_bytes = ctypes.string_at(ctypes.addressof(c_struct), ctypes.sizeof(c_struct))
        tr_code_bytes = szTRCode.encode("utf-8")

        # wmcaQuery 호출 (요청만 전송)
        logger.debug(f"wmcaQuery() 호출 - hwnd={self.hwnd}, TrIndex={nTRID}, TrCode={szTRCode}")
        result = self.wmca_query(
            self.hwnd, nTRID, tr_code_bytes, input_bytes, len(input_bytes), nAccountIndex
        )

        if not result:
            logger.error("wmcaQuery() 호출 실패")
            raise RuntimeError("TR 조회 함수 호출 실패")

        logger.debug(f"TR 조회 요청 완료 - TrIndex={nTRID}")
        return bool(result)

    def attach(self, szBCType: str, szInput: str, nCodeLen: int, nInputLen: int) -> bool:
        """
        실시간 시세 등록 (wmcaAttach)

        실시간 패킷을 등록하여 지속적으로 데이터를 수신합니다.
        명시적으로 detach하거나 프로그램 종료 시까지 실시간 데이터가 수신됩니다.

        Args:
            szBCType: 실시간 서비스 코드 (2자리, 예: "j8" - 주식체결가, "h1" - 주식호가)
            szInput: 입력값 (예: 종목코드 "000660" 또는 여러 종목 "000660005940005930")
            nCodeLen: 입력값 개별 길이 (예: 주식종목코드 = 6)
            nInputLen: 입력값 전체 길이 (예: 종목 1개 = 6, 종목 3개 = 18)

        Returns:
            bool: 등록 성공 여부

        Example:
            >>> # 단일 종목 (SK하이닉스) 실시간 체결가 등록
            >>> agent.attach(
            ...     szBCType="j8",
            ...     szInput="000660",
            ...     nCodeLen=6,
            ...     nInputLen=6
            ... )
            >>>
            >>> # 3개 종목 동시 등록
            >>> agent.attach(
            ...     szBCType="j8",
            ...     szInput="000660005940005930",  # SK하이닉스,NH투자증권,삼성증권
            ...     nCodeLen=6,
            ...     nInputLen=18  # 6 * 3
            ... )
            >>>
            >>> # 실시간 데이터 수신 (CA_RECEIVESISE 메시지)
            >>> # register_callback으로 콜백 등록하여 처리

        Note:
            - 실시간 서비스 코드는 시세_SPEC.pdf 참고
            - 주식 실시간 코드:
              - j8: 주식 체결가
              - h1: 주식 호가
              - f8: 선물 체결가
              - f1: 선물 호가
              - o2: 옵션 체결가
              - o1: 옵션 호가
            - 응답은 CA_RECEIVESISE 메시지로 수신됨
            - 콜백 등록: register_callback(tr_index, callback_func)

        Reference:
            - SDK.pdf 페이지 7: wmcaAttach() 함수
            - api/SAMPLES/VC++/WMCALOADERDlg.cpp:663-669 (실시간 등록 예제)
        """

        logger.debug(
            f"실시간 시세 등록: BC={szBCType}, Input={szInput}, CodeLen={nCodeLen}, InputLen={nInputLen}"
        )

        # 입력값을 cp949로 인코딩
        bc_type_bytes = szBCType.encode("cp949")
        input_bytes = szInput.encode("cp949")

        # wmcaAttach 호출
        logger.debug(f"wmcaAttach() 호출 - hwnd={self.hwnd}, BC={szBCType}")
        result = self.wmca_attach(self.hwnd, bc_type_bytes, input_bytes, nCodeLen, nInputLen)

        if result:
            logger.info(f"실시간 시세 등록 성공: {szBCType} - {szInput}")
        else:
            logger.error(f"실시간 시세 등록 실패: {szBCType} - {szInput}")

        return bool(result)

    def detach(self, szBCType: str, szInput: str, nCodeLen: int, nInputLen: int) -> bool:
        """
        실시간 시세 해제 (wmcaDetach)

        등록된 실시간 패킷 수신을 취소합니다.

        Args:
            szBCType: 실시간 서비스 코드 (2자리, 예: "j8")
            szInput: 입력값 (예: 종목코드 "000660")
            nCodeLen: 입력값 개별 길이
            nInputLen: 입력값 전체 길이

        Returns:
            bool: 해제 성공 여부

        Example:
            >>> # 등록했던 실시간 시세 해제
            >>> agent.detach(
            ...     szBCType="j8",
            ...     szInput="000660",
            ...     nCodeLen=6,
            ...     nInputLen=6
            ... )

        Note:
            - attach와 동일한 파라미터로 호출해야 함
            - 필요없는 실시간 데이터는 반드시 해제해야 성능 저하 방지

        Reference:
            - SDK.pdf 페이지 8: wmcaDetach() 함수
        """

        logger.info(f"실시간 시세 해제: BC={szBCType}, Input={szInput}")

        # 입력값을 cp949로 인코딩
        bc_type_bytes = szBCType.encode("cp949")
        input_bytes = szInput.encode("cp949")

        # wmcaDetach 호출
        logger.debug(f"wmcaDetach() 호출 - hwnd={self.hwnd}, BC={szBCType}")
        result = self.wmca_detach(self.hwnd, bc_type_bytes, input_bytes, nCodeLen, nInputLen)

        if result:
            logger.info(f"실시간 시세 해제 성공: {szBCType} - {szInput}")
        else:
            logger.error(f"실시간 시세 해제 실패: {szBCType} - {szInput}")

        return bool(result)

    def _initialize(self):
        """
        WMCA Agent 초기화

        Windows 메시지 윈도우 생성만 수행합니다.

        Note:
            - SDK.pdf 페이지 3: wmcaLoad()는 사용 순서에 없음
            - C++ 샘플 코드도 wmcaLoad()를 호출하지 않음
            - wmcaConnect()가 내부적으로 필요한 초기화를 수행하는 것으로 추정
            - 컨텍스트 매니저(__enter__)에서 자동 호출됨
        """
        if self.initialized:
            logger.warning("이미 초기화됨")
            return

        logger.info("WMCA Agent 초기화 시작")

        # Windows 메시지 윈도우 생성
        self._start_message_loop()
        logger.debug(f"메시지 윈도우 생성 완료: hwnd={self.hwnd}")

        logger.info("WMCA Agent 초기화 완료")
        self.initialized = True

    def _dispose(self):
        """리소스 정리"""
        if not self.initialized:
            logger.debug("초기화되지 않음 - dispose 스킵")
            return

        logger.debug("WMCA Agent 리소스 정리 시작")

        # 1. 연결 해제
        logger.debug("연결 해제 수행")
        self.disconnect()

        # 2. WMCA 모듈 해제
        if self.dll is not None:
            try:
                self.wmca_free()
                logger.debug("WMCA 모듈 해제 완료")
            except Exception as e:
                logger.error(f"WMCA 모듈 해제 중 오류: {e}")

        # 3. 윈도우 파괴
        if self.hwnd is not None:
            try:
                win32gui.DestroyWindow(self.hwnd)
                logger.debug(f"윈도우 파괴 완료: hwnd={self.hwnd}")
                self.hwnd = None
            except Exception as e:
                logger.error(f"윈도우 파괴 중 오류: {e}")

        # 4. 윈도우 클래스 등록 해제
        if self.wnd_class_atom is not None:
            try:
                user32.UnregisterClassW(self.wnd_class_atom, win32gui.GetModuleHandle(None))
                logger.debug(f"윈도우 클래스 등록 해제 완료: atom={self.wnd_class_atom}")
                self.wnd_class_atom = None
            except Exception as e:
                logger.error(f"윈도우 클래스 등록 해제 중 오류: {e}")

        self.initialized = False
        logger.info("WMCA Agent 리소스 정리 완료")

    def __enter__(self):
        """
        컨텍스트 매니저 진입

        자동으로 초기화 수행:
        1. Windows 메시지 윈도우 생성
        2. WMCA 모듈 로드
        """
        self._initialize()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        컨텍스트 매니저 종료

        자동으로 정리 수행:
        1. 연결 해제 (로그아웃)
        2. WMCA 모듈 해제
        3. 윈도우 파괴
        4. 윈도우 클래스 등록 해제
        """
        self._dispose()
        return False
