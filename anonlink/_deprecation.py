import functools as _functools
import typing as _typing
import warnings as _warnings


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


# Mypy typing this is too hard. ¯\_(ツ)_/¯
def make_decorator(module_name):
    def deprecate_decorator(f=None, *, replacement=None):
        def deprecate_decorator_inner(f):
            @_functools.wraps(f)
            def f_inner(*args, **kwargs):
                _warn_deprecated(module_name, f.__name__, replacement)
                return f(*args, **kwargs)
            return f_inner
        # Use decorator with or without arguments.
        if f is None:
            return deprecate_decorator_inner
        else:
            return deprecate_decorator_inner(f)
    return deprecate_decorator


