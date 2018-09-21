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
from module_generator.clang_translation_unit_visitor import *


def generate_c_values(node, jval, funcname, name, index='0',
                      is_setter=False, check_type=True):
    result = ''
    buffers_to_free = []
    callbacks = []

    if isinstance(node, ClangASTNode):
        node_type = node.node_type
    elif isinstance(node, ClangASTNodeType):
        node_type = node
    if node_type.is_const():
        node_type_name = node_type.type_name.replace('const ', '')
    else:
        node_type_name = node_type.type_name
    node_declaration = node_type.get_declaration()
    node_declaration_kind = node_declaration.node_kind

    if (node_declaration_kind.is_struct_decl() or
        node_declaration_kind.is_union_decl()):
        struct_decl = node_declaration.get_as_struct_or_union_decl()
        struct_name = struct_decl.name

        if struct_name == '':
            struct_name = node_type_name + index
        else:
            struct_name += index

        if check_type:
            result = JS_CHECK_TYPE.format(TYPE='object', JVAL=jval,
                                          FUNC=funcname)

        if not is_setter:
            result += "  {TYPE} {NAME};".format(TYPE=node_type_name, NAME=name)

        for field in struct_decl.field_decls:
            member_name = struct_name + '_' + field.name
            member_val = member_name + '_value'

            getval, buffers, _ = generate_c_values(field, member_val, funcname,
                                                   member_name, index)

            buffers_to_free += buffers

            result += JS_GET_PROP.format(NAME=struct_name, MEM=field.name,
                                         OBJ=jval, GET_VAl=getval, STRUCT=name)
    elif node_type.is_pointer() or node_type.is_array():
        if node_type.is_pointer():
            pointee_type = node_type.get_pointee_type()
        else:
            # Array
            pointee_type = node_type.get_array_type()
            size = node_type.get_array_size()
        if pointee_type.is_const():
            pointee_type_name = pointee_type.type_name.replace('const ', '')
        else:
            pointee_type_name = pointee_type.type_name

        if pointee_type.is_char():
            if check_type:
                result = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval,
                                              FUNC=funcname)
            if is_setter:
                if node_type.is_pointer():
                    result += JS_SET_CHAR_PTR.format(TYPE=pointee_type_name,
                                                     NAME=name, JVAL=jval)
                else:
                    result += JS_SET_CHAR_ARR.format(NAME=name, JVAL=jval,
                                                     SIZE=(size-1))
            else:
                result += JS_GET_STRING.format(TYPE=pointee_type_name,
                                               NAME=name, JVAL=jval)
        elif pointee_type.is_number():
            if check_type:
                result = JS_CHECK_TYPES.format(TYPE1='typedarray', TYPE2='null',
                                               JVAL=jval, FUNC=funcname)
            if is_setter:
                result += JS_SET_TYPEDARRAY.format(TYPE=pointee_type_name,
                                                   NAME=name, JVAL=jval)
            else:
                result += JS_GET_TYPEDARRAY.format(TYPE=pointee_type_name,
                                                   NAME=name, JVAL=jval)
                buffers_to_free.append(JS_WRITE_ARRAYBUFFER.format(NAME=name,
                                                                   JVAL=jval))
        elif pointee_type.is_func() and not is_setter:
            if check_type:
                result = JS_CHECK_TYPE.format(TYPE='function', JVAL=jval,
                                              FUNC=funcname)
            result += JS_GET_FUNCTION.format(FUNC=funcname, NAME=name,
                                             JVAL=jval)
            callbacks.append(create_c_function(node, jval, funcname, name))
        else:
            result = JS_GET_UNSUPPORTED.format(TYPE=node_type_name, NAME=name)
    elif node_type.is_bool():
        if is_setter:
            result = JS_SET_BOOL.format(NAME=name, JVAL=jval)
        else:
            result = JS_GET_BOOL.format(TYPE=node_type_name, NAME=name,
                                        JVAL=jval)
    elif node_type.is_number() or node_type.is_enum():
        if check_type:
            result = JS_CHECK_TYPE.format(TYPE='number', JVAL=jval,
                                          FUNC=funcname)
        if is_setter:
            result += JS_SET_NUM.format(NAME=name, JVAL=jval)
        else:
            result += JS_GET_NUM.format(TYPE=node_type_name, NAME=name,
                                        JVAL=jval)
    elif node_type.is_char():
        if check_type:
            result = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval,
                                          FUNC=funcname)
        if is_setter:
            result += JS_SET_CHAR.format(NAME=name, JVAL=jval)
        else:
            result += JS_GET_CHAR.format(TYPE=node_type_name, NAME=name,
                                         JVAL=jval)
    elif node_type.is_func() and not is_setter:
        if check_type:
            result = JS_CHECK_TYPE.format(TYPE='function', JVAL=jval,
                                          FUNC=funcname)
        result += JS_GET_FUNCTION.format(FUNC=funcname, NAME=name, JVAL=jval)
        callbacks.append(create_c_function(node, jval, funcname, name))
    else:
        result = JS_GET_UNSUPPORTED.format(TYPE=node_type_name, NAME=name)

    return result, buffers_to_free, callbacks


def create_c_function(node, jval, funcname, name):
    func = node.get_as_function()
    params = []
    create_val = []

    for index, param in enumerate(func.params):
        index = str(index)
        param_name = ' p_' + index
        arg_name = ' arg_'+ index
        params.append(param.node_type.type_name + param_name)
        create_val.append(generate_js_value(param, param_name, arg_name))
        create_val.append('    args[' + index + '] =' + arg_name + ';')

    if func.return_type.type_name == 'void':
        res= ''
        ret = ''
    else:
        res, _, _ = generate_c_values(func.return_type, 'result', funcname,
                                      'ret', check_type=False)
        ret = 'ret'

    return JS_CB_FUNCTION.format(FUNC=funcname, NAME=name,
                                 RET_TYPE=func.return_type.type_name,
                                 PARAMS=(', ').join(params),
                                 LEN=len(func.params),
                                 CREATE_VAL=('\n').join(create_val),
                                 RESULT=res, RET=ret)


def generate_js_value(node, cval, name):
    if node.node_kind.is_function_decl():
        node_type = node.return_type
    else:
        node_type = node.node_type

    result = None

    node_type_declaration = node_type.get_declaration()
    node_type_declaration_kind = node_type_declaration.node_kind

    if (node_type_declaration_kind.is_struct_decl() or
        node_type_declaration_kind.is_union_decl()):
        struct_decl = node_type_declaration.get_as_struct_or_union_decl()
        struct_name = struct_decl.name

        if struct_name == '':
            struct_name = struct_decl.node_type.type_name

        result = JS_CREATE_VAL.format(NAME=name, TYPE='object', FROM='')

        for field in struct_decl.field_decls:
            member = cval + '.' + field.name
            member_js = 'js_' + struct_name + '_' + field.name
            mem_val = generate_js_value(field, member, member_js)
            result += mem_val

            result += JS_SET_PROP.format(NAME=struct_name, MEM=field.name,
                                         OBJ=name, JVAL=member_js)
    elif node_type.is_pointer() or node_type.is_array():
        if node_type.is_pointer():
            pointee_type = node_type.get_pointee_type()
        else:
            # Array
            pointee_type = node_type.get_array_type()
        pointee_type_name = pointee_type.type_name

        if pointee_type.is_char():
            result = JS_CREATE_STRING.format(NAME=name, FROM=cval)
        elif pointee_type.is_number():
            array_type = TYPEDARRAY_TYPES[pointee_type_name]
            result = JS_CREATE_TYPEDARRAY.format(NAME=name, FROM=cval,
                                                 TYPE=pointee_type_name,
                                                 ARRAY_TYPE=array_type)
        else:
            result = JS_CREATE_UNSUPPORTED.format(NAME=name, FROM=cval)
    elif node_type.is_void():
        result = JS_CREATE_VAL.format(NAME=name, TYPE='undefined', FROM='')
    elif node_type.is_bool():
        result = JS_CREATE_VAL.format(NAME=name, TYPE='boolean', FROM=cval)
    elif node_type.is_number():
        result = JS_CREATE_VAL.format(NAME=name, TYPE='number', FROM=cval)
    elif node_type.is_char():
        result = JS_CREATE_CHAR.format(NAME=name, FROM=cval)
    elif node_type.is_enum():
        result = JS_CREATE_VAL.format(NAME=name, TYPE='number', FROM=cval)
    else:
        result = JS_CREATE_UNSUPPORTED.format(NAME=name, FROM=cval)

    return result


def generate_jerry_functions(functions):
    for function in functions:
        funcname = function.name
        params = function.params
        return_type = function.return_type.type_name
        jerry_function = []
        native_params = []
        buffers_to_free = []
        callbacks = []

        if params:
            jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=len(params),
                                                            FUNC=funcname))

            for index, param in enumerate(params):
                index = str(index)
                jval = 'args_p[' + index + ']'
                name = 'arg_' + index
                result, buffers, callbacks = generate_c_values(param, jval,
                                                               funcname, name,
                                                               index)

                native_params.append('arg_' + index)
                buffers_to_free += buffers
                jerry_function.append(result)
        else:
            jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=0,
                                                            FUNC=funcname))

        native_params = (', ').join(native_params)

        result = generate_js_value(function, 'result', 'ret_val')

        if return_type == 'void':
            native_call = '  {} ({});\n'.format(funcname, native_params)
        else:
            native_call = '  {} {} = {} ({});\n'.format(return_type, 'result',
                                                        funcname, native_params)

        jerry_function.append('  // native function call\n' + native_call)
        jerry_function += buffers_to_free
        jerry_function.append(result)

        yield (JS_EXT_FUNC.format(NAME=funcname + '_handler',
                                  BODY=('\n').join(jerry_function)),
               ('\n').join(callbacks))


def generate_getter_setter(var):
    name = var.name
    get_result = generate_js_value(var, name, 'ret_val')
    set_result, buffers, _ = generate_c_values(var, 'args_p[0]',
                                               name + '_setter', name,
                                               is_setter=True)

    set_result += '  jerry_value_t ret_val = jerry_create_undefined();'

    getter = JS_EXT_FUNC.format(NAME=name + '_getter', BODY=get_result)
    setter = JS_EXT_FUNC.format(NAME=name + '_setter', BODY=set_result)

    return getter, setter


def regist_macro(macro):
    result = ''
    name = macro.name

    if macro.is_char():
        result = '  char {NAME}_value = {NAME};'.format(NAME=name)
        result += JS_CREATE_CHAR.format(NAME=name + '_js', FROM=name + '_value')
    elif macro.is_string():
        result = JS_CREATE_STRING.format(NAME=name + '_js', FROM=name)
    elif macro.is_number():
        result = JS_CREATE_VAL.format(NAME=name + '_js', TYPE='number',
                                      FROM=name)

    return result


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

    visitor = ClangTranslationUnitVisitor(header, api_headers, visit_args)
    visitor.visit()

    generated_source = [INCLUDE.format(HEADER=dirname + '_js_wrapper.h')]

    init_function = []

    if 'functions' not in args.off:
        # 'functions' is (jerry_function, callbacks)
        for functions in generate_jerry_functions(visitor.function_decls):
            generated_source.append(functions[1])
            generated_source.append(functions[0])

        for function in visitor.function_decls:
            init_function.append(INIT_REGIST_FUNC.format(NAME=function.name))

    if 'enums' not in args.off:
        for decl in visitor.enum_constant_decls:
            for enum in decl.enums:
                init_function.append(INIT_REGIST_ENUM.format(ENUM=enum))

    if 'variables' not in args.off:
        for var in visitor.var_decls:
            if var.node_type.is_const():
                result = generate_js_value(var, var.name, var.name + '_js')
                init_function.append(result)
                init_function.append(INIT_REGIST_CONST.format(NAME=var.name))
            elif (var.node_type.is_array() and
                  var.node_type.get_array_type().is_number()):
                array_type = var.node_type.get_array_type()
                type_name = array_type.type_name
                size = var.node_type.get_array_size()
                array_type = TYPEDARRAY_TYPES[type_name]
                result = INIT_REGIST_NUM_ARR.format(NAME=var.name,
                                                    TYPE=type_name,
                                                    SIZE=size,
                                                    ARRAY_TYPE=array_type)
                init_function.append(result)
            else:
                getter, setter = generate_getter_setter(var)
                generated_source.append(getter)
                generated_source.append(setter)
                init_function.append(INIT_REGIST_VALUE.format(NAME=var.name))

    if 'macros' not in args.off:
        for macro in visitor.macro_defs:
            result = regist_macro(macro)
            if result:
                init_function.append(result)
                init_function.append(INIT_REGIST_CONST.format(NAME=macro.name))


    generated_source.append(INIT_FUNC.format(NAME=dirname,
                                             BODY=('\n').join(init_function)))

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
        checker = ClangTranslationUnitChecker(header_file, api_headers,
                                              args.check_all)
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
