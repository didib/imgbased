# -*- coding: utf-8 -*-
#
# Persist installed packages on imgbased, via a dnf plugin
#
# Copyright © 2016 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Author: Ryan Barry <rbarry@redhat.com>
#

import logging
import os
import shutil

import dnf

from imgbased.bootsetup import BootSetupHandler

logger = logging.getLogger('dnf.plugin')
logger.setLevel(logging.INFO)


class ImgbasedPersist(dnf.Plugin):
    name = 'imgbased-persist'
    config_name = 'imgbased-persist'
    persist_path = "/var/imgbased/persisted-rpms/"
    excluded_pkgs = []
    bootsetup_pkgs = []

    def __init__(self, base, cli):
        super(ImgbasedPersist, self).__init__(base, cli)
        self.base = base
        cp = self.read_config(self.base.conf)
        self.excluded_pkgs = cp.get("main", "exclude_pkgs").split(',')
        self.bootsetup_pkgs = cp.get("main", "bootsetup_pkgs").split(',')

    def check_excludes(self, name):
        return name in self.excluded_pkgs

    def check_bootsetup(self, name):
        return name in self.bootsetup_pkgs

    def transaction(self):
        if self.base.transaction.install_set:
            if not os.path.isdir(self.persist_path):
                os.makedirs(self.persist_path)
            bootsetup = False
            for p in self.base.transaction.install_set:
                if self.check_bootsetup(p.name):
                    bootsetup = True
                if self.check_excludes(p.name):
                    continue
                rpm = p.localPkg()
                logger.info("Persisting: %s" % os.path.basename(rpm))
                shutil.copy2(rpm, self.persist_path + os.path.basename(rpm))
            if bootsetup:
                logger.info("Updating boot configuration")
                BootSetupHandler().setup()

        if self.base.transaction.remove_set:
            for p in self.base.transaction.remove_set:
                rpm = "{}-{}-{}.{}.rpm".format(p.name, p.v, p.r, p.a)
                try:
                    logger.info("Unpersisting: %s" % rpm)
                    os.remove(self.persist_path + rpm)
                except Exception:
                    # Has probably never been persisted. Manual RPM install?
                    pass
