#!/usr/bin/env python3
"""
Setup script for Smart Media Icon System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="smart-media-icon",
    version="1.0.0",
    author="Smart Media Icon Team",
    author_email="smart@mediaicon.dev",
    description="Professional Windows desktop utility for automatic media icon management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smart-media-icon",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
        "Topic :: Multimedia :: Graphics",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "smart-media-icon=smart_media_icon.cli:main",
            "smi=smart_media_icon.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "smart_media_icon": [
            "*.json",
            "*.ini",
        ],
    },
    zip_safe=False,
    keywords="media icons windows desktop ffmpeg posters",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/smart-media-icon/issues",
        "Source": "https://github.com/yourusername/smart-media-icon",
        "Documentation": "https://github.com/yourusername/smart-media-icon/wiki",
    },
)
