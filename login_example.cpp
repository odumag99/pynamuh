// login_example.cpp
// NH증권 WMCA API를 이용한 간단한 로그인 예제
// Console 애플리케이션으로 빌드해야 합니다.

#include <windows.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <cstring>

using namespace std;

// ============================================================================
// WMCA DLL 함수 포인터 정의
// ============================================================================

typedef BOOL(__stdcall *FUNC_wmcaLoad)();
typedef BOOL(__stdcall *FUNC_wmcaFree)();
typedef BOOL(__stdcall *FUNC_wmcaSetServer)(const char* szServer);
typedef BOOL(__stdcall *FUNC_wmcaSetPort)(int nPort);
typedef BOOL(__stdcall *FUNC_wmcaIsConnected)();
typedef BOOL(__stdcall *FUNC_wmcaConnect)(
    HWND hWnd,
    DWORD dwMsg,
    char cMediaType,
    char cUserType,
    const char* pszID,
    const char* pszPassword,
    const char* pszSignPassword
);
typedef BOOL(__stdcall *FUNC_wmcaDisconnect)();

// ============================================================================
// WMCA 클라이언트 클래스
// ============================================================================

class WMCAClient {
private:
    HINSTANCE m_hDll;
    FUNC_wmcaLoad m_pLoad;
    FUNC_wmcaFree m_pFree;
    FUNC_wmcaSetServer m_pSetServer;
    FUNC_wmcaSetPort m_pSetPort;
    FUNC_wmcaIsConnected m_pIsConnected;
    FUNC_wmcaConnect m_pConnect;
    FUNC_wmcaDisconnect m_pDisconnect;
    bool m_bConnected;

public:
    WMCAClient() : m_hDll(NULL), m_bConnected(false) {
        m_pLoad = NULL;
        m_pFree = NULL;
        m_pSetServer = NULL;
        m_pSetPort = NULL;
        m_pIsConnected = NULL;
        m_pConnect = NULL;
        m_pDisconnect = NULL;
    }

    ~WMCAClient() {
        Cleanup();
    }

    // DLL 로드
    bool LoadDLL(const char* szDLLPath = "wmca.dll") {
        // DLL 로드
        m_hDll = LoadLibraryA(szDLLPath);
        if (!m_hDll) {
            printf("✗ %s 로드 실패\n", szDLLPath);
            printf("  DLL이 다음 경로에 있는지 확인하세요:\n");
            printf("  - C:\\Windows\\System32\\\n");
            printf("  - 프로그램과 같은 디렉토리\n");
            return false;
        }
        printf("✓ %s 로드 성공\n", szDLLPath);

        // 함수 포인터 획득
        m_pLoad = (FUNC_wmcaLoad)GetProcAddress(m_hDll, "wmcaLoad");
        m_pFree = (FUNC_wmcaFree)GetProcAddress(m_hDll, "wmcaFree");
        m_pSetServer = (FUNC_wmcaSetServer)GetProcAddress(m_hDll, "wmcaSetServer");
        m_pSetPort = (FUNC_wmcaSetPort)GetProcAddress(m_hDll, "wmcaSetPort");
        m_pIsConnected = (FUNC_wmcaIsConnected)GetProcAddress(m_hDll, "wmcaIsConnected");
        m_pConnect = (FUNC_wmcaConnect)GetProcAddress(m_hDll, "wmcaConnect");
        m_pDisconnect = (FUNC_wmcaDisconnect)GetProcAddress(m_hDll, "wmcaDisconnect");

        if (!m_pLoad || !m_pFree || !m_pSetServer || !m_pSetPort ||
            !m_pIsConnected || !m_pConnect || !m_pDisconnect) {
            printf("✗ 함수 포인터 설정 실패\n");
            FreeLibrary(m_hDll);
            m_hDll = NULL;
            return false;
        }
        printf("✓ 함수 포인터 설정 완료\n");

        return true;
    }

    // WMCA 모듈 로드
    bool Load() {
        if (!m_pLoad) {
            printf("✗ DLL이 로드되지 않았습니다.\n");
            return false;
        }

        if (m_pLoad()) {
            printf("✓ WMCA 모듈 로드 성공\n");
            return true;
        } else {
            printf("✗ WMCA 모듈 로드 실패\n");
            return false;
        }
    }

    // 서버 설정
    bool SetServer(const char* szServer) {
        if (!m_pSetServer) {
            printf("✗ SetServer 함수가 없습니다.\n");
            return false;
        }

        if (m_pSetServer(szServer)) {
            printf("✓ 서버 설정 완료: %s\n", szServer);
            return true;
        } else {
            printf("✗ 서버 설정 실패: %s\n", szServer);
            return false;
        }
    }

    // 포트 설정
    bool SetPort(int nPort) {
        if (!m_pSetPort) {
            printf("✗ SetPort 함수가 없습니다.\n");
            return false;
        }

        if (m_pSetPort(nPort)) {
            printf("✓ 포트 설정 완료: %d\n", nPort);
            return true;
        } else {
            printf("✗ 포트 설정 실패: %d\n", nPort);
            return false;
        }
    }

    // 연결 상태 확인
    bool IsConnected() {
        if (!m_pIsConnected) {
            return false;
        }
        return m_pIsConnected() ? true : false;
    }

    // 로그인
    bool Connect(const char* szID, const char* szPassword, const char* szCertPW,
                 const char* szMediaType = "0", const char* szUserType = "1") {
        if (!m_pConnect) {
            printf("✗ Connect 함수가 없습니다.\n");
            return false;
        }

        printf("\n로그인 시도 중...\n");

        // Connect 함수 호출
        // HWND: NULL (콘솔 앱이므로)
        // dwMsg: 0 (메시지 ID, 콘솔 앱에서는 사용 안 함)
        if (m_pConnect(
            NULL,                   // HWND hWnd
            0,                      // DWORD dwMsg
            szMediaType[0],         // char cMediaType
            szUserType[0],          // char cUserType
            szID,                   // const char* pszID
            szPassword,             // const char* pszPassword
            szCertPW                // const char* pszSignPassword
        )) {
            printf("✓ 로그인 성공: %s\n", szID);
            m_bConnected = true;
            return true;
        } else {
            printf("✗ 로그인 실패\n");
            return false;
        }
    }

    // 로그아웃
    bool Disconnect() {
        if (!m_pDisconnect) {
            printf("✗ Disconnect 함수가 없습니다.\n");
            return false;
        }

        if (m_pDisconnect()) {
            printf("✓ 로그아웃 성공\n");
            m_bConnected = false;
            return true;
        } else {
            printf("✗ 로그아웃 실패\n");
            return false;
        }
    }

    // WMCA 모듈 해제
    bool Free() {
        if (!m_pFree) {
            printf("✗ Free 함수가 없습니다.\n");
            return false;
        }

        if (m_pFree()) {
            printf("✓ WMCA 모듈 해제 완료\n");
            return true;
        } else {
            printf("✗ WMCA 모듈 해제 실패\n");
            return false;
        }
    }

    // 정리
    void Cleanup() {
        if (m_bConnected) {
            Disconnect();
        }
        Free();
        if (m_hDll) {
            FreeLibrary(m_hDll);
            m_hDll = NULL;
        }
    }
};

// ============================================================================
// 입력 함수
// ============================================================================

string GetInput(const char* szPrompt, const char* szDefault = NULL) {
    printf("%s", szPrompt);
    if (szDefault) {
        printf(" (기본값: %s): ", szDefault);
    } else {
        printf(": ");
    }

    string input;
    getline(cin, input);

    if (input.empty() && szDefault) {
        return szDefault;
    }
    return input;
}

// ============================================================================
// 메인 함수
// ============================================================================

int main() {
    setlocale(LC_ALL, "");

    printf("============================================================\n");
    printf("NH증권 WMCA API 로그인 예제\n");
    printf("============================================================\n");

    // 입력값 받기
    printf("\n다음 정보를 입력하세요:\n");
    string server = GetInput("서버 주소", "127.0.0.1");
    string portStr = GetInput("포트 번호", "9000");
    int port = stoi(portStr);

    string userID = GetInput("사용자 ID");
    string password = GetInput("비밀번호");
    string certPassword = GetInput("인증서 비밀번호");

    if (userID.empty() || password.empty() || certPassword.empty()) {
        printf("✗ 필수 정보가 입력되지 않았습니다.\n");
        return 1;
    }

    // WMCA 클라이언트 생성
    WMCAClient client;

    // 1. DLL 로드
    if (!client.LoadDLL("wmca.dll")) {
        return 1;
    }

    // 2. WMCA 모듈 로드
    if (!client.Load()) {
        return 1;
    }

    // 3. 서버 설정
    if (!client.SetServer(server.c_str())) {
        client.Free();
        return 1;
    }

    // 4. 포트 설정
    if (!client.SetPort(port)) {
        client.Free();
        return 1;
    }

    // 5. 로그인 시도
    if (!client.Connect(userID.c_str(), password.c_str(), certPassword.c_str())) {
        client.Free();
        return 1;
    }

    // 6. 연결 상태 확인
    printf("\n연결 상태 확인 중...\n");
    if (client.IsConnected()) {
        printf("✓ 서버와 연결되어 있습니다.\n");
    } else {
        printf("✗ 서버와 연결되어 있지 않습니다.\n");
    }

    // 7. 대기 (메시지 수신 대기)
    printf("\n5초 대기 중... (메시지 수신 대기)\n");
    Sleep(5000);

    // 8. 로그아웃
    printf("\n로그아웃 처리 중...\n");
    client.Disconnect();

    // 정리
    client.Cleanup();

    printf("\n============================================================\n");
    printf("프로그램 종료\n");
    printf("============================================================\n");

    return 0;
}
