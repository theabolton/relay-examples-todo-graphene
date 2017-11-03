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
import graphql_relay

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

    instance = None # a lazily-initialized singleton for get_node()

    @classmethod
    def get_node(cls, info, id):
        if cls.instance is None:
            cls.instance = User()
        return cls.instance

    def resolve_total_count(_, info):
        return TodoModel.objects.count()

    def resolve_completed_count(_, info):
        return TodoModel.objects.filter(complete=True).count()


class Query(object):
    node = relay.Node.Field()
    viewer = graphene.Field(User)

    def resolve_viewer(self, info):
        return True  # no Viewer resolvers will need Viewer()


class AddTodo(relay.ClientIDMutation):
    # mutation AddTodoMutation($input: AddTodoInput!) {
    #   addTodo(input: $input) {
    #     todoEdge { __typename cursor node { complete id text } }
    #     viewer { id totalCount }
    #   }
    # }
    # example variables: input: { text: "New Item!", clientMutationId: 0 }

    # This feels like some disturbed dark magic....
    todo_edge = graphene.Field(Todo._meta.connection.Edge)
    viewer = graphene.Field(User)

    class Input:
        text = graphene.String(required=True)
        # client_mutation_id is supplied automatically

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        todo = TodoModel.objects.create(text=input.get('text'), complete=False)
        count = TodoModel.objects.count()  # ick, race condition if multi-user
        edge = Todo._meta.connection.Edge(
            node=todo,
            # A graphql_relay cursor is nothing more than an index into the edge
            # list at one particular time in the past? That's just wrong....
            cursor=graphql_relay.connection.arrayconnection.offset_to_cursor(count - 1)
        )
        return AddTodo(todo_edge=edge)


class ChangeTodoStatus(relay.ClientIDMutation):
    # mutation ChangeTodoStatusMutation($input: ChangeTodoStatusInput!) {
    #   changeTodoStatus(input: $input) {
    #     todo { id complete }
    #     viewer { id completedCount }
    #   }
    # }
    # example variables: input: { complete: true, id: "VG9kbzoy"}
    todo = graphene.Field(Todo)
    viewer = graphene.Field(User)

    class Input:
        complete = graphene.Boolean(required=True)
        id = graphene.ID(required=True)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        id = input.get('id')
        complete = input.get('complete')
        try:
            typ, pk = graphql_relay.from_global_id(id) # may raise if improperly encoded
            assert typ == 'Todo', 'changeTodoStatus called with type {}'.format(typ)
            todo = TodoModel.objects.get(pk=pk) # may raise if invalid pk
        except:
            raise Exception("received invalid Todo id '{}'".format(id))
        todo.complete = complete
        todo.save()
        return ChangeTodoStatus(todo=todo, viewer=User())


class Mutation(object):
    add_todo = AddTodo.Field()
    change_todo_status = ChangeTodoStatus.Field()
