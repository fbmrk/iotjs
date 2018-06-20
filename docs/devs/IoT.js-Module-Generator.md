# C API to IoT.js module generator

This tool generates a module from a C API, and you can use it in IoT.js as other modules. The input of the generator is a directory, which contains the headers and the static library of the API.

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
console.log(x);                   // print 4
console.log(lib.bar());           // print 'Hello!'
```

### Resolved types:

| C type | JS type |
| - | - |
| void | undefined |
| char | one length String |
| int / enum | Number |
| float / double | Number |
| _Bool | Boolean |
| struct / union | Object |
| char * / char [] | String |
| int * / int [] | TypedArray |
