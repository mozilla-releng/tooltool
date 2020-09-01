ToolTool API, Frontend and Client

Basics
^^^^^^

Some of the jobs in the releng infrastructure make use of generic binary artifacts, which are stored in dedicated artifacts repositories.

Tooltool is the client program, written in Python, which is used to retrieve these artifacts from the servers, and to perform integrity checks on them based on hashcode verification. Hence, the servers storing these artifacts are named "tooltool servers".

A set of files to be fetched by tooltool is specified via a tooltool manifest, usually a file in JSON format with tt extension.

The following is an example of a valid tooltool manifest::

    [
    {
    "size": 139308,
    "digest": "b2a463249bb3a9e7f2a3604697b000d2393db4f37b623fc099beb8456fbfdb332567013a3131ad138d8633cb19c50a8b77df3990d67500af896cada8b6f698b4",
    "algorithm": "sha512",
    "filename": "file2.pdf"
    },
    {
    "size": 3017536,
    "digest": "630d01a329c70aedb66ae7118d12ff7dc6fe06223d1c27b793e1bacc0ca84dd469ec1a6050184f8d9c35a0636546b0e2e5be08d9b51285e53eb1c9f959fef59d",
    "algorithm": "sha512",
    "filename": "file1.pdf"
    },
    {
    "size": 3420686,
    "digest": "931eb84f798dc9add1a10c7bbd4cc85fe08efda26cac473411638d1f856865524a517209d4c7184d838ee542c8ebc9909dc64ef60f8653a681270ce23524e8e4",
    "algorithm": "sha512",
    "filename": "file3.pdf"
    }
    ]

The simplest usecase for tooltool is to run a "fetch" command to download the files mentioned in the manifest::

    python tooltool.py fetch -m my-manifest.tt

Uploading to Tooltool
^^^^^^^^^^^^^^^^^^^^^

First, plan out your upload. Are all of the files you need to upload public? If not, tooltool also offers storage of "internal" files, which are not made publicly available but can be downloaded by those with proper permissions. Internal files might be under a non-redistribution license (e.g., Google SDKs, Microsoft DLLs), but must not include secrets such as passwords or private keys.

Use the `tooltool.py` client to build a manifest containing the files you would like to upload, annotating each file with its visibility level::

    python tooltool.py add --visibility public gcc.tar.gz

Next, you will need credentials for the upload. Tooltool uses Taskcluster for authentication. To retrieve taskcluster credentials, run::

    export TASKCLUSTER_ROOT_URL=https://firefox-ci-tc.services.mozilla.com/
    taskcluster signin

...and then put the clientId and accessToken you obtained into a JSON file as follows::

    {
        "clientId": "xxxxxxxxxxxxx",
        "accessToken": "xxxxxxxxxxxxxx"
    }

Now, you're ready to upload with a command like::

   python tooltool.py upload --authentication-file=~/.tooltool-token --message "Bug 1234567: add new frobnicator binaries"


Local Development
^^^^^^^^^^^^^^^^^

Run::

    export TASKCLUSTER_ROOT_URL=https://firefox-ci-tc.services.mozilla.com/
    # Use "taskcluster signing" if you don't have these
    export TASKCLUSTER_CLIENT_ID=xxxxx
    export TASKCLUSTER_ACCESS_TOKEN=xxxxx
    # You will need to create your own bucket & AWS credentials
    export S3_REGIONS=us-west-2:your-s3-bucket
    export S3_REGIONS_ACCESS_KEY_ID=xxxxxx
    export S3_REGIONS_SECRET_ACCESS_KEY=xxxxxx
    docker-compose up

Tooltool should then be ready for use on https://localhost:8010.

Deployment process
^^^^^^^^^^^^^^^^^^

To trigger the deployment you have to push the code to the branch with the same
name as environment you want to deploy to.

This will start Taskcluster graph which will build and push docker
image to docker hub (`mozilla/releng-tooltool`_) with the same tag as is the
environment.

Cloudops team Jenkins is listening for the change and will deploy it to `GCP`_
once it confirms that the docker images was build in a trusted environment. It
usually takes around 5min for deployment to be done. For more how things are 
configures you can check `cloudops infrastructure`_.:

You can check that the service was deployed correctly by visiting the
``/__version__`` endpoint which should include

.. _`GCP`: https://cloud.google.com
.. _`mozilla/releng-tooltool`: https://hub.docker.com/r/mozilla/releng-tooltool
.. _`cloudops infrastructure`: https://github.com/mozilla-services/cloudops-infra/tree/master/projects/relengapi/


Deployed Environments
^^^^^^^^^^^^^^^^^^^^^

We have a number of deployed ToolTool environments.

- Dev (currently broken, possibly permanently)

   :URL: https://dev.tooltool.mozilla-releng.net/
   :Deploys from: `dev` branch

- Staging

   :URL: https://stage.tooltool.mozilla-releng.net/
   :Deploys from: `staging` branch

- Production

   :URL: https://tooltool.mozilla-releng.net/
   :Deploys from: `production` branch
