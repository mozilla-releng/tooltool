# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Add soft-dependencies on all kind-dependencies
"""
from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def add_dependencies(config, tasks):
    for task in tasks:
        task.setdefault("soft-dependencies", [])
        task["soft-dependencies"].extend(
            dep_task.label
            for dep_task in config.kind_dependencies_tasks.values()
        )
        yield task
