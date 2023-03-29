#! /bin/bash

# VERILATOR_ROOT="$PWD/verilator"

# Clone repo only if it doesn't exist
if [ ! -d "verilator" ]; then
    git clone https://github.com/verilator/verilator.git
fi

cd verilator

# Returns non-zero if no .o files exist
find -name '*.o' | grep -q .

# If .o files don't exist, do autoconf and do make
if [ $? -ne 0 ]; then
    git checkout v5.008
    echo "autoconf"
    autoconf
    echo "configure"
    ./configure --prefix="$VERILATOR_ROOT"
    echo "make"
    make -d -j `nproc`
    echo "make install"
    #make -d install
else
    echo "Verilator already built, skipping compile/install steps"
    # make -d install
fi
