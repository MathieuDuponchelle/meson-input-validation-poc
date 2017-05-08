# Meson input validation POC

A simple proof-of-concept for user input validation in meson.

In that context, user input is limited to the Domain Specific Language
exposed by meson, and parsed from `meson.build` and `meson_options.txt` files.

## Proposed approach

The proposed approach is [ad hoc polymorphism]: where meson currently maps
function names from its Domain Specific Language (hereafter DSL-name) with
a python method that accepts generic arguments and implements both input
validation and the actual behaviour (hereafter implementation), I propose
mapping the DSL-name with a (list of) Prototype object(s), which will be
in charge of:

* performing input validation
* preparing adequate args and kwargs, to be passed to the implementation,
  which would now accept *explicit* arguments.

Illustration (pseudo-code):

Where we had:

``` python
def foo (*args, **kwargs):
    # Input validation, implementation

...

funcs = {'foo': foo}
funcs(args, kwargs)
```

We would now have:

``` python
def foo(arg1, arg2, arg3):
    # Implementation, arguments are guaranteed to have the correct type,
    # possibly having been validated against callables (os.path.exists ..),
    # etc.

prototypes = {'foo': Prototype(foo, ...)}
func, args, kwargs = get_prototype(args, kwargs)
func(*args, **kwargs)
```

See the unit tests in `test_prototype.py` for more detailed examples,
run them with `python3 -m unittest test_prototype.py`

## Going further

While this isn't in the scope of this simple proposal, two areas that
would directly benefit from this approach are error reporting and
generating the DSL reference (the current Reference-Manual.md).

Regarding error reporting, we should ideally be able to match the raw
user input with the reported error, in order to provide the user with
compiler-grade error reporting (showing the exact line and column where the
error occured, along with a helpful message).

Regarding documentation, I've already started playing around a bit in error
to generate user-readable prototypes, I'm not yet entirely sure about the
formatting (I did see the proposal on the playground page). You can
look at the formatted versions of the currently tested prototypes by running
`python3 test_prototype.py`

## Existing solutions

A promising feature currently being developed in python itself is the
[typing] module. The reasons why I didn't pick this solution are:

* Very recent
* This API is explicitly advertised as unstable
* It doesn't support lists of prototypes, ie matching user input
  with one or another implementation.

## Legal note

I chose to base my work on an MIT-licensed python module, called "schema", which
is a tiny (one single file) and IMHO pretty neat and expressive way to perform
input validation.

[ad hoc polymorphism]: https://en.wikipedia.org/wiki/Ad_hoc_polymorphism
[typing]: https://docs.python.org/3/library/typing.html
