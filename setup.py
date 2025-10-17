"""
Setup script for Discord Guild Manager
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="discord-guild-manager",
    version="1.0.0",
    author="maxxunit1",
    author_email="",
    description="Simple and powerful tool for managing Discord guilds across multiple accounts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maxxunit1/discord-guild-manager",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat :: Discord",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "discord-guild-manager=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/maxxunit1/discord-guild-manager/issues",
        "Source": "https://github.com/maxxunit1/discord-guild-manager",
    },
)