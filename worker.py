#!/usr/bin/env python
"""Worker script for OpenDroneMap transformer
"""
import os
import yaml

from opendm import config

from stages.odm_app import ODMApp

# Forbidden OpenDroneMap setting overrides when using custom configuration
NO_OVERRIDE_SETTINGS = ["project_path"]

def perform_work():
    """Prepares for and runs the ODM code
    """
    print("[worker] Starting")

    arg_file = os.environ.get('ODM_SETTINGS')
    project_path = os.environ.get('ODM_PROJECT')

    if not project_path:
        print("[worker] raising missing environment variable ODM_PROJECT")
        raise ValueError("Missing project path environment variable")

    print("[worker] settings file: " + str(arg_file))

    new_settings = None
    print("[worker] loading settings")
    with open(arg_file) as in_f:
        new_settings = yaml.safe_load(in_f)

    print("[worker] getting config")
    args = config.config()

    print("[worker] merging config")
    if new_settings:
        for name in new_settings:
            if name not in NO_OVERRIDE_SETTINGS:
                setattr(args, name, new_settings[name])

    print("[worker] setting project path")
    args.project_path = project_path

    os.chdir(project_path)

    print("[worker] Starting")
    app = ODMApp(args=args)
    app.execute()

    print("[worker] finishing")

perform_work()
