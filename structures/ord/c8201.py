"""주문 관련 TR 구조체 정의 (trio_ord.h 기반)"""

from typing import ClassVar, Type
from dataclasses import dataclass
import ctypes
from ctypes import Structure

from pydantic import Field, field_validator

from ..common import InBlock, OutBlock


# ==============================================================================
# C 구조체 정의 (trio_ord.h 기반)
# ==============================================================================

class CTc8201InBlock(Structure):
    """주식잔고조회(예수금, 종목) 입력 블록 C 구조체"""
    _fields_ = [
        ("pswd_noz44", ctypes.c_char * 44),    # 계좌비밀번호
        ("bnc_bse_cdz1", ctypes.c_char * 1),   # 잔고구분
    ]


# ==============================================================================
# Pydantic 모델 (사용자 친화적 인터페이스)
# ==============================================================================

class Tc8201InBlock(InBlock):
    """주식잔고조회(예수금, 종목) 입력 블록

    Attributes:
        pswd_noz44: 해시 처리된 계좌비밀번호 (44자)
        bnc_bse_cdz1: 잔고구분 (1: 체결기준, 2: 결제잔고, 3: 시간외종가 체결잔고, 4: 시간외종가 결제잔고, 5: 주식잔고평가)

    사용 예:
        >>> from api.wmca_agent import WMCAAgent
        >>> from api.structures.ord import C8201Input
        >>>
        >>> agent = WMCAAgent()
        >>> # 로그인 완료 후...
        >>>
        >>> # 1. 계좌 비밀번호를 44자 해시로 변환
        >>> hash_pwd = agent.get_account_hash_password(
        ...     account_index=1,
        ...     password="계좌비밀번호"
        ... )
        >>> print(len(hash_pwd))  # 44
        >>>
        >>> # 2. InputBlock 생성
        >>> input_data = C8201Input(
        ...     pswd_noz44=hash_pwd,  # 44자 해시값
        ...     bnc_bse_cdz1=1  # 1: 체결기준 (int → str 자동 변환)
        ... )
        >>>
        >>> # 3. TR 조회
        >>> blocks = agent.query("c8201", input_data, nAccountIndex=1)
        >>> for block in blocks:
        ...     print(f"블록명: {block.pData.szBlockName}")
    """

    # C 구조체 타입 지정
    C_STRUCT: ClassVar[Type[ctypes.Structure]] = CTc8201InBlock

    pswd_noz44: str = Field(
        min_length=44,
        max_length=44,
        description="해시 처리된 계좌비밀번호"
    )

    bnc_bse_cdz1: str = Field(
        pattern=r'^[1-5]$',
        description="잔고구분 (1~5)"
    )


# ==============================================================================
# Output 구조체
# ==============================================================================

class CTc8201OutBlock(ctypes.Structure):
    """c8201 잔고조회 Output C 구조체 (헤더 정보)"""
    _fields_ = [
        ("dpsit_amtz16", ctypes.c_char * 16),       # 예수금
        ("_dpsit_amtz16", ctypes.c_char * 1),       # 속성 바이트
        ("mrgn_amtz16", ctypes.c_char * 16),        # 신용융자금
        ("_mrgn_amtz16", ctypes.c_char * 1),
        ("mgint_npaid_amtz16", ctypes.c_char * 16), # 이자미납금
        ("_mgint_npaid_amtz16", ctypes.c_char * 1),
        ("chgm_pos_amtz16", ctypes.c_char * 16),    # 출금가능금액
        ("_chgm_pos_amtz16", ctypes.c_char * 1),
        ("cash_mrgn_amtz16", ctypes.c_char * 16),   # 현금증거금
        ("_cash_mrgn_amtz16", ctypes.c_char * 1),
        ("subst_mgamt_amtz16", ctypes.c_char * 16), # 대용증거금
        ("_subst_mgamt_amtz16", ctypes.c_char * 1),
        ("coltr_ratez6", ctypes.c_char * 6),        # 담보비율
        ("_coltr_ratez6", ctypes.c_char * 1),
        ("rcble_amtz16", ctypes.c_char * 16),       # 현금미수금
        ("_rcble_amtz16", ctypes.c_char * 1),
        ("order_pos_csamtz16", ctypes.c_char * 16), # 주문가능액
        ("_order_pos_csamtz16", ctypes.c_char * 1),
        ("ecn_pos_csamtz16", ctypes.c_char * 16),   # ECN주문가능액
        ("_ecn_pos_csamtz16", ctypes.c_char * 1),
        ("nordm_loan_amtz16", ctypes.c_char * 16),  # 미상환금
        ("_nordm_loan_amtz16", ctypes.c_char * 1),
        ("etc_lend_amtz16", ctypes.c_char * 16),    # 기타대여금
        ("_etc_lend_amtz16", ctypes.c_char * 1),
        ("subst_amtz16", ctypes.c_char * 16),       # 대용금액
        ("_subst_amtz16", ctypes.c_char * 1),
        ("sln_sale_amtz16", ctypes.c_char * 16),    # 대주담보금
        ("_sln_sale_amtz16", ctypes.c_char * 1),
        ("bal_buy_ttamtz16", ctypes.c_char * 16),   # 매입원가(계좌합산)
        ("_bal_buy_ttamtz16", ctypes.c_char * 1),
        ("bal_ass_ttamtz16", ctypes.c_char * 16),   # 평가금액(계좌합산)
        ("_bal_ass_ttamtz16", ctypes.c_char * 1),
        ("asset_tot_amtz16", ctypes.c_char * 16),   # 순자산액(계좌합산)
        ("_asset_tot_amtz16", ctypes.c_char * 1),
        ("actvt_type10", ctypes.c_char * 10),       # 활동유형
        ("_actvt_type10", ctypes.c_char * 1),
        ("lend_amtz16", ctypes.c_char * 16),        # 대출금
        ("_lend_amtz16", ctypes.c_char * 1),
        ("accnt_mgamt_ratez6", ctypes.c_char * 6),  # 계좌증거금율
        ("_accnt_mgamt_ratez6", ctypes.c_char * 1),
        ("sl_mrgn_amtz16", ctypes.c_char * 16),     # 매도증거금
        ("_sl_mrgn_amtz16", ctypes.c_char * 1),
        ("pos_csamt1z16", ctypes.c_char * 16),      # 20%주문가능금액
        ("_pos_csamt1z16", ctypes.c_char * 1),
        ("pos_csamt2z16", ctypes.c_char * 16),      # 30%주문가능금액
        ("_pos_csamt2z16", ctypes.c_char * 1),
        ("pos_csamt3z16", ctypes.c_char * 16),      # 40%주문가능금액
        ("_pos_csamt3z16", ctypes.c_char * 1),
        ("pos_csamt4z16", ctypes.c_char * 16),      # 100%주문가능금액
        ("_pos_csamt4z16", ctypes.c_char * 1),
        ("dpsit_amtz_d1_16", ctypes.c_char * 16),   # D1예수금
        ("_dpsit_amtz_d1_16", ctypes.c_char * 1),
        ("dpsit_amtz_d2_16", ctypes.c_char * 16),   # D2예수금
        ("_dpsit_amtz_d2_16", ctypes.c_char * 1),
        ("noticez30", ctypes.c_char * 30),          # 공지사항
        ("_noticez30", ctypes.c_char * 1),
        ("tot_eal_plsz18", ctypes.c_char * 18),     # 총평가손익
        ("_tot_eal_plsz18", ctypes.c_char * 1),
        ("pft_rtz15", ctypes.c_char * 15),          # 수익율
        ("_pft_rtz15", ctypes.c_char * 1),
    ]


@dataclass
class Tc8201OutBlock(OutBlock):
    """c8201 잔고조회 OutBlock (계좌 요약 정보)

    Reference: api/SAMPLES/VC++/trio_ord.h

    사용 예:
        >>> # Received.from_c_struct()가 자동으로 파싱
        >>> result = agent.query("c8201", input_data, nAccountIndex=1)
        >>> if result.success:
        ...     # szData는 이미 Tc8201OutBlock 타입
        ...     outblock: Tc8201OutBlock = result.pData.szData
        ...     print(f"예수금: {outblock.dpsit_amtz16}")
        ...     print(f"출금가능금액: {outblock.chgm_pos_amtz16}")
    """
    dpsit_amtz16: str           # 예수금
    mrgn_amtz16: str            # 신용융자금
    mgint_npaid_amtz16: str     # 이자미납금
    chgm_pos_amtz16: str        # 출금가능금액
    cash_mrgn_amtz16: str       # 현금증거금
    subst_mgamt_amtz16: str     # 대용증거금
    coltr_ratez6: str           # 담보비율
    rcble_amtz16: str           # 현금미수금
    order_pos_csamtz16: str     # 주문가능액
    pos_csamt4z16: str          # 100%주문가능금액
    bal_buy_ttamtz16: str       # 매입원가
    bal_ass_ttamtz16: str       # 평가금액
    asset_tot_amtz16: str       # 순자산액
    tot_eal_plsz18: str         # 총평가손익
    pft_rtz15: str              # 수익율


class CTc8201OutBlock1(ctypes.Structure):
    """c8201 잔고조회 Output C 구조체 (보유종목 목록 - 반복)

    Note:
        - 반복 레코드 (최대 20건)
    """
    _fields_ = [
        ("issue_codez6", ctypes.c_char * 6),        # 종목번호
        ("_issue_codez6", ctypes.c_char * 1),
        ("issue_namez40", ctypes.c_char * 40),      # 종목명
        ("_issue_namez40", ctypes.c_char * 1),
        ("bal_typez6", ctypes.c_char * 6),          # 잔고유형
        ("_bal_typez6", ctypes.c_char * 1),
        ("loan_datez10", ctypes.c_char * 10),       # 대출일
        ("_loan_datez10", ctypes.c_char * 1),
        ("bal_qtyz16", ctypes.c_char * 16),         # 잔고수량
        ("_bal_qtyz16", ctypes.c_char * 1),
        ("unstl_qtyz16", ctypes.c_char * 16),       # 미결제수량
        ("_unstl_qtyz16", ctypes.c_char * 1),
        ("slby_amtz16", ctypes.c_char * 16),        # 평균매입가
        ("_slby_amtz16", ctypes.c_char * 1),
        ("prsnt_pricez16", ctypes.c_char * 16),     # 현재가
        ("_prsnt_pricez16", ctypes.c_char * 1),
        ("lsnpf_amtz16", ctypes.c_char * 16),       # 손익(천원)
        ("_lsnpf_amtz16", ctypes.c_char * 1),
        ("earn_ratez9", ctypes.c_char * 9),         # 손익율
        ("_earn_ratez9", ctypes.c_char * 1),
        ("mrgn_codez4", ctypes.c_char * 4),         # 신용코드
        ("_mrgn_codez4", ctypes.c_char * 1),
        ("jan_qtyz16", ctypes.c_char * 16),         # 잔량
        ("_jan_qtyz16", ctypes.c_char * 1),
        ("expr_datez10", ctypes.c_char * 10),       # 만기일
        ("_expr_datez10", ctypes.c_char * 1),
        ("ass_amtz16", ctypes.c_char * 16),         # 평가금액
        ("_ass_amtz16", ctypes.c_char * 1),
        ("issue_mgamt_ratez6", ctypes.c_char * 6),  # 증거금율
        ("_issue_mgamt_ratez6", ctypes.c_char * 1),
        ("medo_slby_amtz16", ctypes.c_char * 16),   # 매도매입금
        ("_medo_slby_amtz16", ctypes.c_char * 1),
        ("post_lsnpf_amtz16", ctypes.c_char * 16),  # 매도손익
        ("_post_lsnpf_amtz16", ctypes.c_char * 1),
    ]

@dataclass
class Tc8201OutBlock1(OutBlock):
    """c8201 잔고조회 OutBlock1 (보유종목 정보)
    """

    issue_codez6: str
    issue_namez40: str
    bal_typez6: str
    loan_datez10: str
    bal_qtyz16: str
    unstl_qtyz16: str
    slby_amtz16: str
    prsnt_pricez16: str
    lsnpf_amtz16: str
    earn_ratez9: str
    mrgn_codez4: str
    jan_qtyz16: str
    expr_datez10: str
    ass_amtz16: str
    issue_mgamt_ratez6: str
    medo_slby_amtz16: str
    post_lsnpf_amtz16: str
