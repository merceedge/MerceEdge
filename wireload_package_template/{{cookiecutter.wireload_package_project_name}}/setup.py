from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from codecs import open
import os
from os import path, walk
import glob
import yaml
from shutil import copyfile

import {{cookiecutter.wireload_package_project_name}}

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


def make_config_yml_backup_file(config_yml_path):
    copyfile(config_yml_path, config_yml_path + '.bak')

def revert_config_yml_backup(config_yml_path):
    copyfile(config_yml_path + '.bak', config_yml_path)

"""
config_install
step 1
0. Check MERCE_EDGE_HOME and config.yml first
1. Read MERCE_EDGE_HOME env and get config.yml file object.
2. Add this wireload package default key-value in MerceEdge config.yml at home path
    wireload_package_template.__config__
---
 step 2 
1. Get this package templates path, add all complate template yml files
 at MerceEdge home config.yml.
--
step 3
1. Install this packate formulas.
2. Add formula load path in this package at MerceEdge home config.yml.
--
step 4
1. Install all wireload class python file.
2. Add wireload load path in this package at MerceEdge home config.yml.

"""
def config_install(is_develop=False):
    from merceedge.exceptions import MerceEdgeError
    from merceedge.util import prefix
    from merceedge.util.yaml import (
        load_yaml,
        write_yaml
    )
    # step 1
    try:
        merce_edge_home = os.path.dirname(os.environ['MERCE_EDGE_HOME'])
    except KeyError:
        error = "MERCE_EDGE_HOME enviorment not fount!" 
        raise MerceEdgeError(error)
    config_yml_path = os.path.join(merce_edge_home, 'config.yml')
    
    make_config_yml_backup_file(config_yml_path)

    try:
        
        config_yml = load_yaml(config_yml_path)
        config_yml.update({{cookiecutter.wireload_package_project_name}}.__config__)
        
        # step 2: templates path config
        wireload_package_install_path = prefix.binaries_directory(is_develop)
        template_path = os.path.join(wireload_package_install_path, 'templates')
        config_yml['component_template']['paths'].append(template_path)

        # step 3: formula path config
        formula_path = os.path.join(wireload_package_install_path, 'formulas')
        config_yml['formula']['paths'].append(formula_path)

        # step 4: wireload path config
        config_yml['wireload']['paths'].append(wireload_package_install_path)

        # write back config.yml
        write_yaml(config_yml_path, config_yml)

    except MerceEdgeError, KeyError:
        revert_config_yml_backup(config_yml_path)


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        develop.run(self)
        config_install(is_develop=True)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        install.run(self)
        config_install(is_develop=False)


setup(
    name='wireload_package_template',
    version={{cookiecutter.wireload_package_project_name}}.__version__,
    description=long_description,
    author={{cookiecutter.wireload_package_project_name}}.__author__,
    author_email={{cookiecutter.wireload_package_project_name}}.__contact__,
    url={{cookiecutter.wireload_package_project_name}}.__homepage__,
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    include_package_data=True,
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    }
    # entry_points={
    #     'console_scripts': [
    #         'edge=merceedge.__main__:main'
    #     ]
    # }
)






