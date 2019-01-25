from setuptools import setup, find_packages
from codecs import open
# import os
from os import path, walk
import glob
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

# data_files = []
# directories = glob.glob('merceedge/tests/')
# print(directories)
# for directory in directories:
#     files = glob.glob(directory+'*')
#     data_files.append((directory, files))

# print('*'*40)
# print(data_files)

# def package_files(directory):
#     paths = []
#     print('='*30)
#     for (filepath, directories, filenames) in walk(directory):
#         for filename in filenames:
#             # p = '/'.join(filepath.split('/')[2:])
#             paths.append(path.join(filepath, filename))
#     print('='*30)
#     print(paths)
#     return paths

# extra_files = package_files('merceedge/tests')

setup(
    name='merceedge',
    version=merceedge.__version__,
    description=long_description,
    author=merceedge.__author__,
    author_email=merceedge.__contact__,
    url=merceedge.__homepage__,
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    package_data={'': ['config.yaml']},    
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'edge=merceedge.__main__:main'
        ]
    }
)






