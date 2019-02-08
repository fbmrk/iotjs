# C/C++ API to IoT.js module generator

This tool generates a JS module from a C/C++ API, and you can use it in IoT.js like other modules. The input of the generator is a directory, which contains the C/C++ header files and the static library of the API.

1. [Dependencies](#dependencies)
2. [Features](#features)
    - [Classes](#classes)
    - [Functions](#functions)
    - [Variables](#variables)
    - [Enums](#enums)
    - [Macros](#macros)
    - [Namespaces](#namespaces)
3. [Supported types](#supported-types)
    - [Examples](#examples)
4. [Usage](#usage)
    - [Optional arguments](#optional-arguments)
5. [Quick example](#quick-example)

## Dependencies:

#### Clang library:

```bash
apt install libclang1-6.0
```

#### Python binding for Clang:

```bash
apt install python-clang-6.0
```

(The tool has been tested with the 5.0 and 6.0 versions.)


## Features:

The C/C++ library is represented as an object in the JavaScript environment. This object is the result of the `require` function call with the right module name parameter. The generated module name is the name of the input folder with `'_module'` suffix.

```javascript
var lib = require('module_name');
```

#### Classes:

If there is a class in the C++ library, the module object has a property with the name of the class, which is a constructor. You can create an object in JavaScript, if you call the constructor with the right parameters. The returned JavaScript variable has some properties, which are represent the members and methods of the class.

```cpp
class MyClass {
  int x;
public:
  MyClass(): x(0) {}
  MyClass(int x): x(x) {}

  void foo(void); // print x
};
```
```javascript
var cpp_lib = require('module_name');

var obj1 = new cpp_lib.MyClass();
var obj2 = new cpp_lib.MyClass(42);

obj1.foo(); // print 0
obj2.foo(); // print 42
```

#### Functions:

Every function from the C/C++ library are represented as properties of the library object.

**C :**

If there is a declaration, like `void foo(int);` in the C library, then the object has a property with the name `foo`.

```javascript
var c_lib = require('module_name');
c_lib.foo(42); // call the C function
```

**C++ :**

The different between C and C++ functions, that you can call C++ functions with the same name, but with different parameter lists. If there is a declaration, like `void foo(int = 0);` in the C++ library, you can use it as below. It works in the case of constructors and methods too.

```javascript
var cpp_lib = require('module_name');
cpp_lib.foo(); // call the C++ function with the default parameter
cpp_lib.foo(42);
```

#### Variables:

The global variables of the C/C++ library are also represented as properties. If there is a declaration, like `int a;` in the C library, then the object has a property with the name `a`, and you can get and set its value, but if there is a definition, like `const int b = 42;` you can only read the value from the property and you can not modify it.

C/C++ header:
```c
int i;
```

JS file:
```javascript
var lib = require('module_name');
lib.i = 1; // set the value of 'i'
console.log(lib.i); // print 1
```

#### Enums:

Enums work like constants above. You can read the value of the enumerator from a property, but you can not modify it.

C/C++ header:
```c
enum abc {A, B, C};
```

JS file:
```javascript
var lib = require('module_name');
console.log(lib.A); // print 0
console.log(lib.B); // print 1
console.log(lib.C); // print 2
```

#### Macros:

Macros also work like constants. You can read the value of the macro from a property, but you can not modify it. There are three supported macro types.
* If the macro defines a character literal, like `#define C 'c'`.
* If the macro defines a string literal, like `#define STR "str"`.
* If the macro defines a numeric literal, or contains some kind of operation, but the result is a number, like `#defines ZERO 0` or `#define TWO 1 + 1`. It also works, if the macro contains other macro identifiers.

C/C++ header:
```c
#define ONE 1
#define TWO 2
#define THREE ONE + TWO
```

JS file:
```javascript
var lib = require('module_name');
console.log(lib.ONE); // print 1
console.log(lib.TWO); // print 2
console.log(lib.THREE); // print 3
```

#### Namespaces:

In JavaScript a namespace represented as an object, which is set to another object as property. Concretely to the object, which represent the scope where the namespace is.

C++ header:
```c
namespace my_ns {
  void foo(void);

  namespace nested {
    void foo(void);
  }
}
```

JS file:
```javascript
var cpp_lib = require('module_name');

cpp_lib.my_ns.foo(); // my_ns::foo

with (lib.my_ns.nested) {
  foo(); // my_ns::nested::foo
}
```

**NOTE**: If there is a `using` command for a namespace in the native header, you also have to call functions etc. through the namespace object. You can use `with` in JavaScript to reduce the code.

## Supported types:

The table below shows which JavaScript type represent the particular C/C++ type.

### Fundamental types:

| C/C++ type | JS type |
| - | - |
| void | undefined |
| char | one length String |
| int / enum | Number |
| float / double | Number |
| _Bool / bool | Boolean |

### Record types:

If you would like to create a record type variable you have to call a constructor through the library object.

| C/C++ type | JS type |
| - | - |
| struct / union / class | Object |

### Pointer types:

If there is a char or int pointer in a native function's parameter list and you call this function from JavaScript with a String or TypedArray the binding layer alloc memory for the native pointers. If after the native call the pointers won't be used you should modify the source code of the binding layer and free them.

| C/C++ type | JS type |
| - | - |
| char * / char [] | String / Null |
| int * / int [] | TypedArray / Null |
| function pointer | Function / Null |
| record pointer (only as function parameter) | Object / Null |

**NOTE**: Other types are not supported, which means that you need to implement how you would like to use these parts of the C/C++ API.

#### Examples:

##### `void`
```c
void f(void);
```
```javascript
var a = lib.f(); // 'a' == undefined
```

##### `char`
```c
char c;
char f(char);
```
```javascript
lib.c = 'c';
var a = lib.f('b');
```

##### `int`
```c
int i;
int f(int);
```
```javascript
lib.i = 42;
var a = lib.f(5);
```

##### `enum`
```c
typedef enum {A, B, C} my_enum;
my_enum e;
my_enum f(my_enum);
```
```javascript
lib.e = lib.B;
var a = lib.f(lib.A);
```

##### `float/double`
```c
float f;
double d;
float f(float);
double g(double);
```
```javascript
lib.f = 1.5;
lib.d = 2.5;
var f = lib.f(1.5);
var d = lib.g(lib.d);
```

##### `bool`
```c
_Bool b;
_Bool f(_Bool);
```
```javascript
lib.b = true;
var a = lib.f(false);
```

##### `char*/char[]`

If there is global pointer to a char, its value could be `null` or a `String`.

```c
char * c_ptr;
char c_arr[6];
char* f(char*);
char* g(char[5]);
```
```javascript
lib.c_ptr = 'some string';
// lib.c_arr = 'maximum string length is 5'; NOT WORK
lib.c_arr = 'works';
var f = lib.f('other string'); // returned value can be null or String
var g = lib.g('1234');
```

##### `int*/int[]`

If there is global pointer to a number, its value could be `null` or a `TypedArray`. If there is an array of numbers, it will be a `TypedArray` in the JS environment, and you can set the values by indexing.

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
lib.i_ptr = typed_array;
lib.i_ptr = null;
// lib.i_arr = typed_array; NOT WORK
lib.i_arr[0] = 1;
lib.i_arr[1] = 2;
lib.i_arr[2] = 3;
var f = lib.f(null); // returned value can be null or TypedArray
var g = lib.g(typed_array);
```

##### `function`

Function pointers supported as parameters. There can be cases when it does not work correctly, if the function will be called asynchronous.

```c
typedef int (callback)(void);

int f(callback c) {
  return c();
}
```
```javascript
var a = lib.f(function () {
  return 42;
});
```

Let's see a dummy example, when function pointers work incorrectly.

```c
typedef void (cb)(void);

cb cb_arr[2];

void foo(cb c) {
  static int i = 0;
  cb_arr[i++] = c;
}

void bar(void) {
  cb_arr[0]();
}
```
```javascript
lib.foo(function() {
  console.log('first callback');
});

lib.foo(function() {
  console.log('second callback');
});

// the second foo call overwrite the first callback function
// it will print 'second callback', which is not the expected
lib.bar();
```

##### `struct / union / class`

```cpp
typedef struct {
  int i;
  char c;
} S;

typedef union {
  int i;
  char c;
} U;

class C {
  int i = 42;
public:
  int get_i() {return i;}
};

S s;
U u;
C c;
S f(S);
U g(U);
C h(C);
void ptr(S*);
```
```javascript
var s = new lib.S();
var u = new lib.U();
var c = new lib.C();

s.i = 42;
s.c = 's';
lib.s = s;
lib.s.i = 0;

// var o = {
//   i: 42,
//   c: 'o'
// }
//
// lib.f(o); NOT WORK 'o' is not a valid S type object
var other_s = lib.f(s);
var other_u = lib.g(u);
var other_c = lib.h(c);
lib.ptr(s);

console.log(lib.c.get_i());
```

## Usage:

You can generate a module using the following command:

```bash
# assuming you are in iotjs folder
$ tools/iotjs_module_generator.py <INPUT_FOLDER> <LANG>
```

The `<INPUT_FOLDER>` should contain the header files and the static library of the C/C++ API. `<LANG>` is the language of the API, which can be `c` or `c++`. These are required arguments for the script. The script generates the source files to the `iotjs/tools/module_generator/output/<INPUT_FOLDER>_module/` folder. The module name will be `<INPUT_FOLDER>_module`. If you would like to modify how the module should work, you have to make some changes in the generated `.c` or `.cpp` file.

#### Optional arguments:

The script has some optional arguments, which are the following:

##### `--out-dir`

The output folder of the generated module. Default is `tools/module_generator/output`

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> <LANG> --out-dir <OUTPUT_FOLDER>
```

##### `--off`
* `functions` | `variables` | `enums` | `macros`

Turn off the processing of the given part of the C API, which means that the script will not generate any code for this part, so you can not use this in the JS environment.

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> <LANG> --off=enums --off=macros
```

##### `--define`

Define a macro for the clang preprocessor.

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> <LANG> --define FOO --define BAR=42
```

##### `--defines`

A file, which contains macro definitions for the clang preprocessor.

`macro_defines.txt`:
```txt
FOO
BAR=42
```

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> <LANG> --defines macro_defines.txt
```

##### `--include`

Add include path to search for other files.

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> <LANG> --include path/to/the/include/folder/
```

##### `--includes`

A file, which contains include paths.

`includes.txt`:
```txt
path/to/include/folder
other/path/to/other/folder
```

```bash
$ tools/iotjs_module_generator.py <INPUT_FOLDER> <LANG> --includes includes.txt
```

## Quick example:

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
$ tools/iotjs_module_generator.py ../my_api/ c
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
