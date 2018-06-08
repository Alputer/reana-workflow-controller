# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017 CERN.
#
# REANA is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# REANA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# REANA; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.

"""Pytest configuration for REANA-Workflow-Controller."""

from __future__ import absolute_import, print_function

import os
import shutil

import pytest
from reana_commons.models import Base, Organization, User, UserOrganization
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from reana_workflow_controller.factory import create_app


@pytest.fixture(scope='module')
def tmp_shared_volume_path(tmpdir_factory):
    """Fixture temporary file system database."""
    temp_path = str(tmpdir_factory.mktemp('data').join('reana'))
    shutil.copytree(os.path.join(os.path.dirname(__file__), "data"),
                    temp_path)

    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture(scope='module')
def base_app(tmp_shared_volume_path):
    """Flask application fixture."""
    config_mapping = {
        'SERVER_NAME': 'localhost:5000',
        'SECRET_KEY': 'SECRET_KEY',
        'TESTING': True,
        'SHARED_VOLUME_PATH': tmp_shared_volume_path,
        'SQLALCHEMY_DATABASE_URI':
        'sqlite:///',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'ORGANIZATIONS': ['default'],
    }
    app_ = create_app(config_mapping)
    return app_


@pytest.fixture(scope='module')
def db_engine(base_app):
    test_db_engine = create_engine(
        base_app.config['SQLALCHEMY_DATABASE_URI'])
    if not database_exists(test_db_engine.url):
        create_database(test_db_engine.url)
    yield test_db_engine
    drop_database(test_db_engine.url)


@pytest.fixture()
def session(db_engine):
    Session = scoped_session(sessionmaker(autocommit=False,
                                          autoflush=False,
                                          bind=db_engine))
    Base.query = Session.query_property()
    from reana_commons.database import Session as _Session
    _Session.configure(bind=db_engine)
    yield Session


@pytest.fixture()
def app(base_app, db_engine, session):
    """Flask application fixture."""
    with base_app.app_context():
        import reana_commons.models
        Base.metadata.create_all(bind=db_engine)
        yield base_app
        for table in reversed(Base.metadata.sorted_tables):
            db_engine.execute(table.delete())


@pytest.fixture()
def default_organization(app, session):
    """Create users."""
    org = Organization.query.filter_by(
        name='default').first()
    if not org:
        org = Organization(name='default')
        session.add(org)
        session.commit()
    return org


@pytest.fixture()
def cwl_workflow_with_name():
    return {'parameters': {'min_year': '1991',
                           'max_year': '2001'},
            'specification': {'first': 'do this',
                              'second': 'do that'},
            'type': 'cwl',
            'name': 'my_test_workflow'}


@pytest.fixture()
def yadage_workflow_with_name():
    return {'parameters': {'min_year': '1991',
                           'max_year': '2001'},
            'specification': {'first': 'do this',
                              'second': 'do that'},
            'type': 'yadage',
            'name': 'my_test_workflow'}


@pytest.fixture()
def cwl_workflow_without_name():
    return {'parameters': {'min_year': '1991',
                           'max_year': '2001'},
            'specification': {'first': 'do this',
                              'second': 'do that'},
            'type': 'cwl',
            'name': ''}


@pytest.fixture()
def yadage_workflow_without_name():
    return {'parameters': {'min_year': '1991',
                           'max_year': '2001'},
            'specification': {'first': 'do this',
                              'second': 'do that'},
            'type': 'yadage',
            'name': ''}
