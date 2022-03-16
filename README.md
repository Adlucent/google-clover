[Docker for Mac]: https://docs.docker.com/docker-for-mac/install/  "Download Docker for Mac"
[Docker for Windows]: https://docs.docker.com/docker-for-windows/install/  "Download Docker for Windows"
[Homebrew]: http://brew.sh/ "Homebrew Homepage"
[Google Cloud SDK]: https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-194.0.0-darwin-x86_64.tar.gz

# Clover API Boilerplate

This boilerplate helps get a new clover application started that is set up to run on GCP App Engine, Cloud SQL, and Cloud Storage.

## Required
- [Docker for Mac] __or__ [Docker for Windows]


## New project - Local Setup

1. Setup this boilerplate in a new GitHub project
   ```bash
   # Pull down the boilerplate
   git clone https://www.github.com/adlucent/clover
   mv clover new-project-name
   cd new-project-name
   rm -rf .git # Clear out the git history from the boilerplate
   
   # Visit https://github.com/organizations/Adlucent/repositories/new
   # Name the new project repo after creating, follow the instructions on github, would be something like the 
   # following:
   git init
   git add .
   git commit -m "first commit"
   git branch -M main
   git remote add origin git@github.com:Adlucent/NAME_OF_REPO
   git push -u origin main
   ```


2. Check if any port conflicts exist across other local docker containers
   1. Review Docker Desktop Dashboard, click into any running containers, especially web-facing ones
   2. Click Inspect
   3. Scroll down and review any Ports in-use
   4. Open `docker-compose.yml`
   5. Change any ports (e.g. 8002 to 8003 if it conflicts)
   6. Make sure any port changes occur across the entire docker-compose file (i.e. if you change the postgres port, change it everywhere)
   7. Remember the port order is external:internal so the changing postgres should be something like 5433:5432  
      ```
      Note: It's an easier setup for file storage to be in the cloud from day 1 vs changing the configuration back and forth
      ```


3. Create a new GCP Project
   1. Ensure that the project is tied to a billing profile for your organization, otherwise you won't be able to proceed
   2. Once you create the project, in your dashboard you will find the [Project number] and [Project ID], both of which you will need for the rest of these instructions


4. Setup Cloud Storage Bucket
   1. Navigate to Cloud Storage (https://console.cloud.google.com/storage/browser)
   2. Click `Create Bucket`
   3. Name it something like `{PROJECTNAME}_file_uploads`
   4. Continue and leave default settings (unless you know what you are doing) and click `Create`
   5. Update /site/config/settings.py `GS_BUCKET_NAME`   


5. Create a Service Account for local cloud storage access
   1. Go to IAM & Admin -> Service Accounts (https://console.cloud.google.com/iam-admin/serviceaccounts)
   2. Click `Create Service Account`
   3. Name it something like `djangofilestorage`
   4. Add the role Storage Admin (or go lower permissions if you want)
   5. Click `Done`
   6. After created, click the 3 vertical dots on the far right, and click `Manage Keys`
   7. Click `Add Key`, using the option to `Create new key`
   8. Choose `JSON`
   9. Place in the root, name something like `cloud-key.json`
   10. Update docker-compose.yml `GOOGLE_APPLICATION_CREDENTIALS` to be set to the file path, will need to be set back a directory from /site so the path would be `../cloud-key.json`
   11. Add cloud-key.json to gitignore to make sure it doesn't end up in the repo  
       ```bash
       vi .gitignore
       
       # Hit s for write, type in
       cloud-key.json
       # Hit escape, and write
       :wq  # Writes the file and closes vi editor
       
       # Check git status to make sure the cloud key json is not listed
       git status	
       ```


6. Build and run the containers  
   ```bash
   make build
   make up     # If you get an error, check for port conflicts from other applications or containers
   make serve  # Run at first to make sure everything is ok, then run Ctrl+C to cancel it and start in background
   
   # Also make sure either the name of the folder matches the name of the containers (e.g. django-gcp_django_1) and if not, simply change the NAME on line 14 of the Makefile to the name of the container
   # Also make sure the port in the Makefile (e.g. :8000) is updated to the port configured in docker-compose.yml
   make serve > /dev/null 2>&1 &
   ```


7. Run Default Migrations  
   ```bash 
   make migrate
   ```
	
	
8. Set up the local admin account  
   ```bash
   make shell
   python manage.py createsuperuser
   ```
	
	
9. Visit the locally running site to confirm (http://localhost:8002/admin/)

## New project - Production Setup

Please follow all the Local Setup steps first

1. Create a Cloud SQL Instance
   1. Within Google Cloud Console - Click SQL on the left side (https://console.cloud.google.com/sql/instances)
   2. Click Create Instance
   3. Choose PostgreSQL
   4. Click Enable API (if necessary)
   5. Name the Instance
   6. Choose a unique password, save it for later populating Cloud Secrets
   7. Depending on the application, Select Customize your instance, and change from High Memory to Lightweight
   8. Choose Maintenance Window according to your application
      1. Worth noting that this incurs a cost of around $30-$50/mo just instantiated and running. 
   9. Note the name of the instance (e.g. clover-gcp:us-central1:clover-gcp)
   10. Update two (2) fields in app.yaml DB_HOST with /cloudsql/NAME_OF_INSTANCE and update cloud_sql_instances: with NAME_OF_INSTANCE  


2. Setup Cloud secrets
   1. Within Google Cloud Console - Select Security -> Secret Manager
   2. Enable the API (if necessary)
   3. Click Create Secret #we need to set up 2 secrets db-password and django-secret-key. 
   4. Populate the values from the Cloud SQL DB Password, and for the django secret key, create a new random string  
   5. Setup yet another secret for Cloud Storage access. New secret named "admin-upload-key". Take contents from the cloud-key.json service account used to access the File Upload Cloud Storage bucket.


3. Configure Cloud Build
   1. Within Google Cloud Console - Cloud Build
   2. Enable Cloud Build API (if Necessary)
   3. Add Cloud Build Service Worker to Cloud Secrets
   4. Create Trigger
   5. Select Push to Branch
   6. Select Branch to push to
   7. (Optional) Specify a Service Account  


4. Set Permissions for Cloud Build
   1. Within Google Cloud Console - Select Security -> Secret Manager
   2. For each secret, select it, click the Permissions tab
   3. Note that the existing Principal permission as [Project number]@cloudservices.gserviceaccount.com
   4. Click Add, and add [Project number]@cloudbuild.gserviceaccount.com with the Role of Secret Manager Secret Accessor
   5. Repeat for each secret.
   6. Add Permission for Cloud Build Service Account (e.g. [Project number]@cloudbuild.gserviceaccount.com) to have the permission App Engine Deployer. Go to IAM & Admin, find the Cloud Build Service Account and Click Edit, and Add a New Role.
   

5. Setup and Configure Production Static
   1. Previously for file uploads, we have set up a Cloud Storage bucket. For static files (e.g. Django js files, images, etc.), we need to configure and use Cloud Storage for these files. 
   2. Set up a new Cloud Storage bucket, (e.g. "clover_static")
   3. Make the cloud build user role an OWNER - Within Cloud Storage, select the static files Bucket, then Permissions, then Add [Project number]@cloudbuild.gserviceaccount.com and specify role as Storage Admin AND Storage Legacy Bucket Owner.
   4. Make the Cloud Storage bucket readable by allUsers - Within Cloud Storage permissions, add a user "allUsers" with the Role Storage Object Viewer and the role Storage Legacy Bucket Reader.
   5. Update app.yaml `STATIC_URL` with the full path both bucket name and subdirectory "static" (e.g. https://storage.googleapis.com/clover_static/static/)
   6. Make sure the static paths in cloudbuild.yaml are pointing to your Static Cloud Storage bucket. To do so, update cloudbuild.yaml gs:// references with the full path (e.g. gs://clover_static/static/)
   7. Make sure the static folder path within the Django config file /site/config/settings.py STATICFILES_DIRS is set to './static'
      ```
      NOTE: For faster builds later on, when no static files have changed, comment out Build Step 1 - 3 in cloudbuild.yaml
      ```


6. Enable App Engine API's
   1. Go to https://console.developers.google.com/apis/api/appengine.googleapis.com/ 
   2. Enable the App Engine Admin API
   3. Go to https://console.developers.google.com/apis/api/deploymentmanager.googleapis.com
   4. Enable the Cloud Deployment Manager V2 API


7. Create the App Engine
   1. Either do so in the UI (e.g. https://console.cloud.google.com/appengine/)
   2. Or using the Cloud SDK 
      ```bash
      gcloud init, gcloud app create
      ```


8. Add Permissions
   1. Access IAM & Admin
   2. Add App Engine Access to Cloud Build User
   3. Select the cloud build service account (e.g. [Project number]@cloudbuild.gserviceaccount.com)
   4. Add the Roles: App Engine Admin, App Engine Service Admin, App Engine flexible environment Service Agent
   5. Add Cloud SQL Client role to App Engine service account
   6. Select the app engine service account (e.g. [Project ID]@appspot.gserviceaccount.com)
   7. Add the Role: Cloud SQL Client
   

9. Set allowed domain
   1. Update ALLOWED_HOSTS /site/config/settings.py
   2. Include the domain "[Project ID].uc.r.appspot.com" in the list where Project ID is located on your dashboard
   

10. Run a Build
    1. Push to main or merge a PR to whichever branch you marked to trigger a build.
    2. Inspect/ view build progress on the Cloud Build Dashboard (e.g. https://console.cloud.google.com/cloud-build)
    3. Builds on the base boilerplate will take around 8 minutes not including syncing static files (Build steps 1 & 2) which takes closer to 23 minutes. 
    

11. Verify Build
    1. Go to Google Cloud App Engine Dashboard (e.g. https://console.cloud.google.com/appengine)
    2. Click the URL in the top right, and access the subdir /admin. (e.g. https://[Project ID].uc.r.appspot.com/admin)
    

12. Run database migrations and setup superuser
    1. SSH into one of your running App Engine instances at App Engine -> Instances -> SSH (SSH into VM) (e.g. https://console.cloud.google.com/appengine/instances)
    2. Access the docker container of the running app by running:
       ```bash
       docker exec -it gaeapp /bin/bash
    
       python manage.py migrate
       ```
    3. (Optional) Setup superuser
       ```bash
       python manage.py createsuperuser
       ```
    

13. Configure a domain (Optional)
    1. Update ALLOWED_HOSTS /site/config/settings.py to include the domain
    2. Access App Engine -> Settings (e.g. https://console.cloud.google.com/appengine/settings)
    3. Select Custom Domains - Follow the prompts to set up a custom domain. You will need to have DNS access to set up records to validate ownership
   

## Contribute

- [See CONTRIBUTING.md](./CONTRIBUTING.md)


## Local Development Setup

```bash
# After pulling the project, from project folder run
make build

make up
# Review and confirm no errors showed, address as needed

# Run migrations
make migrate

# Create a super user for logging in, as needed
docker exec -it admin_django_1 python manage.py createsuperuser

# Run the django server on 8000
make serve
```

## Deploy Prep
For deployments, Google Cloud SDK required.
- [See Google Cloud SDK Docs] https://cloud.google.com/sdk/docs/quickstarts
- Confirm accuracy of app.yaml (GCP uses) and settings.py

## Deployments
- Managed by cloudbuild.yaml
- Cloud Build Triggers Builds on merge to master
- Status available at https://console.cloud.google.com/cloud-build/builds
```bash
# launches the above url
make check build
```

## Database Updates
```bash
# Running Migrations on CloudSQL can be done in a few ways. Preferable, is to SSH into one of the AppEngine instances and run on the docker container there
docker exec -it gaeapp python manage.py migrate
```

```bash
# TODO:
# gcloud app versions delete `gcloud app versions list | sed 's/  */:/g' | cut -f 2 -d : | tail -n +2 | ghead -n -5 | tr "\n" " "`
```
