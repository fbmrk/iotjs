var assert = require("assert");
var lib = require("test_module");

// MACROS
assert.equal(lib.BIN, 5);
assert.equal(lib.DEC, 42);
assert.equal(lib.OCT, 15);
assert.equal(lib.HEX, 255);
assert.equal(lib.one_l, 1);
assert.equal(lib.one_L, 1);
assert.equal(lib.one_u, 1);
assert.equal(lib.one_U, 1);
assert.equal(lib.SIGNED, -42);
assert.equal(lib.FLOAT, 1.5);
assert.equal(lib.SFLOAT, -1.5);
assert.equal(lib.PI, 3.14159);
assert.equal(lib.CH, 'a');
assert.equal(lib.STRING, 'AaBb');
assert.equal(lib.ONE, 1);
assert.equal(lib.TWO, 2);
assert.equal(lib.THREE, 3);

// VARIABLES
assert.equal(lib.c, '\u0000');
assert.equal(lib.i, 0);
assert.equal(lib.A, 0);
assert.equal(lib.B, 10);
assert.equal(lib.f, 0);
assert.equal(lib.d, 0);
assert.equal(lib.b, false);
assert.equal(lib.test_s.i, 0);
assert.equal(lib.test_s.c, '\u0000');
assert.equal(lib.test_u.i, 0);
assert.equal(lib.test_u.c, '\u0000');
assert.equal(lib.c_ptr, null);
assert.equal(lib.c_arr, '');
assert.equal(lib.i_ptr, null);
assert.equal(lib.i_arr.length, 5);
for (var i = 0; i < 5; i++) {
 assert.equal(lib.i_arr[i], 0);
}

lib.c = 'Z';
assert.equal(lib.c, 'Z');

lib.i = 42;
assert.equal(lib.i, 42);

lib.A = 1;
lib.B = 2;
assert.equal(lib.A, 0);
assert.equal(lib.B, 10);

lib.f = 1.5;
assert.equal(lib.f, 1.5);

lib.d = 2.5;
assert.equal(lib.d, 2.5);

lib.b = undefined;
assert(!lib.b);
lib.b = null;
assert(!lib.b);
lib.b = true;
assert(lib.b);
lib.b = 0;
assert(!lib.b);
lib.b = 1;
assert(lib.b);
lib.b = '';
assert(!lib.b);
lib.b = 't';
assert(lib.b);
lib.b = {};
assert(lib.b);

lib.test_s = {i: 11, c: 's'};
assert.equal(lib.test_s.i, 11);
assert.equal(lib.test_s.c, 's');

lib.test_u = {i: 65};
assert.equal(lib.test_u.i, 65);
lib.test_u = {c: 'u'};
assert.equal(lib.test_u.c, 'u');
lib.test_u = {i: 65, c: 'u'};
assert.equal(lib.test_u.c, 'u');

lib.c_ptr = 'abcdefghijklmnopqrstuvwxyz';
assert.equal(lib.c_ptr, 'abcdefghijklmnopqrstuvwxyz');
lib.c_ptr = '';
assert.equal(lib.c_ptr, '');

lib.c_arr = 'a';
assert.equal(lib.c_arr, 'a');
lib.c_arr = 'ab';
assert.equal(lib.c_arr, 'ab');
lib.c_arr = 'abc';
assert.equal(lib.c_arr, 'abc');
lib.c_arr = 'abcd';
assert.equal(lib.c_arr, 'abcd');
lib.c_arr = 'abcde';
assert.equal(lib.c_arr, 'abcd');

var i_ptr = new Int32Array(new ArrayBuffer(4), 0, 1);
i_ptr[0] = 42;
lib.i_ptr = i_ptr;
assert.equal(lib.i_ptr[0], 42);
assert.equal(lib.i_ptr[0], i_ptr[0]);
assert(lib.i_ptr instanceof Int32Array);
lib.i_ptr = null;
assert.equal(lib.i_ptr, null);

assert(lib.i_arr instanceof Int32Array);
for (var i = 0; i < 5; i++) {
 lib.i_arr[i] = i*i;
}
for (var i = 0; i < 5; i++) {
 assert.equal(lib.i_arr[i], i*i);
}
lib.i_arr = null;
assert(lib.i_arr instanceof Int32Array);

// FUNCTIONS
assert.equal(lib.f_void(), undefined);
assert.equal(lib.f_int(5), 5);
assert.equal(lib.f_char('a'), 'a');
assert.equal(lib.f_enum(lib.A), 0);
assert.equal(lib.f_float(1.5), 1.5);
assert.equal(lib.f_double(2.5), 2.5);
assert.equal(lib.f_bool(true), true);
assert.equal(lib.f_struct({i:42}).i, 42);
assert.equal(lib.f_struct({c:'A'}).c, 'A');
assert.equal(lib.f_union({i:42}).i, 42);
assert.equal(lib.f_union({c:'A'}).c, 'A');
assert.equal(lib.f_char_ptr('string'), 'string');
assert.equal(lib.f_char_arr('string'), 'string');
assert.equal(lib.f_int_ptr(null), null);
assert.equal(lib.f_int_ptr(i_ptr)[0], 42);
assert.equal(lib.f_int_arr(null), null);
assert.equal(lib.f_int_arr(i_ptr)[0], 42);
assert.equal(lib.f_func(function () {
  return 42;
}), 42);
assert.equal(lib.f_func_ptr(function () {
  return 42;
}), 42);

console.log('Test Run Succeeded!');
