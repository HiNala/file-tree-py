"""Setup configuration for the file tree analyzer."""
from setuptools import setup, find_packages

setup(
    name="file-tree-py",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "rich>=10.0.0",
        "python-dotenv>=1.0.0",
        "openai>=1.3.0"
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "filetree=filetree.cli:main",
        ],
    },
    author="Nala",
    description="A tool for analyzing directory structures and managing duplicates",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="file, directory, duplicate, analysis",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 