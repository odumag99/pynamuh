from pathlib import Path
from datetime import datetime
from typing import Literal
import logging

LEVELS = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

def get_logger(
    name: str = "wmca",
    print: bool = True, print_level: LEVELS = "INFO", 
    file: bool = False, file_level: LEVELS = "DEBUG", file_name: str = None
):
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    
    if print:
        if print_level not in LEVELS.__args__:
            raise ValueError(f"print_level must be one of {LEVELS.__args__}")
        
    if file:
        if file_level not in LEVELS.__args__:
            raise ValueError(f"file_level must be one of {LEVELS.__args__}")
        
        if file_name is None:
            file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + name + ".txt"
        if not isinstance(file_name, str):
            raise TypeError("file_name must be a string")

        log_dir = Path(__file__).parent / "logs"

        try:
            log_dir.mkdir(exist_ok=True, parents=True)
            fpath = log_dir / file_name
            fpath.touch(exist_ok=True)
        except OSError:
            raise ValueError(f"Cannot create or access log file: {file_name}")
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 이미 핸들러가 있으면 추가하지 않음 (중복 로그 방지)
    if logger.handlers:
        return logger

    # 파일명과 줄 번호 포함
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if print:
        sh = logging.StreamHandler()
        sh.setLevel(getattr(logging, print_level))
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    if file:
        fh = logging.FileHandler(fpath, mode='a', encoding='utf-8')
        fh.setLevel(getattr(logging, file_level))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

logger = get_logger(file=True)