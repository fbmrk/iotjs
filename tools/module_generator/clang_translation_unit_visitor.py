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

    @property
    def type_name(self):
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
            element_type = ClangASTNodeType(clang_ast_type._canonical_type.element_type)
            return ClangASTNodeType.visit_array(element_type)
        else:
            return clang_ast_type

    def get_array_type(self):
        assert self.is_array()

        return ClangASTNodeType.visit_array(self)

    # Resolves all pointers recursively and returns with the underlying final pointee.
    @staticmethod
    def visit_pointer(clang_ast_type):
        if clang_ast_type.is_pointer():
            pointee_type = ClangASTNodeType(clang_ast_type._canonical_type.get_pointee())
            return ClangASTNodeType.visit_pointer(pointee_type)
        else:
            return clang_ast_type

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
class ClangEnumConstantDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)


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


# This class responsible for initializing and visiting the AST provided by libclang.
class ClangTranslationUnitVisitor:
    def __init__(self, header, api_headers, args):
        # TODO: Avoid hard-coding paths and args in general.
        clang.cindex.Config.set_library_file('libclang-5.0.so.1')
        index = clang.cindex.Index.create()

        # TODO: C++ needs a different configuration (-x C++).
        self.clang_args = ['-x', 'c', '-I/usr/include/clang/5.0/include/']
        self.translation_unit = index.parse(header, args=args.append(self.clang_args))

        self.api_headers = api_headers

        self.enum_constant_decls = []
        self.function_decls = []
        self.var_decls = []

    def visit(self, cursor=None):
        if cursor is None:
            cursor = self.translation_unit.cursor

        if cursor.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
            decl = ClangEnumConstantDecl(cursor)
            self.enum_constant_decls.append(decl)

        elif (cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL and
            cursor.location.file != None and
            cursor.location.file.name in self.api_headers):
            self.function_decls.append(ClangFunctionDecl(cursor))

        elif (cursor.kind == clang.cindex.CursorKind.VAR_DECL and
            cursor.location.file != None and
            cursor.location.file.name in self.api_headers):
            self.var_decls.append(ClangVarDecl(cursor))

        children = list(cursor.get_children())
        for child in children:
            self.visit(child)
