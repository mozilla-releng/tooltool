# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from taskgraph.transforms.base import TransformSequence


transforms = TransformSequence()


@transforms.add
def set_coverage_env(config, tasks):
    for task in tasks:
        env = task.setdefault("worker", {}).setdefault("env", {})
        env["CI_HEAD_REV"] = config.params["head_rev"]
        env["CI_PR_NUMBER"] = os.environ.get("TOOLTOOL_PULL_REQUEST_NUMBER", "")
        yield task


@transforms.add
def get_secret(config, tasks):
    for task in tasks:
        secret = 'export CODECOV_TOKEN=$(wget -qO- $SECRET_URL | jq -r \'.["secret"]["codecov"]["token"]\')'
        task["run"][
            "command"
        ] = f"set +x && {secret} && set -x && {task['run']['command']}"
        yield task
