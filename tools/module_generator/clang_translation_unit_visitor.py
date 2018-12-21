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

from clang.cindex import Config, Index, conf, CursorKind, TypeKind, \
    AccessSpecifier

# This class is a wrapper for the TypeKind and Type classes.
class ClangASTNodeType:
    char_type_kinds = [
        TypeKind.CHAR_U,
        TypeKind.CHAR16,
        TypeKind.CHAR32,
        TypeKind.CHAR_S,
        TypeKind.WCHAR
    ]

    number_type_kinds = [
        TypeKind.UCHAR,
        TypeKind.SCHAR,
        TypeKind.USHORT,
        TypeKind.UINT,
        TypeKind.ULONG,
        TypeKind.ULONGLONG,
        TypeKind.UINT128,
        TypeKind.SHORT,
        TypeKind.INT,
        TypeKind.LONG,
        TypeKind.LONGLONG,
        TypeKind.INT128,
        TypeKind.FLOAT,
        TypeKind.DOUBLE,
        TypeKind.LONGDOUBLE
    ]

    def __init__(self, clang_type):
        # We are only interested in the underlying canonical types.
        self._canonical_type = clang_type.get_canonical()
        self._type_name = clang_type.spelling

    @property
    def name(self):
        return self._type_name

    @property
    def canonical_name(self):
        return self._canonical_type.spelling

    def is_bool(self):
        return self._canonical_type.kind == TypeKind.BOOL

    def is_char(self):
        return self._canonical_type.kind in ClangASTNodeType.char_type_kinds

    def is_number(self):
        return self._canonical_type.kind in ClangASTNodeType.number_type_kinds

    def is_enum(self):
        return self._canonical_type.kind == TypeKind.ENUM

    def is_void(self):
        return self._canonical_type.kind == TypeKind.VOID

    def is_pointer(self):
        return (self._canonical_type.kind == TypeKind.POINTER or
                self._canonical_type.kind == TypeKind.CONSTANTARRAY or
                self._canonical_type.kind == TypeKind.INCOMPLETEARRAY)

    def is_array(self):
        return (self._canonical_type.kind == TypeKind.CONSTANTARRAY or
                self._canonical_type.kind == TypeKind.INCOMPLETEARRAY)

    def is_record(self):
        return self._canonical_type.kind == TypeKind.RECORD

    def is_function(self):
        return (self._canonical_type.kind == TypeKind.FUNCTIONPROTO or
                self._canonical_type.kind == TypeKind.FUNCTIONNOPROTO)

    def is_const(self):
        return self._canonical_type.is_const_qualified()

    def get_array_type(self):
        return ClangASTNodeType(self._canonical_type.get_array_element_type())

    def get_array_size(self):
        assert self.is_array()
        return self._canonical_type.element_count

    def get_pointee_type(self):
        if self.is_array():
            array_type = self._canonical_type.get_array_element_type()
            return ClangASTNodeType(array_type)
        if self.is_pointer():
            return ClangASTNodeType(self._canonical_type.get_pointee())

    def get_declaration(self):
        return ClangASTNode(self._canonical_type.get_declaration())

    def get_as_record_decl(self):
        assert (self.is_record())
        return ClangRecordDecl(self._canonical_type.get_declaration())


# This class is a wrapper for the Cursor type.
class ClangASTNode:
    def __init__(self, cursor):
        self._cursor = cursor
        self._type = ClangASTNodeType(cursor.type)
        self._kind = cursor.kind

    @property
    def name(self):
        return self._cursor.spelling

    @property
    def type(self):
        return self._type

    @property
    def kind(self):
        return self._kind

    def get_as_record_decl(self):
        assert (self.type.is_record())
        return ClangRecordDecl(self._cursor)

    def get_as_function(self):
        return ClangFunctionDecl(self._cursor)


# This class represents enum declarations in libclang.
class ClangEnumDecl:
    def __init__(self, cursor):
        self._enum_constant_decls = []

        for child in cursor.get_children():
            if child.kind == CursorKind.ENUM_CONSTANT_DECL:
                self._enum_constant_decls.append(child.spelling)

    @property
    def enums(self):
        return self._enum_constant_decls


# This class represents function declarations in libclang.
class ClangFunctionDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)

        if cursor.type.get_canonical().kind == TypeKind.POINTER:
            return_type = cursor.type.get_canonical().get_pointee().get_result()
        else:
            return_type = cursor.type.get_canonical().get_result()

        self._return_type = ClangASTNodeType(return_type)

        self._parm_decls = []
        if cursor.type.kind == TypeKind.TYPEDEF:
            children = cursor.type.get_declaration().get_children()
            function_arguments = [child for child in children
                                  if child.kind == CursorKind.PARM_DECL]
        else:
            function_arguments = cursor.get_arguments()

        for arg in function_arguments:
            arg = ClangASTNode(arg)
            if arg.type.is_const():
                arg.type.name = arg.type.name.replace('const ', '')
            self._parm_decls.append(arg)

    @property
    def return_type(self):
        return self._return_type

    @property
    def params(self):
        return self._parm_decls


# This class represents macro definitions in libclang.
# TokenKinds:
#    'PUNCTUATION' = 0
#    'KEYWORD' = 1
#    'IDENTIFIER' = 2
#    'LITERAL' = 3
#    'COMMENT' = 4
class ClangMacroDef(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)

        self.tokens = []
        self.token_kinds = []
        for token in cursor.get_tokens():
            self.tokens.append(token.spelling)
            self.token_kinds.append(token.kind.value)

    @property
    def content(self):
        return (' ').join(self.tokens[1:])

    def is_char(self):
        if (self.token_kinds == [2, 3] and # "#define CH 'a'" like macros
            "'" in self.tokens[1]): # char literal
                return True
        return False

    def is_string(self):
        if (self.token_kinds == [2, 3] and # '#define STR "abc"' like macros
            '"' in self.tokens[1]): # string literal
                return True
        return False

    # macro contains only number literals and punctuations
    def is_number(self):
        if (self.content and
            not [x for x in self.token_kinds[1:] if x in [1, 2, 4]] and
            "'" not in self.content and '"' not in self.content):
            return True
        return False

    def is_valid(self):
        return self.is_char() or self.is_string() or self.is_number()

    def is_function(self):
        return conf.lib.clang_Cursor_isMacroFunctionLike(self._cursor)


class ClangRecordConstructor:
    def __init__(self, cursor_list):

        self._parm_decls = {}
        for cursor in cursor_list:
            arguments = list(cursor.get_arguments())
            param_lists = [arguments]

            # handle default arguments
            for arg in reversed(arguments):
                if '=' in [t.spelling for t in arg.get_tokens()]:
                    arguments = arguments[:-1]
                    param_lists.append(arguments)

            for param_list in param_lists:
                params = []
                for param in param_list:
                    param = ClangASTNode(param)
                    if param.type.is_const():
                        param.type.name = param.type.name.replace('const ', '')
                    params.append(param)
                if len(param_list) in self._parm_decls:
                    self._parm_decls[len(param_list)].append(params)
                else:
                    self._parm_decls[len(param_list)] = [params]


    @property
    def params(self):
        return self._parm_decls


class ClangRecordMethod(ClangRecordConstructor):
    def __init__(self, name, cursor_list):
        ClangRecordConstructor.__init__(self, cursor_list)

        self._method_name = name
        return_type = cursor_list[0].type.get_canonical().get_result()
        self._return_type = ClangASTNodeType(return_type)

    @property
    def name(self):
        return self._method_name

    @property
    def return_type(self):
        return self._return_type


# This class represents struct/union/class declarations in libclang.
class ClangRecordDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)

        self._field_decls = []
        self._has_default_constructor = False
        self._has_copy_constructor = False

        constructors = []
        methods = {}
        for child in cursor.get_children():
            if child.access_specifier == AccessSpecifier.PUBLIC:
                if child.kind == CursorKind.CONSTRUCTOR:
                    if child.is_default_constructor():
                        self._has_default_constructor = True
                    if child.is_copy_constructor():
                        self._has_copy_constructor = True
                    constructors.append(child)
                if child.kind == CursorKind.FIELD_DECL:
                    self._field_decls.append(ClangASTNode(child))
                if child.kind == CursorKind.CXX_METHOD:
                    if child.spelling in methods:
                        methods[child.spelling].append(child)
                    else:
                        methods[child.spelling] = [child]

        if not constructors:
            self._has_default_constructor = True
        self._constructor = ClangRecordConstructor(constructors)
        self._methods = [ClangRecordMethod(k, v) for k, v in methods.items()]

    @property
    def name(self):
        if self._cursor.spelling:
            return self._cursor.spelling
        else:
            return self.type.name

    @property
    def constructor(self):
        return self._constructor

    def has_default_constructor(self):
        return self._has_default_constructor

    def has_copy_constructor(self):
        return self._has_copy_constructor

    @property
    def field_decls(self):
        return self._field_decls

    @property
    def methods(self):
        return self._methods


# This class responsible for initializing and visiting
# the AST provided by libclang.
class ClangTUVisitor:
    def __init__(self, lang, header, api_headers, args):
        # TODO: Avoid hard-coding paths and args in general.
        Config.set_library_file('libclang-5.0.so.1')
        index = Index.create()

        self.is_cpp = True if lang == 'c++' else False
        self.clang_args = ['-x', lang, '-I/usr/include/clang/5.0/include/']
        self.translation_unit = index.parse(header, args + self.clang_args,
                                            options=1)
        self.api_headers = api_headers
        self.enum_constant_decls = []
        self.function_decls = []
        self.var_decls = []
        self.macro_defs = []
        self.record_decls = []

    def visit(self):
        children = self.translation_unit.cursor.get_children()

        cpp_funcs = {}
        for cursor in children:
            if (cursor.location.file != None and
                cursor.location.file.name in self.api_headers):

                if cursor.kind == CursorKind.ENUM_DECL:
                    self.enum_constant_decls.append(ClangEnumDecl(cursor))

                elif cursor.kind == CursorKind.FUNCTION_DECL:
                    if self.is_cpp:
                        if cursor.spelling in cpp_funcs:
                            cpp_funcs[cursor.spelling].append(cursor)
                        else:
                            cpp_funcs[cursor.spelling] = [cursor]
                    else:
                        self.function_decls.append(ClangFunctionDecl(cursor))

                elif cursor.kind == CursorKind.VAR_DECL:
                    self.var_decls.append(ClangASTNode(cursor))

                elif cursor.kind == CursorKind.MACRO_DEFINITION:
                    self.macro_defs.append(ClangMacroDef(cursor))

                elif (cursor.kind == CursorKind.CLASS_DECL or
                      cursor.kind == CursorKind.STRUCT_DECL or
                      cursor.kind == CursorKind.UNION_DECL):
                    self.record_decls.append(ClangRecordDecl(cursor))

        if self.is_cpp:
            for name, cursor_list in cpp_funcs.items():
                self.function_decls.append(ClangRecordMethod(name, cursor_list))

        # Resolve other macros in macro definition
        for first in self.macro_defs:
            for second in self.macro_defs:
                for i, token in enumerate(second.tokens):
                    if i and first.name == token:
                        second.tokens = (second.tokens[:i] +
                                          first.tokens[1:] +
                                          second.tokens[i+1:])
                        second.token_kinds = (second.token_kinds[:i] +
                                               first.token_kinds[1:] +
                                               second.token_kinds[i+1:])


class ClangTUChecker:

    valid_types = [
    #void
    TypeKind.VOID,
    # char
    TypeKind.CHAR_U, # valid pointer types
    TypeKind.UCHAR,
    TypeKind.CHAR16,
    TypeKind.CHAR32,
    TypeKind.CHAR_S,
    TypeKind.SCHAR,
    TypeKind.WCHAR,
    # number
    TypeKind.USHORT,
    TypeKind.UINT,
    TypeKind.ULONG,
    TypeKind.ULONGLONG,
    TypeKind.UINT128,
    TypeKind.SHORT,
    TypeKind.INT,
    TypeKind.LONG,
    TypeKind.LONGLONG,
    TypeKind.INT128,
    TypeKind.FLOAT,
    TypeKind.DOUBLE,
    TypeKind.LONGDOUBLE, # valid pointer types end
    # enum
    TypeKind.ENUM,
    # _Bool
    TypeKind.BOOL
    ]

    function_types = [
    TypeKind.FUNCTIONNOPROTO,
    TypeKind.FUNCTIONPROTO
    ]

    def __init__(self, header, api_headers, check_all):
        # TODO: Avoid hard-coding paths and args in general.
        Config.set_library_file('libclang-5.0.so.1')
        index = Index.create()

        # TODO: C++ needs a different configuration (-x C++).
        self.clang_args = ['-x', 'c', '-I/usr/include/clang/5.0/include/']
        self.translation_unit = index.parse(header, self.clang_args, options=1)

        self.api_headers = api_headers
        self.check_all = check_all

        self.OK = '\033[92m'
        self.WARN = '\033[91m'
        self.ENDC = '\033[00m'

    def check(self):
        children = [c for c in self.translation_unit.cursor.get_children()
                    if (c.location.file != None and
                        c.location.file.name in self.api_headers)]

        macros = [ClangMacroDef(macro) for macro in children
                  if macro.kind == CursorKind.MACRO_DEFINITION]

        for first in macros:
            for second in macros:
                for i, token in enumerate(second.tokens):
                    if i and first.name == token:
                        second.tokens = (second.tokens[:i] +
                                          first.tokens[1:] +
                                          second.tokens[i+1:])
                        second.token_kinds = (second.token_kinds[:i] +
                                               first.token_kinds[1:] +
                                               second.token_kinds[i+1:])

        for macro in macros:
            location = (macro._cursor.location.file.name +
                        ':' + str(macro._cursor.location.line) +
                        ':' + str(macro._cursor.location.column) + '\n')
            if not macro.is_valid():
                print (self.WARN + 'Unsupported macro' + self.ENDC + ': ' +
                       macro.name + '\nat ' + location)
            elif self.check_all:
                print (self.OK + 'Supported macro' + self.ENDC + ': ' +
                       macro.name + '\nat ' + location)

        for cursor in children:
            msg = ''
            location = (cursor.location.file.name +
                        ':' + str(cursor.location.line) +
                        ':' + str(cursor.location.column) + '\n')
            if cursor.kind == CursorKind.FUNCTION_DECL:
                is_ok, msg = self.check_func(cursor)
                if not is_ok:
                    print (self.WARN + 'Unsupported function' + self.ENDC + ': '
                           + cursor.spelling + '() ' + '\nat ' + location + msg)
                elif self.check_all:
                    print (self.OK + 'Supported function' + self.ENDC + ': ' +
                           cursor.spelling + '() ' + '\nat ' + location + msg)
            elif cursor.kind == CursorKind.VAR_DECL:
                if cursor.type.get_canonical().kind == TypeKind.RECORD:
                    cursor_type = cursor.type.get_canonical().get_declaration()
                    is_ok, msg = self.check_record(cursor_type)
                else:
                    is_ok = self.check_type(cursor.type)

                if not is_ok:
                    print (self.WARN + 'Unsupported variable' + self.ENDC + ': '
                           + cursor.type.spelling + ' ' + cursor.spelling +
                           '\nat ' + location + msg)
                elif self.check_all:
                    print (self.OK + 'Supported variable' + self.ENDC + ': ' +
                           cursor.type.spelling + ' ' + cursor.spelling +
                           '\nat ' + location + msg)

    def check_type(self, cursor_type):
        cursor_type = cursor_type.get_canonical()
        if cursor_type.kind == TypeKind.POINTER:
            if cursor_type.get_pointee().kind not in self.valid_types[1:21]:
                return False
        elif cursor_type.kind == TypeKind.CONSTANTARRAY:
            if cursor_type.element_type.kind not in self.valid_types[1:21]:
                return False
        elif cursor_type.kind not in self.valid_types:
            return False
        return True

    def check_func(self, cursor):
        message = ''
        param_is_ok = True

        if cursor.type.get_canonical().kind == TypeKind.POINTER:
            return_type = cursor.type.get_canonical().get_pointee().get_result()
        else:
            return_type = cursor.type.get_canonical().get_result()

        record_msg = ''
        if return_type.get_canonical().kind == TypeKind.RECORD:
            decl = return_type.get_canonical().get_declaration()
            ret_is_ok, record_msg = self.check_record(decl)
        else:
            ret_is_ok = self.check_type(return_type)

        if not ret_is_ok:
            message += (self.WARN + 'Unsupported return type' + self.ENDC +
                        ': ' + return_type.spelling + '\n' + record_msg)

        if cursor.type.kind == TypeKind.TYPEDEF:
            function_children = cursor.type.get_declaration().get_children()
        else:
            function_children = cursor.get_children()

        for child in function_children:
            msg = ''
            is_ok = True
            child_type = child.type.get_canonical()
            if child.kind == CursorKind.PARM_DECL:
                if child_type.kind == TypeKind.RECORD:
                    is_ok, msg = self.check_record(child_type.get_declaration())
                elif (child_type.kind in self.function_types or
                      child_type.get_pointee().kind in self.function_types):
                      is_ok, msg = self.check_func(child)
                else:
                    if not self.check_type(child.type):
                        is_ok = False

                if not is_ok:
                    param_is_ok = False
                    message += (self.WARN + 'Unsupported parameter type' +
                                self.ENDC + ': ' + child.type.spelling + '\n' +
                                msg)

        return (ret_is_ok and param_is_ok), message

    def check_record(self, cursor):
        message = ''
        record_is_ok = True

        for child in cursor.get_children():
            msg = ''
            is_ok = True
            child_type = child.type.get_canonical()
            if child.kind == CursorKind.FIELD_DECL:
                if child_type.kind == TypeKind.RECORD:
                    is_ok, msg = self.check_record(child_type.get_declaration())
                elif (child_type.kind in self.function_types or
                      child_type.get_pointee().kind in self.function_types):
                      is_ok, msg = self.check_func(child)
                else:
                    if not self.check_type(child.type):
                        is_ok = False

                if not is_ok:
                    record_is_ok = False
                    message += (self.WARN + 'Unsupported member type' +
                                self.ENDC + ': ' + child.type.spelling + '\n' +
                                msg)

        return record_is_ok, message
