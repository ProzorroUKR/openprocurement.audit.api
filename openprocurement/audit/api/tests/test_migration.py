# -*- coding: utf-8 -*-
import unittest

from openprocurement.audit.api.constants import (
    SCHEMA_VERSION
)
from openprocurement.audit.api.migration import (
    migrate_data, get_db_schema_version
)
from openprocurement.audit.api.tests.base import BaseWebTest


class MigrateTest(BaseWebTest):

    def setUp(self):
        super(MigrateTest, self).setUp()
        migrate_data(self.app.app.registry)

    def test_migrate(self):
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)
        migrate_data(self.app.app.registry, 1)
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)
