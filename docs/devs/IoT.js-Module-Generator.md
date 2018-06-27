# C API to IoT.js module generator

This tool generates a module from a C API, and you can use it in IoT.js as other modules. The input of the generator is a directory, which contains the headers and the static library of the API.

### Dependecies:

#### Clang library:

```bash
apt install libclang1-5.0
```

#### Python binding for Clang:

```bash
apt install python-clang-5.0
```

### Example:

#### Directory structure:

* iotjs/
* example_api/
  * foo/
    * foo.h
  * bar.h
  * libexample.a

#### Header files:

foo.h:
```c
int foo(int x); //return x+x
```

bar.h:
```c
void bar(); // print "Hello!"
```

#### Build:
```bash
# assuming you are in iotjs folder
$ tools/build.py --generate-module=../example_api/
```

#### Usage:
api.js:
```javascript
// the name of the module is same as the directory name with '_module' suffix
var lib = require('example_api_module');
var x = lib.foo(2);
console.log(x); // print 4
lib.bar(); // print 'Hello!'
```

### Features:

The C library is represented as an object in the JavaScript environment. This object is the result of the `require` function with the right module name parameter.

```javascript
var c_lib = require('module_name');
```

#### Functions:

Every function from the C library are represented as properties of the library object. If there is a declaration, like `void foo(int);` in the C library, then the object has a property with the name `foo`.

```javascript
var c_lib = require('module_name');
c_lib.foo(42); // call the C function
```

#### Variables (WIP):

The global variables of the C library are also represented as properties. If there is a declaration, like `int a;` in the C library, then the object has a property with the name `a`, and you can get and set its value.

```javascript
var c_lib = require('module_name');
var a = c_lib.a; // get the value of a global variable from the C library
c_lib.a = 42; // set the value
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
| other pointers | ??? | WIP |

#### Macros (WIP):
