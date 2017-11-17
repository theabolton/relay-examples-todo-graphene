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


# ========== utility functions ==========

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


def create_test_data():
    TodoModel.objects.create(text='Taste JavaScript', complete=True)
    TodoModel.objects.create(text='Buy a unicorn', complete=False)


# ========== GraphQL schema general tests ==========

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


# ========== Relay Node tests ==========

class RelayNodeTests(TestCase):
    """Test that model nodes can be retreived via the Relay Node interface."""
    def test_node_for_todo(self):
        todo = TodoModel.objects.create(text='Test', complete=False)
        todo_gid = graphql_relay.to_global_id('Todo', todo.pk)
        query = '''
          query {
            node(id: "%s") {
              id
              ...on Todo {
                text
              }
            }
          }
        ''' % todo_gid
        expected = {
          'node': {
            'id': todo_gid,
            'text': 'Test',
          }
        }
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))

    def test_node_for_viewer(self):
        query = '''
          query {
            viewer {
              id
            }
          }
        '''
        schema = graphene.Schema(query=Query)
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        viewer_gid = result.data['viewer']['id']
        query = '''
          query {
            node(id: "%s") {
              id
            }
          }
        ''' % viewer_gid
        expected = {
          'node': {
            'id': viewer_gid,
          }
        }
        result = schema.execute(query)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))


# ========== Todo query tests ==========

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


# ========== Todo mutation tests ==========

class AddTodoTests(TestCase):
    def test_add_todo(self):
        query = '''
          mutation AddTodoMutation($input: AddTodoInput!) {
            addTodo(input: $input) {
              todoEdge { cursor node { text } }
              viewer { totalCount }
              clientMutationId
            }
          }
        '''
        variables = {
            'input': {
                'text': 'Test Todo',
                'clientMutationId': 'give_this_back_to_me',
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
                },
                'clientMutationId': 'give_this_back_to_me',
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
              clientMutationId
            }
          }
        '''
        variables = {
            'input': {
                'id': graphql_relay.to_global_id('Todo', 1),
                'complete': False,
                'clientMutationId': 'give_this_back_to_me',
            }
        }
        expected = {
            'changeTodoStatus': {
                'todo': {
                    'complete': False,
                },
                'viewer': {
                    'completedCount': 0,
                },
                'clientMutationId': 'give_this_back_to_me',
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
              clientMutationId
            }
          }
        '''
        variables = {
            'input': {
                'complete': True,
                'clientMutationId': 'give_this_back_to_me',
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
                },
                'clientMutationId': 'give_this_back_to_me',
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
              clientMutationId
            }
          }
        '''
        variables = {
            'input': {
                'clientMutationId': 'give_this_back_to_me',
            },
        }
        expected = {
            'removeCompletedTodos': {
                'deletedTodoIds': [graphql_relay.to_global_id('Todo', 1)],
                'viewer': {
                    'completedCount': 0,
                    'totalCount': 1,
                },
                'clientMutationId': 'give_this_back_to_me',
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
              clientMutationId
            }
          }
        '''
        todo_gid = graphql_relay.to_global_id('Todo', 1)
        variables = {
            'input': {
                'id': todo_gid,
                'clientMutationId': 'give_this_back_to_me',
            }
        }
        expected = {
            'removeTodo': {
                'deletedTodoId': todo_gid,
                'viewer': {
                    'completedCount': 0,
                    'totalCount': 1,
                },
                'clientMutationId': 'give_this_back_to_me',
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
              clientMutationId
            }
          }
        '''
        variables = {
            'input': {
                'id': graphql_relay.to_global_id('Todo', 1),
                'text': 'Taste Python',
                'clientMutationId': 'give_this_back_to_me',
            }
        }
        expected = {
            'renameTodo': {
                'todo': {
                    'text': 'Taste Python',
                },
                'clientMutationId': 'give_this_back_to_me',
            }
        }
        schema = graphene.Schema(query=Query, mutation=Mutation)
        result = schema.execute(query, variable_values=variables)
        self.assertIsNone(result.errors, msg=format_graphql_errors(result.errors))
        self.assertEqual(result.data, expected, msg='\n'+repr(expected)+'\n'+repr(result.data))
