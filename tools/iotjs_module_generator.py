#!/usr/bin/env python

# Copyright 2015-present Samsung Electronics Co., Ltd. and other contributors
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
from module_generator.clang_translation_unit_visitor import ClangTranslationUnitVisitor

C_NUMBER_TYPES = {
    'signed char': 'INT8',
    'unsigned char': 'UINT8',
    'short': 'INT16',
    'short int': 'INT16',
    'signed short': 'INT16',
    'signed short int': 'INT16',
    'unsigned short': 'UINT16',
    'unsigned short int': 'UINT16',
    'int': 'INT32',
    'signed': 'INT32',
    'signed int': 'INT32',
    'unsigned': 'UINT32',
    'unsigned int': 'UINT32',
    'long': 'INT32',
    'long int': 'INT32',
    'signed long': 'INT32',
    'signed long int': 'INT32',
    'unsigned long': 'UINT32',
    'unsigned long int': 'UINT32',
    'long long': 'INT32',
    'long long int': 'INT32',
    'signed long long': 'INT32',
    'signed long long int': 'INT32',
    'unsigned long long': 'UINT32',
    'unsigned long long int': 'UINT32',
    'float': 'FLOAT32',
    'double': 'FLOAT64',
    'long double': 'FLOAT64'
}


def clang_generate_c_values(node, jval, funcname, name, index='0'):
    result = None
    buffers_to_free = []

    node_type = node.node_type
    node_declaration = node_type.get_declaration()
    node_declaration_kind = node_declaration.node_kind

    if node_declaration_kind.is_struct_decl() or node_declaration_kind.is_union_decl():
        struct_decl = node_declaration.get_as_struct_or_union_decl()
        struct_name = struct_decl.name

        if struct_name == '':
            struct_name = struct_decl.node_type.type_name + index
            struct_type = struct_decl.node_type.type_name
        elif node_declaration_kind.is_struct_decl():
            struct_type = 'struct ' + struct_name
            struct_name += index
        elif node_declaration_kind.is_union_decl():
            struct_type = 'union ' + struct_name
            struct_name += index


        result = JS_CHECK_TYPE.format(TYPE='object',
                                      JVAL=jval,
                                      FUNC=funcname)

        result += "  {TYPE} {NAME};".format(TYPE=struct_type, NAME=name)

        for field in struct_decl.field_decls:
            member_name = struct_name + '_' + field.name
            member_val = member_name + '_value'

            getval, buffers = clang_generate_c_values(field,
                                                      member_val,
                                                      funcname,
                                                      member_name,
                                                      index)

            buffers_to_free += buffers

            result += JS_GET_PROP.format(NAME=struct_name,
                                         MEM=field.name,
                                         OBJ=jval,
                                         GET_VAl=getval,
                                         STRUCT=name)

            if node_declaration_kind.is_union_decl():
                break

    elif node_type.is_pointer() or node_type.is_array():
        if node_type.is_pointer():
            pointee_type, count = node_type.get_pointee_type()
        else:
            # Array
            pointee_type, count = node_type.get_array_type()

        if pointee_type.is_char() and count == 1:
            check_type = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval, FUNC=funcname)
            get_type = JS_GET_STRING.format(NAME=name, JVAL=jval)
            result = check_type + get_type

        elif pointee_type.is_number() and count == 1:
            check_type = JS_CHECK_TYPES.format(TYPE1='typedarray',
                                               TYPE2='null',
                                               JVAL=jval,
                                               FUNC=funcname)

            get_type = JS_GET_TYPEDARRAY.format(TYPE=pointee_type.type_name, NAME=name, JVAL=jval)

            result = check_type + get_type

            buffers_to_free.append(JS_WRITE_ARRAYBUFFER.format(NAME=name, JVAL=jval))
        else:
            result = JS_GET_UNSUPPORTED.format(TYPE=node_type.type_name,
                                               NAME=name)

    elif node_type.is_bool():
        result = JS_GET_BOOL.format(NAME=name, JVAL=jval)
    elif node_type.is_number():
        check_type = JS_CHECK_TYPE.format(TYPE='number', JVAL=jval, FUNC=funcname)
        get_type = JS_GET_NUM.format(TYPE=node_type.type_name, NAME=name, JVAL=jval)
        result = check_type + get_type
    elif node_type.is_char():
        check_type = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval, FUNC=funcname)
        get_type = JS_GET_CHAR.format(NAME=name, JVAL=jval)
        result = check_type + get_type
    elif node_type.is_enum():
        check_type = JS_CHECK_TYPE.format(TYPE='number', JVAL=jval, FUNC=funcname)
        get_type = JS_GET_NUM.format(TYPE='int', NAME=name, JVAL=jval)
        result = check_type + get_type

    else:
        result = JS_GET_UNSUPPORTED.format(TYPE=node_type.type_name,
                                           NAME=name)

    return result, buffers_to_free


def clang_generate_js_value(node, cval, name):
    if node.node_kind.is_function_decl():
        node_type = node.return_type
    else:
        node_type = node.node_type

    node_type_name = node_type.type_name

    result = None

    node_type_declaration = node_type.get_declaration()
    node_type_declaration_kind = node_type_declaration.node_kind

    if node_type_declaration_kind.is_struct_decl() or node_type_declaration_kind.is_union_decl():
        struct_decl = node_type_declaration.get_as_struct_or_union_decl()
        struct_name = struct_decl.name

        if struct_name == '':
            struct_name = struct_decl.node_type.type_name
            struct_type = struct_decl.node_type.type_name
        elif node_type_declaration_kind.is_struct_decl():
            struct_type = 'struct ' + struct_name
        elif node_type_declaration_kind.is_union_decl():
            struct_type = 'union ' + struct_name

        result = JS_CREATE_VAL.format(NAME=name, TYPE='object', FROM='')

        for field in struct_decl.field_decls:
            member = cval + '.' + field.name
            member_js = 'js_' + struct_name + '_' + field.name
            _, mem_val = clang_generate_js_value(field, member, member_js)
            result += mem_val

            result += JS_SET_PROP.format(NAME=struct_name,
                                         MEM=field.name,
                                         OBJ=name,
                                         JVAL=member_js)

        return struct_type, result

    elif node_type.is_pointer():
        pointee_type, count = node_type.get_pointee_type()
        pointee_type_name = pointee_type.type_name

        if pointee_type.is_char() and count == 1:
            result = JS_CREATE_STRING.format(NAME=name, FROM=cval)
        elif pointee_type.is_number() and count == 1:
            array_type = C_NUMBER_TYPES[pointee_type_name]
            result = JS_CREATE_TYPEDARRAY.format(NAME=name,
                                                 FROM=cval,
                                                 TYPE=pointee_type_name,
                                                 ARRAY_TYPE=array_type)
        else:
            result = JS_CREATE_UNSUPPORTED.format(NAME=name, FROM=cval)

        return node_type_name, result

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

    return node_type_name, result


def clang_generate_jerry_functions(functions):
    for function in functions:
        funcname = function.name
        params = function.params
        jerry_function = []
        native_params = []
        buffers_to_free = []

        if params:
            jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=len(params),
                                                            FUNC=funcname))

            for index, param in enumerate(params):
                index = str(index)
                result, buffers = clang_generate_c_values(param,
                                                          'args_p['+index+']',
                                                          funcname,
                                                          'arg_' + index,
                                                          index)

                if result:
                    native_params.append('arg_' + index)
                    buffers_to_free += buffers
                    comment = '\n  // {}. argument\n'.format(index)
                    jerry_function.append(comment + result)
                else:
                    jerry_function[0] = JS_CHECK_ARG_COUNT.format(COUNT=0,
                                                                  FUNC=funcname)
        else:
            jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=0,
                                                            FUNC=funcname))

        native_params = (', ').join(native_params)

        return_type, result = clang_generate_js_value(function, 'result', 'ret_val')

        if return_type == 'void':
            native_call = '  {} ({});\n'.format(funcname, native_params)
        else:
            native_call = '  {} {} = {} ({});\n'.format(return_type,
                                                        'result',
                                                        funcname,
                                                        native_params)

        jerry_function.append(native_call)
        jerry_function += buffers_to_free
        jerry_function.append(result)

        yield JS_EXT_FUNC.format(NAME=funcname + '_handler',
                                 BODY=('\n').join(jerry_function))


def generate_getter_setter(var):
    _, get_result = clang_generate_js_value(var, var.name, 'ret_val')
    set_result, buffers = clang_generate_c_values(var, 'args_p[0]',
                                                  var.name + '_setter',
                                                  var.name + '_val')

    if buffers:
        set_result += '  jerry_release_value ({}_buffer);\n'.format(var.name + '_val')


    set_result += '  {} = {};\n'.format(var.name, var.name + '_val')
    set_result += '  jerry_value_t ret_val = jerry_create_undefined();'

    getter = JS_EXT_FUNC.format(NAME=var.name + '_getter',
                                BODY=get_result)
    setter = JS_EXT_FUNC.format(NAME=var.name + '_setter',
                                BODY=set_result)

    return getter, setter


def generate_c_source(header, api_headers, dirname):

    clang_visitor = ClangTranslationUnitVisitor(header, api_headers, [])
    clang_visitor.visit()

    generated_source = [INCLUDE.format(HEADER=dirname + '_js_wrapper.h')]

    init_function = []

    for jerry_function in clang_generate_jerry_functions(clang_visitor.function_decls):
        generated_source.append(jerry_function)

    for function in clang_visitor.function_decls:
        init_function.append(INIT_REGIST_FUNC.format(NAME=function.name))

    for decl in clang_visitor.enum_constant_decls:
        for enum in decl.enums:
            init_function.append(INIT_REGIST_ENUM.format(ENUM=enum))

    for var in clang_visitor.var_decls:
        if var.node_type.is_const():
            _, result = clang_generate_js_value(var, var.name, var.name + '_js')
            init_function.append(result)
            init_function.append(INIT_REGIST_CONST.format(NAME=var.name))
        else:
            getter, setter = generate_getter_setter(var)
            generated_source.append(getter)
            generated_source.append(setter)
            init_function.append(INIT_REGIST_VALUE.format(NAME=var.name))

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
    lib_name = ''
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.startswith('lib') and file.endswith('.a'):
                return root, file


def generate_module(directory):
    if fs.isdir(directory):
        # handle strings ends with '/'
        if directory[-1] == '/':
            directory = directory[:-1]

        dirname = fs.basename(directory)
    else:
        sys.exit('Please give an existing directory.')

    output_dir = fs.join(fs.join(path.TOOLS_ROOT, 'module_generator'), 'output')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    output_dir = fs.join(output_dir, dirname + '_module')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    lib_root, lib_name = search_for_lib(directory)

    header_file = fs.join(output_dir, dirname + '_js_wrapper.h')
    header_text, api_headers = generate_header(directory)

    with open(header_file, 'w') as h:
        h.write(header_text)

    c_file = generate_c_source(header_file, api_headers, dirname)
    json_file = MODULES_JSON.format(NAME=dirname)
    cmake_file = MODULE_CMAKE.format(NAME=dirname, LIBRARY=lib_name[3:-2])

    with open(fs.join(output_dir, dirname + '_js_wrapper.c'), 'w') as c:
        c.write(c_file)

    with open(fs.join(output_dir, 'modules.json'), 'w') as json:
        json.write(json_file)

    with open(fs.join(output_dir, 'module.cmake'), 'w') as cmake:
        cmake.write(cmake_file)

    fs.copyfile(fs.join(lib_root, lib_name), fs.join(output_dir, lib_name))

    return output_dir, dirname + '_module'

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('directory',
                        help='Root directory of c api headers.')

    args = parser.parse_args()

    generate_module(args.directory)
