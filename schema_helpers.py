# Copyright 2016 The Meson development team

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import itertools

from schema import *

anyKwArgs = {Optional(str): object}

class NonEmptyString:
    def validate(self, data):
        return And(str, len).validate(data)

    def __repr__(self):
        return 'Non-empty string'


class Anything(object):
    def validate(self, data):
        return True

    def __repr__(self):
        return 'Anything'


class AutoList(object):
    def __init__(self, validator, error=None):
        self._nested_validator = validator
        self._validator = Schema(validator)
        self._list_validator = Schema([validator], error=error)
        self._error = error

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._nested_validator)

    def __str__(self):
        return '%s, optionally in a list' % (self._nested_validator)

    def validate(self, data):
        try:
            return [self._validator.validate(data)]
        except SchemaError:
            pass

        return self._list_validator.validate(data)


class TypedList(object):
    def __init__(self, types, extra_type=None, error=None):
        self._types = types
        self._error = error
        self._extra_type = extra_type

    def __repr__(self):
        return '%s(%r %r)' % (self.__class__.__name__, self._types, self._extra_type)

    def validate(self, data):
        new_data = []
        if not self._extra_type:
            if not isinstance(data, (list, tuple)) or len(data) != len(self._types):
                raise SchemaError(
                        '%r should be a list of size %d' % (data, len(self._types)),
                        self._error.format(data) if self._error else None)
        else:
            if not isinstance(data, (list, tuple)) or len(data) < len(self._types):
                raise SchemaError(
                        '%r should be a list of minimum size %d' % (data, len(self._types)),
                        self._error.format(data) if self._error else None)

        i = -1
        for i, t in enumerate(self._types):
            try:
                new_data.append(Schema(t).validate(data[i]))
            except SchemaError as x:
                raise SchemaError([None] + x.autos, [self._error] + x.errors)

        for d in data[i+1:]:
            try:
                new_data.append(Schema(self._extra_type).validate(d))
            except SchemaError as x:
                raise SchemaError([None] + x.autos, [self._error] + x.errors)

        return new_data


class Prototype:
    def __init__(self, func, pos_args, extra_arg_type=None, kw_args=None):
        assert (kw_args is None or isinstance(kw_args, dict))
        self.args_schema = TypedList(pos_args, extra_type=extra_arg_type)
        self.kwargs_schema = Schema(kw_args or {})
        self.func = func

    def validate(self, args, kwargs):
        new_args = self.args_schema.validate(args)
        new_kwargs = self.kwargs_schema.validate(kwargs)
        extra_args = new_args[len(self.args_schema._types):]
        new_args = new_args[:len(self.args_schema._types)]
        if (extra_args):
            new_args.append(extra_args)
        return self.func, new_args, new_kwargs

    def format(self, func_name):
        params = []
        sig = inspect.signature (self.func)
        sig_params = list(sig.parameters.values())
        pos_args = zip(sig_params[:len(self.args_schema._types)],
            self.args_schema._types)

        if (self.args_schema._extra_type):
            extra_arg = (sig_params[len(self.args_schema._types)],
                self.args_schema._extra_type)
            kwargs = zip(sig_params[len(self.args_schema._types) + 1:],
                self.kwargs_schema._schema.values())
        else:
            kwargs = zip(sig_params[len(self.args_schema._types):],
                self.kwargs_schema._schema.values())
            extra_arg = None

        indent = ' ' * (len(func_name) + 1)

        for param, type_ in pos_args:
            params.append ('%s<%s> (%s)' % (indent if params else '',
                                            param.name,
                                            str(type_)))

        if extra_arg:
            params.append ('%s<%s, ...> (%s)' % (indent if params else '',
                                                 extra_arg[0].name,
                                                 str(self.args_schema._extra_type)))

        for param, type_ in kwargs:
            params.append ('%s%s: <%s>' % (indent if params else '',
                                            param.name,
                                            str(type_)))

        res = '%s(%s)' % (func_name, ',\n'.join (params))
        return res
