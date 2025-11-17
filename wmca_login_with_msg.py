#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NH증권 WMCA API - Windows 메시지 처리를 포함한 로그인 예제
Windows 환경, 32비트 Python 필요
"""

import os
import sys
import ctypes
from ctypes import wintypes
import time

# Windows 환경 확인
if sys.platform != "win32":
    print("이 스크립트는 Windows 환경에서만 실행 가능합니다.")
    sys.exit(1)

# 32비트 Python 확인
import platform
if platform.architecture()[0] != "32bit":
    print("=" * 70)
    print("⚠️  경고: 64비트 Python이 감지되었습니다.")
    print("=" * 70)
    print(f"현재 Python: {platform.architecture()[0]}")
    print(f"wmca.dll 요구사항: 32bit")
    print("\n32비트 Python을 설치하고 다음과 같이 실행하세요:")
    print("  py -3.11-32 wmca_login_with_msg.py")
    print("=" * 70)
    sys.exit(1)

# Windows API 상수 및 구조체
WM_USER = 0x0400
CA_CONNECTED = WM_USER + 110
CA_DISCONNECTED = WM_USER + 120
CA_SOCKETERROR = WM_USER + 130
CA_RECEIVEDATA = WM_USER + 210
CA_RECEIVESISE = WM_USER + 220
CA_RECEIVEMESSAGE = WM_USER + 230
CA_RECEIVECOMPLETE = WM_USER + 240
CA_RECEIVEERROR = WM_USER + 250
CA_WMCAEVENT = WM_USER + 8400

# Windows API 함수
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 윈도우 프로시저 타입 정의
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

# WNDCLASSEX 구조체
class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]

# MSG 구조체
class MSG(ctypes.Structure):
    _fields_ = [
        ("hWnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]

# ACCOUNTINFO 구조체 (완전한 구조체)
class ACCOUNTINFO(ctypes.Structure):
    _fields_ = [
        ("szAccountNo", ctypes.c_char * 11),      # 계좌번호
        ("szAccountName", ctypes.c_char * 40),    # 계좌명
        ("act_pdt_cdz3", ctypes.c_char * 3),      # 상품코드
        ("amn_tab_cdz4", ctypes.c_char * 4),      # 관리점코드
        ("expr_datez8", ctypes.c_char * 8),       # 계좌만료일
        ("granted", ctypes.c_char),               # 미결제주문 권한여부 (G:가능)
        ("filler", ctypes.c_char * 189),          # filler
    ]

# LOGININFO 구조체
class LOGININFO(ctypes.Structure):
    _fields_ = [
        ("szDate", ctypes.c_char * 14),           # 접속시간
        ("szServerName", ctypes.c_char * 15),     # 서버명
        ("szUserID", ctypes.c_char * 8),          # 사용자ID
        ("szAccountCount", ctypes.c_char * 3),    # 계좌수
        ("accountlist", ACCOUNTINFO * 999),       # 계좌 리스트
    ]

# LOGINBLOCK 구조체
class LOGINBLOCK(ctypes.Structure):
    _fields_ = [
        ("TrIndex", ctypes.c_int),                # 트랜잭션 인덱스
        ("pLoginInfo", ctypes.POINTER(LOGININFO)), # 로그인 정보 포인터
    ]

# MSGHEADER 구조체 (서버 메시지용)
class MSGHEADER(ctypes.Structure):
    _fields_ = [
        ("msg_cd", ctypes.c_char * 5),      # 메시지 코드 (00000: 정상, 기타: 오류)
        ("user_msg", ctypes.c_char * 80),   # 사용자 메시지
    ]

# RECEIVED 구조체
class RECEIVED(ctypes.Structure):
    _fields_ = [
        ("szBlockName", ctypes.c_char_p),   # 블록 이름
        ("szData", ctypes.c_char_p),        # 데이터
        ("nLen", ctypes.c_int),             # 데이터 길이
    ]

# OUTDATABLOCK 구조체
class OUTDATABLOCK(ctypes.Structure):
    _fields_ = [
        ("TrIndex", ctypes.c_int),          # 트랜잭션 인덱스
        ("pData", ctypes.POINTER(RECEIVED)), # 데이터 포인터
    ]


class WMCAClient:
    """WMCA API 클라이언트 - Windows 메시지 처리 포함"""

    def __init__(self, dll_path: str = "wmca.dll"):
        self.dll_path = dll_path
        self.dll = None
        self.connected = False
        self.hwnd = None
        self.login_result = None
        self.error_code = None

        # DLL 함수 포인터
        self.wmca_load = None
        self.wmca_free = None
        self.wmca_set_server = None
        self.wmca_set_port = None
        self.wmca_is_connected = None
        self.wmca_connect = None
        self.wmca_disconnect = None

        # DLL 로드
        self._load_dll()

    def _load_dll(self):
        """DLL 로드 및 함수 포인터 설정"""
        try:
            # DLL 경로를 절대 경로로 변환
            dll_abs_path = os.path.abspath(self.dll_path)
            dll_dir = os.path.dirname(dll_abs_path)

            # PATH에 DLL 디렉토리 추가 (의존성 DLL 로드용)
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

            # DLL 로드
            self.dll = ctypes.WinDLL(dll_abs_path)
            print(f"✓ DLL 로드: {dll_abs_path}")

            # 함수 포인터 설정
            self.wmca_load = self.dll.wmcaLoad
            self.wmca_free = self.dll.wmcaFree
            self.wmca_set_server = self.dll.wmcaSetServer
            self.wmca_set_port = self.dll.wmcaSetPort
            self.wmca_is_connected = self.dll.wmcaIsConnected
            self.wmca_connect = self.dll.wmcaConnect
            self.wmca_disconnect = self.dll.wmcaDisconnect

            print("✓ 함수 포인터 설정 완료")

        except Exception as e:
            print(f"✗ DLL 로드 실패: {e}")
            sys.exit(1)

    def _window_proc(self, hwnd, msg, wparam, lparam):
        """Windows 메시지 처리 콜백"""
        if msg == CA_WMCAEVENT:
            msg_type = wparam

            # 메시지 타입 출력 (디버깅용)
            msg_name = {
                CA_CONNECTED: "CA_CONNECTED",
                CA_DISCONNECTED: "CA_DISCONNECTED",
                CA_SOCKETERROR: "CA_SOCKETERROR",
                CA_RECEIVEDATA: "CA_RECEIVEDATA",
                CA_RECEIVESISE: "CA_RECEIVESISE",
                CA_RECEIVEMESSAGE: "CA_RECEIVEMESSAGE",
                CA_RECEIVECOMPLETE: "CA_RECEIVECOMPLETE",
                CA_RECEIVEERROR: "CA_RECEIVEERROR",
            }.get(msg_type, f"UNKNOWN({msg_type})")
            print(f"\n[메시지 수신] {msg_name} (wparam={msg_type}, lparam={lparam})")

            if msg_type == CA_CONNECTED:
                print("✓ 로그인 성공!")
                self.connected = True

                # LOGINBLOCK 구조체 읽기
                if lparam:
                    try:
                        login_block = ctypes.cast(lparam, ctypes.POINTER(LOGINBLOCK)).contents

                        # pLoginInfo 포인터가 NULL인지 확인
                        if not login_block.pLoginInfo:
                            print("  ⚠️  pLoginInfo가 NULL입니다.")
                        else:
                            login_info = login_block.pLoginInfo.contents

                            # 접속 정보
                            date_str = login_info.szDate.decode('cp949', errors='ignore').strip()
                            server_str = login_info.szServerName.decode('cp949', errors='ignore').strip()
                            user_str = login_info.szUserID.decode('cp949', errors='ignore').strip()

                            print(f"  접속시간: {date_str}")
                            print(f"  서버명: {server_str}")
                            print(f"  사용자ID: {user_str}")

                            # 계좌 수 파싱 (문자열 -> 정수)
                            account_count_str = login_info.szAccountCount.decode('cp949', errors='ignore').strip()
                            account_count = int(account_count_str) if account_count_str else 0
                            print(f"  계좌수: {account_count}")

                            # 계좌 정보 출력
                            if account_count > 0:
                                print(f"\n  계좌 목록:")
                                for i in range(min(account_count, 10)):  # 최대 10개 출력
                                    acc = login_info.accountlist[i]
                                    acc_no = acc.szAccountNo.decode('cp949', errors='ignore').strip()
                                    acc_name = acc.szAccountName.decode('cp949', errors='ignore').strip()
                                    acc_pdt = acc.act_pdt_cdz3.decode('cp949', errors='ignore').strip()
                                    granted = acc.granted.decode('cp949', errors='ignore') if acc.granted else ''

                                    print(f"    [{i+1}] {acc_no} - {acc_name}")
                                    if acc_pdt:
                                        print(f"        상품코드: {acc_pdt}, 미결제권한: {granted}")

                    except Exception as e:
                        print(f"  ⚠️  로그인 정보 파싱 오류: {e}")
                        import traceback
                        traceback.print_exc()

                self.login_result = True

            elif msg_type == CA_DISCONNECTED:
                print("✓ 연결 종료")
                self.connected = False
                # 로그인 실패로 간주
                if self.login_result is None:
                    self.login_result = False

            elif msg_type == CA_SOCKETERROR:
                error_code = lparam
                print(f"✗ 소켓 오류 발생: 코드 {error_code}")
                self.error_code = error_code
                self.login_result = False

            elif msg_type == CA_RECEIVEMESSAGE:
                print("✓ 서버 메시지 수신")
                # 메시지 내용 파싱
                if lparam:
                    try:
                        # OUTDATABLOCK 구조체로 캐스팅
                        out_data = ctypes.cast(lparam, ctypes.POINTER(OUTDATABLOCK)).contents

                        if out_data.pData:
                            received = out_data.pData.contents

                            # MSGHEADER 구조체로 캐스팅
                            msg_header = ctypes.cast(received.szData, ctypes.POINTER(MSGHEADER)).contents

                            msg_cd = msg_header.msg_cd.decode('cp949', errors='ignore').strip()
                            user_msg = msg_header.user_msg.decode('cp949', errors='ignore').strip()

                            print(f"  [TrIndex: {out_data.TrIndex}]")
                            print(f"  메시지 코드: {msg_cd}")
                            print(f"  메시지 내용: {user_msg}")

                            # 메시지 코드가 00000이 아니면 오류
                            if msg_cd != "00000":
                                print(f"  ⚠️  오류 메시지!")
                                self.login_result = False

                    except Exception as e:
                        print(f"  ⚠️  메시지 파싱 오류: {e}")
                        import traceback
                        traceback.print_exc()

            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def create_message_window(self):
        """메시지 수신용 숨겨진 윈도우 생성"""
        # 윈도우 프로시저 콜백 생성
        self.wnd_proc_func = WNDPROC(self._window_proc)

        # 윈도우 클래스 등록
        h_inst = kernel32.GetModuleHandleW(None)
        class_name = "WMCAMessageWindow"

        wnd_class = WNDCLASSEX()
        wnd_class.cbSize = ctypes.sizeof(WNDCLASSEX)
        wnd_class.lpfnWndProc = self.wnd_proc_func
        wnd_class.hInstance = h_inst
        wnd_class.lpszClassName = class_name

        class_atom = user32.RegisterClassExW(ctypes.byref(wnd_class))
        if not class_atom:
            print(f"✗ 윈도우 클래스 등록 실패")
            return None

        # 윈도우 생성 (메시지 전용)
        hwnd = user32.CreateWindowExW(
            0,
            class_name,
            "WMCA Message Window",
            0,  # WS_OVERLAPPEDWINDOW 대신 0 사용 (숨겨진 윈도우)
            0, 0, 0, 0,
            None, None, h_inst, None
        )

        if not hwnd:
            print(f"✗ 윈도우 생성 실패")
            return None

        print(f"✓ 메시지 윈도우 생성: HWND={hwnd}")
        return hwnd

    def process_messages(self, timeout_seconds=5):
        """Windows 메시지 처리 (타임아웃 포함)"""
        msg = MSG()
        start_time = time.time()

        print(f"메시지 대기 중... (최대 {timeout_seconds}초)")

        while time.time() - start_time < timeout_seconds:
            # 메시지 확인 (블로킹하지 않음)
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE = 1
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

                # 로그인 결과가 나오면 종료
                if self.login_result is not None:
                    return self.login_result

            time.sleep(0.1)  # CPU 사용률 감소

        print("⚠️  타임아웃: 응답을 받지 못했습니다.")
        return False

    def load(self):
        """WMCA 모듈 로드"""
        result = self.wmca_load()
        if result:
            print("✓ WMCA 모듈 로드 성공")
            return True
        else:
            print("✗ WMCA 모듈 로드 실패")
            return False

    def set_server(self, server: str):
        """서버 주소 설정"""
        result = self.wmca_set_server(server.encode('utf-8'))
        if result:
            print(f"✓ 서버 설정: {server}")
            return True
        return False

    def set_port(self, port: int):
        """포트 설정"""
        result = self.wmca_set_port(port)
        if result:
            print(f"✓ 포트 설정: {port}")
            return True
        return False

    def connect(self, user_id: str, password: str, cert_password: str,
                 media_type: str = 'T', user_type: str = 'W'):
        """로그인 시도

        Args:
            user_id: 사용자 ID
            password: 비밀번호
            cert_password: 인증서 비밀번호
            media_type: 매체 타입 (기본값: 'T' - 예제 코드와 동일)
            user_type: 사용자 타입 (기본값: 'W' - 예제 코드와 동일)
        """
        if not self.hwnd:
            print("✗ 메시지 윈도우가 생성되지 않았습니다.")
            return False

        print(f"로그인 파라미터: MediaType='{media_type}', UserType='{user_type}'")

        # char 타입으로 변환 (ord()로 정수값으로 전달)
        media_char = ord(media_type[0])  # 'T' -> 84
        user_char = ord(user_type[0])    # 'W' -> 87

        result = self.wmca_connect(
            self.hwnd,
            CA_WMCAEVENT,
            media_char,  # char (정수)
            user_char,   # char (정수)
            user_id.encode('utf-8'),
            password.encode('utf-8'),
            cert_password.encode('utf-8')
        )

        if result:
            print("✓ 로그인 요청 전송 성공 (응답 대기 중...)")
            return True
        else:
            print("✗ 로그인 요청 전송 실패")
            return False

    def disconnect(self):
        """연결 종료"""
        result = self.wmca_disconnect()
        if result:
            print("✓ 연결 종료 요청")
            return True
        return False

    def free(self):
        """WMCA 모듈 해제"""
        if self.wmca_free:
            self.wmca_free()
            print("✓ WMCA 모듈 해제")

    def cleanup(self):
        """정리 작업"""
        if self.connected:
            self.disconnect()
        self.free()
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)


def main():
    """메인 함수"""
    print("=" * 70)
    print("NH증권 WMCA API 로그인 - Windows 메시지 처리 버전")
    print("=" * 70)

    # DLL 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dll_path = os.path.join(script_dir, "bin", "wmca.dll")

    if not os.path.exists(dll_path):
        print(f"✗ DLL 파일을 찾을 수 없습니다: {dll_path}")
        return

    # 사용자 입력
    print("\n로그인 정보를 입력하세요:")
    user_id = input("사용자 ID: ").strip()
    password = input("비밀번호: ").strip()
    cert_password = input("인증서 비밀번호: ").strip()

    if not all([user_id, password, cert_password]):
        print("✗ 필수 정보가 입력되지 않았습니다.")
        return

    # 클라이언트 생성
    client = WMCAClient(dll_path)

    try:
        # 1. WMCA 모듈 로드
        if not client.load():
            return

        # 2. 메시지 윈도우 생성
        client.hwnd = client.create_message_window()
        if not client.hwnd:
            return

        # 3. 서버/포트는 DLL 내장 기본값 사용 (wmca.nhqv.com:8200)
        print("\n✓ 서버: DLL 내장 기본값 사용 (wmca.nhqv.com:8200)")

        # 4. 로그인
        print("\n로그인 시도 중...")
        if not client.connect(user_id, password, cert_password):
            return

        # 5. 메시지 처리 (응답 대기)
        success = client.process_messages(timeout_seconds=10)

        if success:
            print("\n" + "=" * 70)
            print("로그인 완료!")
            print("=" * 70)

            # 잠시 대기
            print("\n5초 후 로그아웃합니다...")
            time.sleep(5)

            client.disconnect()
            client.process_messages(timeout_seconds=2)
        else:
            print("\n✗ 로그인 실패")

    finally:
        client.cleanup()

    print("\n프로그램 종료")


if __name__ == "__main__":
    main()
