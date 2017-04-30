import pytest

import dicty


def test_shadow():
    class Object(dicty.DictObject):
        foo = dicty.ShadowField()

    obj = Object()
    with pytest.raises(AttributeError):
        obj.foo
    obj.foo = 123
    assert obj == {'foo': 123}
    assert obj._shadow == {'foo': 123}

    with pytest.raises(dicty.FieldError):
        Object.fromjson({})

    class Object(dicty.DictObject):
        foo = dicty.ShadowField(optional=True)
    obj = Object()
    assert obj.foo is None
    obj = Object.fromjson({})
    assert obj == {}


def test_filters():
    class Object(dicty.DictObject):
        foo = dicty.Field(filters=[lambda x: x.upper()])
    obj = Object.fromjson({'foo': 'xxx'})
    assert obj.foo == 'XXX'
    assert obj == {'foo': 'XXX'}

    def failure(value):
        raise ValueError('failure {}'.format(value))

    class Object(dicty.DictObject):
        foo = dicty.Field(filters=[failure])

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'foo': 'xxx'})
    assert exc.value.path == 'foo'
    assert exc.value.args == ('failure xxx',)

    # Shadow filters
    class Object(dicty.DictObject):
        foo = dicty.ShadowField(filters=[lambda x: x.upper()])

    obj = Object.fromjson({'foo': 'xxx'})
    assert obj.foo == 'XXX'
    assert obj._shadow == {'foo': 'XXX'}
    assert obj == {'foo': 'xxx'}


def test_typed_list_field():
    class Nested(dicty.DictObject):
        foo = dicty.Field()

    class Object(dicty.DictObject):
        nested = dicty.TypedListField(Nested)

    obj = Object.fromjson({'nested': []})
    assert obj.nested == []

    obj = Object.fromjson({'nested': [{'foo': 123}]})
    assert obj.nested[0].foo == 123

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'nested': [{}]})
    assert exc.value.path == 'nested[0].foo'
    assert exc.value.args == ('Is required',)

    obj = Object()
    assert obj.nested == []
    obj.nested.append(Nested(foo=123))
    assert obj == {'nested': [{'foo': 123}]}

    with pytest.raises(dicty.FieldError) as exc:
        Object.fromjson({'nested': 123})
    assert exc.value.path == 'nested'
    assert exc.value.args == ('must be list',)


def test_typed_dict_field():
    class Nested(dicty.DictObject):
        foo = dicty.Field()

    class Object(dicty.DictObject):
        nested = dicty.TypedDictField(Nested)

    obj = Object.fromjson({'nested': {}})
    assert obj.nested == {}

    obj = Object.fromjson({'nested': {'xxx': {'foo': 123}}})
    assert obj.nested['xxx'].foo == 123

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'nested': {'xxx': {}}})
    assert exc.value.path == "nested['xxx'].foo"
    assert exc.value.args == ('Is required',)

    obj = Object()
    assert obj.nested == {}
    obj.nested['xxx'] = Nested(foo=123)
    assert obj == {'nested': {'xxx': {'foo': 123}}}

    with pytest.raises(dicty.FieldError) as exc:
        Object.fromjson({'nested': 123})
    assert exc.value.path == 'nested'
    assert exc.value.args == ('must be dict',)


def test_integer_field():
    class Object(dicty.DictObject):
        foo = dicty.IntegerField()

    obj = Object.fromjson({'foo': 123})
    assert obj == {'foo': 123}

    # obj = Object.fromjson({'foo': 123L})
    # assert obj == {'foo': 123L}

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'foo': 1.223})
    assert exc.value.path == 'foo'


def test_float_field():
    class Object(dicty.DictObject):
        foo = dicty.FloatField()

    obj = Object.fromjson({'foo': 1.234})
    assert obj == {'foo': 1.234}

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'foo': 123})
    assert exc.value.path == 'foo'


def test_string_field():
    class Object(dicty.DictObject):
        foo = dicty.StringField()

    obj = Object.fromjson({'foo': "string"})
    assert obj == {'foo': "string"}

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'foo': 123})
    assert exc.value.path == 'foo'


def test_regexp_string_field():
    class Object(dicty.DictObject):
        foo = dicty.RegexpStringField(regexp="^a+$")

    obj = Object.fromjson({'foo': "aaa"})
    assert obj == {'foo': "aaa"}

    with pytest.raises(dicty.FieldError) as exc:
        obj = Object.fromjson({'foo': 'bbb'})
    assert exc.value.path == 'foo'
    assert exc.value.args == ('Does not match regular expression',)


def test_dict_of_lists_of_objects_regression():
    class Foo(dicty.DictObject):
        foo = dicty.StringField()

    class Bar(dicty.DictObject):
        foos = dicty.TypedDictField(
            dicty.TypedListField(Foo), optional=True)

    o = Bar.fromjson({'foos': {'x': [{'foo': 'foo'}, {'foo': 'bar'}]}})
    assert o.jsonize() == {'foos': {'x': [{'foo': 'foo'}, {'foo': 'bar'}]}}
