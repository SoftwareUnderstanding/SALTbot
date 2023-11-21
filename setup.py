# -*- coding: utf-8 -*-

import os

from setuptools import find_packages, setup

install_requires = [
    "bs4==0.0.1",
    "markdown==3.3.6",
    "numpy==1.22.0",
    "pandas==1.3.4",
    "textblob==0.17.1",
    "xgboost==1.5.0",
    "inflect>=5.4.0",
    "contractions>=0.1.66",
    "chardet==5.0.0",
    "imbalanced-learn>=0.8.1",
    "pytest",
    "bibtexparser==1.4.0",
    "click==8.1.3",
    "click_option_group==0.5.3",
    "numpy==1.22.0",
    "PyYAML==6.0",
    "wikibaseintegrator==0.12.3",
    "setuptools>=42",
    "wheel"
]


# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8').read()


def find_package_data(dirname):
    def find_paths(dirname):
        items = []
        for fname in os.listdir(dirname):
            path = os.path.join(dirname, fname)
            if os.path.isdir(path):
                items += find_paths(path)
            elif not path.endswith(".py") and not path.endswith(".pyc"):
                items.append(path)
        return items

    items = find_paths(dirname)
    return [os.path.relpath(path, dirname) for path in items]


version = {}
with open("src/SALTbot/__init__.py") as fp:
    exec(fp.read(), version)

setup(
    name="SALTbot",
    version="0.0.1",
    author="Jorge Bolinches",
    author_email="j.bolinches2000@gmail.com",
    description="SALTbot: the Software and Article Linker Toolbot",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/KnowledgeCaptureAndDiscovery/somef",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Science/Research",
        "Operating System :: Unix",
    ],
    entry_points={"console_scripts": ["SALTbot = SALTbot.__main__:cli"]},
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"SALTbot": find_package_data("src/SALTbot")},
    exclude_package_data={"somef": ["test/*"]},
    zip_safe=False,
    install_requires=install_requires,
    python_requires=">=3.9",
)