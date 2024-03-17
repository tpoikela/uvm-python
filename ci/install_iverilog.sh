#! /bin/bash

git clone https://github.com/steveicarus/iverilog.git
cd iverilog
git pull
git checkout 52d049b5
sh autoconf.sh
./configure
make -j `nproc`
make install
