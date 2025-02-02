from typing import Callable, List, ContextManager, Set, Optional, Dict, NewType, Union, Any
from types import ModuleType
import logging
import dataclasses
import sys
import inspect
from unittest.mock import Mock, patch, MagicMock
from .patch_logger import PatchLogger

__all__ = (
    'ArgumentName',
    'ArgumentIndex',
    'IdentifierName',
    'IdentifierPath',
    'ArgsKwargs',
    'ReversePatchDTO',
    'ReversePatch',
    'Rp',
    'ResultReversePatchDTO',
    'Rc',
    'Rcl',
)

ArgumentName = NewType('ArgumentName', str)
"""
The name of an argument if function or method signature.

example:

```py
def my_func(self, x):
    # ArgumentName('self') the name of the argument with ArgumentIndex(0)
    # ArgumentName('x) the name of the argument with ArgumentIndex(1)
    pass
```
"""

ArgumentIndex = NewType('ArgumentIndex', int)
"""
The index of argument in order of a method or a function signature

example:

```py
def my_func(self, x):
    # ArgumentIndex(0) the index of the ArgumentName('self') argument
    # ArgumentIndex(1) the index of the ArgumentName('x') argument
    pass
```
"""

IdentifierName = NewType('IdentifierName', str)
"""
The name of python (identifier) variable in a scope 
"""

IdentifierPath = NewType('IdentifierPath', str)
"""
The python path to identifier
"""


class ArgsKwargs(list):
    """
    Container for `*args` and `**kwargs` based in list.

    Usage example:

    ```py
    m0 = MagicMock()
    m1 = MagicMock()

    args_kwargs = ArgsKwargs()
    args_kwargs.add_argument(argument_name=ArgumentName('self'), argument_value=m0)
    args_kwargs.add_argument(argument_name=ArgumentName('x'), argument_value=m1)

    assert args_kwargs[0] is m0
    assert args_kwargs.self is m0

    assert args_kwargs[1] is m1
    assert args_kwargs.x is m1

    # you can unpack ArgsKwargs
    # `c(*args_kwargs)` the same as `c(m0, m1)`
    ```
    """
    _index_map: Dict[ArgumentName, ArgumentIndex] = {}  # {'argument name': argument index}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._index_map: Dict[ArgumentName, ArgumentIndex] = {}

    def __getattr__(self, item: ArgumentName) -> MagicMock:
        try:
            return super().__getitem__(self._index_map[item])
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, key, value):
        if key not in dir(self):
            super().__setitem__(self._index_map[key], value)
        else:
            super().__setattr__(key, value)

    def add_argument(self, argument_name: ArgumentName, argument_value: MagicMock) -> None:
        """Adds argument and its value to this list"""
        self._index_map[argument_name] = ArgumentIndex(len(self._index_map))
        super().append(argument_value)


@dataclasses.dataclass
class CallableDTO:
    args: ArgsKwargs
    """
    The list of arguments, 
    including `self` for methods (args[0] or args.self) and `cls` for class-methods (args[0] or args.cls)
    """
    c: Callable
    """callable, you have to call in your unit-test like: `rp.c(*rp.args)`"""


@dataclasses.dataclass
class ReversePatchDTO:
    """
    Patching result. Mock arguments and callable to call.
    """

    args: ArgsKwargs
    """
    The list of arguments, 
    including `self` for methods (args[0] or args.self) and `cls` for class-methods (args[0] or args.cls)
    """
    c: Callable
    """callable, you have to call in your unit-test like: `rp.c(*rp.args)`"""
    exclusions: Dict[Union[Callable, IdentifierPath, str], CallableDTO]
    """The list of arguments for excluded callable"""

    def __iter__(self):
        """
        with ReversePatch(f) as rp, c, args, s:
            assert rp.c == c
            assert rp.args == args
            assert rp.args.self == s  # or assert rp.args.cls == s
        """
        yield self
        yield self.c
        yield self.args
        yield getattr(self.args, 'self', getattr(self.args, 'cls', None))


class FakeModule:
    def __init__(self, tm):
        self.tm = tm


class ReversePatch:
    """
    Reverse patch context manager. Creates mock scope, mock argument list and give your callable to call
    in your unit-test, extracted from testing method or function

    example:

    ```py
    # pytests/pytest__my_module.py

    import my_module as tm  # testing module
    from reverse_patch import ReversePatch

    with ReversePatch(tm.my_func) as rp:
        # all scope around of tm.my_func will me mocked
        # rp.c - callable you need to use in your unit-tests
        # rp_ato.args - mocked argument list you need to use in your unit-tests
        result = rp.c(*rp.args)  # call testing method or function
        # your asserts
    ```
    """

    _include_set: Set[Union[IdentifierName, IdentifierPath]] = {'id'}
    """
    Identifiers (variables) names or qualified names which have to be mocked

    example:

    ```py
    with ReversePatch(tm.my_func, include_set={'type'}) as rp:
        # `tm.type` will be a MagicMock in the testing module `tm`
        result = rp.c(*rp.args)
        assert tm.type.assert_called()  # do asserts with mocked `type`
        tm.something.assert_called_once_with(type_=tm.type.return_value)  # using mocked `type` return value
    ```
    """
    _exclude_set: Set[Union[IdentifierName, Callable]] = set()
    """
    Identifiers (variables) names or objects which have to be excluded from mocking

    example:

    ```py
    with ReversePatch(tm.MyClass.my_method, exclude_set={'my_func', tm.MyClass.__init__}) as rp:
        # `tm.my_func` will not be mocked in the testing module `tm`
        result = rp.c(*rp.args)
        assert not isinstance(tm.my_func, Mock)
    ```
    """
    # region exclusions
    _exclude_identifier_set: Set[IdentifierName] = set()
    _exclude_path_set: Set[IdentifierPath] = set()
    _exclude_first_path_identifier_set: Set[IdentifierName] = set()
    _exclude_object_set: Set[Callable] = set()
    _exclude_object_path_set: Set[IdentifierPath] = set()
    _exclude_first_object_path_identifier_set: Set[IdentifierName] = set()
    # endregion exclusions

    def __init__(
        self,
        func: Callable,
        include_set: Optional[Set[Union[IdentifierName, IdentifierPath, str]]] = None,
        exclude_set: Optional[Set[Union[IdentifierName, IdentifierPath, Callable, str]]] = None
    ):
        """

        :param func: the method or the function around which will created all mocked scope (testing function or method)
        :param include_set: set of identifiers (variables) names, which need to be mocked, like: {'type'}
        :param exclude_set: set of identifiers (variables) names, which will excluding from mocking, like: {'my_func'}
          or set of object, which need to be excluded from mocking, like: {tm.FirstClass.__init__}
          or set of python paths, like {'FirstClass.__init__'}

        Note: exclude_set has more priority than include_set.
        """
        self._func: Callable = func
        """ testing function or method """
        self._patchers: List[ContextManager] = []
        """ Applied patchers in __enter__, to exit in __exit__ """

        if include_set:
            self._include_set: Set[IdentifierName] = self._include_set | include_set
            """
            set of identifiers (variables) names, which need to be mocked, like: {'type'}
            """

        if exclude_set:
            self._exclude_set: Set[Union[IdentifierName, Callable]] = self._exclude_set | exclude_set
            """
            set of identifiers (variables) names, which will excluding from mocking, like: {'my_func'}
            """
            self._init_exclusions()

    def _init_exclusions(self) -> None:
        exclude_path_set: Set[IdentifierPath] = {
            exclude_path for exclude_path in self._exclude_set
            if isinstance(exclude_path, str) and '.' in exclude_path
        }
        exclude_first_path_identifier_set: Set[IdentifierName] = {
            exclude_path.split('.')[0] for exclude_path in self._exclude_set
            if isinstance(exclude_path, str) and '.' in exclude_path
        }
        exclude_identifier_set: Set[IdentifierName] = {
            exclude_identifier for exclude_identifier in self._exclude_set
            if isinstance(exclude_identifier, str) and '.' not in exclude_identifier
        }
        exclude_object_set: Set[Callable] = {
            exclude_object for exclude_object in self._exclude_set
            if not isinstance(exclude_object, str)
        }
        self._exclude_path_set: Set[Union[IdentifierName, Callable]] = self._exclude_path_set | exclude_path_set
        self._exclude_identifier_set = self._exclude_identifier_set | exclude_identifier_set
        self._exclude_object_set = self._exclude_object_set | exclude_object_set
        self._exclude_object_path_set = {
            self._get_exclude_object_path(exclude_object=exclude_object)
            for exclude_object in self._exclude_object_set
        }
        self._exclude_first_path_identifier_set = (
            self._exclude_first_path_identifier_set | exclude_first_path_identifier_set
        )
        exclude_first_object_path_identifier_set = {
            exclude_object_path.split('.')[0] for exclude_object_path in self._exclude_object_path_set
        }
        self._exclude_first_object_path_identifier_set = (
            self._exclude_first_object_path_identifier_set | exclude_first_object_path_identifier_set
        )

    def _get_testing_module(self) -> ModuleType:
        """Returns the module of the testing function or method"""
        module_path: str = getattr(self._func, '__module__')
        testing_module: ModuleType = sys.modules[module_path]
        return testing_module

    def __enter__(self) -> ReversePatchDTO:
        testing_module: ModuleType = self._get_testing_module()
        fake_parent_module = FakeModule(tm=testing_module)

        patcher = patch.object(fake_parent_module, 'tm', autospec=True)
        self._patchers.append(patcher)
        mocked_module = patcher.__enter__()
        patching_list: List[MagicMock] = self.get_patching_list(test_method=self._func, mock_module=mocked_module)

        args_kwargs_dto: CallableDTO = self._get_args_and_callable(func=self._func, patching_list=patching_list)
        args: ArgsKwargs = args_kwargs_dto.args
        c: Callable = args_kwargs_dto.c

        self._patch_module_identifiers(
            testing_module=testing_module, mocked_module=mocked_module, patching_list=patching_list
        )
        self._patch_include_set(testing_module=testing_module)

        exclusions: Dict[Union[Callable, IdentifierPath], CallableDTO] = {}
        all_exclude_set = self._exclude_path_set | self._exclude_object_path_set

        for exclude_path in all_exclude_set:
            exclude_path: IdentifierPath
            exclude_object: Callable = self._getattr_by_path(obj=testing_module, path=exclude_path)

            # region experiment
            # exclude_module_path: Optional[str] = getattr(exclude_object, '__module__', None)
            # if not exclude_module_path:
            #     raise ValueError(f'exclude_object does not have attribute `__module__`: {exclude_object}')
            # endregion experiment

            exclude_identifiers = exclude_path.split('.')
            if len(exclude_identifiers) < 2:
                raise ValueError(f'len(exclude_identifiers)<2')

            if len(patching_list):  # and patching_list[0] == getattr(mocked_module, exclude_identifiers[0]):
                parent_object: MagicMock = mocked_module
                for idx, exclude_identifier in enumerate(exclude_identifiers):
                    idx: int
                    exclude_identifier: IdentifierName
                    current_object = getattr(parent_object, exclude_identifier)

                    if len(patching_list) > idx and patching_list[idx] == current_object:
                        pass
                    else:
                        if idx < (len(exclude_identifiers) - 1):
                            patcher = patch.object(parent_object, exclude_identifier, current_object)
                        else:
                            if exclude_identifier == '__init__':
                                # it is not possible to set `__init__` attribute in MagicMock instance
                                # in case of `__init__` use `m__init__` instead
                                patcher = patch.object(
                                    parent_object, f'm{exclude_identifier}', exclude_object, create=True
                                )
                                exclusion_dto: CallableDTO = self._get_args_and_callable(
                                    func=exclude_object,
                                    patching_list=[parent_object],
                                )
                                exclusions[exclude_object] = exclusion_dto
                                exclusions[exclude_path] = exclusion_dto
                            else:
                                patcher = patch.object(parent_object, exclude_identifier, exclude_object)

                        patcher.__enter__()
                        self._patchers.append(patcher)

                    parent_object = current_object

        return ReversePatchDTO(args=args, c=c, exclusions=exclusions)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in reversed(self._patchers):
            patcher.__exit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def _getattr_by_path(obj: Any, path: IdentifierPath) -> Callable:
        """
        example:

        ```py
        class X:
            class Y:
                t = 4

        print(getattr_by_path(X, 'Y.t'))  # prints 4
        ```
        """
        obj_ = obj

        for path_item in path.split('.'):
            obj_ = getattr(obj_, path_item)

        return obj_

    @staticmethod
    def _get_exclude_object_path(exclude_object: Callable) -> IdentifierPath:
        exclude_object_path: Optional[IdentifierPath] = getattr(exclude_object, '__qualname__', None)
        if not exclude_object_path:
            raise ValueError(f'exclude_object does not have attribute `__qualname__: {exclude_object}')

        return exclude_object_path

    @classmethod
    def _get_args_and_callable(cls, func: Callable, patching_list: List[MagicMock]) -> CallableDTO:
        args = ArgsKwargs()
        params = inspect.signature(func).parameters
        c: Callable = func

        if cls.is_class_method(class_method=func):
            c: Callable = getattr(func, '__func__')

            if len(patching_list):
                args.add_argument(argument_name=ArgumentName('cls'), argument_value=patching_list[-1])

            for param_name in params.keys():
                param_name: str
                args.add_argument(argument_name=ArgumentName(param_name), argument_value=MagicMock())
        else:
            for param_name in params.keys():
                param_name: str
                if len(patching_list):
                    if param_name == 'self':
                        args.add_argument(argument_name=ArgumentName(param_name), argument_value=patching_list[-1])
                    else:
                        args.add_argument(argument_name=ArgumentName(param_name), argument_value=MagicMock())
                else:
                    args.add_argument(argument_name=ArgumentName(param_name), argument_value=MagicMock())

        return CallableDTO(args=args, c=c)

    def _patch_module_identifiers(
        self,
        testing_module: ModuleType,
        mocked_module: MagicMock,
        patching_list: List[MagicMock]
    ):
        """ Move mocks from mocked_module to testing_module """
        for identifier, identifier_value in testing_module.__dict__.copy().items():
            identifier: IdentifierName  # The name of the attribute (variable) in the testing module
            all_exclude: Set[IdentifierName] = (
                self._exclude_identifier_set
                | self._exclude_first_path_identifier_set
                | self._exclude_first_object_path_identifier_set
            )

            if identifier in all_exclude:
                continue

            if (
                identifier.startswith('__')  # skip magics,
                and identifier not in self._include_set  # if identifier is set to be mocked explicitly
            ):
                continue

            if identifier_value is self._func:
                continue

            if isinstance(identifier_value, Mock):
                continue  # do not mock that has already mocked

            if inspect.isclass(identifier_value) and issubclass(identifier_value, Exception):
                continue  # skip exception classes

            if len(patching_list) and identifier == getattr(patching_list[0], '_mock_name'):
                continue  #

            identifier_patcher: ContextManager = patch.object(
                testing_module, identifier, getattr(mocked_module, identifier)
            )
            identifier_patcher.__enter__()
            self._patchers.append(identifier_patcher)

    def _patch_include_set(self, testing_module: ModuleType) -> None:
        """ patches identifiers in defined in include set """
        exclude_set = self._exclude_identifier_set | self._exclude_path_set | self._exclude_object_path_set
        exclude_set: Set[Union[IdentifierName, IdentifierPath]]
        include_set = self._include_set - exclude_set  # exclude_set has more priority than include_set
        include_set: Set[Union[IdentifierName, IdentifierPath]]

        for identifier_path in include_set:
            identifier_path: Union[IdentifierName, IdentifierPath]

            parent = testing_module

            for identifier in identifier_path.split('.')[:-1]:
                identifier: IdentifierName

                parent = getattr(parent, identifier)

            if isinstance(getattr(parent, identifier_path.split('.')[-1], None), Mock):
                continue  # python 3.10 does not not support autospec on that already mocked

            patcher = patch.object(parent, identifier_path.split('.')[-1], create=True)
            patcher.__enter__()
            self._patchers.append(patcher)

    @classmethod
    def is_class_method(cls, class_method: Callable) -> bool:
        """ True if method is classmethod, otherwise False """
        is_class_method: bool = inspect.ismethod(class_method)
        return is_class_method

    @classmethod
    def get_patching_list(cls, test_method: Callable, mock_module: MagicMock) -> List[MagicMock]:
        """
        MagicMock-и от [testing_module, [class1, [class2, [...]]]]

        example:

        ```py
        # module
        class FirstClass:
            class SecondClass:
                def testing_method(self, x):
                    pass

        # patching_list for testing method will be:
        [
          MagickMock for testing_module,
          MagickMock for FirstClass,
          MagickMock for SecondClass
        ]
        ```
        """
        qualified_name: str = test_method.__qualname__

        patching_list: List = []
        names: List[str] = qualified_name.split('.')[:-1]
        current_object = mock_module

        for name in names:
            name: str
            current_object = getattr(current_object, name)
            patching_list.append(current_object)

        return patching_list


class Rp(ReversePatch):
    """ shortcut for ReversePatch. """
    pass


@dataclasses.dataclass
class ResultReversePatchDTO(ReversePatchDTO):
    """ReversePatchDTO with result of `rp.c(*rp.args)`"""
    r: Any
    """result of `rp.c(*rp.args)`"""

    def __iter__(self):
        """
        with Rc(f) as r, rp, c, args, s:
            assert rp.c == c
            assert rp.args == args
            assert rp.args.self == s  # or assert rp.args.cls == s
        """
        yield self.r
        yield from super().__iter__()


class Rc(Rp):
    """
    `Rc` automatically perform `r = rp.c(*rp.args)`.
    Its `__enter__` returns `ResultReversePatchDTO` which `r` attribute contains the result of `rp.c(*rp.args)`.
    Thus `Rc` is more short version of `ReversePath`.
    """
    def __enter__(self) -> ResultReversePatchDTO:
        rp: ReversePatchDTO = super().__enter__()

        try:
            result = rp.c(*rp.args)
        except Exception:
            self.__exit__(None, None, None)
            raise
        else:
            rc = ResultReversePatchDTO(r=result, args=rp.args, c=rp.c, exclusions=rp.exclusions)
            return rc


class Rcl(Rp):
    """
    `Rcl` extends `ReversePath` for testing code, that including logging.
    `Rcl` work like `Rc`, it perform `r = rp.c(*rp.args)` automatically.
    It is very easy to make a mistake in message template and other arguments, like `logger.debug("%s %s", arg1)`.
    This code will produce `TypeError: not enough arguments for format string`. We need to patch `debug` method.

    Long example, without Rcl
    ```py
    def test_do_log_debug_success(self):
        with ReversePatch(tm.do_log_debug_success, exclude_set={'logging', 'logger'}) as rp:
            with PatchLogger(tm.logger):
                assert rp.c(*rp.args) is None
    ```

    Sort example.
    ```py
    ```
    """
    _patch_logger_manager: Optional[PatchLogger] = None

    def __init__(
        self,
        func: Callable,
        include_set: Optional[Set[Union[IdentifierName, IdentifierPath, str]]] = None,
        exclude_set: Optional[Set[Union[IdentifierName, IdentifierPath, Callable, str]]] = None
    ):
        exclude_set_: Optional[Set[Union[IdentifierName, IdentifierPath, Callable, str]]] = {
            IdentifierName('logging'),
            IdentifierName('logger'),
        }

        if exclude_set is not None:
            exclude_set_ = exclude_set_ | exclude_set

        super().__init__(func=func, include_set=include_set, exclude_set=exclude_set_)

    def __enter__(self) -> ResultReversePatchDTO:
        rp: ReversePatchDTO = super().__enter__()
        testing_module: ModuleType = self._get_testing_module()
        logger_: logging.Logger = getattr(testing_module, 'logger')
        self._patch_logger_manager = PatchLogger(logger=logger_).__enter__()

        try:
            result = rp.c(*rp.args)
        except Exception:
            self.__exit__(None, None, None)
            raise
        else:
            rc = ResultReversePatchDTO(r=result, args=rp.args, c=rp.c, exclusions=rp.exclusions)
            return rc

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._patch_logger_manager is not None:
            self._patch_logger_manager.__exit__(None, None, None)
        super().__exit__(exc_type, exc_val, exc_tb)
