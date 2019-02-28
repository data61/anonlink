import functools as _functools
import typing as _typing
import warnings as _warnings

import mypy_extensions as _mypy_extensions


def _warn_deprecated(
    module_name: str,
    f_name: str,
    replacement: _typing.Optional[str]
) -> None:
    msg = f'anonlink.{module_name}.{f_name} has been deprecated '
    if replacement is not None:
        msg += f'(use anonlink.{replacement} instead)'
    else:
        msg += 'without replacement'
    _warnings.warn(msg, DeprecationWarning, stacklevel=3)


_WrappedF = _typing.TypeVar('_WrappedF',
                            bound=_typing.Callable[..., _typing.Any])
def make_decorator(
    module_name: str
) -> _typing.Callable[..., _typing.Any]:
    @_typing.overload
    def deprecate_decorator(
        f: None = None,
        *,
        replacement: _typing.Optional[str] = None
    ) -> _typing.Callable[[_WrappedF], _WrappedF]:
        ...
    @_typing.overload
    def deprecate_decorator(
        f: _WrappedF,
        *,
        replacement: _typing.Optional[str] = None
    ) -> _WrappedF:
        ...
    def deprecate_decorator(
        f: _typing.Optional[_WrappedF] = None,
        *,
        replacement: _typing.Optional[str] = None
    ) -> _typing.Union[_WrappedF, _typing.Callable[[_WrappedF], _WrappedF]]:
        def deprecate_decorator_inner(f: _WrappedF) -> _WrappedF:
            @_functools.wraps(f)
            def f_inner(*args, **kwargs):
                _warn_deprecated(module_name, f.__name__, replacement)
                return f(*args, **kwargs)
            return _typing.cast(_WrappedF, f_inner)
        # Use decorator with or without arguments.
        if f is None:
            return deprecate_decorator_inner
        else:
            return deprecate_decorator_inner(f)
    return deprecate_decorator
