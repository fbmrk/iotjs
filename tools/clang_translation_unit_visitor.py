#!/usr/bin/env python

# TODO: License, documentation etc.

import clang.cindex



class ClangASTNode:
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

    def __init__(self, cursor):
        self._cursor = cursor
        self._cursor_type_kind = cursor.type.get_canonical().kind

    @property
    def name(self):
        return self._cursor.spelling

    @property
    def canonical_type_name(self):
        return self._cursor.type.get_canonical().spelling

    def is_bool(self):
        return self._cursor_type_kind == clang.cindex.TypeKind.BOOL

    def is_char(self):
        return self._cursor_type_kind in ClangASTNode.char_type_kinds

    def is_number(self):
        return self._cursor_type_kind in ClangASTNode.number_type_kinds

    def is_enum(self):
        return self._cursor_type_kind == clang.cindex.TypeKind.ENUM

    def is_builtin(self):
        return (self.is_bool() or self.is_char() or self.is_number())


class ClangEnumConstantDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)


class ClangFunctionDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)
        self._parm_decls = []
        self._canonical_return_type = cursor.type.get_result().get_canonical()

        function_children = list(cursor.get_children())
        for child in function_children:
            if child.kind == clang.cindex.CursorKind.PARM_DECL:
                self._parm_decls.append(ClangFunctionParameterDecl(child))

    @property
    def canonical_return_type_name(self):
        return self._canonical_return_type.spelling

    @property
    def params(self):
        return self._parm_decls

    def is_return_type_enum(self):
        return self._canonical_return_type.kind == clang.cindex.TypeKind.ENUM

    def is_return_type_void(self):
        return self._canonical_return_type.kind == clang.cindex.TypeKind.VOID

    def is_return_type_bool(self):
        return self._canonical_return_type.kind == clang.cindex.TypeKind.BOOL

    def is_return_type_char(self):
        return self._canonical_return_type.kind in ClangASTNode.char_type_kinds

    def is_return_type_number(self):
        return self._canonical_return_type.kind in ClangASTNode.number_type_kinds


class ClangFunctionParameterDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)



class ClangTranslationUnitVisitor:
    def __init__(self, header, api_headers, args):
        # TODO: Avoid hard-coding paths and args in general.
        clang.cindex.Config.set_library_file('libclang-5.0.so.1')
        index = clang.cindex.Index.create()
        self.clang_args = ['-x', 'c', '-I/usr/include/clang/5.0/include/']
        self.translation_unit = index.parse(header, args=args.append(self.clang_args))

        self.api_headers = api_headers

        self.enum_constant_decls = []
        self.function_decls = []

    def visit(self, cursor=None):
        if cursor is None:
            cursor = self.translation_unit.cursor

        if cursor.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
            decl = ClangEnumConstantDecl(cursor)
            self.enum_constant_decls.append(decl)

        if (cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL and
            cursor.location.file != None and
            cursor.location.file.name in self.api_headers):
            self.function_decls.append(ClangFunctionDecl(cursor))

        children = list(cursor.get_children())
        for child in children:
            self.visit(child)

