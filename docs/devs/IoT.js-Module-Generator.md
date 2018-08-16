# C API to IoT.js module generator

This tool generates a JS module from a C API, and you can use it in IoT.js like other modules. The input of the generator is a directory, which contains the C header files and the static library of the API.

1. [Dependencies](#dependencies)
2. [Features](#features)
    - [Functions](#functions)
    - [Variables](#variables)
    - [Enums](#enums)
    - [Macros](#macros)
    - [Types](#types)
3. [Usage](#usage)
    - [Optional arguments](#optional-arguments)
4. [Quick example](#quick-example)

### Dependencies:

#### Clang library:

```bash
apt install libclang1-5.0
```

#### Python binding for Clang:

```bash
apt install python-clang-5.0
```

(The tool has been tested only with the 5.0 version.)

### Features:

The C library is represented as an object in the JavaScript environment. This object is the result of the `require` function call with the right module name parameter. The generated module name is the name of the input folder with `'_module'` suffix.

```javascript
var c_lib = require('module_name');
```

#### Functions:

Every function from the C library are represented as properties of the library object. If there is a declaration, like `void foo(int);` in the C library, then the object has a property with the name `foo`.

```javascript
var c_lib = require('module_name');
c_lib.foo(42); // call the C function
```

#### Variables:

The global variables of the C library are also represented as properties. If there is a declaration, like `int a;` in the C library, then the object has a property with the name `a`, and you can get and set its value, but if there is a definition, like `const int b = 42;` you can only read the value from the property and you can not modify it.

C header:
```c
int i;
```

JS file:
```javascript
var c_lib = require('module_name');
c_lib.i = 1; // set the value of 'i'
console.log(c_lib.i); // print 1
```

#### Enums:

C enums work like constants above. You can read the value of the enumerator from a property, but you can not modify it.

C header:
```c
enum abc {A, B, C};
```

JS file:
```javascript
var c_lib = require('module_name');
console.log(c_lib.A); // print 0
console.log(c_lib.B); // print 1
console.log(c_lib.C); // print 2
```

#### Macros:

C macros also work like constants. You can read the value of the macro from a property, but you can not modify it. There are three supported types of C macros. If the macro defines a character literal, like `#define C 'c'`. If the macro defines a string literal, like `#define STR "str"`. If the macro defines a numeric literal, or contains some kind of operation, but the result is a number, like `#defines ZERO 0` or `#define TWO 1 + 1`. It also works, if the macro contains other macro identifiers.

C header:
```c
#define ONE 1
#define TWO 2
#define THREE ONE + TWO
```

JS file:
```javascript
var c_lib = require('module_name');
console.log(c_lib.ONE); // print 1
console.log(c_lib.TWO); // print 2
console.log(c_lib.THREE); // print 3
```

#### Types:

The table below shows which JavaScript type represent the particular C type.

| C type | JS type | Status |
| - | - | - |
| void | undefined | solved |
| char | one length String | solved |
| int / enum | Number | solved |
| float / double | Number | solved |
| _Bool | Boolean | solved |
| struct / union | Object | solved |
| char * / char [] | String | solved |
| int * / int [] | TypedArray | solved |
| function pointer | Function | WIP |

Other types are not supported, which means that you need to implement how you would like to use these parts of the C API.

##### Examples:

##### `void`
```c
void f(void);
```
```javascript
var a = c_lib.f(); // 'a' == undefined
```

##### `char`
```c
char c;
char f(char);
```
```javascript
c_lib.c = 'c';
var a = c_lib.f('b');
```

##### `int`
```c
int i;
int f(int);
```
```javascript
c_lib.i = 42;
var a = c_lib.f(5);
```

##### `enum`
```c
typedef enum {A, B, C} c_lib_enum;
c_lib_enum e;
c_lib_enum f(c_lib_enum);
```
```javascript
c_lib.e = c_lib.B;
var a = c_lib.f(c_lib.A);
```

##### `float/double`
```c
float f;
double d;
float f(float);
double g(double);
```
```javascript
c_lib.f = 1.5;
c_lib.d = 2.5;
var f = c_lib.f(1.5);
var d = c_lib.g(c_lib.d);
```

##### `bool`
```c
_Bool b;
_Bool f(_Bool);
```
```javascript
c_lib.b = true;
var a = c_lib.f(false);
```

##### `struct/union`
```c
typedef struct {int i; char c;} S;
typedef union {int i; char c;} U;
S s;
U u;
S f(S);
U g(U);
```
```javascript
// c_lib.s.i = 42; does NOT work
c_lib.s = {i:42, c:'a'};
c_lib.u = {i:42};
c_lib.u = {c:'a'};
var s = c_lib.f({c:'c', i:0});
var u = c_lib.g({i:0});
```

##### `char*/char[]`
```c
char * c_ptr;
char c_arr[6];
char* f(char*);
char* g(char[5]);
```
```javascript
c_lib.c_ptr = 'some string';
// c_lib.c_arr = 'maximum string length is 5'; does NOT work
c_lib.c_arr = 'wrks';
var f = c_lib.f('other string');
var g = c_lib.g('1234');
```

##### `int*/int[]`
```c
int * i_ptr;
int i_arr[5];
int* f(int*);
int* g(int[5]);
```
```javascript
var typed_array = new Int32Array(new ArrayBuffer(8), 0, 2);
typed_array[0] = 10;
typed_array[1] = 20;
c_lib.i_ptr = typed_array;
c_lib.i_ptr = null;
// c_lib.i_arr = typed_array; does NOT work
c_lib.i_arr[0] = 1;
c_lib.i_arr[1] = 2;
c_lib.i_arr[2] = 3;
var f = c_lib.f(null); // f is null or TypedArray
var g = c_lib.g(typed_array);
```

### Usage:

You can generate a module using the following command:

```bash
# assuming you are in iotjs folder
$ tools/iotjs_module_generator.py <INPUT_FOLDER>
```

The `<INPUT_FOLDER>` should contain the header files and the static library of the C API, and this is a required argument for the script. The script generates four files to the `iotjs/tools/module_generator/output/<INPUT_FOLDER>_module/` folder. A `.h`, `.c`, `.json` and a `.cmake` file. The module name will be `<INPUT_FOLDER>_module`. If you would like to modify how the module should work, you have to make some changes in the generated `.c` file.

#### Optional arguments:

The script has some optional arguments, which are the following:

##### `--off`
* `functions` | `variables` | `enums` | `macros`

Turn off the processing of the given part of the C API, which means that the script will not generate any code for this part, so you can not use this in the JS environment.

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> --off=enums --off=macros
```

##### `--no-lib`

Does not search for the static library and does not generate `.cmake` file.

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> --no-lib
```

##### `--define`

Define a macro for the clang preprocessor.

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> --define FOO --define BAR=42
```

##### `--defines`

A file, which contains macro definitions for the clang preprocessor.

`macro_defines.txt`:
```txt
FOO
BAR=42
```

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> --defines macro_defines.txt
```

##### `--include`

Add include path to search for other files.

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> --include path/to/the/include/folder/
```

##### `--includes`

A file, which contains include paths.

`includes.txt`:
```txt
path/to/include/folder
other/path/to/other/folder
```

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> --includes includes.txt
```

### Quick example:

#### Directory structure:

* iotjs/
* my_api/
  * foo/
    * foo.h
  * bar.h
  * libexample.a

#### Header files:

foo.h:
```c
#define N 10
int foo(int x); //return x+x
```

bar.h:
```c
typedef enum {A, B, C} flags;
void bar(); // print "Hello!"
```

#### Build:
```bash
# assuming you are in iotjs folder
$ tools/iotjs_module_generator.py ../my_api/
tools/build.py --external-module=tools/module_generator/output/my_api_module --cmake-param=-DENABLE_MODULE_MY_API_MODULE=ON
```

#### Usage:
api.js:
```javascript
// the name of the module is same as the directory name with '_module' suffix
var c_lib = require('my_api_module');
var x = c_lib.foo(2);
console.log(x); // print 4
c_lib.bar(); // print 'Hello!'
console.log(c_lib.N); // print 10
console.log(c_lib.B); // print 1
```
