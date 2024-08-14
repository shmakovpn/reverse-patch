from typing import cast
import pytest
from unittest.mock import NonCallableMock, Mock, MagicMock
from reverse_patch import ReversePatch, ArgsKwargs, ArgumentName
import reverse_patch_data.testing_fixtures as tm


"""
TLDR: We recommended to look at test_success_method, and test_success_class_method, because it more basic.
test_success_method, test_success_class_method is enough to write your first unit-tests based on ReversePatch.

These are very short, it covered tested methods to 100%.
Please. look at the basic test structure, that represents the minimal successfully test without asserts.
Wow!! Only three lines, including `def test_success_method(self):`, it is amazing.

```py
    def test_success_method(self):
        with ReversePatch(tm.FirstClass.success_method) as rp_dto:
            r = rp_dto.c(*rp_dto.args)
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
        with ReversePatch(tm.FirstClass.success_method) as rp_dto:
            assert isinstance(rp_dto.args[0].first_class_const, NonCallableMock)

    def test_second_class__second_class_const(self):
        """
        All attributes in internal class in `testing module.FistClass.SecondClass` have to be mocked,
        including string constant `FirstClass.SecondClass.second_class_const`.
        This mocking is not performing directly, see comments in this test, to learn how to access to mocked attributes.

        Lets check, that `FirstClass.SecondClass.second_class_const` become a Mock.
        """
        with ReversePatch(tm.FirstClass.success_method) as rp_dto:
            # Note: rp_dto.args[0] == rp_dto.args.self
            # if you need access to mocked `FirstClass.SecondClass.second_class_const`,
            # you have to use rp_dto.args[0] or rp_dto.args.self
            # Please: don't use `tm.FirstClass.SecondClass.second_class_const`,
            # because classes that are in path to testing method
            # are not mocked in `testing module` to stay access for original classes for future.
            assert isinstance(rp_dto.args[0].SecondClass.second_class_const, NonCallableMock)

    def test_second_class(self):
        """
        All classes in path to testing method have to be mocked,
        including `FirstClass.SecondClass`.
        This mocking is not performing directly, see comments in this test, to learn how to access to mocked attributes.

        Lets check, that `FirstClass.SecondClass` become a Mock.
        """
        with ReversePatch(tm.FirstClass.success_method) as rp_dto:
            # Note: rp_dto.args[0] == rp_dto.args.self
            # if you need access to mocked `FistClass.SecondClass`
            # you have to use rp_dto[0] or rp_dto.args.self
            # Please: don't use `tm.FirstClass.SecondClass`,
            # because classes that are in path to testing method
            # are not mocked in `testing module` to stay access for original classes for future.
            assert isinstance(rp_dto.args[0].SecondClass, Mock)

    def test_success_method(self):
        """
        Full test (with 100% coverage) for `success_method`.

        In this case `success_method` calls other functions that fails.
        But the `success_method` itself does not contain errors, so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.success_method) as rp_dto:
            r = rp_dto.c(*rp_dto.args)
            assert r == cast(Mock, tm.failed_function).return_value
            cast(Mock, tm.failed_function).assert_called_once_with(tm.id.return_value)  # noqa
            # Note: rp_dto.args[0] == rp_dto.args.self
            # In the case of `FirstClass.success_method`, see method signature,
            # one can access to mocked `method_argument` like `rp_dto.args[1]` or `rp_dto.args.method_argument`.
            cast(Mock, getattr(tm, 'id')).assert_called_once_with(rp_dto.args.method_argument)

            # Please, don't use `tm.FirstClass.failed_method`, because class that are in path to testing method
            # are not mocked in `testing_module` to stay access for original classes for future
            # use `rp_dto.args.self.failed_method` or `rp_dto.args[0].failed_method` instead
            cast(Mock, rp_dto.args.self.failed_method).assert_called_once_with(1, 2)
            cast(Mock, rp_dto.args[0].failed_class_method).assert_called_once_with(1, 2)
            cast(Mock, rp_dto.args[0].failed_static_method).assert_called_once_with(1, 2)

    def test_success_class_method(self):
        """
        Full test (with 100% coverage) for `success_class_method`.

        In this case `success_class_method` calls other functions that fails.
        But the `success_class_method` itself does not contain errors, so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.success_class_method) as rp_dto:
            r = rp_dto.c(*rp_dto.args)
            assert r == cast(Mock, tm.failed_function).return_value
            # None: rp_dto.args[0] == rp_dto.args.cls
            # In the case of `FirstClass.success_class_method`, see method signature,
            # one can access to mocked `class_method_argument` like `rp_dto.args[1]`
            # or `rp_dto.args.class_method_argument`
            cast(Mock, tm.id).assert_called_once_with(rp_dto.args.class_method_argument)  # noqa

            # Please, don't use `tm.FirstClass.failed_class_method`,
            # because class that are in path to testing class method are not mocked in `testing_module`
            # to stay access for original classes for future
            # user `rp_dto.args.cls.failed_class_method` or `rp_dto.args[0].failed_class_method`
            cast(Mock, rp_dto.args.cls.failed_class_method).assert_called_once_with(1, 2)
            cast(Mock, rp_dto.args[0].failed_static_method).assert_called_once_with(1, 2)
            cast(Mock, tm.failed_function).assert_called_once_with(tm.id.return_value)  # noqa

    def test_success_static_method(self):
        """
        Minimal test (without asserts) for `success_static_method`.

        In this case `success_static_method` calls other functions that fails.
        But the `success_static_method` itself does not contain errors, so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.success_static_method) as rp_dto:
            _r = rp_dto.c(*rp_dto.args)

    def test_fail_method__failed_function(self):
        """
        Minimal test (without asserts) for `fail_method__failed_function`.

        In this case `fail_method__failed_function` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_function) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_method__failed_method(self):
        """
        Minimal test (without asserts) for `fail_method__failed_method`.

        In this case `fail_method__failed_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `fail_method__failed_class_method`.

        In this case `fail_method__failed_class_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_class_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `fail_method__failed_static_method`.

        In this case `fail_method__failed_static_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_method__failed_static_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_class_method__failed_function(self):
        """
        Minimal test (without asserts) for `fail_class_method__failed_function`.

        In this case `fail_class_method__failed_function` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_class_method__failed_function) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_class_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `fail_class_method__failed_class_method`.

        In this case `fail_class_method__failed_class_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_class_method__failed_class_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_class_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `fail_class_method__failed_static_method`.

        In this case `fail_class_method__failed_static_method` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_class_method__failed_static_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_static_method__failed_function(self):
        """
        Minimal test (without asserts) for `fail_static_method__failed_functions`.

        In this case `fail_static_method__failed_functions` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.fail_static_method__failed_functions) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_second_success_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_success_method`

        In this case `FirstClass.SecondClass.second_success_method` calls other functions that fails.
        But the `FirstClass.SecondClass.second_success_method` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_success_method) as rp_dto:
            rp_dto.c(*rp_dto.args)

    def test_second_success_class_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_success_class_method`

        In this case `FirstClass.SecondClass.second_success_class_method` calls other functions that fails.
        But the `FirstClass.SecondClass.second_success_class_method` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_success_class_method) as rp_dto:
            rp_dto.c(*rp_dto.args)

    def test_second_success_static_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_success_static_method`

        In this case `FirstClass.SecondClass.second_success_static_method` calls other functions that fails.
        But the `FirstClass.SecondClass.second_success_static_method` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_success_static_method) as rp_dto:
            rp_dto.c(*rp_dto.args)

    def test_second_fail_method__failed_function(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_function`

        In this case `FirstClass.SecondClass.second_fail_method__failed_function`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_function) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_method__failed_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_method`

        In this case `FirstClass.SecondClass.second_fail_method__failed_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_class_method`

        In this case `FirstClass.SecondClass.second_fail_method__failed_class_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_class_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_method__failed_static_method`

        In this case `FirstClass.SecondClass.second_fail_method__failed_static_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_method__failed_static_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_class_method__failed_function(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_class_method__failed_function`

        In this case `FirstClass.SecondClass.second_fail_class_method__failed_function`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_class_method__failed_function) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_class_method__failed_class_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_class_method__failed_class_method`

        In this case `FirstClass.SecondClass.second_fail_class_method__failed_class_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_class_method__failed_class_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_class_method__failed_static_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_class_method__failed_static_method`.

        In this case `FirstClass.SecondClass.second_fail_class_method__failed_static_method`
        calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_class_method__failed_static_method) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_success_function(self):
        """
        Minimal test (without asserts) for `success_function`.

        In this case `success_function` calls other functions that fails.
        But the `success_function` itself does not contain errors,
        so this test must be performed successfully.
        """
        with ReversePatch(tm.success_function) as rp_dto:
            rp_dto.c(*rp_dto.args)

    def test_fail__failed_function(self):
        """
        Minimal test (without asserts) for `fail__failed_function`.

        In this case `fail__failed_function` calls other function with wrong signature.
        Here we catch `TypeError` that raised when trying to call a MagicMock callable with wrong signature
        """
        with ReversePatch(tm.fail__failed_function) as rp_dto:
            with pytest.raises(TypeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_no_method(self):
        """
        Minimal test (without asserts) for `FirstClass.fail_no_method`.

        In this case `FirstClass.fail_no_method` try to call a method that does not exist.
        Here we catch `AttributeError`.
        """
        with ReversePatch(tm.FirstClass.fail_no_method) as rp_dto:
            with pytest.raises(AttributeError):
                rp_dto.c(*rp_dto.args)

    def test_fail_no_function(self):
        """
        Minimal test (without asserts) for `FirstClass.fail_no_function`.

        In this case `FirstClass.fail_no_function` try to call a global function that does not exist.
        Here we catch `NameError`.
        """
        with ReversePatch(tm.FirstClass.fail_no_function) as rp_dto:
            with pytest.raises(NameError):
                rp_dto.c(*rp_dto.args)

    def test_fail_no_function1(self):
        """
        Minimal test (without asserts) for `fail_no_function1`.

        In this case `fail_no_function1` try to call a global function that does not exist.
        Here we catch `NameError`.
        """
        with ReversePatch(tm.fail_no_function1) as rp_dto:
            with pytest.raises(NameError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_no_method(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_no_method`.

        In this case `FirstClass.SecondClass.second_fail_no_method` try to call a method that does not exist.
        Here we catch `AttributeError`.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_no_method) as rp_dto:
            with pytest.raises(AttributeError):
                rp_dto.c(*rp_dto.args)

    def test_second_fail_no_function(self):
        """
        Minimal test (without asserts) for `FirstClass.SecondClass.second_fail_no_function`.

        In this case `FirstClass.SecondClass.second_fail_no_function` try to call a function that does not exist.
        Here we catch `NameError`.
        """
        with ReversePatch(tm.FirstClass.SecondClass.second_fail_no_function) as rp_dto:
            with pytest.raises(NameError):
                rp_dto.c(*rp_dto.args)

    def test_success_static_method__include(self):
        """
        We put `type` in `include_set`,
        then `type` called in `FirstClass.success_static_method__include` will be mocked,
        after we checks that `type` was a MagicMock
        """
        with ReversePatch(tm.FirstClass.success_static_method__include, include_set={'type'}) as rp_dto:
            r = rp_dto.c(*rp_dto.args)
            assert r == tm.type.return_value  # noqa type is MagicMock, and has `return_value`

    def test_success_static_method__exclude(self):
        """
        `id` is mocked by default.
        Here we put `id` to `exclude_set`. After checks, that `id` was not mocked and return an integer, not a Mock
        """
        with ReversePatch(tm.FirstClass.success_static_method__exclude, exclude_set={'id'}) as rp_dto:
            r = rp_dto.c(*rp_dto.args)
            assert isinstance(r, int)


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
