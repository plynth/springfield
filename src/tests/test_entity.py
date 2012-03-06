from springfield import Entity, FlexEntity, fields
import pytest

def test_entity():
    class TestEntity(Entity):
        id = fields.IntField()
        name = fields.StringField()
        bool = fields.BooleanField()

    e = TestEntity(id='1', bool='1')
    e.name = 'foo'

    assert e.id == 1
    assert e.name == 'foo'
    assert e.bool is True


    with pytest.raises(AttributeError):
        e.invalid_field

def test_bool_field():
    class TestEntity(Entity):
        bool = fields.BooleanField()

    e = TestEntity()
    
    for i in [True, 'yes', 'YES', 'on', 'true', '1', 1]:
        e.bool = i
        assert e.bool is True

    for i in [False, 'no', 'OFF', 'off', 'FALSE', '0', 0]:
        e.bool = i
        assert e.bool is False

    e.bool = None
    assert e.bool is None


    for i in [22, object(), 2.4, 'frag']:
        with pytest.raises(TypeError):
            e.bool = i

def test_flex_entity():
    class TestEntity(FlexEntity):
        id = fields.IntField()
        name = fields.StringField()

    e = TestEntity(name='test', nofield='foo')
    assert e.name == 'test'
    assert e.nofield == 'foo'

def test_entity_field():
    class SubEntity(Entity):  
        id = fields.IntField()

    class TestEntity(Entity):    
        sub = fields.EntityField(SubEntity)

    e = TestEntity(sub=dict(id='2'))
    assert e.sub.id == 2
