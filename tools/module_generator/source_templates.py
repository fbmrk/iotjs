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
// external function for API functions or for getters / setters
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
  // check the count of the external function's arguments
  if (args_cnt != {COUNT})
  {{
    char* msg = "Wrong argument count for {FUNC}(), expected {COUNT}.";
    return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
  }}
'''


# Templates for check the type of a jerry_value_t variable

JS_CHECK_TYPE = '''
  // check the type of a jerry_value_t variable
  if (!jerry_value_is_{TYPE} ({JVAL}))
  {{
    char* msg = "Wrong argument type for {FUNC}(), expected {TYPE}.";
    return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
  }}
'''

JS_CHECK_TYPES = '''
  // check the type of a jerry_value_t variable
  if (!jerry_value_is_{TYPE1} ({JVAL}) && !jerry_value_is_{TYPE2} ({JVAL}))
  {{
    char* msg = "Wrong argument type for {FUNC}(), expected {TYPE1} or {TYPE2}.";
    return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
  }}
'''


# Templates for get the value from a jerry_value_t variable

# Boolean to _Bool
JS_GET_BOOL = '''
  // create a _Bool value from a jerry_value_t
  {TYPE} {NAME} = jerry_value_to_boolean ({JVAL});
'''

# Number to int/float/enum
JS_GET_NUM = '''
  // create an integer / floating point number from a jerry_value_t
  {TYPE} {NAME} = jerry_get_number_value ({JVAL});
'''

# one length String to char
JS_GET_CHAR = '''
  // create a character value from a jerry_value_t
  {TYPE} {NAME};
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)(&{NAME}), 1);
'''

# String to char[]
JS_GET_STRING = '''
  // create an array of characters from a jerry_value_t
  jerry_size_t {NAME}_size = jerry_get_string_size ({JVAL});
  {TYPE} {NAME}[{NAME}_size + 1];
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, {NAME}_size);
  {NAME}[{NAME}_size] = '\\0';
'''

# Object to struct/union
JS_GET_PROP = '''
  // get a property from a jerry_value_t object
  jerry_value_t {NAME}_{MEM}_name = jerry_create_string ((const jerry_char_t *) "{MEM}");
  jerry_value_t {NAME}_{MEM}_value = jerry_get_property ({OBJ}, {NAME}_{MEM}_name);
  jerry_release_value ({NAME}_{MEM}_name);

  // get the value from the property and set the {STRUCT} struct/union's member
  if (!jerry_value_is_undefined ({NAME}_{MEM}_value))
  {{
    {GET_VAl}
    {STRUCT}.{MEM} = {NAME}_{MEM};
  }}
  jerry_release_value ({NAME}_{MEM}_value);
'''

# TypedArray to pointer
JS_GET_TYPEDARRAY = '''
  // create a pointer to number from a jerry_value_t
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
  jerry_value_t {NAME};
  if ({FROM} != NULL)
  {{
    {NAME} = jerry_create_string ((jerry_char_t*){FROM});
  }}
  else
  {{
    {NAME} = jerry_create_null ();
  }}
'''

# Set object property
JS_SET_PROP = '''
  // set a property to a jerry_value_t object
  jerry_value_t {NAME}_{MEM}_name = jerry_create_string ((const jerry_char_t *) "{MEM}");
  jerry_value_t {NAME}_{MEM}_res = jerry_set_property ({OBJ}, {NAME}_{MEM}_name, {JVAL});
  jerry_release_value ({JVAL});
  jerry_release_value ({NAME}_{MEM}_name);
  jerry_release_value ({NAME}_{MEM}_res);
'''

# Create TypedArray or Null
JS_CREATE_TYPEDARRAY = '''
  // create a typedarray or null from a pointer
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

TYPEDARRAY_TYPES = {
    'signed char': 'INT8',
    'unsigned char': 'UINT8',
    'short': 'INT16',
    'unsigned short': 'UINT16',
    'int': 'INT32',
    'unsigned int': 'UINT32',
    'long': 'INT32',
    'unsigned long': 'UINT32',
    'long long': 'INT32',
    'unsigned long long': 'UINT32',
    'float': 'FLOAT32',
    'double': 'FLOAT64',
    'long double': 'FLOAT64'
}


# Template for write the values back into an ArrayBuffer after the native call

JS_WRITE_ARRAYBUFFER = '''
  // write the values back into an arraybuffer from a pointer
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    jerry_arraybuffer_write ({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
    jerry_release_value ({NAME}_buffer);
    // TODO: if you won't use {NAME} pointer, uncomment the line below
    //free ({NAME});
  }}
'''


# Template for unsupported C types

JS_GET_UNSUPPORTED = '''
  // TODO: Define the right value of the variable.
  {TYPE} {NAME};
'''

JS_CREATE_UNSUPPORTED = '''
  // TODO: Create a valid jerry_value_t from '{FROM}'.
  jerry_value_t {NAME} = jerry_create_undefined ();
'''


# Templates for setter functions

# Set a _Bool variable
JS_SET_BOOL = '''
  // set the value of {NAME}
  {NAME} = jerry_value_to_boolean ({JVAL});
'''

# Set an int/float/enum variable
JS_SET_NUM = '''
  // set the value of {NAME}
  {NAME} = jerry_get_number_value ({JVAL});
'''

# Set a char variable
JS_SET_CHAR = '''
  // set the value of {NAME}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)(&{NAME}), 1);
'''

# Set a char* variable
JS_SET_CHAR_PTR = '''
  // set the value of {NAME}
  jerry_size_t {NAME}_size = jerry_get_string_size ({JVAL});
  if (!{NAME})
  {{
    {NAME} = ({TYPE}*) malloc ({NAME}_size + 1);
  }}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, {NAME}_size);
  {NAME}[{NAME}_size] = '\\0';
'''

# Set a char[] variable
JS_SET_CHAR_ARR = '''
  // set the value of {NAME}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, {SIZE});
  {NAME}[{SIZE}] = '\\0';
'''

# Set a pointer
JS_SET_TYPEDARRAY = '''
  // set the value of {NAME}
  jerry_length_t {NAME}_byteLength = 0;
  jerry_length_t {NAME}_byteOffset = 0;
  jerry_value_t {NAME}_buffer;
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    {NAME}_buffer = jerry_get_typedarray_buffer ({JVAL}, &{NAME}_byteOffset, &{NAME}_byteLength);
    if ({NAME} == NULL)
    {{
      {NAME} = ({TYPE}*) malloc ({NAME}_byteLength);
    }}
    jerry_arraybuffer_read ({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
    jerry_release_value ({NAME}_buffer);
  }}
  else
  {{
    {NAME} = NULL;
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
// init function for the module
jerry_value_t Init_{NAME}()
{{
  jerry_value_t object = jerry_create_object();
{BODY}
  return object;
}}
'''

INIT_REGIST_FUNC = '''
  // set an external function as a property to the module object
  jerry_value_t {NAME}_name = jerry_create_string ((const jerry_char_t*)"{NAME}");
  jerry_value_t {NAME}_func = jerry_create_external_function ({NAME}_handler);
  jerry_value_t {NAME}_ret = jerry_set_property (object, {NAME}_name, {NAME}_func);
  jerry_release_value ({NAME}_name);
  jerry_release_value ({NAME}_func);
  jerry_release_value ({NAME}_ret);
'''

INIT_REGIST_ENUM = '''
  // set an enum constant as a property to the module object
  jerry_property_descriptor_t {ENUM}_prop_desc;
  jerry_init_property_descriptor_fields (&{ENUM}_prop_desc);
  {ENUM}_prop_desc.is_value_defined = true;
  {ENUM}_prop_desc.value = jerry_create_number ({ENUM});
  jerry_value_t {ENUM}_name = jerry_create_string ((const jerry_char_t *)"{ENUM}");
  jerry_value_t {ENUM}_ret = jerry_define_own_property (object, {ENUM}_name, &{ENUM}_prop_desc);
  jerry_release_value ({ENUM}_ret);
  jerry_release_value ({ENUM}_name);
  jerry_free_property_descriptor_fields (&{ENUM}_prop_desc);
'''

INIT_REGIST_VALUE = '''
  // set a global variable as a property to the module object
  jerry_property_descriptor_t {NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{NAME}_prop_desc);
  {NAME}_prop_desc.is_get_defined = true;
  {NAME}_prop_desc.is_set_defined = true;
  {NAME}_prop_desc.getter = jerry_create_external_function ({NAME}_getter);
  {NAME}_prop_desc.setter = jerry_create_external_function ({NAME}_setter);
  jerry_value_t {NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {NAME}_return_value = jerry_define_own_property (object, {NAME}_prop_name, &{NAME}_prop_desc);
  jerry_release_value ({NAME}_return_value);
  jerry_release_value ({NAME}_prop_name);
  jerry_free_property_descriptor_fields (&{NAME}_prop_desc);
'''

INIT_REGIST_CONST = '''
  // set a global constant or a macro as a property to the module object
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

INIT_REGIST_NUM_ARR = '''
  // set a global numeric array as a property to the module object
  jerry_value_t {NAME}_buffer = jerry_create_arraybuffer_external (sizeof({TYPE}) * {SIZE}, (uint8_t*){NAME}, NULL);
  jerry_value_t {NAME}_typedarray = jerry_create_typedarray_for_arraybuffer_sz (JERRY_TYPEDARRAY_{ARRAY_TYPE}, {NAME}_buffer, 0, {SIZE});
  jerry_property_descriptor_t {NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{NAME}_prop_desc);
  {NAME}_prop_desc.is_value_defined = true;
  {NAME}_prop_desc.value = {NAME}_typedarray;
  jerry_value_t {NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {NAME}_return_value = jerry_define_own_property (object, {NAME}_prop_name, &{NAME}_prop_desc);
  jerry_release_value ({NAME}_return_value);
  jerry_release_value ({NAME}_prop_name);
  jerry_release_value ({NAME}_buffer);
  jerry_free_property_descriptor_fields (&{NAME}_prop_desc);
'''


# Templates for modules.json and module.cmake

MODULES_JSON = '''
{{
  "modules": {{
    "{NAME}_module": {{
      "native_files": ["{NAME}_js_wrapper.c"],
      "init": "Init_{NAME}",
      "cmakefile": "{CMAKE}"
    }}
  }}
}}
'''

MODULE_CMAKE = '''
set(MODULE_NAME "{NAME}_module")
link_directories(${{MODULE_DIR}})
list(APPEND MODULE_LIBS {LIBRARY})
'''
