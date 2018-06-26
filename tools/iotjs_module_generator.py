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

from pycparser import c_ast, parse_file
from common_py import path
from common_py.system.filesystem import FileSystem as fs

from clang_translation_unit_visitor import ClangTranslationUnitVisitor

C_VOID_TYPE = 'void'

C_BOOL_TYPE = '_Bool'

C_CHAR_TYPES = 'char'

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

INCLUDE = '''
#include <stdlib.h>  // If there are pointers, malloc() and free() required
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

#define CHECK_TYPES(TYPE1, TYPE2, JVAL, FUNC) \\
  do { \\
    if (!jerry_value_is_##TYPE1 (JVAL) && !jerry_value_is_##TYPE2 (JVAL)) \\
    { \\
      const char* msg = "Wrong argument type for "#FUNC"(), expected "#TYPE1" or "#TYPE2"."; \\
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

#define REGIST_ENUM(OBJECT, ENUM) \\
  do { \\
    jerry_value_t ENUM##_name = jerry_create_string((const jerry_char_t*)#ENUM); \\
    jerry_value_t ENUM##_enum = jerry_create_number(ENUM); \\
    jerry_value_t ENUM##_ret = jerry_set_property(OBJECT, ENUM##_name, ENUM##_enum); \\
    jerry_release_value(ENUM##_name); \\
    jerry_release_value(ENUM##_enum); \\
    jerry_release_value(ENUM##_ret); \\
  } while (0)

#define REGIST_VALUE(OBJECT, NAME, GETTER) \\
  do { \\
    jerry_property_descriptor_t NAME##_prop_desc; \\
    jerry_init_property_descriptor_fields (&NAME##_prop_desc); \\
    NAME##_prop_desc.is_get_defined = true; \\
    NAME##_prop_desc.getter = jerry_create_external_function(GETTER); \\
    jerry_value_t NAME##_prop_name = jerry_create_string ((const jerry_char_t *)#NAME); \\
    jerry_value_t NAME##_return_value = jerry_define_own_property (OBJECT, NAME##_prop_name, &NAME##_prop_desc); \\
    jerry_release_value (NAME##_return_value); \\
    jerry_release_value (NAME##_prop_name); \\
    jerry_free_property_descriptor_fields (&NAME##_prop_desc); \\
  } while (0)

#define REGIST_CONST(OBJECT, NAME, VALUE) \\
  do { \\
    jerry_property_descriptor_t NAME##_prop_desc; \\
    jerry_init_property_descriptor_fields (&NAME##_prop_desc); \\
    NAME##_prop_desc.is_value_defined = true; \\
    NAME##_prop_desc.value = VALUE; \\
    jerry_value_t NAME##_prop_name = jerry_create_string ((const jerry_char_t *)#NAME); \\
    jerry_value_t NAME##_return_value = jerry_define_own_property (OBJECT, NAME##_prop_name, &NAME##_prop_desc); \\
    jerry_release_value (NAME##_return_value); \\
    jerry_release_value (NAME##_prop_name); \\
    jerry_free_property_descriptor_fields (&NAME##_prop_desc); \\
  } while (0)
'''

JS_FUNC = '''
jerry_value_t {NAME} (const jerry_value_t function_obj,
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

JS_CHECK_TYPES = '''
  CHECK_TYPES({TYPE1}, {TYPE2}, {JVAL}, {FUNC});
'''

JS_GET_NUM = '''
  {TYPE} {NAME} = jerry_get_number_value ({JVAL});
'''

JS_GET_BOOL = '''
  _Bool {NAME} = jerry_value_to_boolean ({JVAL});
'''

JS_GET_CHAR = '''
  char {NAME};
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)(&{NAME}), 1);
'''

JS_GET_STRING = '''
  jerry_size_t size_{NAME} = jerry_get_string_size ({JVAL});
  char {NAME}[size_{NAME}];
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, size_{NAME});
  {NAME}[size_{NAME}] = '\\0';
'''

JS_GET_POINTER = '''
  {TYPE} * {NAME} = NULL;
  jerry_length_t {NAME}_byteLength = 0;
  jerry_length_t {NAME}_byteOffset = 0;
  jerry_value_t {NAME}_buffer;
  if(jerry_value_is_typedarray({JVAL}))
  {{
    {NAME}_buffer = jerry_get_typedarray_buffer ({JVAL}, &{NAME}_byteOffset, &{NAME}_byteLength);
    {NAME} = ({TYPE}*)malloc({NAME}_byteLength);
    if({NAME} == NULL)
    {{
      jerry_release_value({NAME}_buffer);
      return jerry_create_error(JERRY_ERROR_COMMON, (const jerry_char_t*)"Fail to allocate memory.");
    }}
    jerry_arraybuffer_read({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
  }}
'''

JS_FREE_POINTER = '''
  if(jerry_value_is_typedarray({JVAL}))
  {{
    jerry_arraybuffer_write({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
    jerry_release_value({NAME}_buffer);
    free({NAME});
  }}
'''

JS_CREATE_BUFFER = '''
  jerry_value_t {NAME};
  if({FROM} != NULL)
  {{
    jerry_length_t {NAME}_byteLength = sizeof({TYPE});
    jerry_value_t {NAME}_buffer = jerry_create_arraybuffer({NAME}_byteLength);
    jerry_arraybuffer_write({NAME}_buffer, 0, (uint8_t*){FROM}, {NAME}_byteLength);
    {NAME} = jerry_create_typedarray_for_arraybuffer_sz (JERRY_TYPEDARRAY_{ARRAY_TYPE}, {NAME}_buffer, 0, 1);
    jerry_release_value({NAME}_buffer);
  }}
  else
  {{
    {NAME} = jerry_create_null();
  }}
'''

C_NATIVE_CALL = '''
  {RETURN}{RESULT}{NATIVE}({PARAM});
'''

JS_CREATE_VAL = '''
  jerry_value_t {NAME} = jerry_create_{TYPE}({FROM});
'''

JS_CREATE_CHAR = '''
  jerry_value_t {NAME} = jerry_create_string_sz((jerry_char_t*)(&({FROM})), 1);
'''

JS_CREATE_STRING = '''
  jerry_value_t {NAME} = jerry_create_string((jerry_char_t*){FROM});
'''

JS_GET_PROP = '''
  jerry_value_t {NAME}_{MEM}_name = jerry_create_string ((const jerry_char_t *) "{MEM}");
  jerry_value_t {NAME}_{MEM}_value = jerry_get_property ({OBJ}, {NAME}_{MEM}_name);
  jerry_release_value({NAME}_{MEM}_name);

  if(!jerry_value_is_undefined({NAME}_{MEM}_value))
  {{
    {GET_VAl}
    {STRUCT}.{MEM} = {NAME}_{MEM};
  }}
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

INIT_REGIST_ENUM = '''  REGIST_ENUM(object, {ENUM});
'''

INIT_REGIST_VALUE = '''  REGIST_VALUE(object, {NAME}, {NAME}_getter);
'''

INIT_REGIST_CONST = '''  REGIST_CONST(object, {NAME}, {NAME}_js);
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


class AST_Visitor(c_ast.NodeVisitor):
    def __init__(self):
        self.structdefs = []
        self.structdecls = []
        self.enumnames = []

    def visit_Struct(self, node):
        if node.decls is None:
            self.structdecls.append(node)
        else:
            self.structdefs.append(node)
        for c in node:
            self.visit(c)

    def visit_Union(self, node):
        if node.decls is None:
            self.structdecls.append(node)
        else:
            self.structdefs.append(node)
        for c in node:
            self.visit(c)

    def visit_Enumerator(self, node):
        if not node.name in self.enumnames:
            self.enumnames.append(node.name)


def get_typedefs(ast):
    typedefs = []

    for decl in ast.ext:
        if type(decl) is c_ast.Typedef:
            typedefs.append(decl)

    return typedefs


def get_functions_and_decls(ast, api_headers):
    funcs = []
    decls = []

    for decl in ast.ext:
        if (type(decl) is c_ast.Decl and
            decl.coord.file in api_headers):
            if type(decl.type) is c_ast.FuncDecl:
                funcs.append(decl)
            elif decl.name:
                decls.append(decl)

    return funcs, decls


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


def create_c_type_value(c_type, jval, funcname, name, is_pointer):
    if c_type == C_BOOL_TYPE:
        if is_pointer:
            sys.exit('Not supported type: (_Bool *)')

        return JS_GET_BOOL.format(NAME=name, JVAL=jval)

    elif c_type in C_NUMBER_TYPES:
        if is_pointer:
            check_type = JS_CHECK_TYPES.format(TYPE1='typedarray', TYPE2='null',
                                               JVAL=jval, FUNC=funcname)
            get_type = JS_GET_POINTER.format(TYPE=c_type, NAME=name, JVAL=jval)
        else:
            check_type = JS_CHECK_TYPE.format(TYPE='number', JVAL=jval,
                                              FUNC=funcname)
            get_type = JS_GET_NUM.format(TYPE=c_type, NAME=name, JVAL=jval)

    elif c_type == C_CHAR_TYPES:
        if is_pointer:
            check_type = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval,
                                              FUNC=funcname)
            get_type = JS_GET_STRING.format(NAME=name, JVAL=jval)
        else:
            check_type = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval,
                                              FUNC=funcname)
            get_type = JS_GET_CHAR.format(NAME=name, JVAL=jval)

    return check_type + get_type


def create_js_type_value(c_type, name, cval, is_pointer):
    if c_type == C_VOID_TYPE:
        if is_pointer:
            sys.exit('Not supported type: (void *)')

        result = JS_CREATE_VAL.format(NAME=name, TYPE='undefined', FROM='')

    elif c_type == C_BOOL_TYPE:
        if is_pointer:
            sys.exit('Not supported type: (_Bool *)')

        result = JS_CREATE_VAL.format(NAME=name, TYPE='boolean', FROM=cval)

    elif c_type in C_NUMBER_TYPES:
        if is_pointer:
            array_type = C_NUMBER_TYPES[c_type]
            result = JS_CREATE_BUFFER.format(NAME=name, FROM=cval, TYPE=c_type,
                                             ARRAY_TYPE=array_type)

        else:
            result = JS_CREATE_VAL.format(NAME=name, TYPE='number', FROM=cval)

    elif c_type == C_CHAR_TYPES:
        if is_pointer:
            result = JS_CREATE_STRING.format(NAME=name, FROM=cval)

        else:
            result = JS_CREATE_CHAR.format(NAME=name, FROM=cval)

    return result


def clang_generate_c_values(node, jval, funcname, name, index):
    result = None
    check_type_str = None
    get_type = None
    buffers_to_free = []

    node_type = node.node_type
    node_declaration = node_type.get_declaration()
    node_declaration_kind = node_declaration.node_kind

    if node_declaration_kind.is_struct_decl() or node_declaration_kind.is_union_decl():
        struct_members = []
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

        for field in struct_decl.field_decls:
            member_name = struct_name + '_' + field.name
            member_val = member_name + '_value'
            struct_members.append(member_name)

            getval, buffers = clang_generate_c_values(field,
                                                      member_val,
                                                      funcname,
                                                      member_name,
                                                      index)

            buffers_to_free += buffers

            result += JS_GET_PROP.format(NAME=struct_name,
                                         MEM=field.name,
                                         OBJ=jval,
                                         GET_VAl=getval)

            if node_declaration_kind.is_union_decl():
                break

        result += C_NATIVE_STRUCT.format(TYPE=struct_type,
                                         NAME=name,
                                         MEM=(',').join(struct_members))

        return result, buffers_to_free

    elif node_type.is_pointer() or node_type.is_array():
        if node_type.is_pointer():
            pointee_type = node_type.get_pointee_type()
        else:
            # Array
            pointee_type = node_type.get_array_type()

        if pointee_type.is_char():
            check_type = JS_CHECK_TYPE.format(TYPE='string', JVAL=jval, FUNC=funcname)
            get_type = JS_GET_STRING.format(NAME=name, JVAL=jval)
            result = check_type + get_type

        elif pointee_type.is_number():
            check_type = JS_CHECK_TYPES.format(TYPE1='typedarray',
                                               TYPE2='null',
                                               JVAL=jval,
                                               FUNC=funcname)

            get_type = JS_GET_POINTER.format(TYPE=pointee_type.type_name, NAME=name, JVAL=jval)

            result = check_type + get_type

            buffers_to_free.append(JS_FREE_POINTER.format(NAME=name, JVAL=jval))
        else:
            raise NotImplementedError('Unhandled pointer/array type: \'{}\' .'.format(node_type.type_name))

        return result, buffers_to_free


    elif node_type.is_bool():
        check_type_str = 'boolean'
        get_type = JS_GET_BOOL.format(NAME=name, JVAL=jval)
    elif node_type.is_number():
        check_type_str = 'number'
        get_type = JS_GET_NUM.format(TYPE=node_type.type_name, NAME=name, JVAL=jval)
    elif node_type.is_char():
        check_type_str = 'string'
        get_type = JS_GET_CHAR.format(NAME=name, JVAL=jval)
    elif node_type.is_enum():
        check_type_str = 'number'
        get_type = JS_GET_NUM.format(TYPE='int', NAME=name, JVAL=jval)

    else:
        raise NotImplementedError('\'{}\' handling is not implemented yet.'.format(node_type.type_name))

    check_type = JS_CHECK_TYPE.format(TYPE=check_type_str, JVAL=jval, FUNC=funcname)

    result = check_type + get_type
    return result, buffers_to_free


def generate_c_values(node, jval, funcname, name, index='0'):
    result = ''
    buffers_to_free = []
    is_pointer = False

    if (type(node.type) is c_ast.PtrDecl or
        type(node.type) is c_ast.ArrayDecl):
        is_pointer = True
        node = node.type

    if type(node.type) is not c_ast.TypeDecl:
        sys.exit('Not supported type: {}'.format(node.coord))
    else:
        if type(node.type.type) is c_ast.IdentifierType:
            nodetype = (' ').join(node.type.type.names)
            if nodetype != C_VOID_TYPE:
                result = create_c_type_value(nodetype, jval, funcname, name, is_pointer)
                if is_pointer and nodetype in C_NUMBER_TYPES:
                    buffers_to_free.append(JS_FREE_POINTER.format(NAME=name,
                                                                  JVAL=jval))
            elif  is_pointer:
                sys.exit('Not supported type: (void *)')

        elif (type(node.type.type) is c_ast.Struct or
            type(node.type.type) is c_ast.Union):

            if is_pointer:
                sys.exit('Not supported type: {}'.format(node.coord))

            struct = node.type.type

            if struct.name is None:
                structname = node.type.declname + index
                structtype = node.type.declname
            elif type(struct) is c_ast.Struct:
                structname = struct.name + index
                structtype = 'struct ' + struct.name
            elif type(struct) is c_ast.Union:
                structname = struct.name + index
                structtype = 'union ' + struct.name

            result = JS_CHECK_TYPE.format(TYPE='object', JVAL=jval,
                                          FUNC=funcname)

            result += "  {TYPE} {NAME};".format(TYPE=structtype, NAME=name)

            for decl in struct:
                member_name = structname + '_' + decl.name
                member_val = member_name + '_value'

                getval, buffers = generate_c_values(decl, member_val, funcname,
                                                    member_name, index)

                buffers_to_free += buffers

                result += JS_GET_PROP.format(NAME=structname, MEM=decl.name,
                                             OBJ=jval, GET_VAl=getval, STRUCT=name)

                if type(struct) is c_ast.Union:
                    break

        elif type(node.type.type) is c_ast.Enum:
            result = create_c_type_value('int', jval, funcname, name, is_pointer)

        else:
            sys.exit('Not supported type: {}'.format(node.coord))

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
            mem_type, mem_val = clang_generate_js_value(field, member, member_js)
            result += mem_val

            result += JS_SET_PROP.format(NAME=struct_name,
                                         MEM=field.name,
                                         OBJ=name,
                                         JVAL=member_js)

        return struct_type, result

    elif node_type.is_pointer():
        pointee_type = node_type.get_pointee_type()
        pointee_type_name = pointee_type.type_name
        node_type_name = pointee_type_name + '*'

        if pointee_type.is_char():
            result = JS_CREATE_STRING.format(NAME=name, FROM=cval)
        elif pointee_type.is_number():
            array_type = C_NUMBER_TYPES[pointee_type_name]
            result = JS_CREATE_BUFFER.format(NAME=name,
                                             FROM=cval,
                                             TYPE=pointee_type_name,
                                             ARRAY_TYPE=array_type)
        else:
             raise NotImplementedError(
                       'Unhandled pointer type: \'{}\' .'.format(node_type.type_name))

        return node_type_name, result

    elif node_type.is_void():
        result = JS_CREATE_VAL.format(NAME=name, TYPE='undefined', FROM='')
    elif node_type.is_bool():
        result = JS_CREATE_VAL.format(NAME=name, TYPE='boolean', FROM=cvale)
    elif node_type.is_number():
        result = JS_CREATE_VAL.format(NAME=name, TYPE='number', FROM=cval)
    elif node_type.is_char():
        result = JS_CREATE_CHAR.format(NAME=name, FROM=cval)
    elif node_type.is_enum():
        node_type_name = 'int'
        result = JS_CREATE_VAL.format(NAME=name, TYPE='number', FROM=cval)
    else:
        raise NotImplementedError('\'{}\' return type handling is not implemented yet.'.format(node_type.type_name))

    return node_type_name, result

def generate_js_value(node, cval, name):
    nodetype = ''
    result = ''
    is_pointer = False

    if type(node.type) is c_ast.PtrDecl:
        is_pointer = True
        node = node.type

    if type(node.type) is not c_ast.TypeDecl:
        sys.exit('Not supported type: {}'.format(node.coord))
    else:
        if type(node.type.type) is c_ast.IdentifierType:
            nodetype = (' ').join(node.type.type.names)
            result = create_js_type_value(nodetype, name, cval, is_pointer)

        elif (type(node.type.type) is c_ast.Struct or
            type(node.type.type) is c_ast.Union):

            if is_pointer:
                sys.exit('Not supported type: {}'.format(node.coord))

            struct = node.type.type

            if struct.name is None:
                structname = node.type.declname
                nodetype = node.type.declname
            elif type(node.type.type) is c_ast.Struct:
                structname = struct.name
                nodetype = 'struct ' + struct.name
            elif type(node.type.type) is c_ast.Union:
                structname = struct.name
                nodetype = 'union ' + struct.name

            result = JS_CREATE_VAL.format(NAME=name, TYPE='object', FROM='')

            for decl in struct:
                member = cval + '.' + decl.name
                member_js = 'js_' + structname + '_' + decl.name
                mem_type, mem_val = generate_js_value(decl, member, member_js)
                result += mem_val

                result += JS_SET_PROP.format(NAME=structname, MEM=decl.name,
                                             OBJ=name, JVAL=member_js)

        elif type(node.type.type) is c_ast.Enum:
            nodetype = 'int'
            result = create_js_type_value(nodetype, name, cval, is_pointer)

        else:
            sys.exit('Not supported type: {}'.format(node.coord))

    if is_pointer:
        nodetype += '*'

    return nodetype, result


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
                    comment = JS_ARG_COMMENT.format(INDEX=index)
                    jerry_function.append(comment + result)
                else:
                    jerry_function[0] = JS_CHECK_ARG_COUNT.format(COUNT=0, FUNC=funcname)

        native_params = (', ').join(native_params)

        return_type, result = clang_generate_js_value(function, 'result', 'ret_val')

        if return_type == 'void':
            jerry_function.append(C_NATIVE_CALL.format(RETURN='',
                                                       RESULT='',
                                                       NATIVE=funcname,
                                                       PARAM=native_params))
        else:
            jerry_function.append(C_NATIVE_CALL.format(RETURN=return_type,
                                                       RESULT=' result = ',
                                                       NATIVE=funcname,
                                                       PARAM=native_params))

        jerry_function += buffers_to_free
        jerry_function.append(result)

        yield JS_FUNC_HANDLER.format(NAME=funcname,
                                     BODY=('\n').join(jerry_function))


def generate_jerry_functions(functions):
    for function in functions:
        funcname = function.name
        funcdecl = function.type
        paramlist = funcdecl.args
        jerry_function = []
        native_params = []
        buffers_to_free = []

        if paramlist:
            params = paramlist.params
            jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=len(params),
                                                            FUNC=funcname))

            for index, param in enumerate(params):
                index = str(index)
                result, buffers = generate_c_values(param, 'args_p['+index+']',
                                           funcname, 'arg_' + index, index)
                if result:
                    native_params.append('arg_' + index)
                    buffers_to_free += buffers
                    comment = JS_ARG_COMMENT.format(INDEX=index)
                    jerry_function.append(comment+result)
                else:
                    jerry_function[0] = JS_CHECK_ARG_COUNT.format(COUNT=0,
                                                                  FUNC=funcname)
        else:
            jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=0,
                                                            FUNC=funcname))

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

        jerry_function += buffers_to_free
        jerry_function.append(result)

        yield JS_FUNC.format(NAME=funcname + '_handler',
                             BODY=('\n').join(jerry_function))


def generate_c_source(header, api_headers, dirname):

    preproc_args = ['-Dbool=_Bool',
                    '-D__attribute__(x)=',
                    '-D__asm__(x)=',
                    '-D__restrict=restrict',
                    '-D__builtin_va_list=void']

    ast = parse_file(header, use_cpp=True, cpp_args=preproc_args)

    visitor = AST_Visitor()
    visitor.visit(ast)

    clang_visitor = ClangTranslationUnitVisitor(header, api_headers, preproc_args)
    clang_visitor.visit()

    functions, decls = get_functions_and_decls(ast, api_headers)
    typedefs = get_typedefs(ast)
    params = get_params(functions)

    resolve_typedefs(typedefs, typedefs)
    resolve_typedefs(typedefs, functions)
    resolve_typedefs(typedefs, params)
    resolve_typedefs(typedefs, decls)

    for structdef in visitor.structdefs:
        resolve_typedefs(typedefs, structdef.decls)
        for structdecl in visitor.structdecls:
            if structdef.name == structdecl.name:
                structdecl.decls = structdef.decls

    generated_source = [INCLUDE.format(HEADER=dirname + '_js_wrapper.h')]

    init_function = []

    if args.libclang:
        for jerry_function in clang_generate_jerry_functions(clang_visitor.function_decls):
            generated_source.append(jerry_function)

        for function in clang_visitor.function_decls:
            init_function.append(INIT_REGIST_FUNC.format(NAME=function.name))

        for decl in clang_visitor.enum_constant_decls:
            init_function.append(INIT_REGIST_ENUM.format(ENUM=decl.name))

    else:
        for jerry_function in generate_jerry_functions(functions):
            generated_source.append(jerry_function)

        for function in functions:
            init_function.append(INIT_REGIST_FUNC.format(NAME=function.name))

        for enumname in visitor.enumnames:
            init_function.append(INIT_REGIST_ENUM.format(ENUM=enumname))


    for decl in decls:
        name = decl.name
        if 'const' in decl.quals:
            type, result = generate_js_value(decl, name, name + '_js')
            init_function.append(result)
            init_function.append(INIT_REGIST_CONST.format(NAME=name))
        else:
            type, result = generate_js_value(decl, name, 'ret_val')
            generated_source.append(JS_FUNC.format(NAME=name + '_getter',
                                                   BODY=result))
            init_function.append(INIT_REGIST_VALUE.format(NAME=name))

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

    output_dir = fs.join(path.TOOLS_ROOT, 'generator_output')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    output_dir = fs.join(output_dir, dirname + '_module')

    if not fs.isdir(output_dir):
        os.mkdir(output_dir)

    lib_root, lib_name = search_for_lib(directory)

    header_file = fs.join(output_dir, dirname + '_js_wrapper.h')
    header_text, api_headers = generate_header(directory)

    with open(header_file, 'w') as h:
        h.write(header_text + MACROS)

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

    parser.add_argument('--libclang',
                        help='use libclang instead of pycparser',
                        action='store_true')

    args = parser.parse_args()

    generate_module(args.directory)
