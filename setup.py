#!/usr/bin/env python

from distutils.core import setup

setup(
    name="jupro",
    version="0.14",
    description="Process jupyter cells into latex snippets",
    author="Wouter van Atteveldt",
    author_email="wouter@vanatteveldt.com",
    packages=["jupro"],
    url='https://github.com/vanatteveldt/jupro',
    keywords = ["latex", "jupyter"],
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=[
        "lxml",
        "cssselect",
    ]
)
