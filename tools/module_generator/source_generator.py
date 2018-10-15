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

from source_templates import *

class CSourceGenerator:
    def __init__(self, visitor):
        self.visitor = visitor
        self.function_names = []
        self.variable_names = []
        self.constant_variables = []
        self.number_arrays = []


    # methods for create/set a C variable
    def js_to_char(self, type_name, name, jval):
        return JS_TO_CHAR.format(TYPE=type_name, NAME=name, JVAL=jval)

    def js_set_char(self, name, jval):
        return JS_SET_CHAR.format(NAME=name, JVAL=jval)

    def js_to_number(self, type_name, name, jval):
        return JS_TO_NUMBER.format(TYPE=type_name, NAME=name, JVAL=jval)

    def js_set_number(self, name, jval):
        return JS_SET_NUMBER.format(NAME=name, JVAL=jval)

    def js_to_bool(self, type_name, name, jval):
        return JS_TO_BOOL.format(TYPE=type_name, NAME=name, JVAL=jval)

    def js_set_bool(self, name, jval):
        return JS_SET_BOOL.format(NAME=name, JVAL=jval)

    def js_to_c(self, c_type, name, jval):
        if c_type.is_char():
            return self.js_to_char(c_type.name, name, jval)
        elif c_type.is_number() or c_type.is_enum():
            return self.js_to_number(c_type.name, name, jval)
        elif c_type.is_bool():
            return self.js_to_bool(c_type.name, name, jval)
        else:
            return JS_TO_UNSUPPORTED.format(TYPE=c_type.name, NAME=name)

    def js_set_c(self, c_type, name, jval):
        if c_type.is_char():
            return self.js_set_char(name, jval)
        elif c_type.is_number() or c_type.is_enum():
            return self.js_set_number(name, jval)
        elif c_type.is_bool():
            return self.js_set_bool(name, jval)
        else:
            return JS_TO_UNSUPPORTED.format(TYPE=c_type.name, NAME=name)

    def js_to_string(self, type_name, name, jval):
        return JS_TO_STRING.format(TYPE=type_name, NAME=name, JVAL=jval)

    def js_set_char_pointer(self, type_name, name, jval):
        return JS_SET_CHAR_PTR.format(TYPE=type_name, NAME=name, JVAL=jval)

    def js_set_char_array(self, name, jval, size):
        return JS_SET_CHAR_ARR.format(NAME=name, JVAL=jval, SIZE=size)

    def js_to_num_pointer(self, type_name, name, jval):
        return JS_TO_TYPEDARRAY.format(TYPE=type_name, NAME=name, JVAL=jval)

    def js_set_num_pointer(self, type_name, name, jval):
        return JS_SET_TYPEDARRAY.format(TYPE=type_name, NAME=name, JVAL=jval)

    def js_free_buffer(self, name, jval):
        return JS_FREE_BUFFER.format(NAME=name, JVAL=jval)

    def js_to_function(self, func, name, jval):
        return JS_TO_FUNCTION.format(FUNC=func, NAME=name, JVAL=jval)

    def js_to_pointer(self, c_type, name, jval):
        pointee_type = c_type.get_pointee_type()
        if pointee_type.is_char():
            return self.js_to_string(pointee_type.name, name, jval)
        elif pointee_type.is_number():
            return self.js_to_num_pointer(pointee_type.name, name, jval)
        else:
            return JS_TO_UNSUPPORTED.format(TYPE=c_type.name, NAME=name)

    def js_set_pointer(self, c_type, name, jval):
        pointee_type = c_type.get_pointee_type()
        if c_type.is_array():
            size = c_type.get_array_size() - 1
            if pointee_type.is_char():
                return self.js_set_char_array(name, jval, size)
            elif pointee_type.is_number():
                return self.js_to_num_pointer(pointee_type.name, name, jval)
            else:
                return JS_TO_UNSUPPORTED.format(TYPE=c_type.name, NAME=name)
        else:
            if pointee_type.is_char():
                return self.js_set_char_pointer(pointee_type.name, name, jval)
            elif pointee_type.is_number():
                return self.js_set_num_pointer(pointee_type.name, name, jval)
            else:
                return JS_TO_UNSUPPORTED.format(TYPE=c_type.name, NAME=name)


    # methods for create a JS variable
    def void_to_js(self, name):
        return JS_CREATE_VAL.format(NAME=name, TYPE='undefined', FROM='')

    def char_to_js(self, name, cval):
        return JS_CREATE_CHAR.format(NAME=name, FROM=cval)

    def number_to_js(self, name, cval):
        return JS_CREATE_VAL.format(NAME=name, TYPE='number', FROM=cval)

    def bool_to_js(self, name, cval):
        return JS_CREATE_VAL.format(NAME=name, TYPE='boolean', FROM=cval)

    def c_to_js(self, c_type, cval, name):
        if c_type.is_void():
            return self.void_to_js(name)
        elif c_type.is_char():
            return self.char_to_js(name, cval)
        elif c_type.is_number() or c_type.is_enum():
            return self.number_to_js(name, cval)
        elif c_type.is_bool():
            return self.bool_to_js(name, cval)
        else:
            return JS_CREATE_UNSUPPORTED.format(NAME=name, FROM=cval)

    def string_to_js(self, name, cval):
        return JS_CREATE_STRING.format(NAME=name, FROM=cval)

    def num_pointer_to_js(self, name, cval, type_name):
        return JS_CREATE_TYPEDARRAY.format(NAME=name, FROM=cval, TYPE=type_name,
                                           ARRAY_TYPE=TYPEDARRAYS[type_name])

    def pointer_to_js(self, c_type, cval, name):
        pointee_type = c_type.get_pointee_type()
        if pointee_type.is_char():
            return self.string_to_js(name, cval)
        elif pointee_type.is_number():
            return self.num_pointer_to_js(name, cval, pointee_type.name)
        else:
            return JS_CREATE_UNSUPPORTED.format(NAME=name, FROM=cval)

    def object_to_record(self, record, name, jval, index=''):
        result = ''
        buffers_to_free = []
        for field in record.field_decls:
            get_val = ''
            field_name = record.name + index + '_' + field.name
            field_val = field_name + '_value'

            if field.type.is_record():
                record = field.type.get_declaration().get_as_record_decl()
                result += "  {TYPE} {NAME};".format(TYPE=record.type.name,
                                                    NAME=field_name)
                res, buff = self.object_to_record(record, field_name, field_val,
                                                  index)
                get_val += res
                buffers_to_free += buff
            elif field.type.is_pointer():
                get_val += self.js_to_pointer(field.type, field_name, field_val)
                if field.type.get_pointee_type().is_number():
                    buffers_to_free.append(self.js_free_buffer(field_name,
                                                               field_val))
            else:
                get_val += self.js_to_c(field.type, field_name, field_val)

            result += JS_GET_PROP.format(NAME=field_name, MEM=field.name,
                                         OBJ=jval, GET_VAl=get_val, RECORD=name)

        return result, buffers_to_free

    def record_to_object(self, record, cval, name):
        result = JS_CREATE_VAL.format(NAME=name, TYPE='object', FROM='')
        for field in record.field_decls:
            field_name = cval + '.' + field.name
            field_js = 'js_' + record.name + '_' + field.name

            if field.type.is_record():
                rec_decl = field.type.get_declaration().get_as_record_decl()
                result += self.record_to_object(rec_decl, field_name, field_js)
            elif field.type.is_pointer():
                result += self.pointer_to_js(field.type, field_name, field_js)
            else:
                result += self.c_to_js(field.type, field_name, field_js)

            result += JS_SET_PROP.format(NAME=record.name, MEM=field.name,
                                         OBJ=name, JVAL=field_js)
        return result

    def check_js_type(self, c_type, jval, funcname):
        if c_type.is_char():
            return JS_CHECK_TYPE.format(TYPE='string', JVAL=jval, FUNC=funcname)
        elif c_type.is_number() or c_type.is_enum():
            return JS_CHECK_TYPE.format(TYPE='number', JVAL=jval, FUNC=funcname)
        elif c_type.is_record():
            return JS_CHECK_TYPE.format(TYPE='object', JVAL=jval, FUNC=funcname)
        elif c_type.is_function():
            return JS_CHECK_TYPE.format(TYPE='function', JVAL=jval,
                                        FUNC=funcname)
        elif c_type.is_pointer():
            if c_type.get_pointee_type().is_char():
                return JS_CHECK_TYPE.format(TYPE='string', JVAL=jval,
                                            FUNC=funcname)
            elif c_type.get_pointee_type().is_number():
                return JS_CHECK_TYPES.format(TYPE1='typedarray', TYPE2='null',
                                             JVAL=jval, FUNC=funcname)
            elif c_type.get_pointee_type().is_function():
                return JS_CHECK_TYPE.format(TYPE='function', JVAL=jval,
                                            FUNC=funcname)
        return ''

    def create_c_function(self, node, funcname, name):
        func = node.get_as_function()
        params = []
        create_val = []

        for index, param in enumerate(func.params):
            index = str(index)
            param_name = 'p_' + index
            arg_name = 'arg_'+ index
            params.append(param.type.name + ' ' + param_name)
            create_val.append(self.c_to_js(param.type, param_name, arg_name))
            create_val.append('  args[' + index + '] = ' + arg_name + ';')

        if func.return_type.is_void():
            res= ''
            ret = ''
        else:
            res = self.js_to_c(func.return_type, 'ret', 'result')
            ret = 'ret'

        return JS_CB_FUNCTION.format(FUNC=funcname, NAME=name,
                                     RET_TYPE=func.return_type.name,
                                     PARAMS=(', ').join(params),
                                     LEN=len(func.params),
                                     CREATE_VAL=('\n').join(create_val),
                                     RESULT=res, RET=ret)

    def create_ext_function(self, function):
        self.function_names.append(function.name)
        funcname = function.name
        params = function.params
        return_type = function.return_type
        jerry_function = []
        native_params = []
        buffers_to_free = []
        callbacks = []

        jerry_function.append(JS_CHECK_ARG_COUNT.format(COUNT=len(params),
                                                        FUNC=funcname))

        for index, param in enumerate(params):
            index = str(index)
            jval = 'args_p[' + index + ']'
            name = 'arg_' + index
            check_type = self.check_js_type(param.type, jval, funcname)

            if param.type.is_record():
                param = param.type.get_declaration().get_as_record_decl()
                result = "  {TYPE} {NAME};".format(TYPE=param.type.name,
                                                   NAME=name)
                res, buff = self.object_to_record(param, name, jval, index)
                result += res
                buffers_to_free += buff
            elif param.type.is_pointer():
                if param.type.get_pointee_type().is_function():
                    result = self.js_to_function(funcname, name, jval)
                    callback = self.create_c_function(param, funcname, name)
                    callbacks.append(callback)
                else:
                    result = self.js_to_pointer(param.type, name, jval)
                    if param.type.get_pointee_type().is_number():
                        buffers_to_free.append(self.js_free_buffer(name, jval))
            elif param.type.is_function():
                result = self.js_to_function(funcname, name, jval)
                callback = self.create_c_function(param, funcname, name)
                callbacks.append(callback)
            else:
                result = self.js_to_c(param.type, name, jval)

            native_params.append('arg_' + index)
            jerry_function.append(check_type + result)

        native_params = (', ').join(native_params)

        if return_type.is_void():
            native_call = '  {} ({});\n'.format(funcname, native_params)
        else:
            native_call = '  {} {} = {} ({});\n'.format(return_type.name,
                                                        'result', funcname,
                                                        native_params)

        jerry_function.append('  // native function call\n' + native_call)
        jerry_function += buffers_to_free

        if return_type.is_record():
            record = return_type.get_declaration().get_as_record_decl()
            result = self.record_to_object(record, 'result', 'ret_val')
        elif return_type.is_pointer():
            result = self.pointer_to_js(return_type, 'result', 'ret_val')
        else:
            result = self.c_to_js(return_type, 'result', 'ret_val')

        jerry_function.append(result)

        callbacks = '\n'.join(callbacks)
        ext_func = JS_EXT_FUNC.format(NAME=funcname + '_handler',
                                      BODY='\n'.join(jerry_function))


        return callbacks + ext_func

    def create_getter_setter(self, var):
        if var.type.is_const():
            self.constant_variables.append(var)
            return ''
        elif var.type.get_array_type().is_number():
            self.number_arrays.append(var)
            return ''
        elif var.type.is_record():
            record = var.type.get_declaration().get_as_record_decl()
            get_result = self.record_to_object(record, var.name, 'ret_val')
            set_result, _ = self.object_to_record(record, var.name, 'args_p[0]')
        elif var.type.is_pointer():
            get_result = self.pointer_to_js(var.type, var.name, 'ret_val')
            set_result = self.js_set_pointer(var.type, var.name, 'args_p[0]')
        else:
            get_result = self.c_to_js(var.type, var.name, 'ret_val')
            set_result = self.js_set_c(var.type, var.name, 'args_p[0]')

        set_result += '  jerry_value_t ret_val = jerry_create_undefined();'
        set_result = self.check_js_type(var.type, 'args_p[0]', var.name + '_setter')

        self.variable_names.append(var.name)

        getter = JS_EXT_FUNC.format(NAME=var.name + '_getter', BODY=get_result)
        setter = JS_EXT_FUNC.format(NAME=var.name + '_setter', BODY=set_result)

        return getter + setter



    def create_init_function(self, dirname, enums, macros):
        init_function = []

        for funcname in self.function_names:
            init_function.append(INIT_REGIST_FUNC.format(NAME=funcname))

        for varname in self.variable_names:
            init_function.append(INIT_REGIST_VALUE.format(NAME=varname))

        for num_array in self.number_arrays:
            type_name = num_array.type.get_array_type().name
            size = num_array.type.get_array_size()
            array = TYPEDARRAYS[type_name]
            init_function.append(INIT_REGIST_NUM_ARR.format(NAME=num_array.name,
                                                            TYPE=type_name,
                                                            SIZE=size,
                                                            ARRAY_TYPE=array))

        for enum in enums:
            init_function.append(INIT_REGIST_ENUM.format(ENUM=enum))

        for macro in macros:
            name = macro.name
            if macro.is_char():
                init_function.append('  char {N}_value = {N};'.format(N=name))
                init_function.append(self.char_to_js(name + '_js',
                                                     name + '_value'))
                init_function.append(INIT_REGIST_CONST.format(NAME=name))
            elif macro.is_string():
                init_function.append(self.string_to_js(name + '_js', name))
                init_function.append(INIT_REGIST_CONST.format(NAME=name))
            elif macro.is_number():
                init_function.append(self.number_to_js(name + '_js', name))
                init_function.append(INIT_REGIST_CONST.format(NAME=name))

        return INIT_FUNC.format(NAME=dirname, BODY=('\n').join(init_function))


class CppSourceGenerator(CSourceGenerator):
    def __init__(self):
        pass
