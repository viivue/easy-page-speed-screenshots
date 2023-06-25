from io import open
from setuptools import setup
from easy_page_speed_screenshots import __version__ as version

setup(
    name='easy-page-speed-screenshots',
    version=version,
    url='https://github.com/viivue/easy-page-speed-screenshots',
    license='MIT',
    author='ViiVue',
    author_email='developers@viivue.com',
    description='📑 Python tool to bulk save page speed screenshots',
    long_description=''.join(open('README.md', encoding='utf-8').readlines()),
    long_description_content_type='text/markdown',
    keywords=['gui', 'executable'],
    packages=['easy_page_speed_screenshots'],
    include_package_data=True,
)
