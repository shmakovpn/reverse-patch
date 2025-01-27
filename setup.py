from setuptools import setup, find_packages
import os

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='reverse-patch',
    version='1.0.0',
    packages=find_packages(),
    author='shmakovpn',
    author_email='shmakovpn@yandex.ru',
    url='https://github.com/shmakovpn/reverse-patch',
    download_url=
    f'https://https://github.com/shmakovpn/reverse-patch/archive/1.0.0.zip',
    desctiption='ReversePatch test unittest utility',
    entry_points={
        'console_scripts': [],
    },
    install_requires=[],
    include_package_data=True,
)