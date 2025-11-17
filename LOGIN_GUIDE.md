# NH증권 WMCA API 로그인 가이드

## 개요
이 가이드는 NH증권의 WMCA (Wireless Mobile Connected Application) API를 사용하여 로그인하는 방법을 설명합니다.

## 파일 설명

- **login_example.py**: Python 버전 (권장 - 더 간단함)
- **login_example.cpp**: C++ 버전
- **SDK.pdf**: WMCA API 상세 문서
- **FAQ.pdf**: 자주 묻는 질문

## 요구사항

### Python 버전
- Windows OS (서버 연결이 Windows 환경 필요)
- Python 3.6+
- wmca.dll 파일이 시스템 경로에 있어야 함:
  - C:\Windows\System32\
  - 또는 프로그램과 같은 디렉토리

### C++ 버전
- Visual Studio 2015 이상
- Windows 운영체제
- wmca.dll 파일

## wmca.dll 위치 찾기

wmca.dll은 보통 다음 위치에 있습니다:

1. **NH증권 트레이딩 플랫폼 설치 디렉토리**
   ```
   C:\Program Files\NH증권\...
   ```

2. **Windows 시스템 디렉토리**
   ```
   C:\Windows\System32\wmca.dll
   ```

3. **찾는 방법**
   ```bash
   # Windows 명령 프롬프트
   where wmca.dll

   # 또는 PowerShell
   Get-ChildItem -Path C: -Filter wmca.dll -Recurse
   ```

## Python 사용 방법

### 1. 스크립트 실행
```bash
python login_example.py
```

### 2. 입력 정보
프로그램이 다음 정보를 요청합니다:

- **서버 주소** (기본값: 127.0.0.1)
  - NH증권 서버 주소
  - 기본값으로 사용 가능

- **포트 번호** (기본값: 9000)
  - NH증권 서버 포트
  - 기본값으로 사용 가능

- **사용자 ID**
  - NH증권 계좌 ID

- **비밀번호**
  - 로그인 비밀번호

- **인증서 비밀번호**
  - 공인인증서 또는 보안카드 비밀번호

### 3. 실행 흐름

```
1. DLL 로드
   ├─ wmca.dll 파일 찾기
   ├─ 함수 포인터 설정

2. WMCA 모듈 로드
   ├─ 모듈 초기화

3. 서버 설정
   ├─ 서버 주소 설정
   ├─ 포트 설정

4. 로그인
   ├─ 사용자 ID, 비밀번호 전송

5. 연결 확인
   ├─ 서버 연결 상태 확인

6. 정리
   ├─ 로그아웃
   ├─ 모듈 해제
```

## C++ 사용 방법

### 1. 컴파일

Visual Studio에서:
```
1. 새 Console Application 프로젝트 생성
2. login_example.cpp 추가
3. 빌드
```

또는 명령줄에서 (Visual Studio 설치 필요):
```bash
cl login_example.cpp
```

### 2. 실행
```bash
login_example.exe
```

### 3. 입력 정보
Python과 동일합니다.

## 구조 설명

### Python 코드 주요 클래스

```python
class WMCAClient:
    def __init__(self, dll_path="wmca.dll")
    def load()                    # WMCA 모듈 로드
    def set_server(address)       # 서버 주소 설정
    def set_port(port)            # 포트 설정
    def connect(id, pw, cert_pw)  # 로그인
    def disconnect()              # 로그아웃
    def free()                    # 모듈 해제
```

### C++ 코드 주요 메서드

```cpp
class WMCAClient {
    bool LoadDLL(const char* path)           // DLL 로드
    bool Load()                              // 모듈 로드
    bool SetServer(const char* server)       // 서버 설정
    bool SetPort(int port)                   // 포트 설정
    bool IsConnected()                       // 연결 상태 확인
    bool Connect(id, pw, cert_pw, ...)       // 로그인
    bool Disconnect()                        // 로그아웃
    bool Free()                              // 모듈 해제
};
```

## 오류 해결

### 1. "wmca.dll을 찾을 수 없습니다"
- wmca.dll 파일 위치 확인
- 시스템 경로에 DLL 복사
- 또는 프로그램과 같은 디렉토리에 복사

### 2. "함수 포인터 설정 실패"
- DLL 버전 확인
- SDK.pdf 문서에서 함수 이름 확인

### 3. "로그인 실패"
- 서버 주소 확인
- 포트 번호 확인
- 사용자 ID, 비밀번호 확인
- 공인인증서 설치 확인
- wmca.log 파일 확인 (로그 분석)

### 4. 로그 파일 분석
프로그램 실행 디렉토리에 wmca.log 파일이 생성됩니다.
이 파일을 열어 상세한 오류 정보를 확인할 수 있습니다.

```
wmca.log 위치: [프로그램 실행 디렉토리]/wmca.log
```

## 참고 자료

### API 문서
- **SDK.pdf**: WMCA API 상세 함수 설명
- **FAQ.pdf**: 자주 묻는 질문 및 해결 방법
- **시세_SPEC_20201015.pdf**: 시세 조회 함수 명세
- **주문_SPEC_20190919.pdf**: 주문 함수 명세

### 주요 함수

| 함수 | 설명 |
|------|------|
| wmcaLoad() | WMCA 모듈 로드 |
| wmcaSetServer() | 서버 주소 설정 |
| wmcaSetPort() | 포트 설정 |
| wmcaConnect() | 로그인 |
| wmcaDisconnect() | 로그아웃 |
| wmcaTransact() | 주문 처리 |
| wmcaQuery() | 데이터 조회 |
| wmcaAttach() | 실시간 시세 구독 |
| wmcaDetach() | 실시간 시세 구독 해제 |

## 다음 단계

### 1. 시세 조회
- wmcaQuery() 함수 사용
- 시세_SPEC 문서 참고

### 2. 주문 처리
- wmcaTransact() 함수 사용
- 주문_SPEC 문서 참고

### 3. 실시간 시세
- wmcaAttach() / wmcaDetach() 사용
- 구독할 종목 코드 필요

## 주의사항

1. **보안**: 비밀번호는 절대 하드코딩하지 마세요
2. **메모리**: DLL 로드 후 반드시 Free() 호출
3. **연결**: 프로그램 종료 전 반드시 Disconnect() 호출
4. **Windows 환경**: Linux/Mac에서는 실행 불가능

## 라이선스 및 지원

- NH증권 공식 API
- 지원: NH증권 콜센터 또는 공식 문서 참고
- 상세한 내용은 SDK.pdf 및 FAQ.pdf 참고
