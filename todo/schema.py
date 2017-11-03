# relay-examples-todo-graphene -- todo/schema.py
#
# Copyright © 2017 Sean Bolton.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import graphene
from graphene import ObjectType, relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import TodoModel


class Todo(DjangoObjectType):
    class Meta:
        model = TodoModel
        filter_fields = {
            'text': ['exact', 'icontains', 'istartswith'],
            'complete': ['exact'],
        }
        interfaces = (relay.Node, )


class User(ObjectType):
    class Meta:
        interfaces = (relay.Node, )

    todos = DjangoFilterConnectionField(Todo, status=graphene.String('any'))
    total_count = graphene.Int()
    completed_count = graphene.Int()

    def resolve_total_count(_, info):
        return TodoModel.objects.count()

    def resolve_completed_count(_, info):
        return TodoModel.objects.filter(complete=True).count()


class Query(object):
    node = relay.Node.Field()
    viewer = graphene.Field(User)

    def resolve_viewer(self, info):
        return True  # no Viewer resolvers will need Viewer()


class Mutation(object):
    pass
