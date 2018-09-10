#!/usr/bin/env python

# TODO: License, documentation etc.

import clang.cindex


# This class is a wrapper for the CursorKind type in the libclang python-bindings.
# See the definition here:
# https://github.com/llvm-mirror/clang/blob/26cac19a0d622afc91cd52a002921074bccc6a27/bindings/python/clang/cindex.py#L640
class ClangASTNodeKind:
    def __init__(self, cursor_kind):
        self._cursor_kind = cursor_kind

    def is_struct_decl(self):
        return self._cursor_kind == clang.cindex.CursorKind.STRUCT_DECL

    def is_union_decl(self):
        return self._cursor_kind == clang.cindex.CursorKind.UNION_DECL

    def is_function_decl(self):
        return self._cursor_kind == clang.cindex.CursorKind.FUNCTION_DECL


# This class is a wrapper for the TypeKind and Type classes in the libclang python-bindings.
# See the definitions here:
# https://github.com/llvm-mirror/clang/blob/26cac19a0d622afc91cd52a002921074bccc6a27/bindings/python/clang/cindex.py#L1936
# https://github.com/llvm-mirror/clang/blob/26cac19a0d622afc91cd52a002921074bccc6a27/bindings/python/clang/cindex.py#L2064
class ClangASTNodeType:
    char_type_kinds = [
        clang.cindex.TypeKind.CHAR_U,
        clang.cindex.TypeKind.UCHAR,
        clang.cindex.TypeKind.CHAR16,
        clang.cindex.TypeKind.CHAR32,
        clang.cindex.TypeKind.CHAR_S,
        clang.cindex.TypeKind.SCHAR,
        clang.cindex.TypeKind.WCHAR
    ]

    number_type_kinds = [
        clang.cindex.TypeKind.USHORT,
        clang.cindex.TypeKind.UINT,
        clang.cindex.TypeKind.ULONG,
        clang.cindex.TypeKind.ULONGLONG,
        clang.cindex.TypeKind.UINT128,
        clang.cindex.TypeKind.SHORT,
        clang.cindex.TypeKind.INT,
        clang.cindex.TypeKind.LONG,
        clang.cindex.TypeKind.LONGLONG,
        clang.cindex.TypeKind.INT128,
        clang.cindex.TypeKind.FLOAT,
        clang.cindex.TypeKind.DOUBLE,
        clang.cindex.TypeKind.LONGDOUBLE
    ]

    def __init__(self, clang_type):
        # We are only interested in the underlying canonical types.
        self._canonical_type = clang_type.get_canonical()
        self._type_name = clang_type.spelling

    @property
    def type_name(self):
        return self._type_name

    @property
    def builtin_type_name(self):
        return self._canonical_type.spelling

    def is_bool(self):
        return self._canonical_type.kind == clang.cindex.TypeKind.BOOL

    def is_char(self):
        return self._canonical_type.kind in ClangASTNodeType.char_type_kinds

    def is_number(self):
        return self._canonical_type.kind in ClangASTNodeType.number_type_kinds

    def is_enum(self):
        return self._canonical_type.kind == clang.cindex.TypeKind.ENUM

    def is_void(self):
        return self._canonical_type.kind == clang.cindex.TypeKind.VOID

    def is_builtin(self):
        return (self.is_bool() or self.is_char() or self.is_number())

    def is_pointer(self):
        return self._canonical_type.kind == clang.cindex.TypeKind.POINTER

    def is_array(self):
        return (self._canonical_type.kind == clang.cindex.TypeKind.CONSTANTARRAY or
                self._canonical_type.kind == clang.cindex.TypeKind.INCOMPLETEARRAY)

    def is_func(self):
        return self._canonical_type.kind == clang.cindex.TypeKind.FUNCTIONPROTO

    def is_const(self):
        return self._canonical_type.is_const_qualified()

    # Resolves all array dimensions recursively and returns with the underlying element type.
    @staticmethod
    def visit_array(clang_ast_type):
        if clang_ast_type.is_array():
            clang_ast_type = ClangASTNodeType(clang_ast_type._canonical_type.element_type)
            element_type, count = ClangASTNodeType.visit_array(clang_ast_type)
            return element_type, count + 1
        else:
            return clang_ast_type, 0

    def get_array_type(self):
        assert self.is_array()

        return ClangASTNodeType(self._canonical_type.element_type)

    def get_array_size(self):
        assert self.is_array()

        return self._canonical_type.element_count

    # Resolves all pointers recursively and returns with the underlying final pointee.
    @staticmethod
    def visit_pointer(clang_ast_type):
        if clang_ast_type.is_pointer():
            clang_ast_type = ClangASTNodeType(clang_ast_type._canonical_type.get_pointee())
            pointee_type, count = ClangASTNodeType.visit_pointer(clang_ast_type)
            return pointee_type, count + 1
        else:
            return clang_ast_type, 0

    def get_pointee_type(self):
        assert self.is_pointer()

        return ClangASTNodeType(self._canonical_type.get_pointee())

    def get_declaration(self):
        decl = self._canonical_type.get_declaration()
        return ClangASTNode(decl)


# This class is a wrapper for the Cursor type in the libclang python-bindings.
# See the definition here:
# https://github.com/llvm-mirror/clang/blob/26cac19a0d622afc91cd52a002921074bccc6a27/bindings/python/clang/cindex.py#L1394
class ClangASTNode:
    def __init__(self, cursor):
        self._cursor = cursor
        self._type = ClangASTNodeType(cursor.type)
        self._kind = ClangASTNodeKind(cursor.kind)

    @property
    def name(self):
        return self._cursor.spelling

    @property
    def node_type(self):
        return self._type

    @property
    def node_kind(self):
        return self._kind

    def get_as_struct_or_union_decl(self):
        assert (self.node_kind.is_struct_decl() or
                self.node_kind.is_union_decl())
        return ClangStructOrUnionDecl(self._cursor)

    def get_as_function(self):
        return ClangFunctionDecl(self._cursor)


# This class represents enum declarations in libclang.
class ClangEnumDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)
        self._enum_constant_decls = []

        children = list(cursor.get_children())
        for child in children:
            if child.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
                self._enum_constant_decls.append(child.spelling)

    @property
    def enums(self):
        return self._enum_constant_decls


# This class represents function declarations in libclang.
class ClangFunctionDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)

        if self.node_type.is_pointer():
            self._return_type = ClangASTNodeType(cursor.type.get_canonical().get_pointee().get_result())
        else:
            self._return_type = ClangASTNodeType(cursor.type.get_canonical().get_result())

        self._parm_decls = []
        if cursor.type.kind == clang.cindex.TypeKind.TYPEDEF:
            function_children = list(cursor.type.get_declaration().get_children())
        else:
            function_children = list(cursor.get_children())

        for child in function_children:
            if child.kind == clang.cindex.CursorKind.PARM_DECL:
                self._parm_decls.append(ClangFunctionParameterDecl(child))

    @property
    def return_type(self):
        return self._return_type

    @property
    def params(self):
        return self._parm_decls


# This class represents function parameter declarations in libclang.
class ClangFunctionParameterDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)


# This class represents funcion/union declarations in libclang.
class ClangStructOrUnionDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)

        self._field_decls = []
        children = list(cursor.get_children())
        for child in children:
            if child.kind == clang.cindex.CursorKind.FIELD_DECL:
                self._field_decls.append(ClangFieldDecl(child))

    @property
    def field_decls(self):
        return self._field_decls



# This class represents funcion/union/class field declarations in libclang.
class ClangFieldDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)


# This class represents variable declarations in libclang.
class ClangVarDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)


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

    def is_number(self):
        if (self.content and # has content
            not [x for x in self.token_kinds[1:] if x in [1, 2, 4]] and # macro contains only literals and punctuations
            "'" not in self.content and '"' not in self.content): # there are no char and string literals
            return True
        return False

    def is_valid(self):
        return self.is_char() or self.is_string() or self.is_number()

    def is_function(self):
        return clang.cindex.conf.lib.clang_Cursor_isMacroFunctionLike(self._cursor)


# This class responsible for initializing and visiting the AST provided by libclang.
class ClangTranslationUnitVisitor:
    def __init__(self, header, api_headers, args):
        # TODO: Avoid hard-coding paths and args in general.
        clang.cindex.Config.set_library_file('libclang-5.0.so.1')
        index = clang.cindex.Index.create()

        # TODO: C++ needs a different configuration (-x C++).
        self.clang_args = ['-x', 'c', '-I/usr/include/clang/5.0/include/']
        self.translation_unit = index.parse(header, args + self.clang_args, options=1)

        self.api_headers = api_headers

        self.enum_constant_decls = []
        self.function_decls = []
        self.var_decls = []
        self.macro_defs = []

    def visit(self):
        children = list(self.translation_unit.cursor.get_children())

        for cursor in children:
            if cursor.kind == clang.cindex.CursorKind.ENUM_DECL:
                self.enum_constant_decls.append(ClangEnumDecl(cursor))

            elif (cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL and
                cursor.location.file != None and
                cursor.location.file.name in self.api_headers):
                self.function_decls.append(ClangFunctionDecl(cursor))

            elif (cursor.kind == clang.cindex.CursorKind.VAR_DECL and
                cursor.location.file != None and
                cursor.location.file.name in self.api_headers):
                self.var_decls.append(ClangVarDecl(cursor))

            elif (cursor.kind == clang.cindex.CursorKind.MACRO_DEFINITION and
                cursor.location.file != None and
                cursor.location.file.name in self.api_headers):
                self.macro_defs.append(ClangMacroDef(cursor))

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


class ClangTranslationUnitChecker:

    valid_types = [
    #void
    clang.cindex.TypeKind.VOID,
    # char
    clang.cindex.TypeKind.CHAR_U, # valid pointer types
    clang.cindex.TypeKind.UCHAR,
    clang.cindex.TypeKind.CHAR16,
    clang.cindex.TypeKind.CHAR32,
    clang.cindex.TypeKind.CHAR_S,
    clang.cindex.TypeKind.SCHAR,
    clang.cindex.TypeKind.WCHAR,
    # number
    clang.cindex.TypeKind.USHORT,
    clang.cindex.TypeKind.UINT,
    clang.cindex.TypeKind.ULONG,
    clang.cindex.TypeKind.ULONGLONG,
    clang.cindex.TypeKind.UINT128,
    clang.cindex.TypeKind.SHORT,
    clang.cindex.TypeKind.INT,
    clang.cindex.TypeKind.LONG,
    clang.cindex.TypeKind.LONGLONG,
    clang.cindex.TypeKind.INT128,
    clang.cindex.TypeKind.FLOAT,
    clang.cindex.TypeKind.DOUBLE,
    clang.cindex.TypeKind.LONGDOUBLE, # valid pointer types end
    # enum
    clang.cindex.TypeKind.ENUM,
    # _Bool
    clang.cindex.TypeKind.BOOL
    ]

    function_types = [
    clang.cindex.TypeKind.FUNCTIONNOPROTO,
    clang.cindex.TypeKind.FUNCTIONPROTO
    ]

    def __init__(self, header, api_headers, args, check_all):
        # TODO: Avoid hard-coding paths and args in general.
        clang.cindex.Config.set_library_file('libclang-5.0.so.1')
        index = clang.cindex.Index.create()

        # TODO: C++ needs a different configuration (-x C++).
        self.clang_args = ['-x', 'c', '-I/usr/include/clang/5.0/include/']
        self.translation_unit = index.parse(header, args + self.clang_args, options=1)

        self.api_headers = api_headers
        self.check_all = check_all

        self.OK = '\033[92m'
        self.WARN = '\033[91m'
        self.ENDC = '\033[00m'

    def check(self):
        children = [c for c in self.translation_unit.cursor.get_children()
                    if (c.location.file != None and
                        c.location.file.name in self.api_headers)]

        macros = [ClangMacroDef(macro) for macro in children if macro.kind == clang.cindex.CursorKind.MACRO_DEFINITION]

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
            if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                is_ok, msg = self.check_func(cursor)
                if not is_ok:
                    print (self.WARN + 'Unsupported function' + self.ENDC + ': '
                           + cursor.spelling + '() ' + '\nat ' + location + msg)
                elif self.check_all:
                    print (self.OK + 'Supported function' + self.ENDC+ ': ' +
                           cursor.spelling + '() ' + '\nat ' + location + msg)
            elif cursor.kind == clang.cindex.CursorKind.VAR_DECL:
                if cursor.type.get_canonical().kind == clang.cindex.TypeKind.RECORD:
                    is_ok, msg = self.check_record(cursor.type.get_canonical().get_declaration())
                else:
                    is_ok = self.check_type(cursor.type)

                if not is_ok:
                    print (self.WARN + 'Unsupported variable' + self.ENDC+ ': ' +
                           cursor.type.spelling + ' ' + cursor.spelling + '\nat ' + location + msg)
                elif self.check_all:
                    print (self.OK + 'Supported variable' + self.ENDC+ ': ' +
                           cursor.type.spelling + ' ' + cursor.spelling + '\nat ' + location + msg)

    def check_type(self, cursor_type):
        if cursor_type.get_canonical().kind == clang.cindex.TypeKind.POINTER:
            if cursor_type.get_canonical().get_pointee().kind not in ClangTranslationUnitChecker.valid_types[1:21]:
                return False
        elif cursor_type.get_canonical().kind == clang.cindex.TypeKind.CONSTANTARRAY:
            if cursor_type.get_canonical().element_type.kind not in ClangTranslationUnitChecker.valid_types[1:21]:
                return False
        elif cursor_type.get_canonical().kind not in ClangTranslationUnitChecker.valid_types:
            return False
        return True

    def check_func(self, cursor):
        message = ''
        param_is_ok = True

        if cursor.type.get_canonical().kind == clang.cindex.TypeKind.POINTER:
            return_type = cursor.type.get_canonical().get_pointee().get_result()
        else:
            return_type = cursor.type.get_canonical().get_result()

        record_msg = ''
        if return_type.get_canonical().kind == clang.cindex.TypeKind.RECORD:
            ret_is_ok, record_msg = self.check_record(return_type.get_canonical().get_declaration())
        else:
            ret_is_ok = self.check_type(return_type)

        if not ret_is_ok:
            message += (self.WARN + 'Unsupported return type' + self.ENDC +
                        ': ' + return_type.spelling + '\n' + record_msg)

        if cursor.type.kind == clang.cindex.TypeKind.TYPEDEF:
            function_children = list(cursor.type.get_declaration().get_children())
        else:
            function_children = list(cursor.get_children())

        for child in function_children:
            msg = ''
            is_ok = True
            if child.kind == clang.cindex.CursorKind.PARM_DECL:
                if child.type.get_canonical().kind == clang.cindex.TypeKind.RECORD:
                    is_ok, msg = self.check_record(child.type.get_canonical().get_declaration())
                elif (child.type.get_canonical().kind in ClangTranslationUnitChecker.function_types or
                      child.type.get_canonical().get_pointee().kind in ClangTranslationUnitChecker.function_types):
                      is_ok, msg = self.check_func(child)
                else:
                    if not self.check_type(child.type):
                        is_ok = False

                if not is_ok:
                    param_is_ok = False
                    message += (self.WARN + 'Unsupported parameter type' + self.ENDC +
                                ': ' + child.type.spelling + '\n' + msg)

        return (ret_is_ok and param_is_ok), message

    def check_record(self, cursor):
        message = ''
        record_is_ok = True

        for child in cursor.get_children():
            msg = ''
            is_ok = True
            if child.kind == clang.cindex.CursorKind.FIELD_DECL:
                if child.type.get_canonical().kind == clang.cindex.TypeKind.RECORD:
                    is_ok, msg = self.check_record(child.type.get_canonical().get_declaration())
                elif (child.type.get_canonical().kind in ClangTranslationUnitChecker.function_types or
                      child.type.get_canonical().get_pointee().kind in ClangTranslationUnitChecker.function_types):
                      is_ok, msg = self.check_func(child)
                else:
                    if not self.check_type(child.type):
                        is_ok = False

                if not is_ok:
                    record_is_ok = False
                    message += (self.WARN + 'Unsupported member type' + self.ENDC +
                                ': ' + child.type.spelling + '\n' + msg)

        return record_is_ok, message
