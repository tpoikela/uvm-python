#! /bin/bash

git clone https://github.com/steveicarus/iverilog.git
cd iverilog
git pull
git checkout v11_0
sh autoconf.sh
./configure
make
make install
