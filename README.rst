ToolTool API, Frontend and Client
---------------------------------


Local Development
^^^^^^^^^^^^^^^^^

Use `docker-compose up db` to run the database. To run `api` open a separate
terminal window and run::

    $ cd api/
    $ export $(gpg --decrypt ./../path/to/private/passwords/tooltool-localdev.txt.gpg 2>/dev/null | xargs) && ./dev run

That will load the secrets needed for local development and start `api` service
in development mode.


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
