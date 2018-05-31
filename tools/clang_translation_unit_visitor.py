#!/usr/bin/env python

# TODO: License, documentation etc.

import clang.cindex


class ClangASTNode:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def name(self):
        return self._cursor.spelling


class ClangEnumConstantDecl(ClangASTNode):
    def __init__(self, cursor):
        ClangASTNode.__init__(self, cursor)


class ClangTranslationUnitVisitor:
    def __init__(self, header, args):
        # TODO: Avoid hard-coding paths and args in general.
        clang.cindex.Config.set_library_file('libclang-5.0.so.1')
        index = clang.cindex.Index.create()
        self.clang_args = ['-x', 'c', '-I/usr/include/clang/5.0/include/']
        self.translation_unit = index.parse(header, args=args.append(self.clang_args))
        self.enum_constant_decls = []

    def visit(self, cursor=None):
        if cursor is None:
            cursor = self.translation_unit.cursor

        if cursor.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
            decl = ClangEnumConstantDecl(cursor)
            self.enum_constant_decls.append(decl)

        children = list(cursor.get_children())
        for child in children:
            self.visit(child)

