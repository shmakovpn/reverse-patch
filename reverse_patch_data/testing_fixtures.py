"""
# testing fixtures for pytest__reverse_patch
"""
MODULE_CONST = '_module_const'


def failed_function(x):
    raise RuntimeError(f'failed_one: {x}')


def success_function(x):
    failed_function(x)


def fail__failed_function():
    success_function()  # noqa, try to call a function with wrong signature, will raise TypeError


def fail_no_function1():
    no_function1()  # noqa, try to call a function that does not exist, will raise NameError


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

    @staticmethod
    def success_static_method__include():
        type_ = type('hello')
        return type_

    @staticmethod
    def success_static_method__exclude():
        id_ = id('4')
        return id_

    @classmethod
    def success_class_method(cls, class_method_argument):
        id_ = id(class_method_argument)
        cls.failed_class_method(1, 2)
        cls.failed_static_method(1, 2)
        return failed_function(id_)

    @staticmethod
    def success_static_method(static_method_argument):
        id_ = id(static_method_argument)
        return failed_function(id_)

    def fail_method__failed_function(self):
        # calls `failed_function` with wrong signature, will raise TypeError
        failed_function(self.first_class_const, 'a')  # noqa

    def fail_method__failed_method(self):
        # calls `failed_method` with wrong signature, will raise TypeError
        self.failed_method()  # noqa

    def fail_method__failed_class_method(self):
        # calls `failed_class_method` with wrong signature, will raise TypeError
        self.failed_class_method()  # noqa

    def fail_method__failed_static_method(self):
        # calls `failed_static_method` with wrong signature, will raise TypeError
        self.failed_static_method()  # noqa

    def fail_no_method(self):
        # calls `no_method` that does not exist, will raise AttributeError
        self.no_method()  # noqa

    # noinspection PyMethodMayBeStatic
    def fail_no_function(self):
        # calls global `no_function` that does not exist, will raise NameError
        no_function()  # noqa

    @classmethod
    def fail_class_method__failed_function(cls):
        # calls global `failed_function` with wrong signature, will raise TypeError
        failed_function(cls.first_class_const, 'a')  # noqa

    @classmethod
    def fail_class_method__failed_class_method(cls):
        # calls `failed_class_method` with wrong signature, will raise TypeError
        cls.failed_class_method()  # noqa

    @classmethod
    def fail_class_method__failed_static_method(cls):
        # calls `failed_static_method` with wrong signature, will raise TypeError
        cls.failed_static_method()  # noqa

    @staticmethod
    def fail_static_method__failed_functions():
        # calls `failed_function` with wrong signature, will raise TypeError
        failed_function()  # noqa

    class SecondClass:
        second_class_const = '_second_class_const'

        def second_failed_method(self, x, y):
            raise RuntimeError('_second_failed_method')

        @classmethod
        def second_failed_class_method(cls, x, y):
            raise RuntimeError('_second_failed_class_method')

        @staticmethod
        def second_failed_static_method(x, y):
            raise RuntimeError('_second_failed_static_method')

        def second_success_method(self, method_argument):
            id_ = id(method_argument)

            self.second_failed_method(1, 2)
            self.second_failed_class_method(1, 2)
            self.second_failed_static_method(1, 2)
            return failed_function(id_)

        @classmethod
        def second_success_class_method(cls, class_method_argument):
            id_ = id(class_method_argument)
            cls.second_failed_class_method(1, 2)
            cls.second_failed_static_method(1, 2)
            return failed_function(id_)

        @staticmethod
        def second_success_static_method(static_method_argument):
            id_ = id(static_method_argument)
            return failed_function(id_)

        def second_fail_method__failed_function(self):
            # calls `failed_function` with wrong signature, will raise TypeError
            failed_function(self.second_class_const, 'a')  # noqa

        def second_fail_method__failed_method(self):
            # calls `second_failed_method` with wrong signature, will raise TypeError
            self.second_failed_method()  # noqa

        def second_fail_method__failed_class_method(self):
            # calls `second_failed_class_method` with wrong signature, will raise TypeError
            self.second_failed_class_method()  # noqa

        def second_fail_method__failed_static_method(self):
            # calls `second_failed_static_method` with wrong signature, will raise TypeError
            self.second_failed_static_method()  # noqa

        @classmethod
        def second_fail_class_method__failed_function(cls):
            # calls `failed_function` with wrong signature, will raise TypeError
            failed_function(cls.second_class_const, 'a')  # noqa

        @classmethod
        def second_fail_class_method__failed_class_method(cls):
            # calls `second_failed_class_method` with wrong signature, will raise TypeError
            cls.second_failed_class_method()  # noqa

        @classmethod
        def second_fail_class_method__failed_static_method(cls):
            # calls `second_failed_static_method` with wrong signature, will raise TypeError
            cls.second_failed_static_method()  # noqa

        def second_fail_no_method(self):
            # try to call a method that does not exist, will raise AttributeError
            self.no_method()  # noqa

        # noinspection PyMethodMayBeStatic
        def second_fail_no_function(self):
            # try to call a function that does not exist, will raise NameError
            no_function()  # noqa
