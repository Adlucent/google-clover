#!/bin/bash

#Authors: Matt Zeiger & Sebastián Muñoz Toro Adlucent
#Thanks to the Server-Side Google Tag Manager team for the inspired setup.sh file https://googletagmanager.com/static/serverjs/setup.sh

WELCOME_TEXT=\
"If you haven't already run gcloud init initially please exit and run before proceeding.

Would you like to use the following project for setting up your CLoVeR server?
Note: Make sure the billing account is assigned and enabled before proceeding.

Please watch this process as there will be multiple prompts to continue (Y/n).

"

#read -r unused #just waits until you press enter

WISH_TO_CONTINUE="Do you wish to continue? (y/N): "

wait_all_operations_complete() {
  local pending_operations
  pending_operations="$(\
    gcloud app operations list --pending --verbosity=none -q 2> /dev/null)" ||
      true
  operations="$(echo "${pending_operations}" |
    sed -n 's/\([a-z0-9-]\{1,\}\)[[:blank:]]\{1,\}.*/\1/p')"
  if [[ -z "${operations}" ]]; then
    operations="$(echo "${pending_operations}" | sed -n 's/ID: \(.*\)/\1/p')"
  fi
  if [[ ! -z "${operations}" ]]; then
    echo "There are existing operations. Waiting for them to finish before continuing."
    for operation in ${operations}; do
      gcloud app operations wait "${operation}" --verbosity=none -q > /dev/null
    done
  fi
}

prompt_continue_default_no() {
  while true; do
    printf "$1"
    read confirmation
    confirmation="$(echo "${confirmation}" | tr '[:upper:]' '[:lower:]')"
    if [[ -z "${confirmation}" || "${confirmation}" == 'n' ]]; then
      printf "Use this command to create a new project:
gcloud projects create
Or use this command to set a different project:
gcloud config set project <PROJECT_ID>
"
      exit 0
    fi
    if [[ "${confirmation}" == "y" ]]; then
      break
    fi
  done
}

#Get the current project id, and ask to confirm if thats the right one
#if its not suggest they run 'gcloud config set project <project_id>' to set their current project
echo "${WELCOME_TEXT}"
echo $(gcloud config get project)
prompt_continue_default_no "${WISH_TO_CONTINUE}"
PROJECT_ID=$(gcloud config get project | tail -1)
echo "Installing config-connector"
gcloud components install config-connector

#1. Enable APIs 
echo "1/10. Enabling APIs
"
gcloud services enable sqladmin.googleapis.com
wait $!
gcloud services enable secretmanager.googleapis.com
wait $!
gcloud services enable storage.googleapis.com
wait $!
gcloud services enable storage-api.googleapis.com
wait $!
gcloud services enable storage-component.googleapis.com
wait $!
gcloud services enable appengine.googleapis.com
wait $!
gcloud services enable deploymentmanager.googleapis.com
wait $!
gcloud services enable servicemanagement.googleapis.com
wait $!
gcloud services enable iam.googleapis.com
wait $!
gcloud services enable cloudbuild.googleapis.com
wait $!

#2. Setup Service Account 
echo "2/10. Setting up Storage Service Account
"
#creates a new service account remotely and get the json secret key cloud-key-storage.json saved locally and is in gitignore
gcloud iam service-accounts create djangostorageadmin \
    --description="Django Storage Admin" \
    --display-name="djangostorageadmin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:djangostorageadmin@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
gcloud iam service-accounts keys create cloud-key-storage.json \
    --iam-account=djangostorageadmin@$PROJECT_ID.iam.gserviceaccount.com
cp cloud-key-storage.json ./site/cloud-key-storage.json

#3. Setup Cloud Storage Buckets 
echo "3/10. Setting up Cloud Secrets
"
gcloud alpha storage buckets create gs://${PROJECT_ID}_file_uploads
gcloud alpha storage buckets create gs://${PROJECT_ID}_clv-app-gcp_static
#Make the cloud build user role an OWNER - Within Cloud Storage, select the static files Bucket, then Permissions, then Add [Project number]@cloudbuild.gserviceaccount.com and specify role as Storage Admin AND Storage Legacy Bucket Owner.
#Figure out the PROJECT_NUMBER
SACCOUNTS=$(gcloud projects get-iam-policy $PROJECT_ID --format 'value(bindings.members[0])')
IFS=';' read -ra ADDR <<< "$SACCOUNTS"
for i in "${ADDR[@]}"; do
  if [[ "$i" == *"@cloudservices.gserviceaccount.com"* ]]; then
	  PROJECT_NUMBER=${i/@cloudservices.gserviceaccount.com/}
	  PROJECT_NUMBER=${PROJECT_NUMBER/serviceAccount:/}	  
  fi    
done
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/storage.admin"
# Make the Cloud Storage file upload bucket readable by allUsers - Within Cloud Storage permissions, add a user "allUsers" with the Role Storage Object Viewer and the role Storage Legacy Bucket Reader.
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}_file_uploads
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}_clv-app-gcp_static

#4. Create a Cloud SQL Instance 
echo "4/10. Creating Cloud SQL Instance
"
DB_PASSWORD=$(echo $RANDOM | base64 | head -c 20;) #generate a random db password,
gcloud sql instances create clover-gcp --database-version=POSTGRES_9_6 --cpu=2 --memory=8GiB --zone=us-central1-a --root-password=$DB_PASSWORD
DB_INSTANCE=$PROJECT_ID:us-central1:clover-gcp

#5. Setup Cloud secrets 
echo "5/10. Setting up Cloud Secrets
"
#for the django secret key, create a new random string  
DJANGO_SECRET=$(echo $RANDOM | base64 | head -c 20;)$(echo $RANDOM | base64 | head -c 20;)$(echo $RANDOM | base64 | head -c 20;)$(echo $RANDOM | base64 | head -c 20;)
#we need to set up 3 secrets db-password and django-secret-key and admin-upload-key
gcloud secrets create db-password --replication-policy="automatic"
echo -n $DB_PASSWORD | gcloud secrets versions add db-password --data-file=-
gcloud secrets create django-secret-key --replication-policy="automatic"
echo -n $DJANGO_SECRET | gcloud secrets versions add django-secret-key --data-file=-
gcloud secrets create admin-upload-key --replication-policy="automatic"
gcloud secrets versions add admin-upload-key --data-file="./cloud-key-storage.json"

#6. Create the App Engine 
echo "6/10. Creating the App Engine
"
gcloud app create

#7. Add Permissions 
echo "7/10. Adding Permissions
"
# Add Cloud SQL Client role to App Engine service account, Select the app engine service account (e.g. [Project ID]@appspot.gserviceaccount.com), Add the Role: Cloud SQL Client
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/cloudsql.admin"
      
# #8. Run a Build 
echo "8/10. Running Initial Build
"
gsutil -m rsync -r ./site/static gs://${PROJECT_ID}_clv-app-gcp_static/static/

#settings.py updates
sed -i "" s/{GCP_PROJECT_ID}/$PROJECT_ID/g ./site/config/settings.py # 4. Update /site/config/settings.py `GS_BUCKET_NAME`   

#cloudbuild.yaml updates
sed -i "" s,gs://clv-app-gcp_static,gs://${PROJECT_ID}_clv-app-gcp_static,g ./cloudbuild.yaml

#app.yaml updates
sed -i "" s,TEMP_DB_PASSWORD,${DB_PASSWORD},g ./site/app.yaml
sed -i "" s,TEMP_SECRET_KEY,${DJANGO_SECRET},g ./site/app.yaml
sed -i "" s/clover-gcp:us-central1:clover-gcp/$DB_INSTANCE/g ./site/app.yaml #Update two (2) fields in app.yaml DB_HOST with /cloudsql/NAME_OF_INSTANCE and update cloud_sql_instances: with NAME_OF_INSTANCE  
sed -i "" s,https://storage.googleapis.com/clover-gcp_static/static/,https://storage.googleapis.com/${PROJECT_ID}_clv-app-gcp_static/static/,g ./site/app.yaml

#run build
gcloud app deploy site/app.yaml --stop-previous-version
wait $!

VERSION=$(gcloud app instances list -s default --format 'value(version)' | cut -d " " -f 2)
INSTANCEID=$(gcloud app instances list -v $VERSION --format 'value(ID)')
    
# #9. Run database migrations 
echo "9/10. Running Database migrations
"
gcloud app instances ssh --service=default --version=$VERSION $INSTANCEID --container=gaeapp -- python manage.py migrate

#10. Setup superuser
echo "10/10. Setting up Superuser
"
SU_PASSWORD=$(echo $RANDOM | base64 | head -c 20;)
gcloud app instances ssh --service=default --version=$VERSION $INSTANCEID --container=gaeapp -- python manage.py createsuperuser_if_none_exists --user=admin --password=$SU_PASSWORD

echo "Generated Default Admin Login: 
Username: admin
Password: $SU_PASSWORD
"

#11. CLEANUP/ Revert file changes for building the app via cloud build
sed -i "" s,${DB_PASSWORD},'',g ./site/app.yaml
sed -i "" s,${DJANGO_SECRET},'',g ./site/app.yaml

open https://$PROJECT_ID.uc.r.appspot.com/admin

# #DEV USE - CLEANUP files before commiting updates to google-clover boilerplate via git
# sed -i "" s/$PROJECT_ID/{GCP_PROJECT_ID}/g ./site/config/settings.py
# sed -i "" s,gs://${PROJECT_ID}_clv-app-gcp_static,gs://clv-app-gcp_static,g ./cloudbuild.yaml
# sed -i "" s,https://storage.googleapis.com/${PROJECT_ID}_clv-app-gcp_static/static/,https://storage.googleapis.com/clover-gcp_static/static/,g ./site/app.yaml
# sed -i "" s/$DB_INSTANCE/clover-gcp:us-central1:clover-gcp/g ./site/app.yaml
# sed -i "" s,${DB_PASSWORD},TEMP_DB_PASSWORD,g ./site/app.yaml
# sed -i "" s,${DJANGO_SECRET},TEMP_SECRET_KEY,g ./site/app.yaml