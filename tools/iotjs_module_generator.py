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

from pycparser import c_parser, c_ast, parse_file, c_generator
from common_py import path
from common_py.system.filesystem import FileSystem as fs

C_VOID_TYPE = 'void'

C_BOOL_TYPE = '_Bool'

C_NUMBER_TYPES = [
    'short',
    'short int',
    'signed short',
    'signed short int',
    'unsigned short',
    'unsigned short int',
    'int',
    'signed',
    'signed int',
    'unsigned',
    'unsigned int',
    'long',
    'long int',
    'signed long',
    'signed long int',
    'unsigned long',
    'unsigned long int',
    'long long',
    'long long int',
    'signed long long',
    'signed long long int',
    'unsigned long long',
    'unsigned long long int',
    'float',
    'double',
    'long double',
]

C_CHAR_TYPES = [
    'char',
    'signed char',
    'unsigned char'
]

INCLUDE = '''
#include "jerryscript.h"
#include "{HEADER}"
'''

MACROS = '''
#define CHECK_ARG_COUNT(COUNT, FUNC) \\
  do { \\
    if (args_cnt != COUNT) \\
    { \\
      const char* msg = "Wrong argument count for "#FUNC"(), expected "#COUNT"."; \\
      return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t*)msg); \\
    } \\
  } while (0)

#define CHECK_TYPE(TYPE, JVAL, FUNC) \\
  do { \\
    if (!jerry_value_is_##TYPE (JVAL)) \\
    { \\
      const char* msg = "Wrong argument type for "#FUNC"(), expected "#TYPE"."; \\
      return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t*)msg); \\
    } \\
  } while (0)

#define REGIST_FUNCTION(OBJECT, NAME, HANDLER) \\
  do { \\
    jerry_value_t NAME##_name = jerry_create_string((const jerry_char_t*)#NAME); \\
    jerry_value_t NAME##_func = jerry_create_external_function(HANDLER); \\
    jerry_value_t NAME##_ret = jerry_set_property(OBJECT, NAME##_name, NAME##_func); \\
    jerry_release_value(NAME##_name); \\
    jerry_release_value(NAME##_func); \\
    jerry_release_value(NAME##_ret); \\
  } while (0)
'''

JS_FUNC_HANDLER = '''
jerry_value_t {NAME}_handler (const jerry_value_t function_obj,
                              const jerry_value_t this_val,
                              const jerry_value_t args_p[],
                              const jerry_length_t args_cnt)
{{
{BODY}
  return ret_val;
}}
'''

JS_ARG_COMMENT = '''
    /***************
     * {INDEX}. ARGUMENT *
     ***************/
'''

JS_CHECK_ARG_COUNT = '''
  CHECK_ARG_COUNT({COUNT}, {FUNC});
'''

JS_CHECK_TYPE = '''
  CHECK_TYPE({TYPE}, {JVAL}, {FUNC});
'''

JS_GET_NUM = '''
  {TYPE} {NAME} = jerry_get_number_value ({JVAL});
'''

JS_GET_BOOL = '''
  bool {NAME} = jerry_get_boolean_value ({JVAL});
'''

JS_GET_CHAR = '''
  jerry_char_t char_{NAME}[1];
  jerry_string_to_char_buffer ({JVAL}, char_{NAME}, 1);
  {TYPE} {NAME} = ({TYPE})char_{NAME}[0];
'''

C_NATIVE_CALL = '''
  {RETURN}{RESULT}{NATIVE}({PARAM});
'''

C_NATIVE_STRUCT = '''
  {TYPE} {NAME} = {{{PARAM}}};
'''

JS_CREATE_VAL = '''
  jerry_value_t {NAME} = jerry_create_{TYPE}({FROM});
'''

JS_GET_PROP = '''
  jerry_value_t {NAME}_{MEM}_name = jerry_create_string ((const jerry_char_t *) "{MEM}");
  jerry_value_t {NAME}_{MEM}_value = jerry_get_property ({OBJ}, {NAME}_{MEM}_name);
  jerry_release_value({NAME}_{MEM}_name);
  {GET_VAl}
  jerry_release_value({NAME}_{MEM}_value);
'''

JS_SET_PROP = '''
  jerry_value_t {NAME}_{MEM}_name = jerry_create_string ((const jerry_char_t *) "{MEM}");
  jerry_value_t {NAME}_{MEM}_res = jerry_set_property ({OBJ}, {NAME}_{MEM}_name, {JVAL});
  jerry_release_value({JVAL});
  jerry_release_value({NAME}_{MEM}_name);
  jerry_release_value({NAME}_{MEM}_res);
'''

INIT_FUNC = '''
jerry_value_t Init{NAME}()
{{
  jerry_value_t object = jerry_create_object();
{BODY}
  return object;
}}
'''

INIT_REGIST_FUNC = '''  REGIST_FUNCTION(object, {NAME}, {NAME}_handler);
'''

MODULES_JSON = '''
{{
  "modules": {{
    "{NAME}_module": {{
      "native_files": ["{NAME}_js_wrapper.c"],
      "init": "Init{NAME}",
      "cmakefile": "module.cmake"
    }}
  }}
}}
'''

MODULE_CMAKE = '''
set(MODULE_NAME "{NAME}_module")
link_directories(${{MODULE_DIR}})
list(APPEND MODULE_LIBS {LIBRARY})
'''


class Struct_Visitor(c_ast.NodeVisitor):
    def __init__(self):
        self.structdefs = []
        self.structdecls = []

    def visit_Struct(self, node):
        if node.decls is None:
            self.structdecls.append(node)
        else:
            self.structdefs.append(node)
        for c in node:
            self.visit(c)


def get_typedefs(ast):
    typedefs = []

    for decl in ast.ext:
        if type(decl) is c_ast.Typedef:
            typedefs.append(decl)

    return typedefs


def get_structs(ast):
    struct_visitor = Struct_Visitor()
    struct_visitor.visit(ast)
    return struct_visitor.structdefs


def get_functions(ast):
    funcs = []

    for decl in ast.ext:
        if type(decl) is c_ast.Decl and type(decl.type) is c_ast.FuncDecl:
            funcs.append(decl)

    return funcs


def get_params(functions):
    params = []

    for func in functions:
        if func.type.args:
            params += func.type.args.params

    return params


def resolve_typedefs(firstlist, secondlist):
    for first in firstlist:
        for second in secondlist:
            parent = second
            child = second.type

            while (type(child) is not c_ast.TypeDecl and
                   hasattr(child, 'type')):
                   parent = child
                   child = child.type

            if (type(child) is c_ast.TypeDecl and
                type(child.type) is c_ast.IdentifierType and
                [first.name] == child.type.names):
                parent.type = first.type


def get_c_type_value(c_type, jval, funcname, name):
    if c_type == C_BOOL_TYPE:
        check_type = JS_CHECK_TYPE.format(TYPE='boolean', JVAL=jval,
                                          FUNC=funcname)
        get_type = JS_GET_BOOL.format(NAME=name, JVAL=jval)

    elif c_type in C_NUMBER_TYPES:
        check_type = JS_CHECK_TYPE.format(TYPE='number', JVAL=jval,
                                          FUNC=funcname)
        get_type = JS_GET_NUM.format(TYPE=c_type, NAME=name, JVAL=jval)

    elif c_type in C_CHAR_TYPES:
        check_type = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval,
                                          FUNC=funcname)
        get_type = JS_GET_CHAR.format(TYPE=c_type, NAME=name, JVAL=jval)

    return check_type + get_type


def create_js_type_value(c_type, name, cval):
    if c_type == C_VOID_TYPE:
        result = JS_CREATE_VAL.format(NAME=name, TYPE='undefined', FROM='')
    elif c_type == C_BOOL_TYPE:
        result = JS_CREATE_VAL.format(NAME=name, TYPE='boolean', FROM=cval)
    elif c_type in C_NUMBER_TYPES:
        result = JS_CREATE_VAL.format(NAME=name, TYPE='number', FROM=cval)
    elif c_type in C_CHAR_TYPES:
        result = JS_CREATE_VAL.format(NAME=name, TYPE='string', FROM=cval)

    return result

def generate_c_values(node, jval, funcname, name, index):
    if type(node.type) is c_ast.TypeDecl:
        if type(node.type.type) is c_ast.IdentifierType:
            nodetype = (' ').join(node.type.type.names)
            if nodetype == C_VOID_TYPE:
                result = None
            else:
                result = get_c_type_value(nodetype, jval, funcname, name)

        elif type(node.type.type) is c_ast.Struct:
            struct_members = []
            struct = node.type.type

            if struct.name is None:
                structname = node.type.declname + index
                structtype = node.type.declname
            else:
                structname = struct.name + index
                structtype = 'struct ' + struct.name

            result = JS_CHECK_TYPE.format(TYPE='object', JVAL=jval, FUNC=funcname)

            for decl in struct:
                getval = generate_c_values(decl, structname+'_'+decl.name+'_value', funcname, structname+'_'+decl.name, index)

                result += JS_GET_PROP.format(NAME=structname,
                                             MEM=decl.name,
                                             OBJ=jval,
                                             GET_VAl=getval)
                struct_members.append(structname+'_'+decl.name)

            result += C_NATIVE_STRUCT.format(TYPE=structtype,
                                             NAME=name,
                                             PARAM=(',').join(struct_members))
        return result


def generate_js_value(node, cval, name):
    if type(node.type) is c_ast.TypeDecl:
        if type(node.type.type) is c_ast.IdentifierType:
            nodetype = (' ').join(node.type.type.names)
            result = create_js_type_value(nodetype, name, cval)

            return nodetype, result

        elif type(node.type.type) is c_ast.Struct:
            struct = node.type.type
            structtypes = []

            if struct.name is None:
                structname = node.type.declname
                structtypes.append(node.type.declname)
            else:
                structname = struct.name
                structtypes.append('struct ' + struct.name)

            result = JS_CREATE_VAL.format(NAME=name,
                                          TYPE='object',
                                          FROM='')

            for decl in struct:
                mem_type, mem_val = generate_js_value(decl, cval+'.'+decl.name, 'js_'+structname+'_'+decl.name)
                result += mem_val

                result += JS_SET_PROP.format(NAME=structname,
                                             MEM=decl.name,
                                             OBJ=name,
                                             JVAL='js_'+structname+'_'+decl.name)

            return structtypes[0], result



def generate_jerry_functions(functions):
    for function in functions:
        funcname = function.name
        funcdecl = function.type
        paramlist = funcdecl.args
        jerry_function = []
        native_params = []

        if paramlist:
            params = paramlist.params
            jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=len(params),
                                                            FUNC=funcname))

            for index, param in enumerate(params):
                index = str(index)
                result = generate_c_values(param, 'args_p['+index+']',
                                           funcname, 'arg_' + index, index)
                if result:
                    native_params.append('arg_' + index)
                    comment = JS_ARG_COMMENT.format(INDEX=index)
                    jerry_function.append(comment+result)
                else:
                    jerry_function[0] = JS_CHECK_ARG_COUNT.format(COUNT=0,
                                                                  FUNC=funcname)

        native_params = (', ').join(native_params)

        return_type, result = generate_js_value(funcdecl, 'result', 'ret_val')

        if return_type == C_VOID_TYPE:
            jerry_function.append(C_NATIVE_CALL.format(RETURN='',
                                                       RESULT='',
                                                       NATIVE=funcname,
                                                       PARAM=native_params))
        else:
            jerry_function.append(C_NATIVE_CALL.format(RETURN=return_type,
                                                       RESULT=' result = ',
                                                       NATIVE=funcname,
                                                       PARAM=native_params))

        jerry_function.append(result)

        yield JS_FUNC_HANDLER.format(NAME=funcname,
                                     BODY=('\n').join(jerry_function))


def gen_c_source(header, dirname):

    preproc_args = ['-Dbool=_Bool',
                    '-D__attribute__(x)=',
                    '-D__asm__(x)=',
                    '-D__restrict=restrict',
                    '-D__builtin_va_list=void']

    ast = parse_file(header, use_cpp=True, cpp_args=preproc_args)

    functions = get_functions(ast)
    typedefs = get_typedefs(ast)
    params = get_params(functions)

    resolve_typedefs(typedefs, typedefs)
    resolve_typedefs(typedefs, functions)
    resolve_typedefs(typedefs, params)

    struct_visitor = Struct_Visitor()
    struct_visitor.visit(ast)
    for structdef in struct_visitor.structdefs:
        resolve_typedefs(typedefs, structdef.decls)
        for structdecl in struct_visitor.structdecls:
            if structdef.name == structdecl.name:
                structdecl.decls = structdef.decls

    generated_source = [INCLUDE.format(HEADER=dirname + '_js_wrapper.h')]

    for jerry_function in generate_jerry_functions(functions):
        generated_source.append(jerry_function)

    init_function = []
    for function in functions:
        init_function.append(INIT_REGIST_FUNC.format(NAME=function.name))

    generated_source.append(INIT_FUNC.format(NAME=dirname,
                                             BODY=('\n').join(init_function)))

    return ('\n').join(generated_source)


def gen_header(directory):
    includes = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.h'):
                includes.append('#include "' +
                                os.path.abspath(os.path.join(root, file)) +
                                '"')

    return ('\n').join(includes)


def create_header_to_parse(header_name, copy_dir):
    header_text = gen_header(copy_dir)
    with open(header_name, 'w') as tmp:
        tmp.write(header_text)

    preproc_args = ['-Dbool=_Bool',
                    '-D__attribute__(x)=',
                    '-D__asm__(x)=',
                    '-D__restrict=restrict',
                    '-D__builtin_va_list=void']

    ast = parse_file(header_name, use_cpp=True, cpp_args=preproc_args)
    typedefs = get_typedefs(ast)
    structs = get_structs(ast)
    ast = c_ast.FileAST(typedefs + structs)

    for root, dirs, files in os.walk(copy_dir):
        for file in files:
            if file.endswith('.h'):
                with open(fs.join(root, file), 'r') as f:
                    text = f.read()
                text = text.replace('#include', '//')
                with open(fs.join(root, file), 'w') as f:
                    f.write(text)

    generator = c_generator.CGenerator()
    types_and_structs = generator.visit(ast)

    with open(header_name, 'w') as tmp:
        tmp.write(types_and_structs + header_text)

    return header_name


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

    output_dir = fs.join(path.TOOLS_ROOT, 'generator_output')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    output_dir = fs.join(output_dir, dirname + '_module')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    copy_dir = fs.join(output_dir, dirname)
    fs.copytree(directory, copy_dir)
    tmp_file = fs.join(output_dir, 'tmp.h')
    header_to_parse = create_header_to_parse(tmp_file, copy_dir)
    lib_root, lib_name = search_for_lib(directory)

    header_file = gen_header(directory)
    c_file = gen_c_source(header_to_parse, dirname)
    json_file = MODULES_JSON.format(NAME=dirname)
    cmake_file = MODULE_CMAKE.format(NAME=dirname, LIBRARY=lib_name[3:-2])

    with open(fs.join(output_dir, dirname + '_js_wrapper.h'), 'w') as h:
        h.write(header_file + MACROS)

    with open(fs.join(output_dir, dirname + '_js_wrapper.c'), 'w') as c:
        c.write(c_file)

    with open(fs.join(output_dir, 'modules.json'), 'w') as json:
        json.write(json_file)

    with open(fs.join(output_dir, 'module.cmake'), 'w') as cmake:
        cmake.write(cmake_file)

    fs.copyfile(fs.join(lib_root, lib_name), fs.join(output_dir, lib_name))

    fs.rmtree(copy_dir)
    fs.remove(tmp_file)

    return output_dir, dirname + '_module'

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('directory',
                        help='Root directory of c api headers.')

    args = parser.parse_args()

    generate_module(args.directory)
