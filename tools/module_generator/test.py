#!/usr/bin/env python

# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common_py import path
from common_py.system.executor import Executor as ex
from common_py.system.filesystem import FileSystem as fs

def test_module_generator():
    module_generator_dir = fs.join(path.TOOLS_ROOT, 'module_generator')
    test_dir = fs.join(module_generator_dir, 'test')
    test_c = fs.join(test_dir, 'test.c')

    # Compile test.c and make a static library
    ex.check_run_cmd('cc', ['-c', test_c, '-o', test_dir + '/test.o'])
    ex.check_run_cmd('ar', ['-cr', test_dir + '/libtest.a',
                     test_dir + '/test.o'])

    # Generate test_module
    generator_script = fs.join(path.TOOLS_ROOT, 'iotjs-generate-module.py')
    ex.check_run_cmd(generator_script, [test_dir])

    # Build iotjs
    module_dir = fs.join(module_generator_dir, 'output', 'test_module')
    build_script = fs.join(path.TOOLS_ROOT, 'build.py')
    args = [
    '--external-module=' + module_dir,
    '--cmake-param=-DENABLE_MODULE_TEST_MODULE=ON',
    '--jerry-profile=es2015-subset'
    ]
    ex.check_run_cmd(build_script, args)

    # Run test.js
    binary = fs.join(path.BUILD_ROOT, 'x86_64-linux', 'debug', 'bin', 'iotjs')
    test_js = fs.join(test_dir, 'test.js')
    ex.check_run_cmd(binary, [test_js])


if __name__ == '__main__':
    test_module_generator()
