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


# Templates for create/set a C variable

# one length String to char
JS_TO_CHAR = '''
  // create a character value from a jerry_value_t
  {TYPE} {NAME};
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)(&{NAME}), 1);
'''

# Set a char variable
JS_SET_CHAR = '''
  // set the value of {NAME}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*)(&{NAME}), 1);
'''

# Number to int/float/enum
JS_TO_NUMBER = '''
  // create an integer / floating point number from a jerry_value_t
  {TYPE} {NAME} = ({TYPE})jerry_get_number_value ({JVAL});
'''

# Set an int/float/enum variable
JS_SET_NUMBER = '''
  // set the value of {NAME}
  {NAME} = jerry_get_number_value ({JVAL});
'''

# Boolean to _Bool
JS_TO_BOOL = '''
  // create a _Bool value from a jerry_value_t
  {TYPE} {NAME} = jerry_value_to_boolean ({JVAL});
'''

# Set a _Bool variable
JS_SET_BOOL = '''
  // set the value of {NAME}
  {NAME} = jerry_value_to_boolean ({JVAL});
'''

# String to char[]
JS_TO_STRING = '''
  // create an array of characters from a jerry_value_t
  jerry_size_t {NAME}_size = jerry_get_string_size ({JVAL});
  {TYPE} {NAME}[{NAME}_size + 1];
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, {NAME}_size);
  {NAME}[{NAME}_size] = '\\0';
'''

# Set a char* variable
JS_SET_CHAR_PTR = '''
  // set the value of {NAME}
  jerry_size_t size = jerry_get_string_size ({JVAL});
  if ({NAME} == NULL)
  {{
    {NAME} = ({TYPE}*) malloc (size + 1);
  }}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, size);
  {NAME}[size] = '\\0';
'''

# Set a char[] variable
JS_SET_CHAR_ARR = '''
  // set the value of {NAME}
  jerry_string_to_char_buffer ({JVAL}, (jerry_char_t*){NAME}, {SIZE});
  {NAME}[{SIZE}] = '\\0';
'''

# TypedArray to number pointer
JS_TO_TYPEDARRAY = '''
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

JS_FREE_BUFFER = '''
  // write the values back into an arraybuffer from a pointer
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    jerry_arraybuffer_write ({NAME}_buffer, {NAME}_byteOffset, (uint8_t*){NAME}, {NAME}_byteLength);
    jerry_release_value ({NAME}_buffer);
    // TODO: if you won't use {NAME} pointer, uncomment the line below
    //free ({NAME});
  }}
'''

# Set a number pointer
JS_SET_TYPEDARRAY = '''
  // set the value of {NAME}
  jerry_length_t byteLength = 0;
  jerry_length_t byteOffset = 0;
  jerry_value_t buffer;
  if (jerry_value_is_typedarray ({JVAL}))
  {{
    buffer = jerry_get_typedarray_buffer ({JVAL}, &byteOffset, &byteLength);
    if ({NAME} == NULL)
    {{
      {NAME} = ({TYPE}*) malloc (byteLength);
    }}
    jerry_arraybuffer_read (buffer, byteOffset, (uint8_t*){NAME}, byteLength);
    jerry_release_value (buffer);
  }}
  else
  {{
    {NAME} = NULL;
  }}
'''

# Object to struct/union
JS_TO_RECORD = '''
  // create a record from a jerry_value_t
  void* {NAME}_void_ptr;
  const jerry_object_native_info_t* {NAME}_type_ptr;
  bool {NAME}_has_ptr = jerry_get_object_native_pointer({JVAL}, &{NAME}_void_ptr, &{NAME}_type_ptr);

  if (!{NAME}_has_ptr || {NAME}_type_ptr != &{RECORD}_type_info) {{
    char* msg = "Failed to get native {TYPE} pointer";
    return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t *)msg);
  }}

  {TYPE} {NAME} = *(({TYPE}*){NAME}_void_ptr);
'''

# Set a struct/union
JS_SET_RECORD = '''
  // set the value of {NAME}
  void* {RECORD}_void_ptr;
  const jerry_object_native_info_t* {RECORD}_type_ptr;
  bool {RECORD}_has_ptr = jerry_get_object_native_pointer({JVAL}, &{RECORD}_void_ptr, &{RECORD}_type_ptr);

  if (!{RECORD}_has_ptr || {RECORD}_type_ptr != &{RECORD}_type_info) {{
    char* msg = "Failed to get native {RECORD} pointer";
    return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t *)msg);
  }}

  {NAME} = *(({TYPE}*){RECORD}_void_ptr);
'''

# Function to C function
JS_TO_FUNCTION = '''
  // create a function pointer from a jerry_value_t
  {FUNC}_{NAME}_js = {JVAL};
  void* {NAME} = {FUNC}_{NAME};
'''

JS_CB_FUNCTION = '''
jerry_value_t {FUNC}_{NAME}_js;
{RET_TYPE} {FUNC}_{NAME} ({PARAMS})
{{
  jerry_value_t args[{LENGTH}];
  {CREATE_VAL}
  jerry_value_t this_val = jerry_create_undefined();
  jerry_value_t result = jerry_call_function({FUNC}_{NAME}_js, this_val, args, {LENGTH});
  {RESULT}
  jerry_release_value(result);
  jerry_release_value(this_val);

  for (int i = 0; i < {LENGTH}; i++)
  {{
    jerry_release_value(args[i]);
  }}
  return {RET};
}}
'''

# Unsupported C type
JS_TO_UNSUPPORTED = '''
  // TODO: Define the right value of the variable.
  {TYPE} {NAME};
'''


# Templates for create a jerry_value_t variable

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

TYPEDARRAYS = {
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

# Create Object
JS_CREATE_OBJECT = '''
  // create object from record
  {TYPE}* {RECORD}_native_ptr = ({TYPE}*)calloc(1, sizeof({TYPE}));
  *{RECORD}_native_ptr = {FROM};
  jerry_value_t {NAME} = {RECORD}_js_creator({RECORD}_native_ptr);
'''

# Unsupported C type
JS_CREATE_UNSUPPORTED = '''
  // TODO: Create a valid jerry_value_t from '{FROM}'.
  jerry_value_t {NAME} = jerry_create_undefined ();
'''


# Templates for record types

# Record destructor
JS_RECORD_DESTRUCTOR = '''
void {RECORD}_js_destructor(void* ptr) {{
    free(({TYPE}*)ptr);
}}

static const jerry_object_native_info_t {RECORD}_type_info = {{
    .free_cb = {RECORD}_js_destructor
}};
'''

# Member getter/setter template
JS_RECORD_MEMBER = '''
// external function for getter/setter of record member
jerry_value_t {RECORD}_{NAME} (const jerry_value_t function_obj,
                               const jerry_value_t this_val,
                               const jerry_value_t args_p[],
                               const jerry_length_t args_cnt)
{{
  void* void_ptr;
  const jerry_object_native_info_t* type_ptr;
  bool has_ptr = jerry_get_object_native_pointer(this_val, &void_ptr, &type_ptr);

  if (!has_ptr || type_ptr != &{RECORD}_type_info) {{
    char* msg = "Failed to get native {RECORD} pointer";
    return jerry_create_error(JERRY_ERROR_TYPE, (const jerry_char_t *)msg);
  }}

  {TYPE}* native_ptr = ({TYPE}*)(void_ptr);
{BODY}
  return ret_val;
}}
'''

# Record constructor
JS_RECORD_CONSTRUCTOR = '''
// external function for record constructor
jerry_value_t {RECORD}_js_constructor (const jerry_value_t function_obj,
                                       const jerry_value_t this_val,
                                       const jerry_value_t args_p[],
                                       const jerry_length_t args_cnt)
{{
  {TYPE}* native_ptr = ({TYPE}*)calloc(1, sizeof({TYPE}));
  return {RECORD}_js_creator(native_ptr);
}}
'''

JS_RECORD_CREATOR = '''
jerry_value_t {RECORD}_js_creator ({TYPE}* native_ptr)
{{
  jerry_value_t js_obj = jerry_create_object();
  jerry_set_object_native_pointer(js_obj, native_ptr, &{RECORD}_type_info);

  {REGIST}

  return js_obj;
}}
'''

JS_REGIST_MEMBER = '''
  // set record member as a property to the object
  jerry_property_descriptor_t {RECORD}_{NAME}_prop_desc;
  jerry_init_property_descriptor_fields (&{RECORD}_{NAME}_prop_desc);
  {RECORD}_{NAME}_prop_desc.is_get_defined = true;
  {RECORD}_{NAME}_prop_desc.is_set_defined = true;
  {RECORD}_{NAME}_prop_desc.getter = jerry_create_external_function ({RECORD}_{NAME}_getter);
  {RECORD}_{NAME}_prop_desc.setter = jerry_create_external_function ({RECORD}_{NAME}_setter);
  jerry_value_t {RECORD}_{NAME}_prop_name = jerry_create_string ((const jerry_char_t *)"{NAME}");
  jerry_value_t {RECORD}_{NAME}_return_value = jerry_define_own_property (js_obj, {RECORD}_{NAME}_prop_name, &{RECORD}_{NAME}_prop_desc);
  jerry_release_value ({RECORD}_{NAME}_return_value);
  jerry_release_value ({RECORD}_{NAME}_prop_name);
  jerry_free_property_descriptor_fields (&{RECORD}_{NAME}_prop_desc);
'''

JS_REGIST_ARR_MEMBER = '''
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

JS_CHECK_TYPEDARRAY = '''
  // check the type of a jerry_value_t variable
  if (!jerry_value_is_typedarray ({JVAL}) && !jerry_value_is_null ({JVAL}))
  {{
    char* msg = "Wrong argument type for {FUNC}(), expected typedarray or null.";
    return jerry_create_error (JERRY_ERROR_TYPE, (const jerry_char_t*)msg);
  }}
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

INIT_REGIST_RECORD = '''
  // set a constructor as a property to the module object
  jerry_value_t {NAME}_name = jerry_create_string ((const jerry_char_t*)"{NAME}");
  jerry_value_t {NAME}_func = jerry_create_external_function ({NAME}_js_constructor);
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


# Template for include the right headers

INCLUDE = '''
#include <stdlib.h>
#include "jerryscript.h"
#include "{HEADER}"
'''


# Templates for modules.json and module.cmake

MODULES_JSON = '''
{{
  "modules": {{
    "{NAME}_module": {{
      "native_files": ["src/{NAME}_js_binding.c"],
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
