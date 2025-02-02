# reverse-patch

![Tests](https://github.com/shmakovpn/reverse-patch/actions/workflows/python-package.yml/badge.svg)
[![codecov](https://codecov.io/github/shmakovpn/reverse-patch/graph/badge.svg?token=744XXMAKOZ)](https://codecov.io/github/shmakovpn/reverse-patch)

Unit-test writing revolution!!

The `reverse-patch` way is:

 - One unit test for one function or method.
 - One patch for one unit test.

# Installation

```bash
pip install reverse-patch
```

# The problem

Let's try to write unit-test for something like this:

```python
# my_code.py
def failed_function(x):
    raise RuntimeError(f'failed_one: {x}')


class FirstClass:
    first_class_const = '_first_class_const'

    def failed_method(self, x, y):
        raise RuntimeError('_failed_method')

    @classmethod
    def failed_class_method(cls, x, y):
        raise RuntimeError('_failed_class_method')

    @staticmethod
    def failed_static_method(x, y):
        raise RuntimeError('_failed_static_method')

    def success_method(self, method_argument):
        id_ = id(method_argument)

        self.failed_method(1, 2)
        self.failed_class_method(1, 2)
        self.failed_static_method(1, 2)
        return failed_function(id_)
```

```python
# pytest__my_code.py
import my_code as tm
from unittest.mock import patch, MagicMock


class TestFirstClass:
    def test_success_method(self):
        """ Minimal test (without asserts) """
        with patch.object(tm, 'id', create=True) as mock_id:  # 1
            with patch.object(tm.FirstClass, 'failed_method') as mock_failed_method:  # 2
                with patch.object(tm.FirstClass, 'failed_class_method') as mock_failed_class_method:  # 3
                    with patch.object(tm.FirstClass, 'failed_static_method') as mock_failed_static_method:  # 4
                        with patch.object(tm, 'failed_function') as mock_failed_function:  # 5
                            with patch.object(tm.FirstClass, '__init__', return_value=None):  # 6
                                fc = tm.FirstClass()
                                mock_method_argument = MagicMock()  # 7
                                result = fc.success_method(method_argument=mock_method_argument)
```

`FirstClass.success_method` does not have errors itself, but it calls other functions and methods that will fail.
Thus, we need to mock them all.

Generally, testing methods or functions call others those need database access, redis, etc.
Those calls have to be mocked.

You can do not mock something, but then you will test not only target method or function.
You will test target method or function and all not mocked dependencies!!
If there are many not mocked dependencies, your test will very complex, very hard to read and difficulty to support.

In other hand we want only 1 failed test for 1 failed method. So, all dependencies have to be mocked.

How you can see in example below, writing a minimal test with mocking all dependencies is very expensive.
In the case below we need to write seven mocks to create a minimal test, that just performs successfully, but does not make any asserts.

Let us do something. Let us write a new in `reverse style`.

```python
# pytest__my_code__reverse.py
import my_code as tm
from unittest.mock import patch, MagicMock


class TestFirstClass:
    def test_success_method(self):
        """ Minimal test (without asserts) """
        c = tm.FirstClass.success_method
        mock_self = MagicMock()  # 1
        with patch.object(tm, 'id', create=True) as mock_id:  # 2
            with patch.object(tm, 'failed_function') as mock_failed_function:  # 3
                mock_method_argument = MagicMock()  # 4
                result = c(self=mock_self, method_argument=mock_method_argument)
```

`Reverse` way is better. One need to create four mocks, but it is expensive too.

## The solution

Please. Look at the code of reverse test. If you write more unit-tests in reverse style, you will checkout,
that all test are very similar to each other.

What happens if we mock all `scope` of testing method automatically in one statement?

```python
# pytest__my_code__reverse_patch.py
import my_code as tm
from reverse_patch import ReversePatch


class TestFirstClass:
    def test_success_method(self):
        with ReversePatch(func=tm.FirstClass.success_method) as rp:  # 1
            result = rp.c(*rp.args)
```

Miracle!!

All minimal tests needs only one mock!!

## Full reverse_patch_test

Let us add testing logic.

```python
# pytest__my_code__reverse_patch.py
import my_code as tm
from reverse_patch import ReversePatch


class TestFirstClass:
    def test_success_method(self):
        """ 
        full test (100% coverage), 
        look pytest__reverse_patch.TestReversePatch.test_success_method for more information.
        Run this test in debugger, play around.
        """
        with ReversePatch(func=tm.FirstClass.success_method) as rp:  # 1 rp contains all needed mocks
            assert rp.c(*rp.args) == tm.failed_function.return_value  # assert 1
            tm.failed_function.assert_called_once_with(tm.id.return_value)  # assert 2
            tm.id.assert_called_once_with(rp.args.method_argument)  # assert 3
            rp.args.self.failed_method.assert_called_once_with(1, 2)  # assert 4
            rp.args[0].failed_class_method.assert_called_once_with(1, 2)  # assert 5
            rp.args[0].failed_static_method.assert_called_once_with(1, 2)  # assert 6
```

Testing method contains five not empty lines and six simple statements, look

```python
    def success_method(self, method_argument):
        id_ = id(method_argument)  # statement 1

        self.failed_method(1, 2)  # statement 2
        self.failed_class_method(1, 2)  # statement 3
        self.failed_static_method(1, 2)  # statement 4
        # return failed_function(id_)  
        result = failed_function(id_)  # statement 5
        return result  # statement 6
```

Great: 6 asserts for 6 statements!!

Just imagine, that you did not write testing method from scratch. Then only one line was added, e.g. `my_other_func()`.
Previously one need to write four or seven mocks, plus mock for `my_other_func`, 
plus one or two asserts that checks: return value of `my_other_func`, and something like `assert_called_once_with`.

The price is so hi, that one do not write them at all.

```python
class TestFirstClass:
    def test_success_method(self):
        with ReversePatch(func=tm.FirstClass.success_method) as rp:
            assert rp.c(*rp.args) == tm.failed_function.return_value
            tm.my_other_func.assert_called_once_with()
```

The entry threshold has been drastically lowered. Such tests are much more likely to be written.


## Testing `@propery`

Use `fget` attribute of the property instead of the property itself.

```python
# example
class ExampleProperty:
    @property
    def message(self):
        return 'hello'
```

```python
# test for example
class TestExampleProperty:
    def test_message(self):
        with ReversePatch(tm.ExampleProperty.message.fget) as rp:  # ! Use fget 
            assert rp.c(*rp.args) == 'hello'
```

## Testing logger message interpolation

```python
import logging
logger = logging.getLogger('some.logger')
logger.setLevel(logging.DEBUG)  # if level lower than DEBUG, debug message will not be interpolated


def do_log_debug_fail():
    """
    Calls logger with wrong message template
    """
    # TypeError: not all arguments converted during string formatting
    logger.debug('debug %s', 'fail', 1)
```

We want to test debug message matches other arguments passed to its call.

```python
    def test_do_log_debug_success(self):
        with ReversePatch(tm.do_log_debug_success, exclude_set={'logging', 'logger'}) as rp:
            with PatchLogger(tm.logger):
                assert rp.c(*rp.args) is None
```

## Unpacking ReversePatchDTO

`ReversePatchDTO` supports unpacking. This can be useful to make your tests more compact.

```py
    def test_rp_dto_unpack(self):
        with ReversePatch(tm.FirstClass.success_method) as (rp, c, args, s):
            assert rp.c == c
            assert rp.args == args
            assert rp.args.self == s

        with ReversePatch(tm.FirstClass.success_class_method) as (rp, c, args, cls):
            assert rp.c == c
            assert rp.args == args
            assert rp.args.cls == cls

        with ReversePatch(tm.FirstClass.success_static_method) as (rp, c, args, s):
            assert rp.c == c
            assert rp.args == args
            assert s is None
        # check short form
        with ReversePatch(tm.FirstClass.success_static_method) as (rp, c, *_):
            assert rp.c == c

        with ReversePatch(tm.FirstClass.success_method) as (rp, *_, s):
            assert rp.args.self == s
```

## Including (`include_set`) and excluding (`exclude_set`)

Sometime we want to patch some builtins, like `id`, `open`, `type`, etc.
This is available using `include_set`.

```py
    def test_success_static_method__include(self):
        with ReversePatch(tm.FirstClass.success_static_method__include, include_set={'type'}) as rp:
            r = rp.c(*rp.args)
            assert r == m(m(tm).type).return_value
```
`id` function is in `include_set` by default.

Note: `exclude_set` has more priority than `include_set`. So, if you put `id` in `exclude_set`, it will not be patched.
Example:

```py
    def test_success_static_method__exclude(self):
        with ReversePatch(tm.FirstClass.success_static_method__exclude, exclude_set={'id'}) as rp:
            r = rp.c(*rp.args)
            assert isinstance(r, int)  # id was not patched
```

Note: python3.10 cannot mock that already mocked. ReversePatch will exclude mock objects from patching.
It is not possible to patch them using `include_set` or any other way.

In `exclude_set` you can use object itself or its python path. 
The excluded object will be collected in ReversePathDTO in `exclusions` dictionary.
Also, you can access it using both ways, the object itself or its python path.

```py
        # region exclude_set
        with ReversePatch(tm.InitCase.use_attrs_inited_in__init, exclude_set={tm.InitCase.__init__}) as rp:
            rp.exclusions[tm.InitCase.__init__].c(*rp.exclusions[tm.InitCase.__init__].args)
            rp.c(*rp.args)

        with ReversePatch(tm.InitCase.use_attrs_inited_in__init, exclude_set={'InitCase.__init__'}) as rp:
            rp.exclusions[tm.InitCase.__init__].c(*rp.exclusions[tm.InitCase.__init__].args)
            rp.c(*rp.args)

        with ReversePatch(tm.InitCase.use_attrs_inited_in__init, exclude_set={'InitCase.__init__'}) as rp:
            rp.exclusions[tm.InitCase.__init__].c(*rp.exclusions['InitCase.__init__'].args)
            rp.c(*rp.args)
        # endregion exclude_set
```

Exception classes will be excluded. You can use `include_set` to force patch this classes.

```py
    def test_skip_exception_classes(self):
        with ReversePatch(tm.raise_some_exception) as rp:
            # SomeException will not be mocked be default
            with pytest.raises(tm.SomeException):
                rp.c(*rp.args)

        with ReversePatch(tm.raise_some_exception, include_set={'SomeException'}) as rp:
            # raise SomeException, if SomeException is a mock object, will produce TypeError
            with pytest.raises(TypeError):  
                rp.c(*rp.args)
```

## Shortcuts

`Rp` is the same as `ReversePath`.

```py
    def test_rp_shortcut__success_method(self):
        with Rp(tm.FirstClass.success_method) as rp:
            rp.c(*rp.args)
```

`Rc` automatically perform `r = rp.c(*rp.args)`. 
Use `Rc` instead of `Rp` or `ReversePatch`. 
This is more short and convenient way.

```py
    def test_rc_shortcut__success_method(self):
        with Rc(tm.FirstClass.success_method) as rc:
            # do not need `r = rp.c(*rp.args)`
            assert rc.r == m(tm.failed_function).return_value
```

`Rcl` like `Rc`, it automatically does `r = rp.c(*rp.args)`.
Also, it uses `PatchLogger` and exclude `logging` and `logger` identifiers in the testing module.

Thus, code below can be more short.

```py
    def test_do_log_debug_success(self):
        with ReversePatch(tm.do_log_debug_success, exclude_set={'logging', 'logger'}) as rp:
            with PatchLogger(tm.logger):
                assert rp.c(*rp.args) is None
```

Like this.

```py
    def test_do_log_debug_success__via_shortcut(self):
        with Rcl(tm.do_log_debug_success):
            pass
```

Note: `Rcl` works only if your testing module imports `logging` and creates a logger with identifier name `logger`.

```py
# testing module
import logging  # Rcl requires
logger = logging.getLogger('my_logger')  # Rcl requires
```

## Examples

Please, look `pytest__reverse_patch`, self-documented file contains the most usage examples, 
those checks `ReversePatch` using `ReversePatch` itself.

More useful examples:
- TestReversePatch.test_success_method
- TestReversePatch.test_success_class_method
- TestReversePatch.test_use_attrs_inited_in__init

## Bonus

All mocks created by `ReversePatch` created with `autospec`. 
So your tests will defend your code against a human factor in the future, like a dirty refactoring.
