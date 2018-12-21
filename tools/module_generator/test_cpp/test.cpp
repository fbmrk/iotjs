#include <iostream>
#include "test.h"

char c;
int i;
float f;
double d;
bool b;
char* c_ptr;
char c_arr[5];
int* i_ptr;
int i_arr[5];

S s;
U u;

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

bool f_bool (bool a)
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
  if (f)
  {
    return f();
  }
  return 0;
}

int f_func_ptr (func_ptr f)
{
  if (f)
  {
    return f();
  }
  return 0;
}
