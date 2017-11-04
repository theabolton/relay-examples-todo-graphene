# relay-examples-todo-graphene -- todo/tests.py
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

import traceback
import unittest

from django.test import TestCase
import graphene
from graphql.error import GraphQLError
import graphql_relay

from project.schema import Mutation, Query
from .models import TodoModel


def format_graphql_errors(errors):
    """Return a string with the usual exception traceback, plus some extra fields that GraphQL
    provides.
    """
    if not errors:
        return None
    text = []
    for i, e in enumerate(errors):
        text.append('GraphQL schema execution error [{}]:\n'.format(i))
        if isinstance(e, GraphQLError):
            for attr in ('args', 'locations', 'nodes', 'positions', 'source'):
                if hasattr(e, attr):
                    if attr == 'source':
                        text.append('source: {}:{}\n'
                                    .format(e.source.name, e.source.body))
                    else:
                        text.append('{}: {}\n'.format(attr, repr(getattr(e, attr))))
        if isinstance(e, Exception):
            text.append(''.join(traceback.format_exception(type(e), e, e.stack)))
        else:
            text.append(repr(e) + '\n')
    return ''.join(text)


class RootTests(TestCase):
    def test_root_query(self):
        """Make sure the root query is 'Query'.

        This test is pretty redundant, given that every other query in this file will fail if this
        is not the case, but it's a nice simple example of testing query execution.
        """
        query = '''
          query RootQueryQuery {
            __schema {
              queryType {
                name  # returns the type of the root query
              }
            }
          }
        '''
        expected = {
            '__schema': {
                'queryType': {
                    'name': 'Query'
                }
            }
        }
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


class ViewerTests(TestCase):
    def test_viewer_schema(self):
        """Check the 'viewer' field User type schema contains the fields we need."""
        query = '''
          query ViewerSchemaTest {
            __type(name: "User") {
              name
              fields {
                name
                type {
                  name
                  kind
                  ofType {
                    name
                  }
                }
              }
            }
          }
        '''
        expected = {
            '__type': {
                'name': 'User',
                'fields': [
                    {
                        'name': 'id',
                        'type': {
                            'name': None,
                            'kind': 'NON_NULL',
                            'ofType': {
                                'name': 'ID',
                            }
                        }
                    },
                    {
                        'name': 'todos',
                        'type': {
                            'name': 'TodoConnection',
                            'kind': 'OBJECT',
                            'ofType': None,
                        }
                    },
                    {
                        'name': 'totalCount',
                        'type': {
                            'name': 'Int',
                            'kind': 'SCALAR',
                            'ofType': None,
                        }
                    },
                    {
                        'name': 'completedCount',
                        'type': {
                            'name': 'Int',
                            'kind': 'SCALAR',
                            'ofType': None,
                        }
                    },
                ]
            }
        }
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        # Check that the fields we need are there, but don't fail on extra fields.
        NEEDED_FIELDS = ('id', 'todos', 'totalCount', 'completedCount')
        result.data['__type']['fields'] = list(filter(
            lambda f: f['name'] in NEEDED_FIELDS,
            result.data['__type']['fields']
        ))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


def create_test_data():
    TodoModel.objects.create(text='Taste JavaScript', complete=True)
    TodoModel.objects.create(text='Buy a unicorn', complete=False)


class TodoTests(TestCase):
    def test_total_count(self):
        """Test viewer totalCount field."""
        create_test_data()
        query = '''
          query TotalCountTest {
            viewer {
              totalCount
            }
          }
        '''
        expected = {
            'viewer': {
                'totalCount': 2,
            }
        }
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))

    def test_completed_count(self):
        """Test viewer completedCount field."""
        create_test_data()
        query = '''
          query CompletedCountTest {
            viewer {
              completedCount
            }
          }
        '''
        expected = {
            'viewer': {
                'completedCount': 1,
            }
        }
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))

    def test_todos(self):
        """Test viewer todos field."""
        create_test_data()
        query = '''
          query TodosTest {
            viewer {
              todos {
                edges {
                  node {
                    text
                  }
                }
              }
            }
          }
        '''
        expected = {
            'viewer': {
                'todos': {
                    'edges': [
                        {
                            'node': {
                                'text': 'Buy a unicorn',
                            }
                        },
                        {
                            'node': {
                                'text': 'Taste JavaScript',
                            }
                        },
                    ]
                }
            }
        }
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        # don't depend on the ordering of the returned nodes
        result.data['viewer']['todos']['edges'].sort(key=lambda d: d['node']['text'])
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))

    @unittest.expectedFailure
    # 'status' is not a field of TodoModel, so DjangoFilterConnectionField can't filter on it.
    # Not sure how to work around that yet.
    def test_todos_filter_by_completed(self):
        """'fragment TodoListFooter_viewer on User' filters todos on 'status: "completed"' – test
        that.
        """
        create_test_data()
        query = '''
          query CompletedTodosTest {
            viewer {
              todos(status: "completed") {
                edges {
                  node {
                    text
                  }
                }
              }
            }
          }
        '''
        expected = {
            'viewer': {
                'todos': {
                    'edges': [
                        {
                            'node': {
                                'text': 'Taste JavaScript',
                            }
                        },
                    ]
                }
            }
        }
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


class AddTodoTests(TestCase):
    def test_add_todo(self):
        query = '''
          mutation AddTodoMutation($input: AddTodoInput!) {
            addTodo(input: $input) {
              todoEdge { cursor node { text } }
              viewer { totalCount }
            }
          }
        '''
        variables = {
            'input': {
                'text': 'Test Todo',
            }
        }
        expected = {
            'addTodo': {
                'todoEdge': {
                    'cursor': 'YXJyYXljb25uZWN0aW9uOjA=',  # 'arrayconnection:0' in base64
                    'node': {
                        'text': 'Test Todo',
                    }
                },
                'viewer': {
                    'totalCount': 1,
                }
            }
        }
        schema = graphene.Schema(query=Query, mutation=Mutation)
        result = schema.execute(query, variable_values=variables)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


class ChangeTodoStatusTests(TestCase):
    def test_change_todo_status(self):
        create_test_data()
        query = '''
          mutation ChangeTodoStatusMutation($input: ChangeTodoStatusInput!) {
            changeTodoStatus(input: $input) {
              todo { complete }
              viewer { completedCount }
            }
          }
        '''
        variables = {
            'input': {
                'id': graphql_relay.to_global_id('Todo', 1),
                'complete': False,
            }
        }
        expected = {
            'changeTodoStatus': {
                'todo': {
                    'complete': False,
                },
                'viewer': {
                    'completedCount': 0,
                }
            }
        }
        schema = graphene.Schema(query=Query, mutation=Mutation)
        result = schema.execute(query, variable_values=variables)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


class MarkAllTodosTests(TestCase):
    def test_mark_all_todos(self):
        create_test_data()
        query = '''
          mutation MarkAllTodosMutation($input: MarkAllTodosInput!) {
            markAllTodos(input: $input) {
              changedTodos { id complete }
              viewer { completedCount }
            }
          }
        '''
        variables = {
            'input': {
                'complete': True,
            }
        }
        expected = {
            'markAllTodos': {
                'changedTodos': [
                    {
                        'id': graphql_relay.to_global_id('Todo', 2),
                        'complete': True,
                    },
                ],
                'viewer': {
                    'completedCount': 2,
                }
            }
        }
        schema = graphene.Schema(query=Query, mutation=Mutation)
        result = schema.execute(query, variable_values=variables)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


class RemoveCompletedTodosTests(TestCase):
    def test_remove_todo(self):
        create_test_data()
        query = '''
          mutation RemoveCompletedTodosMutation($input: RemoveCompletedTodosInput!) {
            removeCompletedTodos(input: $input) {
              deletedTodoIds
              viewer { completedCount totalCount }
            }
          }
        '''
        variables = {
            'input': {},
        }
        expected = {
            'removeCompletedTodos': {
                'deletedTodoIds': [graphql_relay.to_global_id('Todo', 1)],
                'viewer': {
                    'completedCount': 0,
                    'totalCount': 1,
                }
            }
        }
        schema = graphene.Schema(query=Query, mutation=Mutation)
        result = schema.execute(query, variable_values=variables)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


class RemoveTodoTests(TestCase):
    def test_remove_todo(self):
        create_test_data()
        query = '''
          mutation RemoveTodoMutation($input: RemoveTodoInput!) {
            removeTodo(input: $input) {
              deletedTodoId
              viewer { completedCount totalCount }
            }
          }
        '''
        todo_gid = graphql_relay.to_global_id('Todo', 1)
        variables = {
            'input': {
                'id': todo_gid,
            }
        }
        expected = {
            'removeTodo': {
                'deletedTodoId': todo_gid,
                'viewer': {
                    'completedCount': 0,
                    'totalCount': 1,
                }
            }
        }
        schema = graphene.Schema(query=Query, mutation=Mutation)
        result = schema.execute(query, variable_values=variables)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


class RenameTodoTests(TestCase):
    def test_rename_todo(self):
        create_test_data()
        query = '''
          mutation RenameTodoMutation($input: RenameTodoInput!) {
            renameTodo(input: $input) {
              todo { text }
            }
          }
        '''
        variables = {
            'input': {
                'id': graphql_relay.to_global_id('Todo', 1),
                'text': 'Taste Python',
            }
        }
        expected = {
            'renameTodo': {
                'todo': {
                    'text': 'Taste Python',
                },
            }
        }
        schema = graphene.Schema(query=Query, mutation=Mutation)
        result = schema.execute(query, variable_values=variables)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))
