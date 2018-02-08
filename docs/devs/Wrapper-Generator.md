# How to use C++ to JS wrapper generator

This tool generates a wrapper from a C++ class, and you can use it in Javascript as a module.

### Example:

#### Directory structure:

* iotjs
* my_project
  * example.cpp
  * example.h

#### Source file:

example.h:
```cpp
class MyClass {

public:
  MyClass() {}

  int foo();
};
```

example.cpp:
```cpp
#include "example.h"

int MyClass::foo() {
  return 13;
}
```

#### Build:
```bash
# assuming you are in iotjs folder
$ tools/build.py --gen-wrap-cpp=../my_project/example.cpp --gen-wrap-header=../my_project/example.h --gen-wrap-class=MyClass
```

#### Usage:
myclass.js:
```javascript
var MyClass = require('myclass');
var obj = new MyClass();
console.log(obj.foo());           // print 13
```
