# Claude Code 작업 기록

## 작업 날짜: 2025-10-22

### 요청 사항
NH증권 증권사 서버에 연결하는 API를 Python 또는 C++로 감싸서 로그인만 시도할 수 있도록 하는 코드 작성

### 작업 내용

#### 1. API 분석
- api 폴더의 구조 확인
- SAMPLES/VC++ 폴더의 샘플 코드 분석
- WmcaIntf.h, WmcaIntf.cpp 코드 분석
- 주요 함수 포인터 구조 파악:
  - wmcaLoad()
  - wmcaSetServer()
  - wmcaSetPort()
  - wmcaConnect()
  - wmcaDisconnect()
  - wmcaFree()

#### 2. Python 로그인 코드 작성 (login_example.py)
- **파일 위치**: /home/odumag99/stock-system/trading-system/api/login_example.py
- **주요 기능**:
  - WMCAClient 클래스 구현
  - ctypes를 이용한 wmca.dll DLL 호출
  - 자동 DLL 로드 및 함수 포인터 설정
  - 서버/포트 설정
  - 로그인 (Connect) 기능
  - 로그아웃 (Disconnect) 기능
  - 모듈 정리 (Free) 기능
  - 오류 처리 및 사용자 친화적 메시지

**핵심 메서드**:
```python
- load()                          # WMCA 모듈 로드
- set_server(address)             # 서버 주소 설정
- set_port(port)                  # 포트 설정
- connect(id, pw, cert_pw)        # 로그인
- disconnect()                    # 로그아웃
- is_connected()                  # 연결 상태 확인
- free()                          # 모듈 해제
- cleanup()                       # 정리 작업
```

#### 3. C++ 로그인 코드 작성 (login_example.cpp)
- **파일 위치**: /home/odumag99/stock-system/trading-system/api/login_example.cpp
- **주요 기능**:
  - WMCAClient 클래스 구현 (C++)
  - Windows API를 이용한 DLL 로드 및 함수 포인터 설정
  - Python 버전과 동일한 기능 제공
  - Visual Studio 컴파일 가능

**핵심 메서드**:
```cpp
- LoadDLL(path)                   // DLL 로드
- Load()                          // 모듈 로드
- SetServer(address)              // 서버 설정
- SetPort(port)                   // 포트 설정
- IsConnected()                   // 연결 상태 확인
- Connect(id, pw, cert_pw)        // 로그인
- Disconnect()                    // 로그아웃
- Free()                          // 모듈 해제
- Cleanup()                       // 정리
```

#### 4. 사용 설명서 작성 (LOGIN_GUIDE.md)
- **파일 위치**: /home/odumag99/stock-system/trading-system/api/LOGIN_GUIDE.md
- **포함 내용**:
  - 개요 및 요구사항
  - wmca.dll 위치 찾는 방법
  - Python/C++ 사용 방법
  - 실행 흐름 다이어그램
  - 구조 설명
  - 오류 해결 가이드
  - 참고 자료 및 다음 단계

### 생성된 파일

| 파일명 | 설명 | 크기 |
|--------|------|------|
| login_example.py | Python 로그인 예제 | ~8KB |
| login_example.cpp | C++ 로그인 예제 | ~9KB |
| LOGIN_GUIDE.md | 사용 설명서 | ~6KB |
| CLAUDE.md | 이 파일 - 작업 기록 | - |

### 주요 기술 스택

#### Python 버전
- **언어**: Python 3.6+
- **라이브러리**: ctypes (표준 라이브러리)
- **DLL 호출**: ctypes를 통한 Windows DLL 직접 호출

#### C++ 버전
- **언어**: C++ (ISO C++11 이상)
- **API**: Windows API (LoadLibrary, GetProcAddress)
- **컴파일러**: Visual Studio 2015+
- **표준 라이브러리**: windows.h, stdio.h, iostream, string

### API 함수 매핑

#### 사용된 WMCA API 함수

| C++ 함수명 | 타입 정의 | 설명 |
|-----------|---------|------|
| wmcaLoad | BOOL() | WMCA 모듈 로드 |
| wmcaFree | BOOL() | WMCA 모듈 해제 |
| wmcaSetServer | BOOL(const char*) | 서버 주소 설정 |
| wmcaSetPort | BOOL(int) | 포트 번호 설정 |
| wmcaIsConnected | BOOL() | 연결 상태 확인 |
| wmcaConnect | BOOL(HWND, DWORD, char, char, const char*, const char*, const char*) | 로그인 |
| wmcaDisconnect | BOOL() | 로그아웃 |

### 실행 흐름

```
프로그램 시작
    ↓
DLL 로드 (wmca.dll)
    ↓
함수 포인터 획득
    ↓
WMCA 모듈 초기화 (wmcaLoad)
    ↓
서버 주소 설정 (wmcaSetServer)
    ↓
포트 설정 (wmcaSetPort)
    ↓
로그인 시도 (wmcaConnect)
    ├─ 성공 → 연결 상태 확인
    └─ 실패 → 오류 메시지
    ↓
5초 대기 (메시지 수신)
    ↓
로그아웃 (wmcaDisconnect)
    ↓
모듈 정리 (wmcaFree)
    ↓
프로그램 종료
```

### 중요 사항

1. **보안**
   - 비밀번호는 절대 소스 코드에 하드코딩하지 말 것
   - 환경 변수나 설정 파일에서 읽을 것

2. **Windows 전용**
   - wmca.dll은 Windows API이므로 Windows 환경에서만 실행 가능
   - Linux/Mac에서는 실행 불가능

3. **DLL 위치**
   - 기본적으로 C:\Windows\System32\ 또는 프로그램 디렉토리에서 찾음
   - NH증권 트레이딩 플랫폼 설치 필요

4. **메모리 관리**
   - DLL 로드 후 반드시 해제 필요
   - 프로그램 종료 시 Cleanup() 호출 필수

### 다음 단계 (향후 작업 가능)

1. **시세 조회 기능 추가**
   - wmcaQuery() 함수 활용
   - 시세_SPEC 문서 참고

2. **주문 기능 추가**
   - wmcaTransact() 함수 활용
   - 주문_SPEC 문서 참고

3. **실시간 시세 구독**
   - wmcaAttach() / wmcaDetach() 함수 활용

4. **데이터베이스 연동**
   - 조회한 데이터를 DB에 저장

5. **REST API 래핑**
   - Flask/FastAPI로 HTTP 엔드포인트 제공

6. **GUI 인터페이스**
   - PyQt/PySimpleGUI로 GUI 추가

### 참고 자료

#### API 사용 시 필수 참고 문서
앞으로 NH증권 OpenAPI 사용 시 다음 문서들을 반드시 참고하세요:

1. **SDK.pdf**: WMCA API 함수 상세 설명서
   - DLL 함수 호출 규약 (stdcall)
   - 응답 메시지 종류 및 처리 방법
   - 함수 프로토타입 및 사용 예제

2. **FAQ.pdf**: 자주 묻는 질문 및 해결 방법
   - 일반적인 오류 해결 방법
   - 개발 시 주의사항

3. **시세_SPEC_20201015.pdf**: 시세 조회 TR 명세서
   - 조회 가능한 시세 서비스 목록
   - 입/출력 데이터 구조체 정의

4. **주문_SPEC_20190919.pdf**: 주문/정정/취소 TR 명세서
   - 주문 관련 서비스 목록
   - 입/출력 데이터 구조체 정의

5. **api/SAMPLES/VC++**: 공식 C++ 샘플 코드
   - WMCALOADERDlg.cpp: 메시지 핸들러 예제
   - WmcaIntf.cpp: DLL 래핑 클래스 예제

### 테스트 환경 요구사항

- Windows OS (7, 10, 11 이상)
- Python 3.6+ (Python 버전 사용 시)
- Visual Studio 2015+ (C++ 버전 컴파일 시)
- NH증권 트레이딩 플랫폼 설치 (wmca.dll 포함)
- 유효한 NH증권 계좌 및 공인인증서

### DLL 응답 메시지 처리 방식 (중요!)

#### Windows 메시지 기반 비동기 통신
WMCA DLL 함수들은 **Windows 메시지 큐를 통해 비동기로 응답을 전달**합니다.

#### 응답 메시지 종류 (SDK.pdf 페이지 11 참고)

| 메시지 상수 | 값 | 설명 | 발생 상황 |
|------------|-------|------|----------|
| CA_CONNECTED | WM_USER+110 | 로그인 성공 | wmcaConnect() 성공 시 |
| CA_DISCONNECTED | WM_USER+120 | 연결 해제 | wmcaDisconnect() 호출 시 |
| CA_SOCKETERROR | WM_USER+130 | 통신 오류 | 네트워크 장애, 서버 오류 시 |
| CA_RECEIVEDATA | WM_USER+210 | TR 결과 수신 | wmcaQuery() 응답 데이터 |
| CA_RECEIVESISE | WM_USER+220 | 실시간 시세 수신 | wmcaAttach() 실시간 데이터 |
| CA_RECEIVEMESSAGE | WM_USER+230 | 상태 메시지 | 처리 상태 문자열 메시지 |
| CA_RECEIVECOMPLETE | WM_USER+240 | 처리 완료 | TR 정상 완료 |
| CA_RECEIVEERROR | WM_USER+250 | 처리 실패 | TR 처리 실패, 입력값 오류 |

#### 메시지 수신 처리 예제 (VC++ 샘플 코드 참고)

```cpp
// 1. 메시지 핸들러 등록 (WMCALOADERDlg.cpp:103)
ON_MESSAGE(CA_WMCAEVENT, OnWmcaEvent)

// 2. 이벤트 분기 처리 (WMCALOADERDlg.cpp:273-305)
LRESULT CWMCALOADERDlg::OnWmcaEvent(WPARAM dwMessageType, LPARAM lParam)
{
    switch(dwMessageType) {
    case CA_CONNECTED:           // 로그인 성공
        OnWmConnected((LOGINBLOCK*)lParam);
        break;
    case CA_DISCONNECTED:        // 접속 해제
        OnWmDisconnected();
        break;
    case CA_SOCKETERROR:         // 통신 오류
        OnWmSocketerror((int)lParam);
        break;
    case CA_RECEIVEDATA:         // TR 데이터 수신
        OnWmReceivedata((OUTDATABLOCK*)lParam);
        break;
    case CA_RECEIVESISE:         // 실시간 시세 수신
        OnWmReceivesise((OUTDATABLOCK*)lParam);
        break;
    case CA_RECEIVEMESSAGE:      // 상태 메시지
        OnWmReceivemessage((OUTDATABLOCK*)lParam);
        break;
    case CA_RECEIVECOMPLETE:     // 처리 완료
        OnWmReceivecomplete((OUTDATABLOCK*)lParam);
        break;
    case CA_RECEIVEERROR:        // 처리 실패
        OnWmReceiveerror((OUTDATABLOCK*)lParam);
        break;
    }
    return TRUE;
}
```

#### 로그인 성공 시 계좌 정보 수신 (WMCALOADERDlg.cpp:307-357)

```cpp
void OnWmConnected(LOGINBLOCK* pLogin)
{
    // 1. 접속 시간 정보
    char szText[256] = {0};
    strncpy(szText, pLogin->pLoginInfo->szDate, sizeof(pLogin->pLoginInfo->szDate));

    // 2. 계좌번호 목록 파싱
    char szAccountCount[8] = {0};
    strncpy(szAccountCount, pLogin->pLoginInfo->szAccountCount, sizeof(pLogin->pLoginInfo->szAccountCount));
    int nAccountCount = atoi(szAccountCount);

    // 3. 계좌번호별 정보 추출
    for(int i = 0; i < nAccountCount; i++) {
        char szAccountNo[16] = {0};
        strncpy(szAccountNo, (char*)&pLogin->pLoginInfo->accountlist[i].szAccountNo,
                sizeof(pLogin->pLoginInfo->accountlist[i].szAccountNo));

        // 계좌번호 인덱스는 1부터 시작 (중요!)
        // wmcaQuery() 호출 시 이 인덱스 사용
    }
}
```

#### TR 조회 결과 수신 (WMCALOADERDlg.cpp:382-517)

```cpp
void OnWmReceivedata(OUTDATABLOCK* pOutData)
{
    // TRID로 어떤 TR의 응답인지 구분
    switch(pOutData->TrIndex) {
    case TRID_c1101:  // 현재가 조회
        if(strcmp(pOutData->pData->szBlockName, "c1101OutBlock") == 0) {
            Tc1101OutBlock* pBlock = (Tc1101OutBlock*)pOutData->pData->szData;
            // 단일 블록 데이터 처리
        }
        else if(strcmp(pOutData->pData->szBlockName, "c1101OutBlock2") == 0) {
            Tc1101OutBlock2* pBlock = (Tc1101OutBlock2*)pOutData->pData->szData;
            // 반복 블록 데이터 처리 (예: 체결내역)
            int nOccursCount = pOutData->pData->nLen / sizeof(Tc1101OutBlock2);
            for(int i = 0; i < nOccursCount; i++) {
                // 각 레코드 처리
                pBlock++;  // 다음 레코드로 이동
            }
        }
        break;
    }
}
```

#### Python에서 메시지 수신 처리 방법

Python에서는 Windows 메시지 루프를 직접 구현해야 합니다:

```python
import ctypes
from ctypes import wintypes
import win32gui
import win32con

# 1. 메시지 상수 정의
CA_CONNECTED = win32con.WM_USER + 110
CA_RECEIVEDATA = win32con.WM_USER + 210
# ... 기타 메시지 상수

# 2. 윈도우 프로시저 콜백 정의
def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == CA_CONNECTED:
        print("로그인 성공!")
        # LOGINBLOCK 구조체 파싱
    elif msg == CA_RECEIVEDATA:
        print("데이터 수신!")
        # OUTDATABLOCK 구조체 파싱
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

# 3. 숨김 윈도우 생성 (메시지 수신용)
wc = win32gui.WNDCLASS()
wc.lpfnWndProc = wnd_proc
wc.lpszClassName = "WMCA_HIDDEN_WINDOW"
win32gui.RegisterClass(wc)
hwnd = win32gui.CreateWindow(wc.lpszClassName, "", 0, 0, 0, 0, 0, 0, 0, 0, None)

# 4. 메시지 루프 실행
win32gui.PumpMessages()
```

### 알려진 제약사항

1. Windows 환경에서만 실행 가능
2. wmca.dll이 시스템에 설치되어 있어야 함
3. **메시지 수신을 위해 Windows 메시지 루프가 필요** (콘솔에서는 제한적)
4. Python에서는 pywin32 패키지 필요 (메시지 루프 처리)
5. 계좌번호 인덱스는 **1부터 시작** (0이 아님에 주의!)

---

**작업 완료 날짜**: 2025-10-22
**사용 언어**: Python 3, C++
**총 파일 수**: 4개 (login_example.py, login_example.cpp, LOGIN_GUIDE.md, CLAUDE.md)

---

## 작업 날짜: 2025-11-06

### CRITICAL: Windows 메시지 콜백에서의 메모리 생명주기

#### 가장 중요한 발견

**Windows 메시지 콜백에서 받은 lparam 포인터는 콜백 함수가 반환되면 즉시 무효화됩니다!**

DLL이 보내는 lparam은 임시 메모리를 가리키는 포인터입니다. 콜백이 끝나면 DLL이 해당 메모리를 해제하므로, **반드시 콜백 함수 안에서 즉시 파싱하고 Python 객체로 복사**해야 합니다.

#### 메모리 생명주기 타이밍

```
Time    DLL                          Python 콜백
----    ---                          -----------
T0:     메모리 할당 (0x6681120)
        LOGININFO 구조체 채움

T1:     SendMessage(CA_CONNECTED, lparam=0x6681120)
                                     ↓
T2:                                  _wnd_proc() 호출
                                     lparam = 0x6681120 (✅ 유효함!)

T3:                                  ✅ login_block = cast(lparam, ...)
                                     ✅ login_time = login_info.szDate.decode()
                                     ✅ accounts = [...] (Python 객체로 복사)

T4:                                  _wnd_proc() return
        ↓
T5:     메모리 해제 (0x6681120)     ← 이제 lparam은 무효!

T6:                                  ❌ 이 시점에 lparam 접근하면 실패!
                                     (이미 해제된 메모리 = 쓰레기 데이터)
```

#### ❌ 잘못된 방법 (실패)

```python
def _wnd_proc(self, hwnd, msg, wparam, lparam):
    if msg == CA_WMCAEVENT:
        # ❌ 포인터만 저장하고 나중에 파싱
        self.message_queue.put((msg_type, wparam, lparam))
        return 0

def login(self):
    # ❌ 큐에서 꺼낼 때는 이미 DLL이 메모리 해제함!
    msg_type, wparam, lparam = self.message_queue.get()
    login_block = ctypes.cast(lparam, POINTER(LoginBlock)).contents
    # 결과: 쓰레기 데이터 읽음 (TrIndex = 77501628 같은 이상한 값)
```

**문제점:**
- lparam은 단순 정수(메모리 주소)
- 콜백이 끝나면 DLL이 해당 주소의 메모리 해제
- 나중에 읽으려 하면 이미 해제된 메모리 접근 → 쓰레기 데이터

#### ✅ 올바른 방법 (성공)

```python
def _handle_wmca_message(self, msg_type, wparam, lparam):
    """
    CRITICAL: lparam이 가리키는 메모리는 이 함수가 반환된 후 DLL이 해제합니다.
    따라서 lparam을 즉시 파싱해서 Python 객체로 변환한 후 큐에 저장해야 합니다.
    """
    if msg_type == WMCAMessage.CA_CONNECTED:
        # ✅ lparam이 유효한 지금 즉시 파싱!
        login_block = ctypes.cast(lparam, POINTER(LoginBlock)).contents
        login_info = login_block.pLoginInfo.contents

        # ✅ 즉시 문자열로 복사 (C 메모리 → Python 힙 메모리)
        login_time = login_info.szDate.decode('cp949').strip()
        server_name = login_info.szServerName.decode('cp949').strip()
        account_count = int(login_info.szAccountCount.decode('cp949').strip())

        # ✅ 계좌 목록도 즉시 복사
        accounts = []
        for i in range(account_count):
            acc_no = login_info.accountlist[i].szAccountNo.decode('cp949').strip()
            accounts.append(acc_no)

        # ✅ Python 객체로 변환 (lparam과 독립적)
        parsed_data = LoginResponse(
            success=True,
            login_time=login_time,
            account_count=account_count,
            accounts=accounts
        )

        # ✅ 파싱된 Python 객체를 큐에 저장 (포인터가 아님!)
        self.message_queue.put((msg_type, parsed_data))

def login(self):
    # ✅ 이미 파싱된 Python 객체를 받음
    msg_type, parsed_data = self.message_queue.get()
    return parsed_data  # LoginResponse 객체 (안전!)
```

#### 메모리 복사 과정

```python
# DLL의 C 메모리 (DLL 소유, 임시):
# 주소 0x6681120:
# "20251106141012htsi194       odumag99005..."
#  [접속시간]    [서버명]      [ID][계좌수]

# decode()를 호출하면:
login_time = login_info.szDate.decode('cp949')
# ↓
# Python str 객체로 복사됨 (Python 힙 메모리에 새로 할당)
# "20251106141012"
#
# 이제 DLL이 원본 메모리를 해제해도 안전!
# Python 문자열은 완전히 독립적인 복사본
```

#### 구조체 레이아웃

```python
# LoginBlock 구조체 (8 bytes):
# +0x00: TrIndex (4 bytes)      = 0 또는 사용자 지정값
# +0x04: pLoginInfo (4 bytes)   = LoginInfo 주소

# LoginInfo 구조체 (255,784 bytes):
# +0x00: szDate[14]         = "20251106141012" (접속시간)
# +0x0E: szServerName[15]   = "htsi194"        (서버명)
# +0x1D: szUserID[8]        = "odumag99"       (사용자ID)
# +0x25: szAccountCount[3]  = "005"            (계좌수)
# +0x28: accountlist[999]   = [AccountInfo * 999] (계좌 배열)

# AccountInfo 구조체 (256 bytes):
# +0x00: szAccountNo[11]    = "20301424288"  (계좌번호)
# +0x0B: szAccountName[40]  = "김재민"        (계좌명)
# +0x33: act_pdt_cdz3[3]    = "004"          (상품코드)
# +0x36: amn_tab_cdz4[4]    = "0202"         (관리점코드)
# +0x3A: expr_datez8[8]     = "20991231"     (만료일)
# +0x42: granted[1]         = "G"            (권한)
# +0x43: filler[189]        = ...            (예약)
```

#### 다른 메시지 타입도 동일한 원칙 적용

**CA_RECEIVEMESSAGE (상태 메시지):**
```python
if msg_type == WMCAMessage.CA_RECEIVEMESSAGE:
    # ✅ 즉시 파싱
    msg_header = ctypes.cast(lparam, POINTER(MSGHEADER)).contents
    msg_cd = msg_header.msg_cd.decode('cp949').strip()
    user_msg = msg_header.user_msg.decode('cp949').strip()

    # ✅ Python 객체로 저장
    parsed_data = MessageResponse(
        message_code=msg_cd,
        message_text=user_msg
    )
    self.message_queue.put((msg_type, parsed_data))
```

**CA_RECEIVEDATA (TR 조회 결과):**
```python
if msg_type == WMCAMessage.CA_RECEIVEDATA:
    # ✅ 즉시 파싱
    outdata_block = ctypes.cast(lparam, POINTER(OUTDATABLOCK)).contents
    received = outdata_block.pData.contents

    # ✅ 데이터를 bytes로 복사 (C 메모리 → Python bytes)
    block_name = received.szBlockName.decode('cp949')
    data_bytes = ctypes.string_at(received.szData, received.nLen)

    # ✅ Python 객체로 저장
    parsed_data = TRResponse(
        tr_code=block_name,
        tr_id=outdata_block.TrIndex,
        data=data_bytes  # bytes 객체 (복사본)
    )
    self.message_queue.put((msg_type, parsed_data))
```

#### 핵심 교훈

1. **즉시 파싱**: Windows 메시지 콜백에서 받은 lparam은 콜백 안에서 즉시 파싱
2. **즉시 복사**: C 구조체 데이터를 Python 객체(str, bytes, list 등)로 즉시 복사
3. **독립적 저장**: 큐에는 포인터가 아닌 복사된 Python 객체 저장
4. **안전한 사용**: 나중에 큐에서 꺼낼 때는 이미 독립적인 데이터라 안전

#### 참고: 공식 C++ 샘플 코드도 동일한 방식

`api/SAMPLES/VC++/WMCALOADERDlg.cpp`의 `OnWmConnected()` 함수:

```cpp
void OnWmConnected(WPARAM wParam, LPARAM lParam) {
    // lparam을 즉시 캐스팅
    LOGINBLOCK* pLoginBlock = (LOGINBLOCK*)lParam;
    LOGININFO* pLoginInfo = pLoginBlock->pLoginInfo;

    // ✅ 즉시 데이터 추출 (멤버 변수에 복사)
    m_szDate = pLoginInfo->szDate;
    m_szServerName = pLoginInfo->szServerName;
    m_nAccountCount = atoi(pLoginInfo->szAccountCount);

    // ✅ 계좌 목록도 즉시 복사
    for (int i = 0; i < m_nAccountCount; i++) {
        m_accountList.Add(pLoginInfo->accountlist[i].szAccountNo);
    }

    // 함수 종료 → DLL이 메모리 해제
}
```

C++도 Python과 동일하게 콜백 함수 안에서 즉시 데이터를 복사합니다!

#### 적용된 파일

- **wmca_client.py**: wmca_client.py:329-431 (_handle_wmca_message 메서드)
  - CA_CONNECTED, CA_RECEIVEMESSAGE, CA_DISCONNECTED 메시지를 즉시 파싱
  - 파싱된 LoginResponse, MessageResponse 객체를 큐에 저장

- **wmca_client.py**: wmca_client.py:532-582 (login 메서드)
  - 큐에서 이미 파싱된 객체를 받아서 반환

#### 테스트 결과

```
[DEBUG] LoginBlock.TrIndex = 0
[DEBUG] pLoginInfo 메모리 HEX: 32303235313130363134313031326874736931393420...
[DEBUG] 접속시간: '20251106141012'
[DEBUG] 서버명: 'htsi194'
[DEBUG] 사용자ID: 'odumag99'
[DEBUG] 계좌수: 5
[DEBUG] 계좌[1]: 20301424288 - 김재민
[DEBUG] 계좌[2]: 20302424288 - 김재민
[DEBUG] 계좌[3]: 20902995333 - 김재민
[DEBUG] 계좌[4]: 20304424288 - 김재민
[DEBUG] 계좌[5]: 20311424288 - 김재민
[INFO] 로그인 성공!
[INFO] 계좌 수: 5
```

**작업 완료 날짜**: 2025-11-06
**핵심 발견**: lparam 메모리 생명주기 이슈 해결
**수정 파일**: wmca_client.py
