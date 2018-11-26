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


# Templates for classes

# Constructor
JS_CLASS_CONSTRUCTOR = '''
// external function for a class constructor
jerry_value_t {NAME}_js_constructor (const jerry_value_t function_obj,
                                     const jerry_value_t this_val,
                                     const jerry_value_t args_p[],
                                     const jerry_length_t args_cnt)
{{
  {NAME}* native_ptr;
  switch (args_cnt) {{
 {CASE}
     default: {{
       char* msg = "Wrong argument count for {NAME} constructor.";
       return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
     }}
  }}

  jerry_value_t js_obj = jerry_create_object();
  jerry_set_object_native_pointer(js_obj, native_ptr, &{NAME}_type_info);

  {REGIST}

  return js_obj;
}}
'''

JS_CONSTR_CALL = '''
      if ({CONDITION})
      {{
        {GET_VAL}
        native_ptr = new {NAME}({PARAMS});
        {FREE}
        break;
      }}
'''

JS_CONSTR_CASE_0 = '''
    case 0: {{
      native_ptr = new {NAME}();
      break;
    }}
'''

JS_CONSTR_CASE = '''
    case {NUM}: {{
{CALLS}
    char* msg = "Wrong argument type for {NAME} constructor.";
    return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
    }}
'''

JS_REGIST_METHOD = '''
  // set an external function as a property to the object
  jerry_value_t {NAME}_name = jerry_create_string ((const jerry_char_t*)"{NAME}");
  jerry_value_t {NAME}_func = jerry_create_external_function ({CLASS}_{NAME}_handler);
  jerry_value_t {NAME}_ret = jerry_set_property (js_obj, {NAME}_name, {NAME}_func);
  jerry_release_value ({NAME}_name);
  jerry_release_value ({NAME}_func);
  jerry_release_value ({NAME}_ret);
'''

JS_REGIST_MEMBER = '''
  // set a class member as a property to the object
  jerry_property_descriptor_t {CLASS}_{NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{CLASS}_{NAME}_prop_desc);
  {CLASS}_{NAME}_prop_desc.is_get_defined = true;
  {CLASS}_{NAME}_prop_desc.is_set_defined = true;
  {CLASS}_{NAME}_prop_desc.getter = jerry_create_external_function ({CLASS}_{NAME}_getter);
  {CLASS}_{NAME}_prop_desc.setter = jerry_create_external_function ({CLASS}_{NAME}_setter);
  jerry_value_t {CLASS}_{NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {CLASS}_{NAME}_return_value = jerry_define_own_property (js_obj, {CLASS}_{NAME}_prop_name, &{CLASS}_{NAME}_prop_desc);
  jerry_release_value ({CLASS}_{NAME}_return_value);
  jerry_release_value ({CLASS}_{NAME}_prop_name);
  jerry_free_property_descriptor_fields (&{CLASS}_{NAME}_prop_desc);
'''

JS_REGIST_CONST_MEMBER = '''
  // set a constant class member as a property to the object
  jerry_property_descriptor_t {CLASS}_{NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{CLASS}_{NAME}_prop_desc);
  {CLASS}_{NAME}_prop_desc.is_value_defined = true;
  {CLASS}_{NAME}_prop_desc.value = {CLASS}_{NAME}_js;
  jerry_value_t {CLASS}_{NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {CLASS}_{NAME}_return_value = jerry_define_own_property (js_obj, {CLASS}_{NAME}_prop_name, &{CLASS}_{NAME}_prop_desc);
  jerry_release_value ({CLASS}_{NAME}_return_value);
  jerry_release_value ({CLASS}_{NAME}_prop_name);
  jerry_free_property_descriptor_fields (&{CLASS}_{NAME}_prop_desc);
'''

JS_REGIST_NUM_ARR_MEMBER = '''
  // set a numeric array member as a property to the object
  jerry_value_t {NAME}_buffer = jerry_create_arraybuffer_external (sizeof({TYPE}) * {SIZE}, (uint8_t*)native_ptr->{NAME}, NULL);
  jerry_value_t {NAME}_typedarray = jerry_create_typedarray_for_arraybuffer_sz (JERRY_TYPEDARRAY_{ARRAY_TYPE}, {NAME}_buffer, 0, {SIZE});
  jerry_property_descriptor_t {NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{NAME}_prop_desc);
  {NAME}_prop_desc.is_value_defined = true;
  {NAME}_prop_desc.value = {NAME}_typedarray;
  jerry_value_t {NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {NAME}_return_value = jerry_define_own_property (js_obj, {NAME}_prop_name, &{NAME}_prop_desc);
  jerry_release_value ({NAME}_return_value);
  jerry_release_value ({NAME}_prop_name);
  jerry_release_value ({NAME}_buffer);
  jerry_free_property_descriptor_fields (&{NAME}_prop_desc);
'''

# Destructor
JS_CLASS_DESTRUCTOR = '''
void {NAME}_js_destructor(void* void_ptr) {{
    delete static_cast<{NAME}*>(void_ptr);
}}

static const jerry_object_native_info_t {NAME}_type_info = {{
    .free_cb = {NAME}_js_destructor
}};
'''

# Method
JS_CLASS_METHOD = '''
// external function for a class method
jerry_value_t {CLASS}_{NAME}_handler (const jerry_value_t function_obj,
                                      const jerry_value_t this_val,
                                      const jerry_value_t args_p[],
                                      const jerry_length_t args_cnt)
{{
  void* void_ptr;
  const jerry_object_native_info_t* type_ptr;
  bool has_ptr = jerry_get_object_native_pointer(this_val, &void_ptr, &type_ptr);

  if (!has_ptr || type_ptr != &{CLASS}_type_info) {{
    char* msg = "Failed to get native {CLASS} pointer";
    return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t *)msg);
  }}

  {CLASS}* native_ptr = static_cast<{CLASS}*>(void_ptr);

  {RESULT}
  switch (args_cnt) {{
{CASE}
    default: {{
      char* msg = "Wrong argument count for {CLASS}.{NAME}().";
      return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
    }}
  }}

  {RET_VAL}
  return ret_val;
}}
'''

JS_METHOD_CALL = '''
      if ({CONDITION})
      {{
        {GET_VAL}
        {RESULT}native_ptr->{NAME}({PARAMS});
        {FREE}
        break;
      }}
'''

JS_METHOD_CASE_0 = '''
    case 0: {{
      {RESULT}native_ptr->{NAME}();
      break;
    }}
'''

JS_METHOD_CASE = '''
    case {NUM}: {{
{CALLS}
    char* msg = "Wrong argument type for {CLASS}.{NAME}().";
    return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
    }}
'''

JS_VALUE_IS = '''jerry_value_is_{TYPE} ({JVAL})'''

# Memeber
JS_CLASS_MEMBER = '''
// external function for a class method
jerry_value_t {CLASS}_{NAME} (const jerry_value_t function_obj,
                      const jerry_value_t this_val,
                      const jerry_value_t args_p[],
                      const jerry_length_t args_cnt)
{{
  void* void_ptr;
  const jerry_object_native_info_t* type_ptr;
  bool has_ptr = jerry_get_object_native_pointer(this_val, &void_ptr, &type_ptr);

  if (!has_ptr || type_ptr != &{CLASS}_type_info) {{
    char* msg = "Failed to get native {CLASS} pointer";
    return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t *)msg);
  }}

  {CLASS}* native_ptr = static_cast<{CLASS}*>(void_ptr);
{BODY}
  return ret_val;
}}
'''


# Templates for C++ functions

# Function
JS_EXT_FUNC_CPP = '''
// external function
jerry_value_t {NAME}_handler (const jerry_value_t function_obj,
                              const jerry_value_t this_val,
                              const jerry_value_t args_p[],
                              const jerry_length_t args_cnt)
{{
  {RESULT}
  switch (args_cnt) {{
{CASE}
    default: {{
      char* msg = "Wrong argument count for {NAME}().";
      return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
    }}
  }}

  {RET_VAL}
  return ret_val;
}}
'''

JS_FUNC_CALL = '''
      if ({CONDITION})
      {{
        {GET_VAL}
        {RESULT}{NAME}({PARAMS});
        {FREE}
        break;
      }}
'''

JS_FUNC_CASE_0 = '''
    case 0: {{
      {RESULT}{NAME}();
      break;
    }}
'''

JS_FUNC_CASE = '''
    case {NUM}: {{
{CALLS}
    char* msg = "Wrong argument type for {NAME}().";
    return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
    }}
'''


# Templates for get/set values

# Set a char* variable
JS_SET_CHAR_PTR_CPP = '''
  // set the value of {NAME}
  jerry_size_t {NAME}_size = jerry_get_string_size ({JVAL});
  if (native_ptr->{NAME} == NULL)
  {{
    native_ptr->{NAME} = new {TYPE}[{NAME}_size + 1];
  }}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)native_ptr->{NAME}, {NAME}_size);
  native_ptr->{NAME}[{NAME}_size] = '\\0';
'''

# Set a char[] variable
JS_SET_CHAR_ARR_CPP = '''
  // set the value of {NAME}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)native_ptr->{NAME}, {SIZE});
  native_ptr->{NAME}[{SIZE}] = '\\0';
'''

# TypedArray to number pointer
JS_TO_TYPEDARRAY_CPP = '''
  // create a pointer to number from a jerry_value_t
  {TYPE} * {NAME} = NULL;
  jerry_length_t {NAME}_byteLength = 0;
  jerry_length_t {NAME}_byteOffset = 0;
  jerry_value_t {NAME}_buffer;
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    {NAME}_buffer = jerry_get_typedarray_buffer ({JVAL}, &{NAME}_byteOffset, &{NAME}_byteLength);
    {NAME} = new {TYPE}[{NAME}_byteLength / sizeof({TYPE})];
    jerry_arraybuffer_read ({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
  }}
'''

# Set a number pointer
JS_SET_TYPEDARRAY_CPP = '''
  // set the value of {NAME}
  jerry_length_t {NAME}_byteLength = 0;
  jerry_length_t {NAME}_byteOffset = 0;
  jerry_value_t {NAME}_buffer;
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    {NAME}_buffer = jerry_get_typedarray_buffer ({JVAL}, &{NAME}_byteOffset, &{NAME}_byteLength);
    if (native_ptr->{NAME} == NULL)
    {{
      native_ptr->{NAME} = new {TYPE}[{NAME}_byteLength / sizeof({TYPE})];
    }}
    jerry_arraybuffer_read ({NAME}_buffer, {NAME}_byteOffset, (uint8_t*)native_ptr->{NAME}, {NAME}_byteLength);
    jerry_release_value ({NAME}_buffer);
  }}
  else
  {{
    native_ptr->{NAME} = NULL;
  }}
'''

# Object to struct/union/class
JS_TO_RECORD = '''
  void* void_ptr;
  const jerry_object_native_info_t* type_ptr;
  bool has_ptr = jerry_get_object_native_pointer({JVAL}, &void_ptr, &type_ptr);

  if (!has_ptr || type_ptr != &{CLASS}_type_info) {{
    char* msg = "Failed to get native {CLASS} pointer";
    return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t *)msg);
  }}

  {CLASS}* native_ptr = static_cast<{CLASS}*>(void_ptr);
  {RECORD} = *native_ptr;
'''


# Templates for the module initialization function

INIT_FUNC_CPP = '''
// init function for the module
extern "C" jerry_value_t Init_{NAME}()
{{
  jerry_value_t object = jerry_create_object();
{BODY}
  return object;
}}
'''

INIT_REGIST_CLASS = '''
  // set a constructor as a property to the module object
  jerry_value_t {NAME}_name = jerry_create_string ((const jerry_char_t*)"{NAME}");
  jerry_value_t {NAME}_func = jerry_create_external_function ({NAME}_js_constructor);
  jerry_value_t {NAME}_ret = jerry_set_property (object, {NAME}_name, {NAME}_func);
  jerry_release_value ({NAME}_name);
  jerry_release_value ({NAME}_func);
  jerry_release_value ({NAME}_ret);
'''


# Template for include the right headers

INCLUDE = '''
#include "jerryscript.h"
#include "{HEADER}"
'''


# Templates for modules.json, module.cmake and CMakeLists.txt

MODULES_JSON = '''
{{
  "modules": {{
    "{NAME}_module": {{
      "native_files": [],
      "init": "Init_{NAME}",
      "cmakefile": "{CMAKE}"
    }}
  }}
}}
'''

MODULE_CMAKE = '''
set(MODULE_NAME "{NAME}_module")
add_subdirectory(${{MODULE_DIR}}/src/ ${{MODULE_BINARY_DIR}}/${{MODULE_NAME}})
link_directories(${{MODULE_DIR}})
list(APPEND MODULE_LIBS {NAME}_binding {LIBRARY})
'''

CMAKE_LISTS = '''
project({NAME} CXX)

add_library({NAME}_binding STATIC
    {NAME}_js_binding.cpp
)
target_include_directories({NAME}_binding PRIVATE ${{JERRY_INCLUDE_DIR}})
target_link_libraries({NAME}_binding PUBLIC stdc++)
'''
