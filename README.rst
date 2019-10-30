ToolTool API, Frontend and Client
---------------------------------


See `client/` and `api/` READMEs fo more details on each.

Frontend is included in `api/` and is located in
`api/src/tooltool_api/static/ui/` folder.


Local Development
^^^^^^^^^^^^^^^^^

Use `docker-compose up` to run `api` (and postgresql database). The API will be
available at https://localhost:8002/apidocs. When visiting
https://localhost:8002 you will be redirected to the location of the frontend.


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

- Dev

   :URL: https://tooltool.testing.mozilla-releng.net/
   :Taskcluster Secret: repo:github.com/mozilla-releng/services:branch:testing
   :Taskcluster Client ID: project/releng/services/heroku-testing


- Staging

   :URL: https://tooltool.staging.mozilla-releng.net/
   :Taskcluster Secret: repo:github.com/mozilla-releng/services:branch:staging
   :Taskcluster Client ID: project/releng/services/heroku-staging

- Production

   :URL: https://tooltool.mozilla-releng.net/
   :Taskcluster Secret: repo:github.com/mozilla-releng/services:branch:production
   :Taskcluster Client ID: project/releng/services/heroku-production
