#!/usr/bin/bash

set -ex

export PATH=$PATH:/sbin:/usr/sbin
export TMPDIR=/var/tmp/

./autogen.sh
./configure

make clean rootfs.ks

make image-build rootfs-manifest-rpm
