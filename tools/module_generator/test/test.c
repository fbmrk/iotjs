#include "test.h"

void f_void (void)
{
  return;
}

int f_int (int a)
{
  return a;
}

char f_char (char a)
{
  return a;
}

e f_enum (e a)
{
  return a;
}

float f_float (float a)
{
  return a;
}

double f_double (double a)
{
  return a;
}

_Bool f_bool (_Bool a)
{
  return a;
}

S f_struct (S a)
{
  return a;
}

U f_union (U a)
{
  return a;
}

char* f_char_ptr (char* a)
{
  return a;
}

char* f_char_arr (char a[5])
{
  return a;
}

int* f_int_ptr (int* a)
{
  return a;
}

int* f_int_arr (int a[5])
{
  return a;
}

int f_func (func f)
{
  return f();
}

int f_func_ptr (func_ptr f)
{
  return f();
}
