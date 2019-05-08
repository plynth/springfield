from springfield import fields, Entity


class Property(Entity):
    name = fields.StringField()
    nested = fields.EntityField(
        'tests.dottedname.foo.bar.bop.PropertyList'
    )


class PropertyList(Entity):
    properties = fields.CollectionField(
        fields.EntityField(Property)
    )