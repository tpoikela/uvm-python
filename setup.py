from os import path
from setuptools import setup


def read_file(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


setup(
    name="uvm-python",
    url="https://github.com/tpoikela/uvm-python",
    author="Tuomas Poikela",
    author_email="tuomas.sakari.poikela@gmail.com",
    description=("uvm-python UVM implementation in Python on top of cocotb"),
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    keywords=["UVM", "SystemVerilog", "Verilog", "RTL", "Coverage"],
    packages=["uvm"],
    package_dir={"": "src"},
    setup_requires=["setuptools_scm",],
    python_requires=">=3.5",
    install_requires=["cocotb>=1.2.0", "cocotb-coverage>=1.0.0", "regex>=2019.11.1"],
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
