# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chitubox",
    version="0.1.5",
    author="Jason S. McMullan",
    author_email="jason.mcmullan@gmail.com",
    description="Utility to manage networked ChiTuBox based LCD Resin printers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ezrec/python-chitubox",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    zip_safe=True,
    include_package_data=False,
    entry_points={
        "console_scripts": [
            "chitucli=chitubox.__main__:cli"
        ],
    }
)
