#!/usr/bin/env python3
"""Setup script for {{cookiecutter.project_name}}."""

from setuptools import setup, find_packages

setup(
    name="{{cookiecutter.project_slug}}",
    version="0.1.0",
    description="{{cookiecutter.description}}",
    author="{{cookiecutter.author_name}}",
    author_email="{{cookiecutter.author_email}}",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">={{cookiecutter.python_version}}",
    install_requires=[
        # Dependencies are managed in pyproject.toml
    ],
)