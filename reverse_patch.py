from typing import Callable, List, ContextManager, Set, Optional, Dict, NewType
from types import ModuleType
from dataclasses import dataclass
import sys
import inspect
from unittest.mock import Mock, patch, MagicMock

__all__ = (
    'ArgumentName',
    'ArgumentIndex',
    'ArgsKwargs',
    'ReversePatchDTO',
    'ReversePatch',
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
        return super().__getitem__(self._index_map[item])

    def add_argument(self, argument_name: ArgumentName, argument_value: MagicMock) -> None:
        """Adds argument and its value to this list"""
        self._index_map[argument_name] = ArgumentIndex(len(self._index_map))
        super().append(argument_value)


@dataclass
class ReversePatchDTO:
    """
    Patching result. Mock arguments and callable to call.
    """

    args: ArgsKwargs
    """
    The list of argument, 
    including `self` for methods (args[0] or args.self) and `cls` for class-methods (args[0] or args.cls)
    """
    c: Callable
    """callable, you have to call in your unit-test like: `rp_dto.c(*rp_dto.args)`"""


class ReversePatch:
    """
    Reverse patch context manager. Creates mock scope, mock argument list and give your callable to call
    in your unit-test, extracted from testing method or function

    example:

    ```py
    # pytests/pytest__my_module.py

    import my_module as tm  # testing module
    from reverse_patch import ReversePatch

    with ReversePatch(tm.my_func) as rp_dto:
        # all scope around of tm.my_func will me mocked
        # rp_dto.c - callable you need to use in your unit-tests
        # rp_ato.args - mocked argument list you need to use in your unit-tests
        result = rp_dto.c(*rp_dto.args)  # call testing method or function
        # your asserts
    ```
    """

    _include_set: Set[IdentifierName] = {'id'}
    """
    Identifiers (variables) names which have to be mocked
    
    example:
    
    ```py
    with ReversePatch(tm.my_func, include_set={'type'}) as rp_dto:
        # `tm.type` will be a MagicMock in the testing module `tm`
        result = rp_dto.c(*rp_dto.args)
        assert tm.type.assert_called()  # do asserts with mocked `type`
        tm.something.assert_called_once_with(type_=tm.type.return_value)  # using mocked `type` return value
    ```
    """
    _exclude_set: Set[IdentifierName] = set()
    """
    Identifiers (variables) names which have to be excluded from mocking
    
    example:
    
    ```py
    with ReversePatch(tm.MyClass.my_method, exclude_set={'my_func'}):
        # `tm.my_func` will not be mocked in the testing module `tm`
        result = rp_dto.c(*rp_dto.args)
        assert not isinstance(tm.my_func, Mock)
    ```
    """

    def __init__(self, func: Callable, include_set: Optional[Set[str]] = None, exclude_set: Optional[Set[str]] = None):
        """

        :param func: the method or the function around which will created all mocked scope (testing function or method)
        :param include_set: set of identifiers (variables) names, which need to be mocked, like: {'type'}
        :param exclude_set: set of identifiers (variables) names, which will excluding from mocking, like: {'my_func'}
        """
        self._func: Callable = func
        """ testing function or method """
        self._patchers: List[ContextManager] = []
        """ Applied patchers in __enter__, to exit in __exit__ """

        if include_set:
            self._include_set = self._include_set | include_set
            """
            set of identifiers (variables) names, which need to be mocked, like: {'type'}
            """

        if exclude_set:
            self._exclude_set = self._exclude_set | exclude_set
            """
            set of identifiers (variables) names, which will excluding from mocking, like: {'my_func'}
            """

    def __enter__(self) -> ReversePatchDTO:
        module_path: str = getattr(self._func, '__module__')
        testing_module: ModuleType = sys.modules[module_path]
        fake_parent_module = Mock(tm=testing_module)
        c: Callable = self._func

        params = inspect.signature(self._func).parameters

        patcher = patch.object(fake_parent_module, 'tm', autospec=True)
        self._patchers.append(patcher)
        mocked_module = patcher.__enter__()
        patching_list: List[MagicMock] = self.get_patching_list(test_method=self._func, mock_module=mocked_module)

        args = ArgsKwargs()

        if self.is_class_method(class_method=self._func):
            c: Callable = getattr(self._func, '__func__')

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

        self._patch_module_identifiers(
            testing_module=testing_module, mocked_module=mocked_module, patching_list=patching_list
        )
        self._patch_include_set(testing_module=testing_module)

        return ReversePatchDTO(args=args, c=c)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in self._patchers:
            patcher.__exit__(exc_type, exc_val, exc_tb)

    def _patch_module_identifiers(
        self,
        testing_module: ModuleType,
        mocked_module: MagicMock,
        patching_list: List[MagicMock]
    ):
        """ Move mocks from mocked_module to testing_module """
        for identifier, identifier_value in testing_module.__dict__.copy().items():
            identifier: IdentifierName  # The name of the attribute (variable) in the testing module

            if identifier in self._exclude_set:
                continue

            if (
                identifier.startswith('__')  # skip magics,
                and identifier not in self._include_set  # if identifier is set to be mocked explicitly
            ):
                continue

            if identifier_value is self._func:
                continue

            if len(patching_list) and identifier == getattr(patching_list[0], '_mock_name'):
                continue  #

            identifier_patcher: ContextManager = patch.object(
                testing_module, identifier, getattr(mocked_module, identifier)
            )
            identifier_patcher.__enter__()
            self._patchers.append(identifier_patcher)

    def _patch_include_set(self, testing_module: ModuleType) -> None:
        """ patches identifiers in defined in include set """
        for identifier in (self._include_set - self._exclude_set):
            identifier: IdentifierName

            patcher = patch.object(testing_module, identifier, create=True)
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
