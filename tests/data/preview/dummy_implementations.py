from typing import NoReturn, Protocol, Union, overload


def dummy(a): ...
def other(b): ...


@overload
def a(arg: int) -> int: ...
@overload
def a(arg: str) -> str: ...
@overload
def a(arg: object) -> NoReturn: ...
def a(arg: Union[int, str, object]) -> Union[int, str]:
    if not isinstance(arg, (int, str)):
        raise TypeError
    return arg

class Proto(Protocol):
    def foo(self, a: int) -> int:
        ...

    def bar(self, b: str) -> str: ...
    def baz(self, c: bytes) -> str:
        ...

# output

from typing import NoReturn, Protocol, Union, overload


def dummy(a): ...
def other(b): ...


@overload
def a(arg: int) -> int: ...
@overload
def a(arg: str) -> str: ...
@overload
def a(arg: object) -> NoReturn: ...


def a(arg: Union[int, str, object]) -> Union[int, str]:
    if not isinstance(arg, (int, str)):
        raise TypeError
    return arg


class Proto(Protocol):
    def foo(self, a: int) -> int: ...

    def bar(self, b: str) -> str: ...
    def baz(self, c: bytes) -> str: ...
