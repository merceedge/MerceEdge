from setuptools import setup, find_packages
from codecs import open
from os import path

import merceedge

here = path.abspath(path.dirname(__file__))


"""
##### How #####
For Dev:
python setup.py develop

For Prod:
python setup.py install
"""

def is_pkg(line):
    return line and not line.startswith(('--', 'git', '#'))


with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


with open('requirements.txt', encoding='utf-8') as reqs:
    install_requires = [l for l in reqs.read().split('\n') if is_pkg(l)]


setup(
    name='merceedge',
    version=merceedge.__version__,
    description=long_description,
    author=merceedge.__author__,
    author_email=merceedge.__contact__,
    url=merceedge.__homepage__,
    packages=find_packages(
        exclude=['tests']
    ),
    install_requires=install_requires,
    include_package_data=True,
    # entry_points={
    #     'console_scripts': [
    #         'log_gw=log_gateway.bin:main'
    #     ]
    # }
)






