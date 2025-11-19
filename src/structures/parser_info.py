"""주문 관련 TR 구조체 정의 (trio_ord.h 기반)"""

from typing import ClassVar, Type, TYPE_CHECKING
from dataclasses import dataclass
import ctypes
from ctypes import Structure

from pydantic import Field, field_validator

if TYPE_CHECKING:
    from .common import OutBlock


def get_parser_info(block_name: str) -> tuple[Type[Structure], Type["OutBlock"], bool]:
    """파서 정보 조회

    Args:
        block_name: 블록명

    Returns:
        (OutBlock C구조체, OutBlock Python Class, is_array) 튜플
    """
    match block_name:
        case "j8":
            from .inv.j8 import CTj8OutBlock, Tj8OutBlock
            return (CTj8OutBlock, Tj8OutBlock, False)
        case "c8201OutBlock":
            from .ord.c8201 import CTc8201OutBlock, Tc8201OutBlock
            return (CTc8201OutBlock, Tc8201OutBlock, False)
        case "c8201OutBlock1":
            from .ord.c8201 import CTc8201OutBlock1, Tc8201OutBlock1
            return (CTc8201OutBlock1, Tc8201OutBlock1, True)
        case "c8201":
            return None    
        case _:
            raise ValueError(f"아직 Block이 구현되지 않음! : {block_name}")

