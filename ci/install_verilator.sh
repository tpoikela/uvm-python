#! /bin/bash

git clone https://github.com/grg/verilator.git
cd verilator
git pull
git checkout v4.106
autoconf
./configure
make
make install
