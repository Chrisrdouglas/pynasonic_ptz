"""Setup configuration for pynasonic_ptz package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pynasonic-ptz",
    version="0.0.1",
    author="Chris Douglas",
    author_email="c@chrisrdouglas.com",
    description="Python library for controlling Panasonic PTZ cameras",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Chrisrdouglas/pynasonic_ptz",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "urllib3>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="panasonic ptz camera control automation video",
    project_urls={
        "Bug Reports": "https://github.com/Chrisrdouglas/pynasonic_ptz/issues",
        "Source": "https://github.com/Chrisrdouglas/pynasonic_ptz",
        "Documentation": "https://github.com/Chrisrdouglas/pynasonic_ptz/blob/main/README.md",
    },
)