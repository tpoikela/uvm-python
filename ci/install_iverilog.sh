#! /bin/bash

git clone https://github.com/steveicarus/iverilog.git
cd iverilog
git pull
#git checkout v11_0
git checkout 01441687
sh autoconf.sh
./configure
make -j `nproc`
make install
