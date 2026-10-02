#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Pass the supported kernel banner-date definition to the pinned compiler.

Open Watcom 1.9 does not honor SOURCE_DATE_EPOCH for __DATE__. Do not patch
linked bytes or replace any component source; use hdr/version.h's public
KERNEL_BUILD_DATE build interface. All other compiler arguments are unchanged.
"""
from datetime import datetime, timezone
import os
import re
import sys

COMPILER = '/opt/openwatcom-1.9/binl/wcc'
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


def banner_date(epoch):
    instant = datetime.fromtimestamp(int(epoch), timezone.utc)
    return '{} {:2d} {:04d}'.format(MONTHS[instant.month - 1], instant.day, instant.year)


def date_definition(epoch):
    return '-dKERNEL_BUILD_DATE="' + banner_date(epoch) + '"'


def verify_banner(data, epoch):
    found = re.findall(rb'\[compiled ([^\]\r\n]+)\]', data)
    if found != [banner_date(epoch).encode('ascii')]:
        raise ValueError('linked kernel banner date is missing, duplicated or not fixed to SOURCE_DATE_EPOCH')


def main():
    definition = date_definition(os.environ['SOURCE_DATE_EPOCH'])
    os.execv(COMPILER, [COMPILER, definition, *sys.argv[1:]])


if __name__ == '__main__':
    main()
