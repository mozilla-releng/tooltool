# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from taskgraph.parameters import get_version
from taskgraph.transforms.base import TransformSequence


transforms = TransformSequence()


@transforms.add
def set_push_image_env(config, tasks):
    for task in tasks:
        env = task.setdefault("worker", {}).setdefault("env", {})
        env["VERSION"] = get_version("api")
        env["VCS_HEAD_REV"] = config.params["head_rev"]
        env["VCS_HEAD_REPOSITORY"] = config.params["head_repository"]
        yield task
