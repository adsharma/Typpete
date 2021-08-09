from typing import List, Tuple, Union


def system(command: str) -> int:
    ...


def getcwd() -> str:
    ...


def getcwdb() -> bytes:
    ...


def ctermid() -> str:
    ...  # Unix only


def getegid() -> int:
    ...  # Unix only


def geteuid() -> int:
    ...  # Unix only


def getgid() -> int:
    ...  # Unix only


def getgrouplist(user: str, gid: int) -> List[int]:
    ...  # Unix only


def getgroups() -> List[int]:
    ...  # Unix only, behaves differently on Mac


def initgroups(username: str, gid: int) -> None:
    ...  # Unix only


def getlogin() -> str:
    ...


def getpgid(pid: int) -> int:
    ...  # Unix only


def getpgrp() -> int:
    ...  # Unix only


def getpid() -> int:
    ...


def getppid() -> int:
    ...


def getpriority(which: int, who: int) -> int:
    ...  # Unix only


def setpriority(which: int, who: int, priority: int) -> None:
    ...  # Unix only


def getresuid() -> Tuple[int, int, int]:
    ...  # Unix only


def getresgid() -> Tuple[int, int, int]:
    ...  # Unix only


def getuid() -> int:
    ...  # Unix only


def setegid(egid: int) -> None:
    ...  # Unix only


def seteuid(euid: int) -> None:
    ...  # Unix only


def setgid(gid: int) -> None:
    ...  # Unix only


def setgroups(groups: List[int]) -> None:
    ...  # Unix only


def setpgrp() -> None:
    ...  # Unix only


def setpgid(pid: int, pgrp: int) -> None:
    ...  # Unix only


def setregid(rgid: int, egid: int) -> None:
    ...  # Unix only


def setresgid(rgid: int, egid: int, sgid: int) -> None:
    ...  # Unix only


def setresuid(ruid: int, euid: int, suid: int) -> None:
    ...  # Unix only


def setreuid(ruid: int, euid: int) -> None:
    ...  # Unix only


def getsid(pid: int) -> int:
    ...  # Unix only


def setsid() -> None:
    ...  # Unix only


def setuid(uid: int) -> None:
    ...  # Unix only


def strerror(code: int) -> str:
    ...


def umask(mask: int) -> int:
    ...


def getenv(key: str) -> str:
    ...


def getenvb(key: bytes, default: bytes = None) -> bytes:
    ...


def putenv(key: Union[bytes, str], value: Union[bytes, str]) -> None:
    ...


def unsetenv(key: Union[bytes, str]) -> None:
    ...


def close(fd: int) -> None:
    ...


def closerange(fd_low: int, fd_high: int) -> None:
    ...


def device_encoding(fd: int) -> str:
    ...


def dup(fd: int) -> int:
    ...


def dup2(fd: int, fd2: int) -> None:
    ...


def fchmod(fd: int, mode: int) -> None:
    ...  # Unix only


def fchown(fd: int, uid: int, gid: int) -> None:
    ...  # Unix only


def fdatasync(fd: int) -> None:
    ...  # Unix only, not Mac


def fpathconf(fd: int, name: Union[str, int]) -> int:
    ...  # Unix only


def fsync(fd: int) -> None:
    ...


def ftruncate(fd: int, length: int) -> None:
    ...  # Unix only


def get_blocking(fd: int) -> bool:
    ...  # Unix only


def set_blocking(fd: int, blocking: bool) -> None:
    ...  # Unix only


def isatty(fd: int) -> bool:
    ...  # Unix only


def lockf(__fd: int, __cmd: int, __length: int) -> None:
    ...  # Unix only


def lseek(fd: int, pos: int, how: int) -> int:
    ...


def open(file: str, flags: int, mode: int = 0, dir_fd: int = 0) -> int:
    ...


def pipe() -> Tuple[int, int]:
    ...


def pipe2(flags: int) -> Tuple[int, int]:
    ...  # some flavors of Unix


def posix_fallocate(fd: int, offset: int, length: int) -> None:
    ...  # Unix only


def posix_fadvise(fd: int, offset: int, length: int, advice: int) -> None:
    ...  # Unix only


def pread(fd: int, buffersize: int, offset: int) -> bytes:
    ...  # Unix only


def pwrite(fd: int, string: bytes, offset: int) -> int:
    ...  # Unix only


def listdir(path: Union[str, int] = None) -> List[str]:
    ...


def mkdir(path: str, mode: int = None, dir_fd: int = 0) -> None:
    ...


def makedirs(name: str, mode: int = None, exist_ok: bool = None) -> None:
    ...


def remove(path: str, dir_fd: int = None) -> None:
    ...


def removedirs(name: str) -> None:
    ...


def rename(src: str, dst: str, src_dir_fd: int = None, dst_dir_fd: int = None) -> None:
    ...
