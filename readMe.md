# Wonderspaced Backend

An app that makes learning fun! Watch videos, read stories, and try cool DIY activities while exploring Ghanaian culture, solving problems, and creating amazing things. We see our users as explorers, and the app is their guide on an adventure to discover, explore and create.

---

## 📂 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Security Measures](#security-measures)
- [Deployment](#deployment)
- [Future Enhancements](#future-enhancements)

---

## Features

- **Videos**: Videos that take kids on a fun learning adventure. They're categorized into themes. Videos can be paused, or forwarded or rewinded with the scrub bar.
- **eBooks**: eBooks that take kids on a fun learning adventure. They're also categorized into themes.
- **DIYs**: DIY tutorials that inspire kids to be creators. DIY is among the Adventure Show Categories.
- **Quizzes**: Quizzes of varying difficulties on eBooks and videos.
- **Themes**: Videos, eBooks and DIYs are catgeorized into their own respective themes.
- **Library**: Branded as "My adventures." Explorers can track their learning here.
- **Read-aloud feature**: eBooks can be read aloud.
- **Explorer Profiles**: Accounts can have multiple explorer profiles. 
- **Avatars**: 2D Avatars to allow explorers to showcase their personality.
- **User Authentication**: JWT-based sessions initiated by password, passwordless and social logins.
- **Real-time notifications**: Notifications for updates and reminders

---

##  Tech Stack

- **Language**: Python 3.12
- **Web Framework**: FastAPI
- **Database**: PostgreSQL (primary), Google CloudSQL
- **Migrations** Alembic
- **Authentication**: JWT, OAuth2 (Google)
- **File Storage**: AWS S3  and Google Cloud Storage
- **Caching**: FastAPICache and Redis
- **Task Queue**: Google Cloud Tasks
- **Cloud Jobs**: Google Cloud Jobs
- **Deployment**: Google Cloud Run, Docker, Uvicorn
- **Secret Management**: Google Secret Manager

---

##  Project Structure

```
.
├── Dockerfile
├── Dockerfile.migrations
├── alembic
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
├── alembic.ini
├── app
│   ├── __init__.py
│   ├── api
│   │   └── v1
│   │       └── routers
│   │           ├── __init__.py
│   │           ├── adventure_progress.py
│   │           ├── adventures.py
│   │           ├── auth.py
│   │           ├── avatars.py
│   │           ├── classrooms.py
│   │           ├── ebooks.py
│   │           ├── ebooks_tab.py
│   │           ├── explore_tab.py
│   │           ├── gcs_urls.py
│   │           ├── my_explorer_tab.py
│   │           ├── notifications.py
│   │           ├── profiles.py
│   │           ├── questions.py
│   │           ├── quiz_attempts.py
│   │           ├── quiz_responses.py
│   │           ├── quizzes.py
│   │           ├── redirects.py
│   │           ├── series.py
│   │           ├── stats.py
│   │           ├── themes.py
│   │           ├── users.py
│   │           ├── videos.py
│   │           └── videos_tab.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── rate_limiter.py
│   │   └── security.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── session.py
│   │   └── ts_vector.py
│   ├── schemas
│   │   ├── adventure.py
│   │   ├── auth.py
│   │   ├── avatar.py
│   │   ├── classroom.py
│   │   ├── ebook.py
│   │   ├── explore.py
│   │   ├── file_upload.py
│   │   ├── my_explorer.py
│   │   ├── notifications.py
│   │   ├── profile.py
│   │   ├── quiz.py
│   │   ├── quiz_attempt.py
│   │   ├── response.py
│   │   ├── series.py
│   │   ├── stats.py
│   │   ├── theme.py
│   │   ├── user.py
│   │   └── video.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── adventure.py
│   │   ├── auth.py
│   │   ├── classroom.py
│   │   ├── cloud_job_init.py
│   │   ├── cloud_task_init.py
│   │   ├── ebook.py
│   │   ├── firebase_init.py
│   │   ├── my_explorer.py
│   │   ├── notifications.py
│   │   ├── profile.py
│   │   ├── quiz.py
│   │   ├── s3.py
│   │   ├── series.py
│   │   ├── stats
│   │   │   ├── __init__.py
│   │   │   ├── adventure.py
│   │   │   ├── content.py
│   │   │   ├── profile.py
│   │   │   └── users.py
│   │   ├── theme.py
│   │   ├── user.py
│   │   └── video.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── logs
│   │   │   └── app.log
│   │   ├── test_profile.py
│   │   └── test_users.py
│   └── utils
│       ├── __init__.py
│       ├── cache.py
│       ├── email.py
│       ├── file.py
│       ├── format_quiz_instruction.py
│       ├── gcs.py
│       └── general.py
├── cloud-sql-proxy
├── cloudbuild.dev.yaml
├── cloudbuild.prod.yaml
├── cors.json
├── github
│   └── workflows
│       └── deploy.yml
├── logs
│   └── app.log
├── main.py
├── readMe.md
├── requirements.txt
└── secrets
```

---

##  Setup Instructions

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/wspaced_backend.git
cd wspaced_backend
```

#### 2. Set up virtual environment and activate it.

```bash
pip install virtualenv
python<version> -m venv <virtual-environment-name>
source <virtual-environment-name>/bin/activate
```

#### 3. Install requirements.

```bash
pip install --no-cache-dir -r requirements.txt
```

#### 4. Set Up Database

We recommend an async database since it's one of the ways FastAPI improves performance. It allows the app to handle more requests concurrently.

This project uses PostgreSQL as the primary database because of its support of more data types, complex queries, concurrent transactions and data integrity, and its community support.

You can either use a local database or a cloud database (but once you deploy your app to Cloud Run, you must use a Cloud database). You can set up your local database with PGAdmin. For a cloud database, you can use Google CloudSQL (This project uses Google Cloud Services). If you're using Google CloudSQL, you'll have to set up a Google CloudSQL instance and create a database for it. 

FastAPI uses SQLAlchemy as the ORM and Alembic for migrations. This project uses SQLModel, an abstraction and improved version of SQLAlchemy to define its database schema. 

Alembic is a lightweight database migration tool for SQLAlchemy. It generates migration scripts for changes to the database schema. This project already has alembic initialized. Alembic is initialized with the command below:

```bash
alembic init alembic
```

This will create an `alembic` folder in the root directory. You'll also need to create an `alembic.ini` file. See the `alembic.ini` file in the root directory for an example. 

This project's `alembic.ini` file doesn't contain the database URL since `alembic/env.py` is set up to use the database credentials defined as environment variables in `app/core/config.py`. If you want to specify the database URL in the `alembic.ini` file, you can add it as shown below:

```ini
sqlalchemy.url = postgresql+asyncpg://<db_user>:<db_password>@<db_host>:<db_port>/<db_name>
```

You'll find among the code snippets below an example of how to modify the `alembic/env.py` to read the database URL from `alembic.ini`.

Additionally, the `env.py` file in the `alembic` folder will need to be modified to use the Google CloudSQL instance. Below is an example of how to modify the env.py file to connect to Google CloudSQL database. This is for an async engine and the connection is done via the Google Cloud SQL Python Connector:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool

from alembic import context
from sqlmodel import SQLModel

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

from google.cloud.sql.connector import Connector, IPTypes


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url", settings.DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
        
        
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()
    
    
async def run_async_migrations():
    """Run migrations in 'online' mode using the async engine."""
    ip_type = IPTypes.PUBLIC

    connector = Connector(refresh_strategy="LAZY")

    def getconn():
        return connector.connect_async(
            settings.INSTANCE_CONNECTION_NAME,
            "asyncpg",
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME,
            ip_type=ip_type,
        )
        
    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator= getconn,
        poolclass=pool.AsyncAdaptedQueuePool,
        echo=True 
    )
    
    
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()
    
    
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

To set up `env.py` for a local database or some other cloud database (maybe Render), you can modify it as shown below. This is for an async engine. It assumes you're using PostgreSQL, that the database URL is stored in the `DATABASE_URL` environment variable in `app/core/config.py` in the `Settings` class. and your `alembic.ini` is in the root directory and contains the `DATABASE_URL` environment variable:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from sqlmodel import SQLModel

from app.core.config import Settings # modify this to the path of your settings class
from sqlalchemy.ext.asyncio import async_engine_from_config


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url", Settings.DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
        
        
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()
        
        
async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

To set up the `env.py` for a local database or some other cloud database (maybe Render) without having to rely on alemic.ini for the `DATABASE_URL`, you can modify it as shown below. This is for an async engine:

```python
import asyncio
from logging.config import fileConfig

import asyncpg
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import sqlalchemy
from sqlmodel import SQLModel

from app.core.config import settings
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine, AsyncEngine


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url", settings.DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
        
        
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

    
async def run_async_migrations():
    """Run migrations in 'online' mode using the async engine."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()
    
    
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### 5. Set Up Environment Variables

You can set up environment variables in a `.env` file, in your system's environment variables or in Google Secret Manager.

To use a `.env` approach, first create a `.env` file. By default, this app retrieves secrets from Google Secret Manager so you'll have to modify app/core/config.py to use environment variables instead.

Below is an example of the `.env` file:

```env
SECRET_KEY=your-secret-key
ALGORITHM=HS256
DB_NAME=db_name
DB_PASSWORD=db_password
DB_USER=db_user
INSTANCE_CONNECTION_NAME=instance_connection_name
GCS_PERMANENT_BUCKET=gcs_permanent_bucket
GCS_TEMPORARY_BUCKET=gcs_temporary_bucket
```

To set up the `Settings` class in `app/core/config.py` to use environment variables, modify the class as shown below:

```python
class Settings:

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    GCP_PROJECT_ID: str
    SECRET_KEY: str 
    ALGORITHM: str
    DB_NAME: str 
    DB_USER: str 
    DB_PASSWORD: str
    INSTANCE_CONNECTION_NAME: str 
    GCS_TEMP_FILES_BUCKET: str 
    GCS_PERMANENT_FILES_BUCKET: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_STORAGE_BUCKET_NAME: str
    AWS_S3_REGION_NAME: str
    AWS_S3_FILE_OVERWRITE: str
    AWS_DEFAULT_ACL: str
    GEMINI_KEY: str
```

Pydantic will automatically load the environment variables from the `.env` file without you having to explicitly set them. It identifies the environment variables by their names so all you have to do is ensure that the environment variables in the `.env` file match the names in the `Settings` class and specify the type of the variable. 

See the Deployment section for how to set up environment variables in Google Secret Manager.

#### 6. Run migrations

Before you run migrations, ensure all your models are imported in alembic/env.py. Else alembic won't be able to detect them.

```bash
alembic revision --autogenerate -m "migration" # Generate migration script
alembic upgrade head # Apply changes to the database
```

Track migration files in version to enable rollback in case of failure. Tracking is easier if migration history is consistent across dev and prod branches. 

Before running migrations from your local device, always check the local environment (whether dev or prod) first. By default, it's set to `dev` if `os.getenv("ENV)` returns `None`. On the main branch, you should set the default to `prod` before you run migrations from your local device.

#### 7. Run Locally (without Docker)

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

---

##  API Endpoints

The API endpoints can be found in our Postman collection with sample requests and responses.
Find the collection here: https://web.postman.co/workspace/cf3d7243-175f-437a-83c2-2fc575c607a4.
Only invited users can access the collection.

## Security Measures

- **Data Encryption**: TLS/SSL for secure data transfer
- **JWT Authentication**: Access and refresh tokens
- **Rate Limiting**: Prevent abuse via middleware
- **Input Validation**: Strict validation for all endpoints

---

## Email Configuration

This project uses Amazon SES for sending emails. 

You'll have to create an IAM user with the AmazonSESFullAccess policy and set up a verified sender email address. 
Then retrieve the access key ID and secret access key from the IAM user and store them securely. You can thene use it to create a boto3 client for sending emails.

You can find the documentation here: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/Welcome.html. 

To use the boto3 client, you can use the `send_email` function in `app/services/email.py`.

---

## Firebase Configuration

This project uses Firebase for notifications. 

You'll have to create a Firebase project, create a service account and download its key and store it securely. If you store the raw json string of the key, remember to use `json.loads()` to convert it to a dictionary before passing it to the `credentials.Certificate` function.

You can find the documentation here: https://firebase.google.com/docs/auth. Once you have the service account key, you can use it to create a Firebase Admin SDK client for sending notifications.

To use the Firebase Admin SDK client, you can use the `send_notification` function in `app/services/notification.py`.

---

## Deployment

### Google Cloud and AWS

1. Create a Google Cloud account and set up billing.

2. Create a Google Cloud Project from the console. You can use the CLI to create a project but we recommend using the console for this step since it's easier.

3. See Google's documentation for instructions on CLI login. You must have the Google SDK installed. You can either use Application Default Credentials or a service account key (remember to gitignore it if you store it in your project's directory) for authentication. Before then, ensure you've initialized gcloud and logged in with `gcloud auth login.` The service account key are required for some services (signed URL uploads), otherwise, you can use Application Default Credentials.

When you get the service account key, add it your path with the command below. Note that it only lasts for the terminal session:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

You can also set the environment variable in your `.bashrc` or `.zshrc` file so that it lasts beyond a single terminal session.

If you already have this variable added to your path with another value, remember to unset it with the command below, before adding the new one to your path:

```bash
unset GOOGLE_APPLICATION_CREDENTIALS"
```

Once authenticated with the CLI, you can run commands to create, manage, access or deploy resources for your Google Cloud project. Set the project ID and quota project to ensure you're working with the right project and billing is associated with it.
 
Here are some commands you might need:

```bash
gcloud init # Initialize gcloud
gcloud components update # Update Google Cloud CLI components
gcloud auth login # Log in to gcloud
gcloud auth application-default login # Log in with application default credentials
gcloud projects create <project-id> # Create a project
gcloud projects list # List projects
gcloud config set project <project-id> # Set the project
gcloud services enable <service-name> # Enable a service
gcloud services list # List enabled services
gcloud auth application-default set-quota-project <project-id> # Set quota project. Ensures billing is associated with the project.
```

The standard sequence of commands for authentication is:

```bash
# Log in to gcloud
gcloud auth login

# Log in with application default credentials
gcloud auth application-default login

# Set the project
gcloud config set project <project-id>

# Set the quota project
gcloud auth application-default set-quota-project <project-id>

# Set Google Application Default Credentials
export GOOGLE_APPLICATION_CREDENTIALS="<path-to-key-file>"
```

4. We recommend creating a user-managed service account for your cloud run service and assign it the necessary roles. Always follow the least privilege principle so that your service account only has the permissions it needs.

```bash
gcloud iam service-accounts create <service-account-name> --display-name "<display-name>"
```

The roles recommended for a cloud run service based on this project are:

- Cloud SQL Admin
- Cloud Tasks Admin
- Secret Manager Accessor
- Service Usage Consumer

You can also create a service account from the console. Create a key for the service account with the command below. This will create a JSON key file for the service account. You can also create a key from the console. Once created, you can download the key and use it for authentication. Remember to gitignore the key file if you store it in your project's directory.

```bash
gcloud iam service-accounts keys create <key-file-name>.json --iam-account <service-account-name>@<project-id>.iam.gserviceaccount.com
```

5. Create a Google Cloud SQL instance and create a database for it.

6. Using Google Secret Manager, create secrets for the variables in the Settings class in app/core/config.py.

7. Create a Cloud Run Service.

8. Create Cloud task queues for any cloud tasks.

9. Create GCS buckets if necessary. Remember to set access control to fine-grained to enable public access and allow writing to and deleting from your FastAPI app. For buckets containing temporary files, configure periodic deletion to save space. You can also configure a soft delete mechanism in case of accidental deletion.
If uploads from a web app return a CORS error, you can set up CORS configuration for the bucket. First, create a `cors.json` file with the following content:

```json
[
    {
        "origin": ["*"],
        "responseHeader": ["Content-Type", "x-goog-acl"],
        "method": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "maxAgeSeconds": 3600
    }
]
```

Then, run the command below to set the CORS configuration for the bucket:

```bash
gsutil cors set cors.json gs://<bucket-name>
```

or

```bash
gcloud storage buckets update gs://<bucket-name> --cors-file=cors.json  
```

10. Enable APIs for all these services.

11. Modify the cloudbuild.yaml file with the appropriate credentials (Project ID, Cloud SQL instance name, Cloud Run service name, region)

12. Create an AWS account and set up billing (If you wish to use any of their services).

13. Create an S3 bucket if required. Enable public access and access control lists for buckets containing files to be accessed by the public. We recommend the policy below for such buckets. Remember to retrieve S3 credentials and store them as environment variables, and set up CORS configuration for the bucket.

```bash
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::<bucket-name>/*"
        }
    ]
}
```

14. To enable your cloud run service generate signed URLs, we recommend creating a dedicated service account (least privilege principle) for it and assign it the following permissions:

- `roles/storage.objectAdmin`
- `roles/iam.serviceAccountTokenCreator`

Then, store the json key in your secrets. To access it in your code, json.loads() the secret and use it to create credentials. The objectAdmin role offers all bucket permissions inclduing delete, upload and read.

15. Run migrations with alembic. You can also include migrations in the deployment process by adding a migrations step to cloudbuild.yaml. If you want to run migrations manually, first generate a migration script with the command below. We recommend running migrations manually, since database changes, should be rare, and to avoid creating redundant migration scripts upon every deployment.

```bash
alembic revision --autogenerate -m "migration"
```
Then run the migration with the command below to apply the changes to the database:

```bash
alembic upgrade head
```

16. Deploy your app to Cloud Run with either cloudbuild.dev.yaml or cloudbuild.prod.yaml, depending on the branch you're working in. 

In production (main branch), run:

```bash
gcloud builds submit --config cloudbuild.prod.yaml .   
```

In development (dev branch), run:

```bash
gcloud builds submit --config cloudbuild.dev.yaml .   
```

---

## Potential Future Enhancements

- **Microservices** for scaling independent modules
- **GraphQL API** for flexible data querying
- **AI/ML** integration for personalization, enhanced read-aloud, etc.

---

## Contact

For questions or feedback, reach out at [wonderspacedapp@gmail.com](mailto:wonderspacedapp@gmail.com).

---

**Stay Wonderful! 🎨✨**

