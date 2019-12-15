#! /bin/bash

git clone https://github.com/steveicarus/iverilog.git
cd iverilog
git pull
sh autoconf.sh
./configure
make
make install
