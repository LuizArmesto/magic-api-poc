#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask.ext.script import Manager

from magic_api.app.extensions import db
from magic_api.app import create_app
from magic_api.api import ResourcesMaker


manager = Manager(create_app)
manager.add_option('-i', '--inst', dest='instance_folder', required=False)
manager.add_option('-b', '--backend', dest='backend', required=False)
manager.add_option('-d', '--datapackage', dest='datapackage', required=True)


@manager.command
def run():
    """Run in local machine."""
    manager.app.run()


@manager.command
def test():
    """Run tests."""
    pass


@manager.command
def initdb():
    """Init or reset database."""
    with manager.app.app_context():
        db.drop_all()
        db.create_all()


@manager.command
def importdata():
    """Import the data to the database."""
    with manager.app.app_context():
        manager.app._resources_maker.models_maker.populate()


if __name__ == "__main__":
    manager.run()
