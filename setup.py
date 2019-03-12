from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from codecs import open
import os
from os import path, walk
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

# packages = find_packages()
# print("*"*40)
# print(packages)
def setup_home_env(is_develop=False):
    from merceedge.util import prefix
    os.environ['MERCE_EDGE_HOME'] = prefix.binaries_directory(is_develop)
    print("MERCE_EDGE_HOME: ", os.environ.get('MERCE_EDGE_HOME'))

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        develop.run(self)
        setup_home_env(is_develop=True)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        install.run(self)
        setup_home_env(is_develop=False)

setup(
    name='merceedge',
    version=merceedge.__version__,
    description=long_description,
    author=merceedge.__author__,
    author_email=merceedge.__contact__,
    url=merceedge.__homepage__,
    packages=find_packages(),
    install_requires=install_requires,
    package_data={
        '': [
            '*.yaml', 
            '*.yml',
            'schema/*'
        ], 
        'merceedge.tests': [ 
            '*',
            'demo/*' 
            'formula/*',
            'swagger_ref/*',
            'wireload/*',
            'component_template/*'
        ]
    },    
    include_package_data=True,
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'edge=merceedge.__main__:main'
        ]
    }
)






