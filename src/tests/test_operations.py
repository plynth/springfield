import pickle
from springfield import Entity, fields
from springfield.timeutil import utcnow

class SampleEntity(Entity):
    id = fields.IntField()
    name = fields.StringField()
    slug = fields.StringField()
    url = fields.UrlField()
    bool = fields.BooleanField()
    entity = fields.EntityField('self')
    collection = fields.CollectionField(fields.StringField)
    entity_collection = fields.CollectionField(fields.EntityField('self'))
    date = fields.DateTimeField()

def test_pickle():
    """
    Make sure a Pickled entity comes out with the same values
    """
    entity = SampleEntity(
        id=1,
        name='test name',
        slug='test-slug',
        url='http://example.com',
        book=True,
        collection=['a', 'b', 'c', 'd'],
        entity_collection=[SampleEntity(id=2),SampleEntity(id=3),SampleEntity(id=4)],
        entity=SampleEntity(id=5, name='sample 5'),
        date=utcnow()
    )


    pickled = pickle.dumps(entity)
    entity2 = pickle.loads(pickled)

    assert entity == entity2

    # Change attributes to make sure every un-pickled ok
    entity2.name = 'New name'
    assert entity2.name == 'New name'

def test_eq():
    entity1 = SampleEntity(
        id=1,
        name='test name'
    )    

    entity2 = SampleEntity(
        id=1,
        name='test name'
    )      

    entity3 = SampleEntity(
        id=2,
        name='test name'
    )       

    assert entity1 == entity2   
    assert entity2 == entity1
    assert entity1 != entity3   
    assert entity2 != entity3

    assert hash(entity1) == hash(entity1)
    assert hash(entity1) != hash(entity2)
    assert hash(entity1) != hash(entity3)
