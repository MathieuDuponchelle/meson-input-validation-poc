import unittest

from schema_helpers import *


nonEmptyStr = NonEmptyString()
anything = Anything()


def foo_no_args_no_kwargs():
    pass


def bar_no_args_no_kwargs():
    pass


def bar_single_arg_no_kwargs(first_arg):
    pass


def bar_single_arg_multiple_extra_args_no_kwargs(first_arg, extra_arg_list):
    pass


def baz_no_args_required_kwarg1(kwarg1):
    pass


def foobar_no_args_optional_kwarg1(kwarg1):
    return kwarg1


def barfoo_autolist_arg(arglist):
    return arglist


# Order matters, "catch-all" prototypes should come last
prototypes = {
        'foo': [Prototype(foo_no_args_no_kwargs, [])],
        'bar': [Prototype(bar_no_args_no_kwargs, []),
                Prototype(bar_single_arg_no_kwargs, [nonEmptyStr]),
                Prototype(bar_single_arg_multiple_extra_args_no_kwargs,
                          [nonEmptyStr], extra_arg_type=anything)],
        'baz': [Prototype(baz_no_args_required_kwarg1, [], None, {'kwarg1': nonEmptyStr})],
        'foobar': [Prototype(foobar_no_args_optional_kwarg1, [], None, {Optional('kwarg1', default='foo'): nonEmptyStr})],
        'barfoo': [Prototype(barfoo_autolist_arg, [AutoList(nonEmptyStr)])]}


def try_prototypes(name, args, kwargs):
    errors = []
    autos = []
    for p in prototypes[name]:
        try:
            return p.validate(args, kwargs)
        except SchemaError as x:
            autos += x.autos
            errors += x.errors

    res = [] 
    raise SchemaError([''.join(res)] + autos, [None] + errors)


class TestPrototype(unittest.TestCase):
    def test_single_prototype(self):
        func, args, kwargs = try_prototypes('foo', [], {})
        self.assertEqual(func, foo_no_args_no_kwargs)
        func(*args, **kwargs)
        with self.assertRaises(SchemaError):
            func, args, kwargs = try_prototypes('foo', ['bar'], {})

    def test_multiple_prototypes(self):
        func, args, kwargs = try_prototypes('bar', [], {})
        self.assertEqual(func, bar_no_args_no_kwargs)
        func(*args, **kwargs)
        func, args, kwargs = try_prototypes('bar', ['foo'], {})
        self.assertEqual(func, bar_single_arg_no_kwargs)
        func(*args, **kwargs)
        func, args, kwargs = try_prototypes('bar', ['foo', 42, 'baz'], {})
        self.assertEqual(func, bar_single_arg_multiple_extra_args_no_kwargs)
        func(*args, **kwargs)

    def test_required_kwarg(self):
        func, args, kwargs = try_prototypes('baz', [], {'kwarg1': 'foo'})
        self.assertEqual(func, baz_no_args_required_kwarg1)
        func(*args, **kwargs)
        with self.assertRaises(SchemaError):
            func, args, kwargs = try_prototypes('baz', [], {'kwarg1': 42})
        with self.assertRaises(SchemaError):
            func, args, kwargs = try_prototypes('baz', [], {'kwarg1': 'foo', 'kwarg2': 'bar'})
        with self.assertRaises(SchemaError):
            func, args, kwargs = try_prototypes('baz', [], {})

    def test_optional_kwarg(self):
        func, args, kwargs = try_prototypes('foobar', [], {})
        self.assertEqual(func, foobar_no_args_optional_kwarg1)
        self.assertEqual(func(*args, **kwargs), 'foo')
        func, args, kwargs = try_prototypes('foobar', [], {'kwarg1': 'bar'})
        self.assertEqual(func, foobar_no_args_optional_kwarg1)
        self.assertEqual(func(*args, **kwargs), 'bar')

    def test_autolist(self):
        func, args, kwargs = try_prototypes('barfoo', ['foo'], {})
        self.assertEqual(func, barfoo_autolist_arg)
        self.assertEqual(func(*args, **kwargs), ['foo'])
        func, args, kwargs = try_prototypes('barfoo', [['foo', 'bar']], {})
        self.assertEqual(func, barfoo_autolist_arg)
        self.assertEqual(func(*args, **kwargs), ['foo', 'bar'])
        with self.assertRaises(SchemaError):
            func, args, kwargs = try_prototypes('barfoo', [], {})

if __name__ == '__main__':
    for name, protos in prototypes.items():
        for p in protos:
            print (p.format (name))
