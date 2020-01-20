Porting SV to Python
====================

This document describes some specifics how to port certain SystemVerilog
constructs into Python code. Python does not have pass-by-reference option for
function arguments, so another solution should be found. It is a first draft to
present some ideas how to port the code.

SV Queue and Assoc. Array as ref args
-------------------------------------

As lists and dicts can be freely mutated in Python, in cases where queue or
associative array is expected, we can replaced them with list/dict in Python.

```systemverilog
function void get_maps(ref uvm_reg_map maps[$]);
function void get_blocks (ref uvm_reg_block blks[string], ...)
```

```python
def get_maps(maps: list)
def get_blocks (blks: list, ...)
```

To make error detection easier, it would make sense to check that given argument
is of required type, and raise an exception (?) if there is a type error.


One possibility is to overload the function to behave differently depending on
the argument given:

```systemverilog
  function void get_args (output string args[$]);  // SV
    args = m_argv;
  endfunction
```

```python
  def get_args(self, args=None):  # Python
      if args is None:
        return self.m_arg.copy()
      elif isinstance(args, list):
          args.extend(self.m_argv)
      else:
          # Exception
```


In cases where both return value and ref/output args are needed, following can
be done:

```systemverilog
  function int get_arg_matches (string match, ref string args[$]);
```

```python
  def get_arg_matches(match, args=None):
    matched_args = []
    ...
    if args is None:
        return matched_args
    else:
        args.extend(matched_args)
        return len(args)  # Or whatever must be returned

  # Usage
  args = get_arg_matches("+UVM_TEST_NAME=")
  # OR
  args = []
  num_args = get_arg_matches("+UVM_TEST_NAME=", args)
```

However, caller must be aware of this overloading and different return values
based on input argument.

TLM 1.0
-------

SystemVerilog cannot return any values from tasks, but Python does not have this
limitations. Porting blocking TLM tasks with ref/output argument is done like
this:

```systemverilog
  task get (output TYPE arg);  // SV
```

```python
  def get(self):  # Python
    ...

  # Usage
  arg = yield tlm_port.get()  # Usage
```


Nonblocking TLM 1.0 functions are ported like this:

```systemverilog
  function bit try_get (output TYPE arg);  // SV
```

```python
  TLM_CALL_FAILED = [False, None]
  def try_get():
      ...
      if success:
          return [True, value]
      else:
          return TLM_CALL_FAILED
```



Pass-by-reference and output arguments
--------------------------------------

In the rare case, that pass-by-reference is really needed, a following helper
class can be used (proposed by eric-wieser):

```python
class ref:
    def __bool__(self):
        return hasattr(self, 'value')

t = ref()
yield tlm_port.get(t)
print(t.value)
```

What about several output arguments like in the task below:

```systemverilog
   extern virtual task read_reg_by_name(
          output uvm_status_e       status,
          input  string             name,
          output uvm_reg_data_t     data,
          input  uvm_path_e    path = UVM_DEFAULT_PATH,
          ...
   )
```

```python
    def read_reg_by_name(status, name, data, path=UVM_DEFAULT_PATH ...)

    # Usage
    # Return output args as a list
    [status, data] = yield read_reg_by_name(status, "reg_name", data)
    # OR as a dict
    my_dict = yield read_reg_by_name(status, "reg_name", data)
    # my_dict.status and my_dict.data should exist now
```
