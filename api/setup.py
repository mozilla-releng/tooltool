# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import glob
import os.path
import setuptools


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(ROOT_DIR, "requirements/base.in")) as f:
    install_requires = f.readlines()

with open(os.path.join(ROOT_DIR, "requirements/test.in")) as f:
    tests_require = [i.strip() for i in f.readlines() if i and not i.startswith('-r')]

with open('VERSION') as f:
    VERSION = f.read().strip()


setuptools.setup(
    name='mozilla-tooltool-api',
    version=VERSION,
    description='The code behind https://tooltool.mozilla-releng.net/',
    author='Mozilla Release Services Team',
    author_email='release-services@mozilla.com',
    url='https://tooltool.mozilla-releng.net',
    tests_require=tests_require,
    install_requires=install_requires,
    packages=setuptools.find_packages('src'),
    package_dir={"": "src"},
    py_modules=[
        os.path.splitext(os.path.basename(path))[0]
        for path in glob.glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    license='MPL2',
)
