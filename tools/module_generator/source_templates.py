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


# Template for a jerry_external_handler_t type function

JS_EXT_FUNC = '''
jerry_value_t {NAME} (const jerry_value_t function_obj,
                      const jerry_value_t this_val,
                      const jerry_value_t args_p[],
                      const jerry_length_t args_cnt)
{{
  {BODY}
  return ret_val;
}}
'''


# Template for check the count of the external function's arguments

JS_CHECK_ARG_COUNT = '''
  if (args_cnt != {COUNT})
  {{
    const jerry_char_t* msg = "Wrong argument count for {FUNC}(), expected {COUNT}.";
    return jerry_create_error (JERRY_ERROR_TYPE, msg);
  }}
'''


# Templates for check the type of a jerry_value_t variable

JS_CHECK_TYPE = '''
  if (!jerry_value_is_{TYPE} ({JVAL}))
  {{
    const jerry_char_t* msg = "Wrong argument type for {FUNC}(), expected {TYPE}.";
    return jerry_create_error (JERRY_ERROR_TYPE, msg);
  }}
'''

JS_CHECK_TYPES = '''
  if (!jerry_value_is_{TYPE1} ({JVAL}) && !jerry_value_is_{TYPE2} ({JVAL}))
  {{
    const jerry_char_t* msg = "Wrong argument type for {FUNC}(), expected {TYPE1} or {TYPE2}.";
    return jerry_create_error (JERRY_ERROR_TYPE, msg);
  }}
'''


# Templates for get the value from a jerry_value_t variable

# Boolean to _Bool
JS_GET_BOOL = '''
  _Bool {NAME} = jerry_value_to_boolean ({JVAL});
'''

# Number to int/float/enum
JS_GET_NUM = '''
  {TYPE} {NAME} = jerry_get_number_value ({JVAL});
'''

# one length String to char
JS_GET_CHAR = '''
  char {NAME};
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)(&{NAME}), 1);
'''

# String to char[]
JS_GET_STRING = '''
  jerry_size_t {NAME}_size = jerry_get_string_size ({JVAL});
  char {NAME}[{NAME}_size];
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, {NAME}_size);
  {NAME}[{NAME}_size] = '\\0';
'''

# Object to struct/union
JS_GET_PROP = '''
  jerry_value_t {NAME}_{MEM}_name = jerry_create_string ((const jerry_char_t *) "{MEM}");
  jerry_value_t {NAME}_{MEM}_value = jerry_get_property ({OBJ}, {NAME}_{MEM}_name);
  jerry_release_value ({NAME}_{MEM}_name);

  if (!jerry_value_is_undefined ({NAME}_{MEM}_value))
  {{
    {GET_VAl}
    {STRUCT}.{MEM} = {NAME}_{MEM};
  }}
  jerry_release_value ({NAME}_{MEM}_value);
'''

# TypedArray to pointer
JS_GET_TYPEDARRAY = '''
  {TYPE} * {NAME} = NULL;
  jerry_length_t {NAME}_byteLength = 0;
  jerry_length_t {NAME}_byteOffset = 0;
  jerry_value_t {NAME}_buffer;
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    {NAME}_buffer = jerry_get_typedarray_buffer ({JVAL}, &{NAME}_byteOffset, &{NAME}_byteLength);
    {NAME} = ({TYPE}*) malloc ({NAME}_byteLength);
    if({NAME} == NULL)
    {{
      jerry_release_value ({NAME}_buffer);
      return jerry_create_error (JERRY_ERROR_COMMON, (const jerry_char_t*)"Fail to allocate memory.");
    }}
    jerry_arraybuffer_read ({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
  }}
'''


# Templates for make a jerry_value_t variable

# Create Undefined/Bool/Number/Object
JS_CREATE_VAL = '''
  jerry_value_t {NAME} = jerry_create_{TYPE} ({FROM});
'''

# Create one length String
JS_CREATE_CHAR = '''
  jerry_value_t {NAME} = jerry_create_string_sz ((jerry_char_t*)(&{FROM}), 1);
'''

# Create String
JS_CREATE_STRING = '''
  jerry_value_t {NAME} = jerry_create_string ((jerry_char_t*){FROM});
'''

# Set object property
JS_SET_PROP = '''
  jerry_value_t {NAME}_{MEM}_name = jerry_create_string ((const jerry_char_t *) "{MEM}");
  jerry_value_t {NAME}_{MEM}_res = jerry_set_property ({OBJ}, {NAME}_{MEM}_name, {JVAL});
  jerry_release_value ({JVAL});
  jerry_release_value ({NAME}_{MEM}_name);
  jerry_release_value ({NAME}_{MEM}_res);
'''

# Create TypedArray or Null
JS_CREATE_TYPEDARRAY = '''
  jerry_value_t {NAME};
  if ({FROM} != NULL)
  {{
    jerry_length_t {NAME}_byteLength = sizeof({TYPE});
    jerry_value_t {NAME}_buffer = jerry_create_arraybuffer ({NAME}_byteLength);
    jerry_arraybuffer_write ({NAME}_buffer, 0, (uint8_t*){FROM}, {NAME}_byteLength);
    {NAME} = jerry_create_typedarray_for_arraybuffer_sz (JERRY_TYPEDARRAY_{ARRAY_TYPE}, {NAME}_buffer, 0, 1);
    jerry_release_value ({NAME}_buffer);
  }}
  else
  {{
    {NAME} = jerry_create_null ();
  }}
'''


# Template for write the values back into the ArrayBuffer after the native call

JS_WRITE_ARRAYBUFFER = '''
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    jerry_arraybuffer_write ({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
    jerry_release_value ({NAME}_buffer);
    free ({NAME});
  }}
'''


# Template for include the right headers

INCLUDE = '''
#include <stdlib.h>  // If there are pointers, malloc() and free() required
#include "jerryscript.h"
#include "{HEADER}"
'''


# Templates for the module initialization function

INIT_FUNC = '''
jerry_value_t Init_{NAME}()
{{
  jerry_value_t object = jerry_create_object();
{BODY}
  return object;
}}
'''

INIT_REGIST_FUNC = '''
  jerry_value_t {NAME}_name = jerry_create_string ((const jerry_char_t*)"{NAME}");
  jerry_value_t {NAME}_func = jerry_create_external_function ({NAME}_handler);
  jerry_value_t {NAME}_ret = jerry_set_property (object, {NAME}_name, {NAME}_func);
  jerry_release_value ({NAME}_name);
  jerry_release_value ({NAME}_func);
  jerry_release_value ({NAME}_ret);
'''

INIT_REGIST_ENUM = '''
  jerry_value_t {ENUM}_name = jerry_create_string ((const jerry_char_t*)"{ENUM}");
  jerry_value_t {ENUM}_enum = jerry_create_number ({ENUM});
  jerry_value_t {ENUM}_ret = jerry_set_property (object, {ENUM}_name, {ENUM}_enum);
  jerry_release_value ({ENUM}_name);
  jerry_release_value ({ENUM}_enum);
  jerry_release_value ({ENUM}_ret);
'''

INIT_REGIST_VALUE = '''
  jerry_property_descriptor_t {NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{NAME}_prop_desc);
  {NAME}_prop_desc.is_get_defined = true;
  {NAME}_prop_desc.getter = jerry_create_external_function ({NAME}_getter);
  jerry_value_t {NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {NAME}_return_value = jerry_define_own_property (object, {NAME}_prop_name, &{NAME}_prop_desc);
  jerry_release_value ({NAME}_return_value);
  jerry_release_value ({NAME}_prop_name);
  jerry_free_property_descriptor_fields (&{NAME}_prop_desc);
'''

INIT_REGIST_CONST = '''
  jerry_property_descriptor_t {NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{NAME}_prop_desc);
  {NAME}_prop_desc.is_value_defined = true;
  {NAME}_prop_desc.value = {NAME}_js;
  jerry_value_t {NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {NAME}_return_value = jerry_define_own_property (object, {NAME}_prop_name, &{NAME}_prop_desc);
  jerry_release_value ({NAME}_return_value);
  jerry_release_value ({NAME}_prop_name);
  jerry_free_property_descriptor_fields (&{NAME}_prop_desc);
'''


# Templates for modules.json and module.cmake

MODULES_JSON = '''
{{
  "modules": {{
    "{NAME}_module": {{
      "native_files": ["{NAME}_js_wrapper.c"],
      "init": "Init_{NAME}",
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
