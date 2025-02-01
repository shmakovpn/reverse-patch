from typing import cast
import pytest
from unittest.mock import NonCallableMock, Mock, MagicMock, patch
from reverse_patch import (
    ReversePatch,
    ArgsKwargs,
    ArgumentName,
    IdentifierName,
    m,
    Rp,
    Rc,
)
import reverse_patch.testing_fixtures as tm
from reverse_patch.patch_logger import PatchLogger


"""
TLDR: We recommended to look at `test_success_method`, and `test_success_class_method`, because it more basic.
test_success_method, test_success_class_method is enough to write your first unit-tests based on ReversePatch.

These are very short, it covered tested methods to 100%.
Please. look at the basic test structure, that represents the minimal successfully test without asserts.
Wow!! Only three lines, including `def test_success_method(self):`, it is amazing.

```py
    def test_success_method(self):
        with ReversePatch(tm.FirstClass.success_method) as rp:
            r = rp.c(*rp.args)
            # your asserts here
```
"""


class TestReversePatch:
    """
    Unit-tests for ReversePatch itself and at the same time helpful examples, how to work this ReversePatch.

    Here we will testing `reverse_patch_data/testing_fixtures.py` module
    """

    def test_module_const(self):
        """
        All identifiers (variables) in testing module `reverse_patch_data/testing_fixtures.py` have to be mocked,
        including string constant `MODULE_CONST`.

        Lets check, that `MODULE_CONST` become a Mock
        """
        with ReversePatch(tm.FirstClass.success_method):
            assert isinstance(tm.MODULE_CONST, NonCallableMock)

    def test_first_class_const(self):
        """
        All attributes in classes in testing module `reverse_patch_data/testing_fixtures.py` have to be mocked,
        including string constant `FirstClass.first_class_const`.

        Lets check, that `FirstClass.first_class_const` become a Mock.
        """
        with ReversePatch(tm.FirstClass.success_method) as rp:
            assert isinstance(rp.args[0].first_class_const, NonCallableMock)

    def test_second_class__second_class_const(self):
        """
        All attributes in internal class in `testing module.FistClass.SecondClass` have to be mocked,
        including string constant `FirstClass.SecondClass.second_class_const`.
        This mocking is not performing directly, see comments in this test, to learn how to access to mocked attributes.

        Lets check, that `FirstClass.SecondClass.second_class_const` become a Mock.
        """
        with ReversePatch(tm.FirstClass.success_method) as rp:
            # Note: rp.args[0] == rp.args.self
            # if you need access to mocked `FirstClass.SecondClass.second_class_const`,
            # you have to use rp.args[0] or rp.args.self
            # Please: don't use `tm.FirstClass.SecondClass.second_class_const`,
            # because classes that are in path to testing method
            # are not mocked in `testing module` to stay access for original classes for future.
            assert isinstance(rp.args[0].SecondClass.second_class_const, NonCallableMock)

    def test_second_class(self):
        """
        All classes in path to testing method have to be mocked,
        including `FirstClass.SecondClass`.
        This mocking is not performing directly, see comments in this test, to learn how to access to mocked attributes.

        Lets check, that `FirstClass.SecondClass` become a Mock.
        """
        with ReversePatch(tm.FirstClass.success_method) as rp:
            # Note: rp.args[0] == rp.args.self
            # if you need access to mocked `FistClass.SecondClass`
            # you have to use rp[0] or rp.args.self
            # Please: don't use `tm.FirstClass.SecondClass`,
            # because classes that are in path to testing method
            # are not mocked in `testing module` to stay access for original classes for future.
            assert isinstance(rp.args[0].SecondClass, Mock)

    def test_success_method(self):
        """
        Full test (with 100% coverage) for `success_method`.

        In this case `success_method` calls other functions that fails.
        But the `success_method` itself does not contain errors, so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.success_method) as rp:
            r = rp.c(*rp.args)
            assert r == cast(Mock, tm.failed_function).return_value
            cast(Mock, tm.failed_function).assert_called_once_with(tm.id.return_value)  # noqa
            # Note: rp.args[0] == rp.args.self
            # In the case of `FirstClass.success_method`, see method signature,
            # one can access to mocked `method_argument` like `rp.args[1]` or `rp.args.method_argument`.
            cast(Mock, getattr(tm, 'id')).assert_called_once_with(rp.args.method_argument)

            # Please, don't use `tm.FirstClass.failed_method`, because class that are in path to testing method
            # are not mocked in `testing_module` to stay access for original classes for future
            # use `rp.args.self.failed_method` or `rp.args[0].failed_method` instead
            cast(Mock, rp.args.self.failed_method).assert_called_once_with(1, 2)
            cast(Mock, rp.args[0].failed_class_method).assert_called_once_with(1, 2)
            cast(Mock, rp.args[0].failed_static_method).assert_called_once_with(1, 2)

    def test_success_class_method(self):
        """
        Full test (with 100% coverage) for `success_class_method`.

        In this case `success_class_method` calls other functions that fails.
        But the `success_class_method` itself does not contain errors, so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.success_class_method) as rp:
            r = rp.c(*rp.args)
            assert r == cast(Mock, tm.failed_function).return_value
            # None: rp.args[0] == rp.args.cls
            # In the case of `FirstClass.success_class_method`, see method signature,
            # one can access to mocked `class_method_argument` like `rp.args[1]`
            # or `rp.args.class_method_argument`
            cast(Mock, tm.id).assert_called_once_with(rp.args.class_method_argument)  # noqa

            # Please, don't use `tm.FirstClass.failed_class_method`,
            # because class that are in path to testing class method are not mocked in `testing_module`
            # to stay access for original classes for future
            # user `rp.args.cls.failed_class_method` or `rp.args[0].failed_class_method`
            cast(Mock, rp.args.cls.failed_class_method).assert_called_once_with(1, 2)
            cast(Mock, rp.args[0].failed_static_method).assert_called_once_with(1, 2)
            cast(Mock, tm.failed_function).assert_called_once_with(tm.id.return_value)  # noqa

    def test_success_static_method(self):
        """
        Minimal test (without asserts) for `success_static_method`.

        In this case `success_static_method` calls other functions that fails.
        But the `success_static_method` itself does not contain errors, so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.success_static_method) as rp:
            _r = rp.c(*rp.args)

    def test_fail_method__failed_function(self):
        """
        Minimal test (without asserts) for `fail_method__failed_function`.

        In this case `fail_method__failed_function` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_function) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_method__failed_method(self):
        """
        Minimal test (without asserts) for `fail_method__failed_method`.

        In this case `fail_method__failed_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `fail_method__failed_class_method`.

        In this case `fail_method__failed_class_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_class_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `fail_method__failed_static_method`.

        In this case `fail_method__failed_static_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_static_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_class_method__failed_function(self):
        """
        Minimal test (without asserts) for `fail_class_method__failed_function`.

        In this case `fail_class_method__failed_function` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_class_method__failed_function) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_class_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `fail_class_method__failed_class_method`.

        In this case `fail_class_method__failed_class_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_class_method__failed_class_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_class_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `fail_class_method__failed_static_method`.

        In this case `fail_class_method__failed_static_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_class_method__failed_static_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_static_method__failed_function(self):
        """
        Minimal test (without asserts) for `fail_static_method__failed_functions`.

        In this case `fail_static_method__failed_functions` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_static_method__failed_functions) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_second_success_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_success_method`

        In this case `FirstClass.SecondClass.second_success_method` calls other functions that fails.
        But the `FirstClass.SecondClass.second_success_method` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_success_method) as rp:
            rp.c(*rp.args)

    def test_second_success_class_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_success_class_method`

        In this case `FirstClass.SecondClass.second_success_class_method` calls other functions that fails.
        But the `FirstClass.SecondClass.second_success_class_method` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_success_class_method) as rp:
            rp.c(*rp.args)

    def test_second_success_static_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_success_static_method`

        In this case `FirstClass.SecondClass.second_success_static_method` calls other functions that fails.
        But the `FirstClass.SecondClass.second_success_static_method` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_success_static_method) as rp:
            rp.c(*rp.args)

    def test_second_fail_method__failed_function(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_function`

        In this case `FirstClass.SecondClass.second_fail_method__failed_function`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_function) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_second_fail_method__failed_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_method`

        In this case `FirstClass.SecondClass.second_fail_method__failed_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_second_fail_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_class_method`

        In this case `FirstClass.SecondClass.second_fail_method__failed_class_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_class_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_second_fail_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_static_method`

        In this case `FirstClass.SecondClass.second_fail_method__failed_static_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_static_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_second_fail_class_method__failed_function(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_class_method__failed_function`

        In this case `FirstClass.SecondClass.second_fail_class_method__failed_function`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_class_method__failed_function) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_second_fail_class_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_class_method__failed_class_method`

        In this case `FirstClass.SecondClass.second_fail_class_method__failed_class_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_class_method__failed_class_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_second_fail_class_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_class_method__failed_static_method`.

        In this case `FirstClass.SecondClass.second_fail_class_method__failed_static_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_class_method__failed_static_method) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_success_function(self):
        """
        Minimal test (without asserts) for `success_function`.

        In this case `success_function` calls other functions that fails.
        But the `success_function` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.success_function) as rp:
            rp.c(*rp.args)

    def test_fail__failed_function(self):
        """
        Minimal test (without asserts) for `fail__failed_function`.

        In this case `fail__failed_function` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.fail__failed_function) as rp:
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_fail_no_method(self):
        """
        Minimal test (without asserts) for `FirstClass.fail_no_method`.

        In this case `FirstClass.fail_no_method` try to call a method that does not exist.
        Here we catch `AttributeError`.
        """
        with ReversePatch(tm.FirstClass.fail_no_method) as rp:
            with pytest.raises(AttributeError):
                rp.c(*rp.args)

    def test_fail_no_function(self):
        """
        Minimal test (without asserts) for `FirstClass.fail_no_function`.

        In this case `FirstClass.fail_no_function` try to call a global function that does not exist.
        Here we catch `NameError`.
        """
        with ReversePatch(tm.FirstClass.fail_no_function) as rp:
            with pytest.raises(NameError):
                rp.c(*rp.args)

    def test_fail_no_function1(self):
        """
        Minimal test (without asserts) for `fail_no_function1`.

        In this case `fail_no_function1` try to call a global function that does not exist.
        Here we catch `NameError`.
        """
        with ReversePatch(tm.fail_no_function1) as rp:
            with pytest.raises(NameError):
                rp.c(*rp.args)

    def test_second_fail_no_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_no_method`.

        In this case `FirstClass.SecondClass.second_fail_no_method` try to call a method that does not exist.
        Here we catch `AttributeError`.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_no_method) as rp:
            with pytest.raises(AttributeError):
                rp.c(*rp.args)

    def test_second_fail_no_function(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_no_function`.

        In this case `FirstClass.SecondClass.second_fail_no_function` try to call a function that does not exist.
        Here we catch `NameError`.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_no_function) as rp:
            with pytest.raises(NameError):
                rp.c(*rp.args)

    def test_success_static_method__include(self):
        """
        We put `type` in `include_set`,
        then `type` called in `FirstClass.success_static_method__include` will be mocked,
        after we checks that `type` was a MagicMock
        """
        with ReversePatch(tm.FirstClass.success_static_method__include, include_set={IdentifierName('type')}) as rp:
            r = rp.c(*rp.args)
            assert r == m(m(tm).type).return_value

    def test_success_static_method__exclude(self):
        """
        `id` is mocked by default.
        Here we put `id` to `exclude_set`. After checks, that `id` was not mocked and return an integer, not a Mock
        """
        with ReversePatch(tm.FirstClass.success_static_method__exclude, exclude_set={'id'}) as rp:
            r = rp.c(*rp.args)
            assert isinstance(r, int)

    def test_use_attrs_inited_in__init(self):
        """
        `x` and `y` attribute creates in `__init__`, these are not attributes of the class,
        and can not be mocked by default using `autospec=True`.
        `tm.InitCase.use_attrs_inited_in__init` try to access these attributes, so `AttributeError` will raised.

        Solutions:
          0. Refactoring, create these attributes in class `InitCase`:
            ```py
            class InitCase:
                x = None
                x = None
            ```
          1. create needed mocks manually - expensive way
            1.1 create needed mocks after patch - more short expensive way
          2. run `__init__` before run testing method
          3. put `__init__` in `exclude_set`, when run it before testing method
        """
        # region default_attribute_error
        with ReversePatch(tm.InitCase.use_attrs_inited_in__init) as rp:
            with pytest.raises(AttributeError):
                rp.c(*rp.args)  # by default will `AttributeError`
        # endregion default_attribute_error

        # region expensive_way
        # You have to mock all attributes of an instance of the class using in testing method.
        # This way may be expensive
        # Note: here we use 40 and 50, not mock objects, because in python3.10 will 'Cannot autospec a Mock object'
        with patch.object(tm.InitCase, 'x', 40, create=True):  # mock 1
            with patch.object(tm.InitCase, 'y', 50, create=True):  # mock 2
                with ReversePatch(tm.InitCase.use_attrs_inited_in__init) as rp:
                    rp.c(*rp.args)
        # endregion expensive_way

        # region more_short_expensive_way
        with ReversePatch(tm.InitCase.use_attrs_inited_in__init) as rp:
            rp.args.self.x = Mock()  # the same as `with patch.object(tm.InitCase, 'x', create=True)`
            rp.args.self.y = Mock()  # the same as `with patch.object(tm.InitCase, 'y', create=True)`
            rp.c(*rp.args)
        # endregion more_short_expensive_way

        # region run_init_before
        with ReversePatch(tm.InitCase.__init__) as rp:
            init_rp = rp

        assert not isinstance(tm.InitCase.__init__, NonCallableMock)

        with ReversePatch(tm.InitCase.use_attrs_inited_in__init) as rp:
            tm.InitCase.__init__(rp.args.self, *init_rp.args[1:])  # noqa
            rp.c(*rp.args)
        # endregion run_init_before

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

        # region exclude_set

        # endregion exclude_set

    def test_do_log_debug_success(self):
        with ReversePatch(tm.do_log_debug_success, exclude_set={'logging', 'logger'}) as rp:
            with PatchLogger(tm.logger):
                assert rp.c(*rp.args) is None

    def test_do_log_debug_fail(self):
        with ReversePatch(tm.do_log_debug_fail, exclude_set={'logging', 'logger'}) as rp:
            with PatchLogger(tm.logger):
                with pytest.raises(TypeError):
                    assert rp.c(*rp.args) is None

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

    def test_skip_exception_classes(self):
        with ReversePatch(tm.raise_some_exception) as rp:
            # SomeException will not be mocked be default
            with pytest.raises(tm.SomeException):
                rp.c(*rp.args)

        with ReversePatch(tm.raise_some_exception, include_set={'SomeException'}) as rp:
            # raise SomeException, if SomeException is a mock object, will produce TypeError
            with pytest.raises(TypeError):
                rp.c(*rp.args)

    def test_classes_with_mocks(self):
        """Test class with mocks can be patched"""
        with ReversePatch(tm.ClassWithMocks.some_method) as rp:
            assert rp.c(*rp.args) == 'hello ClassWithMocks'

    def test_rp_shortcut__success_method(self):
        """
        Test `success_method` using `Rp` shortcut instead of `ReversePath`.
        """
        with Rp(tm.FirstClass.success_method) as rp:
            rp.c(*rp.args)

    def test_rc_shortcut__success_method(self):
        """
        `Rc` automatically perform `r = rp.c(*rp.args)`.
        """
        with Rc(tm.FirstClass.success_method) as rc:
            # do not need `r = rp.c(*rp.args)`
            assert rc.r == m(tm.failed_function).return_value

    def test_rc_dto_unpack(self):
        """
        Use `Rc` instead of `Rp` or `ReversePatch`.
        This is more short and convenient way.
        """
        with Rc(tm.FirstClass.success_method) as (r, rc, c, args, s):
            assert rc.r == r
            assert rc.c == c
            assert rc.args == args
            assert rc.args.self == s

        with Rc(tm.FirstClass.success_class_method) as (r, rc, c, args, cls):
            assert rc.r == r
            assert rc.c == c
            assert rc.args == args
            assert rc.args.cls == cls

        with Rc(tm.FirstClass.success_static_method) as (r, rc, c, args, s):
            assert rc.r == r
            assert rc.c == c
            assert rc.args == args
            assert s is None
        # check short form
        with Rc(tm.FirstClass.success_static_method) as (r, rc, c, *_):
            assert rc.r == r
            assert rc.c == c

        with Rc(tm.FirstClass.success_method) as (r, rc, *_, s):
            assert rc.r == r
            assert rc.args.self == s


class TestArgsKwargs:
    def test_args_kwargs(self):
        args_kwargs = ArgsKwargs()
        args_kwargs.add_argument(ArgumentName('cls'), cast(MagicMock, '_cls'))
        args_kwargs.add_argument(ArgumentName('self'), cast(MagicMock, '_self'))
        args_kwargs.add_argument(ArgumentName('foo'), cast(MagicMock, '_foo'))
        args_kwargs.add_argument(ArgumentName('bar'), cast(MagicMock, '_bar'))
        assert args_kwargs.cls == '_cls'
        assert args_kwargs.self == '_self'
        assert args_kwargs.foo == '_foo'
        assert args_kwargs.bar == '_bar'

        assert args_kwargs[0] == '_cls'
        assert args_kwargs[1] == '_self'
        assert args_kwargs[2] == '_foo'
        assert args_kwargs[3] == '_bar'

        unpacked = [*args_kwargs]
        assert unpacked == ['_cls', '_self', '_foo', '_bar']

        # region setattr
        args_kwargs.foo = '_new_foo'
        assert args_kwargs.foo == '_new_foo'
        assert args_kwargs[2] == '_new_foo'
        # endregion setattr


class TestUtilsM:
    def test_m(self):
        """check that m is a shortcut for cast(Mock, arg)"""
        assert m('hello') == 'hello'
