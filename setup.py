import os
from setuptools import setup, find_packages

# Read the content of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

version = os.getenv('PACKAGE_VERSION', '1.0.0')

setup(
    name='graphlit-tools',
    version=version,
    packages=find_packages(),
    install_requires=[
        'graphlit-client',
        'langchain-core'
    ],
    python_requires='>=3.6',
    author='Unstruk Data Inc.',
    author_email='questions@graphlit.com',
    description='Graphlit Agent Tools',
    url='https://github.com/graphlit/graphlit-tools/',
    long_description=long_description,
    long_description_content_type="text/markdown",
)
