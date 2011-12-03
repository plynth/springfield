from springfield import Entity, FlexEntity, fields
import pytest

def test_entity():
    class TestEntity(Entity):
        id = fields.IntField()
        name = fields.StringField()

    e = TestEntity(id='1')
    e.name = 'foo'

    assert e.id == 1
    assert e.name == 'foo'

    with pytest.raises(AttributeError):
        e.invalid_field

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
