from springfield import Entity, FlexEntity, fields, Empty
import pytest

class PositionEntity(Entity):
    top = fields.IntField()
    left = fields.IntField()

class ChildEntity(Entity):
    id = fields.IntField()
    slug = fields.StringField()
    pos = PositionEntity

class ExampleTestEntity(Entity):
    id = fields.IntField()
    name = fields.StringField()
    child = ChildEntity

def test_dot_notation():
    e = ExampleTestEntity()

    assert e['child'] is None
    assert e['child'] is e.child

    # Use soak to allow empty fields
    assert e['child?.pos'] is Empty
    assert not e['child?.pos']
    assert e['child?.pos?.top'] is Empty
    assert not e['child?.pos?.top']

    with pytest.raises(ValueError):
        # `child` is empty so `child.pos` should fail
        e['child.pos']

    with pytest.raises(ValueError):
        # `child.pos` is empty so `child.pos.top` should fail
        e['child.pos.top']

    with pytest.raises(KeyError):
        # `child.foo` does not exist
        e['child.foo']

    # Set by dot notation
    e['child.pos.top'] = 10
    assert e.child.pos.top == 10
    assert e['child.pos.top'] == 10
    assert e['child.pos'] is e.child.pos

    # Setting with a soak ignores the soak
    e.child = None
    assert e['child'] is None

    e['child?.pos.top'] = 10
    assert e.child.pos.top == 10    

    # Can not set invalid fields
    with pytest.raises(KeyError):
        # `child.foo` does not exist
        e['child.foo'] = 10

    # Test update
    e.update({
        'child.pos.top': 20,
        'child.pos.left': 21,
    })

    assert e.child.pos.top == 20
    assert e.child.pos.left == 21

    e.child.pos = {'top': 14}
    assert e.child.pos.top == 14

    # Test creating a new Entity
    e2 = ExampleTestEntity(**{
        'child.pos': {'top': 12, 'left': 67},
    })

    assert e2.child.pos.top == 12
    assert e2.child.pos.left == 67    


