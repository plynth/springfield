from springfield import fields, Entity


class Zap(Entity):
    name = fields.StringField()


NotCallable = Zap(name='NotCallable')
