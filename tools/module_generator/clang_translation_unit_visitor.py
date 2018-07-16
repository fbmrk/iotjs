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

        return ClangASTNodeType.visit_array(self)

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

        return ClangASTNodeType.visit_pointer(self)

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
        self._return_type = ClangASTNodeType(cursor.type.get_result())

        self._parm_decls = []
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
        self._is_char = False
        self._is_string = False
        self._is_number = False
        self._is_function_like = clang.cindex.conf.lib.clang_Cursor_isMacroFunctionLike(cursor)

        self._tokens = []
        self._token_kinds = []
        for token in cursor.get_tokens():
            self._tokens.append(token.spelling)
            self._token_kinds.append(token.kind.value)

        if self._token_kinds == [2, 3]: # '#define NUM 42' like macros
            literal = self._tokens[1]

            if "'" in literal: # char literal
                self._is_char = True
            elif '"' in literal: # string literal
                self._is_string = True
            else: # numeric literal
                self._is_number = True

        elif self._token_kinds == [2, 0, 3]: # '#define NUM -42' like macros
            punct = self._tokens[1]
            literal = self._tokens[2]

            if ((punct == '+' or punct == '-') and
            "'" not in literal and '"' not in literal): # numeric literal
                self._is_number = True

        elif self._token_kinds == [2, 3, 0, 3]: # '#define NUM 42 + 24' like macros
            literal = self._tokens[1] + self._tokens[3]

            if "'" not in literal and '"' not in literal: # numeric literal
                self._is_number = True

    @property
    def tokens(self):
        return self._tokens

    @property
    def token_kinds(self):
        return self._token_kinds

    def is_char(self):
        return self._is_char

    def is_string(self):
        return self._is_string

    def is_number(self):
        return self._is_number

    def is_function(self):
        return self._is_function_like


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
