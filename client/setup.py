# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import setuptools


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(ROOT_DIR, "version.txt")) as f:
    version = f.read().rstrip()

with open(
    os.path.join(ROOT_DIR, "requirements/base.in")
) as f:
    install_requires = f.readlines()

with open(
    os.path.join(ROOT_DIR, "requirements/test.in")
) as f:
    tests_require = [i.strip() for i in f.readlines() if i and not i.startswith('-r')]

setuptools.setup(
    name='mozilla-tooltool-client',
    version=version,
    description='Secure, cache-friendly access to large binary blobs for builds and tests',
    author='Mozilla Release Services Team',
    author_email='release-services@mozilla.com',
    url='https://tooltool.mozilla-releng.net',
    tests_require=tests_require,
    install_requires=install_requires,
    py_modules=['tooltool'],
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
