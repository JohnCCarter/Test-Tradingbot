#!/usr/bin/env python

from setuptools import setup, find_packages
import os

# Read the README.md file for the long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="dsd-backend",
    version="1.0.0",
    description="Backend för DSD-projektet, en tradingbot byggd med Python och Flask.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="John Carter",
    license="MIT",
    python_requires=">=3.9",
    packages=["backend", "backend.src", "backend.src.modules"],
    include_package_data=True,
    install_requires=[
        "Flask",
        "ccxt",
        "pandas",
        "numpy",
        "TA-Lib",
        "Pydantic",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "dsd-dashboard=backend.src.dashboard:start_dashboard",
        ],
    },
)