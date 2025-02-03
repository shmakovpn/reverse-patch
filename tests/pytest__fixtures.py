import pytest
import reverse_patch.testing_fixtures as tm


class TestFailedFunction:
    def test_failed_function(self):
        with pytest.raises(RuntimeError):
            tm.failed_function('foo')


class TestFirstClass:
    def test_failed_method(self):
        fc = tm.FirstClass()

        with pytest.raises(RuntimeError):
            fc.failed_method('a', 'b')

    def test_failed_class_method(self):
        with pytest.raises(RuntimeError):
            tm.FirstClass.failed_class_method('c', 'd')

    def test_failed_static_method(self):
        with pytest.raises(RuntimeError):
            tm.FirstClass.failed_static_method('e', 'h')

    class TestSecondClass:
        def test_second_failed_method(self):
            cs = tm.FirstClass.SecondClass()

            with pytest.raises(RuntimeError):
                cs.second_failed_method('a', 'b')

        def test_second_failed_class_method(self):
            with pytest.raises(RuntimeError):
                tm.FirstClass.SecondClass.second_failed_class_method('c', 'd')

        def test_second_failed_static_method(self):
            with pytest.raises(RuntimeError):
                tm.FirstClass.SecondClass.second_failed_static_method('e', 'f')
