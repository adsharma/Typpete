from typing import List


class IO:
    def mode(self) -> str:
        ...

    def name(self) -> str:
        ...

    def close(self) -> None:
        ...

    def closed(self) -> bool:
        ...

    def fileno(self) -> int:
        ...

    def flush(self) -> None:
        ...

    def isatty(self) -> bool:
        ...

    def read(self, n: int = 0) -> str:
        ...

    def readable(self) -> bool:
        ...

    def readline(self, limit: int = 1) -> str:
        ...

    def readlines(self, hint: int = 1) -> List[str]:
        ...

    def seek(self, offset: int, whence: int = 1) -> int:
        ...

    def seekable(self) -> bool:
        ...

    def tell(self) -> int:
        ...

    def truncate(self, size: int = 1) -> int:
        ...

    def writable(self) -> bool:
        ...

    def write(self, s: str) -> int:
        ...

    def writelines(self, lines: List[str]) -> None:
        ...

    def next(self) -> str:
        ...


class TextIO:
    def write(self, arg: str) -> None:
        ...


argv = [""]
stdout = TextIO()

stderr = IO()


def exit(arg: object) -> None:
    pass
