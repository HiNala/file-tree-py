"""Setup configuration for the file tree analyzer."""
from setuptools import setup, find_packages

setup(
    name="filetree",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "rich>=10.0.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "filetree=filetree.cli:main",
        ],
    },
) 