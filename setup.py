
import os
from setuptools import setup

setup(
  name = "uvm-python",
  packages=['uvm'],
  package_dir = {'' : 'src'},
  author = "Tuomas Poikela",
  author_email = "tuomas.sakari.poikela@gmail.com",
  description = ("uvm-python UVM implementation in Python on top of cocotb"),
  license = "Apache 2.0",
  keywords = ["SystemVerilog", "Verilog", "RTL", "Coverage"],
  url = "https://github.com/tpoikela/uvm-python",
  setup_requires=[
    'setuptools_scm',
  ],
  install_requires=[
    "cocotb>=1.2.0",
    "cocotb-coverage>=1.0.0",
    "regex>=2019.11.1"
  ],
)

