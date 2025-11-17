#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMCA 고수준 클라이언트
wmca_agent의 receive_events() generator를 활용한 사용자 친화적 API 제공
"""

from typing import Optional, List, Callable, Generator, Tuple, Any
from .wmca_agent import WMCAAgent, WMCAMessage
from .wmca_logger import logger
from .wmca_dtos import LoginBlock, OutDataBlock, MessageHeader
from .structures.base import InBlock


class WMCAClient:
    """
    WMCA 고수준 클라이언트

    wmca_agent의 receive_events() generator를 활용하여
    connect, query, attach 등의 작업을 간편하게 수행합니다.

    Example:
        >>> with WMCAClient() as client:
        ...     # 로그인
        ...     login_info = client.connect(
        ...         szID="user_id",
        ...         szPW="password",
        ...         szCertPW="cert_password"
        ...     )
        ...     print(f"계좌 수: {len(login_info.pLoginInfo.accountlist)}")
        ...
        ...     # TR 조회
        ...     results = client.query("c8201", input_block, nAccountIndex=1)
        ...     for block in results:
        ...         print(f"블록: {block.pData.szBlockName}")
        ...
        ...     # 실시간 시세 등록
        ...     client.attach("j8", "000660", on_realtime_data)
    """

    def __init__(self, dll_path: Optional[str] = None):
        """
        WMCAClient 초기화

        Args:
            dll_path: wmca.dll 경로 (None이면 자동 탐색)
        """
        self.agent = WMCAAgent(dll_path=dll_path)
        self.connected = False

        # TrIndex 관리 (client에서 담당)
        self._next_tr_index = 1

    def _get_next_tr_index(self) -> int:
        """
        다음 TrIndex 값 자동 생성

        Returns:
            사용 가능한 TrIndex (1부터 시작)
        """
        tr_index = self._next_tr_index
        self._next_tr_index += 1
        return tr_index

    def connect(
        self,
        szID: str,
        szPW: str,
        szCertPW: str,
        MediaType: str = 'T',
        UserType: str = 'W',
        timeout: float = 10.0
    ) -> LoginBlock:
        """
        서버 연결 및 로그인

        Args:
            szID: 사용자 ID
            szPW: 사용자 비밀번호
            szCertPW: 공인인증서 비밀번호
            MediaType: 매체유형 ('P': QV계좌, 'T': Namuh계좌)
            UserType: 사용자유형 ('1': QV계좌, 'W': Namuh계좌)
            timeout: 응답 대기 시간(초)

        Returns:
            LoginBlock: 로그인 정보 (계좌 목록 포함)

        Raises:
            RuntimeError: 로그인 실패 시
            TimeoutError: 응답 시간 초과 시

        Example:
            >>> with WMCAClient() as client:
            ...     login_info = client.connect(
            ...         szID="myid",
            ...         szPW="mypassword",
            ...         szCertPW="certpassword"
            ...     )
            ...     print(f"접속 시간: {login_info.pLoginInfo.szDate}")
            ...     for acc in login_info.pLoginInfo.accountlist:
            ...         print(f"{acc.szAccountNo}: {acc.szAccountName}")
        """
        logger.info(f"로그인 시작: ID={szID}")

        # 1. agent.connect() 호출 (요청만 전송)
        result = self.agent.connect(
            szID=szID,
            szPW=szPW,
            szCertPW=szCertPW,
            MediaType=MediaType,
            UserType=UserType
        )

        if not result:
            raise RuntimeError("로그인 함수 호출 실패")

        logger.debug("wmcaConnect() 호출 완료, 응답 대기 중...")

        # 2. receive_events()로 응답 수신
        error_message = None

        for msg_type, parsed_data in self.agent.receive_events(timeout=timeout):
            logger.debug(f"connect: 메시지 수신 - {msg_type.name}")

            # CA_CONNECTED - 로그인 성공!
            if msg_type == WMCAMessage.CA_CONNECTED:
                if isinstance(parsed_data, LoginBlock) and parsed_data.success:
                    logger.info("로그인 성공!")
                    self.connected = True
                    self.agent.connected = True  # agent도 연결 상태로 설정
                    return parsed_data
                else:
                    raise RuntimeError(f"로그인 실패: {parsed_data.error_message}")

            # CA_RECEIVEMESSAGE - 오류 메시지 수집
            elif msg_type == WMCAMessage.CA_RECEIVEMESSAGE:
                if isinstance(parsed_data, OutDataBlock) and parsed_data.pData:
                    msg_header: MessageHeader = parsed_data.pData.szData
                    error_message = f"[{msg_header.msg_cd}] {msg_header.user_msg}"
                    logger.info(f"서버 메시지: {error_message}")

            # CA_DISCONNECTED - 로그인 실패
            elif msg_type == WMCAMessage.CA_DISCONNECTED:
                raise RuntimeError(f"로그인 실패: {error_message or '서버 연결 해제'}")

        # timeout 발생
        raise TimeoutError(f"로그인 응답 시간 초과 ({timeout}초)")

    def disconnect(self) -> bool:
        """
        서버 연결 해제 (로그아웃)

        Returns:
            bool: 연결 해제 성공 여부
        """
        if not self.connected:
            logger.warning("이미 연결 해제됨")
            return True

        result = self.agent.wmca_disconnect()
        if result:
            self.connected = False
            logger.info("연결 해제 완료")
        return bool(result)

    def query(
        self,
        szTRCode: str,
        input_block: InBlock,
        nAccountIndex: int = 0,
        timeout: float = 10.0
    ) -> List[OutDataBlock]:
        """
        TR 조회 (동기 방식)

        Args:
            szTRCode: 서비스 코드 (5자리, 예: "c1101", "c8201")
            input_block: TR 입력 데이터 (InBlock 기반 Pydantic 모델)
            nAccountIndex: 계좌 인덱스 (0: 불필요, 1~: 계좌 순서)
            timeout: 응답 대기 시간(초)

        Returns:
            List[OutDataBlock]: TR 응답 블록 리스트

        Raises:
            RuntimeError: 서버 미연결, TR 조회 실패 시
            TimeoutError: 응답 시간 초과 시

        Example:
            >>> from api.structures.ord import C8201Input
            >>>
            >>> # 계좌 비밀번호 해시 생성
            >>> hash_pwd = client.get_account_hash_password(1, "계좌비번")
            >>>
            >>> # InputBlock 생성
            >>> input_data = C8201Input(
            ...     pswd_noz44=hash_pwd,
            ...     bnc_bse_cdz1="1"  # 체결기준
            ... )
            >>>
            >>> # TR 조회
            >>> blocks = client.query("c8201", input_data, nAccountIndex=1)
            >>> for block in blocks:
            ...     print(f"블록명: {block.pData.szBlockName}")
        """
        if not self.connected:
            raise RuntimeError("서버에 연결되지 않았습니다")

        # 1. TrIndex 생성
        tr_index = self._get_next_tr_index()
        logger.info(f"TR 조회 시작: TrCode={szTRCode}, TrIndex={tr_index}, AccountIndex={nAccountIndex}")

        # 2. TR 조회 요청 전송
        self.agent.query(tr_index, szTRCode, input_block, nAccountIndex)
        logger.debug(f"TR 조회 요청 완료 (TrIndex={tr_index}), 응답 대기 중...")

        # 3. receive_events()로 응답 수신
        received_blocks = []
        error_message = None

        for msg_type, parsed_data in self.agent.receive_events(timeout=timeout):
            # TrIndex가 일치하는지 확인
            received_tr_index = getattr(parsed_data, 'TrIndex', None)
            if received_tr_index is not None and received_tr_index != tr_index:
                logger.debug(f"TrIndex 불일치: 기대={tr_index}, 수신={received_tr_index}, 스킵")
                # 다른 TR의 메시지 → 다시 큐에 넣기
                self.agent.message_queue.put((msg_type, parsed_data))
                continue

            logger.debug(f"query: 메시지 수신 - {msg_type.name}, TrIndex={received_tr_index}")

            # CA_RECEIVEDATA - 데이터 수신 (누적)
            if msg_type == WMCAMessage.CA_RECEIVEDATA:
                if isinstance(parsed_data, OutDataBlock):
                    logger.info(f"TR 블록 수신: {parsed_data.pData.szBlockName if parsed_data.pData else 'None'}")
                    received_blocks.append(parsed_data)

            # CA_RECEIVEMESSAGE - 상태 메시지
            elif msg_type == WMCAMessage.CA_RECEIVEMESSAGE:
                if isinstance(parsed_data, OutDataBlock) and parsed_data.pData:
                    msg_header: MessageHeader = parsed_data.pData.szData
                    error_message = f"[{msg_header.msg_cd}] {msg_header.user_msg}"
                    logger.info(f"서버 메시지: {error_message}")

            # CA_RECEIVECOMPLETE - 처리 완료 (수집 종료)
            elif msg_type == WMCAMessage.CA_RECEIVECOMPLETE:
                logger.info(f"TR 처리 완료 (TrIndex={tr_index}, 총 {len(received_blocks)}개 블록)")
                if len(received_blocks) == 0:
                    raise RuntimeError("CA_RECEIVECOMPLETE 수신했으나 블록이 없음")
                return received_blocks

            # CA_RECEIVEERROR - 처리 실패
            elif msg_type == WMCAMessage.CA_RECEIVEERROR:
                logger.error(f"TR 처리 실패 (TrIndex={tr_index})")
                raise RuntimeError(error_message or "TR 처리 실패")

        # timeout 발생
        raise TimeoutError(f"TR 응답 시간 초과 ({timeout}초)")

    def attach(
        self,
        szBCType: str,
        szInput: str,
        callback: Optional[Callable] = None,
        nCodeLen: int = 6,
        nInputLen: Optional[int] = None
    ) -> bool:
        """
        실시간 시세 등록

        Args:
            szBCType: 실시간 서비스 코드 (예: "j8" - 주식체결가, "h1" - 주식호가)
            szInput: 종목코드 (예: "000660" 또는 여러 종목 "000660005940")
            callback: 실시간 데이터 수신 시 호출할 콜백 함수 (msg_type, data)
            nCodeLen: 종목코드 개별 길이 (기본값: 6)
            nInputLen: 전체 입력 길이 (None이면 자동 계산)

        Returns:
            bool: 등록 성공 여부

        Example:
            >>> def on_price(msg_type, data):
            ...     print(f"실시간 체결: {data}")
            >>>
            >>> client.attach("j8", "000660", on_price)
            >>>
            >>> # 실시간 데이터는 receive_events()로 수신
            >>> for msg_type, data in client.receive_events():
            ...     if msg_type == WMCAMessage.CA_RECEIVESISE:
            ...         print(f"실시간 시세: {data}")
        """
        if not self.connected:
            raise RuntimeError("서버에 연결되지 않았습니다")

        # nInputLen 자동 계산
        if nInputLen is None:
            nInputLen = len(szInput)

        logger.info(f"실시간 시세 등록: BC={szBCType}, Input={szInput}")

        # wmcaAttach 호출
        result = self.agent.attach(szBCType, szInput, nCodeLen, nInputLen)

        # 콜백 등록 (선택사항)
        if callback:
            # 실시간 데이터는 TrIndex가 없으므로 별도 처리 필요
            # TODO: 실시간 콜백 시스템 구현
            logger.warning("실시간 콜백은 아직 미구현 - receive_events()로 직접 수신하세요")

        return result

    def detach(
        self,
        szBCType: str,
        szInput: str,
        nCodeLen: int = 6,
        nInputLen: Optional[int] = None
    ) -> bool:
        """
        실시간 시세 해제

        Args:
            szBCType: 실시간 서비스 코드
            szInput: 종목코드
            nCodeLen: 종목코드 개별 길이
            nInputLen: 전체 입력 길이 (None이면 자동 계산)

        Returns:
            bool: 해제 성공 여부
        """
        if nInputLen is None:
            nInputLen = len(szInput)

        return self.agent.detach(szBCType, szInput, nCodeLen, nInputLen)

    def receive_events(self, timeout: float = 10.0) -> Generator[Tuple[WMCAMessage, Any], None, None]:
        """
        이벤트 수신 Generator (agent의 receive_events 직접 노출)

        Args:
            timeout: 최대 대기 시간 (초)

        Yields:
            Tuple[WMCAMessage, Any]: (메시지 타입, 파싱된 데이터)

        Example:
            >>> for msg_type, data in client.receive_events(timeout=30.0):
            ...     if msg_type == WMCAMessage.CA_RECEIVESISE:
            ...         print(f"실시간 시세: {data}")
            ...     elif msg_type == WMCAMessage.CA_RECEIVEDATA:
            ...         print(f"TR 데이터: {data}")
        """
        yield from self.agent.receive_events(timeout=timeout)

    def get_account_hash_password(self, account_index: int, password: str) -> str:
        """
        계좌 비밀번호를 44자 해시값으로 변환

        Args:
            account_index: 계좌 인덱스 (1부터 시작)
            password: 평문 비밀번호

        Returns:
            str: 44자 해시 문자열

        Example:
            >>> hash_pwd = client.get_account_hash_password(1, "1234")
            >>> len(hash_pwd)
            44
        """
        return self.agent.get_account_hash_password(account_index, password)

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.agent.is_connected()

    def dispose(self):
        """리소스 정리"""
        if self.connected:
            self.disconnect()
        self.agent._dispose()

    def __enter__(self):
        """
        컨텍스트 매니저 진입

        자동으로 agent 초기화 수행:
        1. Windows 메시지 윈도우 생성
        2. WMCA 모듈 로드
        """
        self.agent.__enter__()  # agent의 initialize() 호출
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        컨텍스트 매니저 종료

        자동으로 agent 정리 수행:
        1. 로그아웃
        2. WMCA 모듈 해제
        3. 윈도우 파괴
        """
        self.agent.__exit__(exc_type, exc_value, traceback)
        return False


# ============================================================================
# 사용 예제
# ============================================================================

if __name__ == "__main__":
    from settings import NamuSettings
    import traceback

    try:
        # .env 파일에서 설정 로드
        settings = NamuSettings()

        with WMCAClient() as client:
            # 1. 로그인
            logger.info(f"로그인 시도: ID={settings.id}")
            login_info = client.connect(
                szID=settings.id,
                szPW=settings.pw,
                szCertPW=settings.cert_pw
            )

            if login_info.success:
                logger.info("로그인 성공!")
                logger.info(f"접속 시간: {login_info.pLoginInfo.szDate}")
                logger.info(f"서버명: {login_info.pLoginInfo.szServerName}")
                logger.info(f"계좌 수: {len(login_info.pLoginInfo.accountlist)}")

                for i, acc in enumerate(login_info.pLoginInfo.accountlist, 1):
                    logger.info(f"계좌[{i}]: {acc.szAccountNo} - {acc.szAccountName}")
            else:
                logger.error(f"로그인 실패: {login_info.error_message}")

            # 2. TR 조회 예제 (c8201 - 잔고조회)
            # from api.structures.ord import C8201Input
            # hash_pwd = client.get_account_hash_password(1, "계좌비번")
            # input_data = C8201Input(pswd_noz44=hash_pwd, bnc_bse_cdz1="1")
            # blocks = client.query("c8201", input_data, nAccountIndex=1)

            # 3. 실시간 시세 예제
            # client.attach("j8", "000660")  # SK하이닉스 실시간 체결가
            # for msg_type, data in client.receive_events(timeout=30.0):
            #     if msg_type == WMCAMessage.CA_RECEIVESISE:
            #         logger.info(f"실시간 시세: {data}")

    except Exception as e:
        logger.error(f"오류 발생: {e}")
        logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
