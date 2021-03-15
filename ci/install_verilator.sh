#! /bin/bash

git clone https://github.com/verilator/verilator.git
cd verilator
git pull
git checkout v4.106
autoconf
./configure
make
make install
