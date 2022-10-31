# CLoVeR

This repo helps get a new clover application started that is set up to run on GCP App Engine, Cloud SQL, and Cloud Storage.

Download or clone a copy of this repo locally to get started.

## Required
- [Google Cloud SDK] https://cloud.google.com/sdk/docs/install
- [Homebrew]: http://brew.sh/ "Homebrew Homepage" (For Mac Users)
- [Docker for Mac]: https://docs.docker.com/docker-for-mac/install/  "Download Docker for Mac"
- [Docker for Windows]: https://docs.docker.com/docker-for-windows/install/  "Download Docker for Windows"

# Create a Google Cloud Platform (GCP) project
For new GCP users: <a href = "https://console.cloud.google.com/">Create a new GCP account</a> and create a GCP billing account.

For existing GCP users: <a href = "https://cloud.google.com/resource-manager/docs/creating-managing-projects">Create a new project in GCP</a>. You can name your project whatever you would like, but we recommend using your container ID for convenience. This name is used only within GCP. Please note your <a href = "https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects">Project ID</a>.

Or you can run this command to create a new project:
```bash
    gcloud projects create 
```
Be sure to also setup/ assign a GCP Billing Account.

The project ID will be your container ID suffixed with a sequence of random characters.
screenshot of GCP project selector, showing a sample Project ID.
![alt text](https://developers.google.com/tag-platform/tag-manager/server-side/img/gcp-project-id.png)

# Install CLoVeR
Open the Google Cloud Platform Cloud Shell
Set the Cloud Platform project in the cloud shell. Replace <PROJECT_ID> with the GCP project ID that you noted earlier:
  ```bash
gcloud config set project <PROJECT_ID>
```

Assuming you've downloaded this repo into a local folder. Run the following command in this directory and follow the instructions given by the script.
  ```bash
  bash -c "$(more setup.sh)"
```

## After the install, you can access your CLoVeR instance via your App Engine URL. You can see this URL by running:
```bash
  gcloud app browse
```


## For Local Development/ Changes - Run After Initial Deployment

1. Check if any port conflicts exist across other local docker containers
   1. Review Docker Desktop Dashboard, click into any running containers, especially web-facing ones and review any Ports in-use   
   2. Change any ports in `docker-compose.yml` (e.g. 8002 to 8003 if it conflicts)
   3. Make sure any port changes occur across the entire docker-compose file (i.e. if you change the postgres port, change it everywhere)
   4. Remember the port order is external:internal so the changing postgres should be something like 5433:5432  

2. Create a Service Account for local cloud storage access
   1. Go to IAM & Admin -> Service Accounts (https://console.cloud.google.com/iam-admin/serviceaccounts)
   2. Click `Create Service Account`
   3. Name it something like `djangofilestorage`
   4. Add the role Storage Admin (or go lower permissions if you want)
   5. Click `Done`
   6. After created, click the 3 vertical dots on the far right, and click `Manage Keys`
   7. Click `Add Key`, using the option to `Create new key`
   8. Choose `JSON`
   9. Place in the root, and name it `cloud-key.json`
   
3. Build and run the containers  
   ```bash
   make build
   make up      # If you get an error, check for port conflicts from other applications or containers
   make migrate # Populate your local DB with the Django Migrations
   make serve   # Run at first to make sure everything is ok, then run Ctrl+C to cancel it and start in background
   docker exec -it admin_django_1 python manage.py createsuperuser # Create your local superuser login and password
   # Also make sure either the name of the folder matches the name of the containers (e.g. django-gcp_django_1) and if not, simply change the NAME on line 14 of the Makefile to the name of the container
   # Also make sure the port in the Makefile (e.g. :8000) is updated to the port configured in docker-compose.yml
   make serve > /dev/null 2>&1 & #Run in Background
   ```

4. Visit the locally running site to confirm (http://localhost:8002/admin/)

## For Deployment From Local Development

If you want to make your own changes to your own CLoVeR instance, you can configure your deployment to build from your own GitHub repo. After you fork this repo, you can follow these steps to setup Cloud Build so that pushing to your own fork would initiate a new build:

1. Configure Cloud Build
   1. Within Google Cloud Console - Cloud Build
   2. Enable Cloud Build API (if Necessary)
   3. Add Cloud Build Service Worker to Cloud Secrets
   4. Create Trigger
   5. Select Push to Branch
   6. Select Branch to push to
   7. (Optional) Specify a Service Account  

2. Set Permissions for Cloud Build
   1. Within Google Cloud Console - Select Security -> Secret Manager
   2. For each secret, select it, click the Permissions tab
   3. Note that the existing Principal permission as [Project number]@cloudservices.gserviceaccount.com
   4. Click Add, and add [Project number]@cloudbuild.gserviceaccount.com with the Role of Secret Manager Secret Accessor
   5. Repeat for each secret.
   6. Add Permission for Cloud Build Service Account (e.g. [Project number]@cloudbuild.gserviceaccount.com) to have the permission App Engine Deployer. Go to IAM & Admin, find the Cloud Build Service Account and Click Edit, and Add a New Role.

3. Add Permissions
   1. Access IAM & Admin
   2. Add App Engine Access to Cloud Build User
   3. Select the cloud build service account (e.g. [Project number]@cloudbuild.gserviceaccount.com)
   4. Add the Roles: App Engine Admin, App Engine Service Admin, App Engine flexible environment Service Agent

4. Final Checks
   1. Confirm accuracy of app.yaml (GCP uses) and settings.py
   2. Deployment steps are managed by cloudbuild.yaml
   3. Per above setup, Cloud Build triggers builds on merge to specified branch (e.g. master)
   4. Status available at https://console.cloud.google.com/cloud-build/builds
    ```bash
    # Also can run the command (which just launches the above URL)
    make check build
    ```

5. Post-Deployment
    1. Apply migrations to production DB. (TODO: Move this to a Cloud Build Step)
    ```bash
    # Running Migrations on CloudSQL can be done in a few ways. One way is to SSH into one of the AppEngine instances and run on the docker container there
    docker exec -it gaeapp python manage.py migrate
    ```
    2. Clean-up previously deployed versions. (TODO: Move this to a Cloud Build Step)
    ```bash
    # gcloud app versions delete `gcloud app versions list | sed 's/  */:/g' | cut -f 2 -d : | tail -n +2 | ghead -n -5 | tr "\n" " "`
    ```
    3. Configure a domain (Optional)
      1. Update ALLOWED_HOSTS /site/config/settings.py to include the domain
      2. Access App Engine -> Settings (e.g. https://console.cloud.google.com/appengine/settings)
      3. Select Custom Domains - Follow the prompts to set up a custom domain. You will need to have DNS access to set up records to validate ownership

## Contribute

- [See CONTRIBUTING.md](./CONTRIBUTING.md)

