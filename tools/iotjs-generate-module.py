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

import os
import sys

from common_py import path
from common_py.system.filesystem import FileSystem as fs

from module_generator.source_templates import *
from module_generator.clang_translation_unit_visitor import ClangTUVisitor, \
    ClangTUChecker
from module_generator.source_generator import CSourceGenerator


def generate_c_source(header, api_headers, dirname, args):

    visit_args = []
    if args.define:
        visit_args += ['-D' + defs for defs in args.define]
    if args.defines:
        visit_args += ['-D' + defs for defs in args.defines.read().splitlines()]
    if args.include:
        visit_args += ['-I' + inc for inc in args.include]
    if args.includes:
        visit_args += ['-I' + inc for inc in args.includes.read().splitlines()]

    visitor = ClangTUVisitor(header, api_headers, visit_args)
    visitor.visit()

    generator = CSourceGenerator(visitor)

    generated_source = [INCLUDE.format(HEADER=dirname + '_js_wrapper.h')]

    if 'functions' not in args.off:
        for function in visitor.function_decls:
            generated_source.append(generator.create_ext_function(function))

    enums = []
    if 'enums' not in args.off:
        for decl in visitor.enum_constant_decls:
            enums += decl.enums

    if 'variables' not in args.off:
        for var in visitor.var_decls:
            generated_source.append(generator.create_getter_setter(var))

    macros = []
    if 'macros' not in args.off:
        macros = visitor.macro_defs

    generated_source.append(generator.create_init_function(dirname, enums,
                                                           macros))

    return ('\n').join(generated_source)


def generate_header(directory):
    includes = []
    api_headers = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.h'):
                api_headers.append(os.path.abspath(os.path.join(root, file)))
                includes.append('#include "' +
                                os.path.abspath(os.path.join(root, file)) +
                                '"')

    return ('\n').join(includes), api_headers


def search_for_lib(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.startswith('lib') and file.endswith('.a'):
                return root, file


def generate_module(args):
    directory = args.directory

    if fs.isdir(directory):
        # handle strings end with '/'
        if directory[-1] == '/':
            directory = directory[:-1]

        dirname = fs.basename(directory)
    else:
        sys.exit('Please give an existing directory.')

    if args.out_dir:
        output_dir = args.out_dir
    else:
        output_dir = fs.join(fs.join(path.TOOLS_ROOT, 'module_generator'),
                             'output')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    output_dir = fs.join(output_dir, dirname + '_module')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    header_file = fs.join(output_dir, dirname + '_js_wrapper.h')
    header_text, api_headers = generate_header(directory)

    with open(header_file, 'w') as h:
        h.write(header_text)

    if args.check or args.check_all:
        checker = ClangTUChecker(header_file, api_headers, args.check_all)
        checker.check()
        return

    c_file = generate_c_source(header_file, api_headers, dirname, args)

    with open(fs.join(output_dir, dirname + '_js_wrapper.c'), 'w') as c:
        c.write(c_file)

    if args.no_lib:
        json_file = MODULES_JSON.format(NAME=dirname, CMAKE='')
    else:
        lib_root, lib_name = search_for_lib(directory)
        cmake_file = MODULE_CMAKE.format(NAME=dirname, LIBRARY=lib_name[3:-2])

        with open(fs.join(output_dir, 'module.cmake'), 'w') as cmake:
            cmake.write(cmake_file)

        fs.copyfile(fs.join(lib_root, lib_name), fs.join(output_dir, lib_name))

        json_file = MODULES_JSON.format(NAME=dirname, CMAKE='module.cmake')

    with open(fs.join(output_dir, 'modules.json'), 'w') as json:
        json.write(json_file)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='Root directory of c api headers.')

    parser.add_argument('--out-dir', help='Output directory for the module. ' +
                        'Default: tools/module_generator/output')

    parser.add_argument('--off', choices=['functions', 'variables', 'enums',
                                          'macros'],
        action='append', default=[], help='Turn off source generating.')

    parser.add_argument('--no-lib', action='store_true', default=False,
        help='Disable static library copying.')

    parser.add_argument('--define', action='append', default=[],
        help='Add macro definition.')
    parser.add_argument('--defines', type=argparse.FileType('r'),
        help='A file, which contains macro definitions.')

    parser.add_argument('--include', action='append', default=[],
        help='Add path to include file.')
    parser.add_argument('--includes', type=argparse.FileType('r'),
        help='A file, which contains paths to include files.')

    parser.add_argument('--check', action='store_true', default=False,
        help='Check the C API headers. Print the unsupported parts.')

    parser.add_argument('--check-all', action='store_true', default=False,
        help='Check the C API headers.')



    args = parser.parse_args()

    generate_module(args)
