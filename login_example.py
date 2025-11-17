#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NH증권 WMCA API를 이용한 로그인 예제
Windows 환경에서만 실행 가능합니다.
"""

import os
import sys
import ctypes
from ctypes import c_char_p, c_int, c_bool, c_void_p, CFUNCTYPE
import time
from typing import Optional

# Windows 환경 확인
if sys.platform != "win32":
    print("이 스크립트는 Windows 환경에서만 실행 가능합니다.")
    sys.exit(1)


class LOGININFO(ctypes.Structure):
    """로그인 정보 구조체"""
    _fields_ = [
        ("szDate", ctypes.c_char * 14),        # 접속시간
        ("szServerName", ctypes.c_char * 15),  # 서버명
        ("szUserID", ctypes.c_char * 8),       # 사용자ID
        ("szAccountCount", ctypes.c_char * 3), # 계좌수
        # ACCOUNTINFO 배열은 복잡하므로 생략
    ]


class WMCAClient:
    """WMCA API 클라이언트"""

    def __init__(self, dll_path: str = "wmca.dll"):
        """
        WMCA DLL 초기화

        Args:
            dll_path: wmca.dll의 경로
        """
        self.dll_path = dll_path
        self.dll = None
        self.connected = False

        # DLL의 함수 포인터들
        self.wmca_load = None
        self.wmca_free = None
        self.wmca_set_server = None
        self.wmca_set_port = None
        self.wmca_is_connected = None
        self.wmca_connect = None
        self.wmca_disconnect = None
        self.wmca_set_option = None

        # DLL 로드 및 함수 초기화
        self._load_dll()

    def _load_dll(self):
        """DLL 로드 및 함수 포인터 설정"""
        try:
            # DLL 경로를 절대 경로로 변환
            dll_abs_path = os.path.abspath(self.dll_path)

            # DLL이 있는 디렉토리를 PATH에 추가 (의존성 DLL도 로드하기 위해)
            dll_dir = os.path.dirname(dll_abs_path)
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

            # DLL 로드
            self.dll = ctypes.WinDLL(dll_abs_path)
            print(f"✓ {dll_abs_path} 로드 성공")
        except OSError as e:
            print(f"✗ {self.dll_path} 로드 실패: {e}")
            print(f"  DLL 파일이 다음 경로에 있는지 확인하세요:")
            print(f"  - C:\\Windows\\System32\\")
            print(f"  - C:\\Program Files\\\\")
            print(f"  - 또는 현재 디렉토리: {os.getcwd()}")
            sys.exit(1)

        try:
            # 함수 포인터 설정
            self.wmca_load = self.dll.wmcaLoad
            self.wmca_free = self.dll.wmcaFree
            self.wmca_set_server = self.dll.wmcaSetServer
            self.wmca_set_port = self.dll.wmcaSetPort
            self.wmca_is_connected = self.dll.wmcaIsConnected
            self.wmca_connect = self.dll.wmcaConnect
            self.wmca_disconnect = self.dll.wmcaDisconnect
            self.wmca_set_option = self.dll.wmcaSetOption

            print("✓ 함수 포인터 설정 완료")
        except AttributeError as e:
            print(f"✗ 함수 포인터 설정 실패: {e}")
            sys.exit(1)

    def load(self) -> bool:
        """DLL 로드"""
        try:
            result = self.wmca_load()
            if result:
                print("✓ WMCA 모듈 로드 성공")
                return True
            else:
                print("✗ WMCA 모듈 로드 실패")
                return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def set_server(self, server_address: str) -> bool:
        """
        서버 설정

        Args:
            server_address: 서버 주소 (예: "127.0.0.1")

        Returns:
            성공 여부
        """
        try:
            result = self.wmca_set_server(server_address.encode('utf-8'))
            if result:
                print(f"✓ 서버 설정 완료: {server_address}")
                return True
            else:
                print(f"✗ 서버 설정 실패: {server_address}")
                return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def set_port(self, port: int) -> bool:
        """
        포트 설정

        Args:
            port: 포트 번호

        Returns:
            성공 여부
        """
        try:
            result = self.wmca_set_port(port)
            if result:
                print(f"✓ 포트 설정 완료: {port}")
                return True
            else:
                print(f"✗ 포트 설정 실패: {port}")
                return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def is_connected(self) -> bool:
        """
        연결 상태 확인

        Returns:
            연결 여부
        """
        try:
            result = self.wmca_is_connected()
            return bool(result)
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def connect(self, user_id: str, password: str, cert_password: str,
                media_type: str = "T", user_type: str = "W") -> bool:
        """
        서버에 로그인

        Args:
            user_id: 사용자 ID
            password: 사용자 비밀번호
            cert_password: 인증서 비밀번호
            media_type: 매체 종류 (기본값: "T")
            user_type: 사용자 종류 (기본값: "W" = 개인)

        Returns:
            성공 여부
        """
        try:
            # 문자열을 바이트로 변환
            user_id_bytes = user_id.encode('utf-8')
            password_bytes = password.encode('utf-8')
            cert_password_bytes = cert_password.encode('utf-8')
            media_type_bytes = media_type.encode('utf-8')
            user_type_bytes = user_type.encode('utf-8')

            # Connect 함수 호출
            # 참고: HWND는 메시지 수신을 위한 윈도우 핸들이므로, 콘솔 앱에서는 NULL(0) 사용
            result = self.wmca_connect(
                c_void_p(0),  # HWND hWnd (NULL)
                ctypes.c_ulong(0),  # DWORD dwMsg
                media_type_bytes[0:1],  # char cMediaType
                user_type_bytes[0:1],   # char cUserType
                user_id_bytes,  # const char* pszID
                password_bytes,  # const char* pszPassword
                cert_password_bytes  # const char* pszSignPassword
            )

            if result:
                print(f"✓ 로그인 성공: {result}")
                self.connected = True
                return True
            else:
                print(f"✗ 로그인 실패")
                return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False

    def disconnect(self) -> bool:
        """
        서버에서 로그아웃

        Returns:
            성공 여부
        """
        try:
            result = self.wmca_disconnect()
            if result:
                print("✓ 로그아웃 성공")
                self.connected = False
                return True
            else:
                print("✗ 로그아웃 실패")
                return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def free(self) -> bool:
        """WMCA 모듈 해제"""
        try:
            result = self.wmca_free()
            if result:
                print("✓ WMCA 모듈 해제 완료")
                return True
            else:
                print("✗ WMCA 모듈 해제 실패")
                return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def cleanup(self):
        """정리 작업"""
        if self.connected:
            self.disconnect()
        self.free()


def main():
    """메인 함수"""
    print("=" * 60)
    print("NH증권 WMCA API 로그인 예제")
    print("=" * 60)

    # DLL 경로 설정 (현재 스크립트 디렉토리의 wmca.dll)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dll_path = os.path.join(script_dir, "bin", "wmca.dll")

    print(f"\nDLL 경로: {dll_path}")
    print(f"DLL 파일 존재: {os.path.exists(dll_path)}\n")

    # 설정값 입력
    print("다음 정보를 입력하세요:")
    server = input("서버 주소 (기본값: wmca.nhqv.com): ").strip() or "wmca.nhqv.com"
    port = input("포트 번호 (기본값: 8200): ").strip()
    port = int(port) if port else 8200

    user_id = input("사용자 ID: ").strip()
    password = input("비밀번호: ").strip()
    cert_password = input("인증서 비밀번호: ").strip()

    if not user_id or not password or not cert_password:
        print("✗ 필수 정보가 입력되지 않았습니다.")
        return

    # WMCA 클라이언트 생성 (DLL 경로 지정)
    client = WMCAClient(dll_path=dll_path)

    try:
        # 1. DLL 로드
        if not client.load():
            return

        # 2. 서버 설정
        if not client.set_server(server):
            return

        # 3. 포트 설정
        if not client.set_port(port):
            return

        # 4. 로그인 시도
        print("\n로그인 시도 중...")
        if not client.connect(user_id, password, cert_password):
            return

        # 5. 연결 상태 확인
        print("\n연결 상태 확인 중...")
        if client.is_connected():
            print("✓ 서버와 연결되어 있습니다.")
        else:
            print("✗ 서버와 연결되어 있지 않습니다.")

        # 6. 잠깐 대기 (로그인 메시지 수신 대기)
        print("\n5초 대기 중... (메시지 수신 대기)")
        time.sleep(5)

        # 7. 로그아웃
        print("\n로그아웃 처리 중...")
        client.disconnect()

    finally:
        # 정리 작업
        client.cleanup()

    print("=" * 60)
    print("프로그램 종료")
    print("=" * 60)


if __name__ == "__main__":
    main()
