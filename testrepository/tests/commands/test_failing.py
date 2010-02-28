#
# Copyright (c) 2010 Testrepository Contributors
# 
# Licensed under either the Apache License, Version 2.0 or the BSD 3-clause
# license at the users choice. A copy of both licenses are available in the
# project source as Apache-2.0 and BSD. You may not use this file except in
# compliance with one of these two licences.
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under these licenses is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# license you chose for the specific language governing permissions and
# limitations under that license.

"""Tests for the failing command."""

import doctest

import testtools
from testtools.matchers import DocTestMatches

from testrepository.commands import failing
from testrepository.ui.model import UI
from testrepository.repository import memory
from testrepository.tests import ResourcedTestCase


class TestCommand(ResourcedTestCase):

    def get_test_ui_and_cmd(self, options=(), args=()):
        ui = UI(options=options, args=args)
        cmd = failing.failing(ui)
        ui.set_command(cmd)
        return ui, cmd

    def test_shows_failures_from_last_run(self):
        ui, cmd = self.get_test_ui_and_cmd()
        cmd.repository_factory = memory.RepositoryFactory()
        repo = cmd.repository_factory.initialise(ui.here)
        inserter = repo.get_inserter()
        inserter.startTestRun()
        class Cases(ResourcedTestCase):
            def failing(self):
                self.fail('foo')
            def ok(self):
                pass
        Cases('failing').run(inserter)
        Cases('ok').run(inserter)
        id = inserter.stopTestRun()
        self.assertEqual(1, cmd.execute())
        self.assertEqual('results', ui.outputs[0][0])
        suite = ui.outputs[0][1]
        ui.outputs[0] = ('results', None)
        # We should have seen test outputs (of the failure) and summary data.
        self.assertEqual([
            ('results', None),
            ('values', [('failures', 1)])],
            ui.outputs)
        result = testtools.TestResult()
        result.startTestRun()
        try:
            suite.run(result)
        finally:
            result.stopTestRun()
        self.assertEqual(1, result.testsRun)
        self.assertEqual(1, len(result.failures))

    def test_with_subunit_shows_subunit_stream(self):
        ui, cmd = self.get_test_ui_and_cmd(options=[('subunit', True)])
        cmd.repository_factory = memory.RepositoryFactory()
        repo = cmd.repository_factory.initialise(ui.here)
        inserter = repo.get_inserter()
        inserter.startTestRun()
        class Cases(ResourcedTestCase):
            def failing(self):
                self.fail('foo')
            def ok(self):
                pass
        Cases('failing').run(inserter)
        Cases('ok').run(inserter)
        id = inserter.stopTestRun()
        self.assertEqual(1, cmd.execute())
        self.assertEqual(1, len(ui.outputs))
        self.assertEqual('stream', ui.outputs[0][0])
        self.assertThat(ui.outputs[0][1], DocTestMatches("""...test: ...failing
...failure: ...failing...""", doctest.ELLIPSIS))

    def test_uses_get_failing(self):
        ui, cmd = self.get_test_ui_and_cmd()
        cmd.repository_factory = memory.RepositoryFactory()
        calls = []
        open = cmd.repository_factory.open
        def decorate_open_with_get_failing(url):
            repo = open(url)
            orig = repo.get_failing
            def get_failing():
                calls.append(True)
                return orig()
            repo.get_failing = get_failing
            return repo
        cmd.repository_factory.open = decorate_open_with_get_failing
        repo = cmd.repository_factory.initialise(ui.here)
        self.assertEqual(0, cmd.execute())
        self.assertEqual([True], calls)
