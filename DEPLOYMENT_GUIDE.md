# Deployment Guide for Healthcare Application on Digital Ocean

This guide will walk you through deploying your Django healthcare application on Digital Ocean using Docker and Docker Compose.

## Prerequisites

1. A Digital Ocean account
2. Basic knowledge of Docker and Docker Compose

## Step 1: Create a Digital Ocean Droplet

1. Log in to your Digital Ocean account
2. Click on "Create" and select "Droplets"
3. Choose the following options:
   - **Image**: Ubuntu 20.04 (LTS) x64
   - **Plan**: Basic (Recommended: at least 2GB RAM / 1 CPU)
   - **Datacenter Region**: Choose the region closest to your users
   - **Authentication**: SSH keys (recommended) or password
   - **Hostname**: Choose a name for your droplet (e.g., healthcare-app)
4. Click "Create Droplet"

## Step 2: Connect to Your Droplet

```bash
ssh root@your_droplet_ip
```

## Step 3: Install Docker and Docker Compose

```bash
# Update package list
apt update

# Install required packages
apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Add Docker repository
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Update package list again
apt update

# Install Docker
apt install -y docker-ce

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

## Step 4: Clone Your Repository and Configure Environment

```bash
# Clone your repository
git clone https://github.com/yourusername/healthcare.git /root/healthcare

# Create .env file
cd /root/healthcare
cp .env.example .env
```

Edit the `.env` file with your production settings:

```
# Django settings
SECRET_KEY=your-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=*

# Security settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True

# Database settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=healthcare_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432
```

## Step 5: Configure Firewall

```bash
# Install UFW if not already installed
apt install -y ufw

# Allow SSH connections
ufw allow ssh

# Allow HTTP and application port
ufw allow 80
ufw allow 8000

# Enable firewall
ufw enable
```

## Step 6: Deploy Your Application

```bash
# Build and start the containers
docker-compose up -d

# Check if containers are running
docker-compose ps
```

## Step 7: Run Database Migrations

```bash
docker-compose exec web python manage.py migrate
```

## Step 8: Create a Superuser (Optional)

```bash
docker-compose exec web python manage.py createsuperuser
```

## Accessing Your Application

You can access your application in two ways:

1. **Direct Django access**: `http://68.183.142.4:8000`
2. **Through Nginx**: `http://68.183.142.4`

## Environment-Specific Settings

The application now uses environment-specific settings to handle both local development and production environments:

### Local Development

For local development, copy the `.env.local` file to `.env`:

```bash
cp .env.local .env
```

This sets `PRODUCTION=False` and configures the application to:
- Use SQLite as the database
- Enable DEBUG mode
- Allow connections only from localhost
- Disable production security settings

### Production Deployment

For production deployment on Digital Ocean, use the `.env.example` as a template:

```bash
cp .env.example .env
```

Then edit the `.env` file to set your production values:
- Set `PRODUCTION=True`
- Set a secure `SECRET_KEY`
- Configure PostgreSQL database credentials
- Set `DEBUG=False`

The application will automatically use the appropriate settings based on the `PRODUCTION` flag.

## Transferring Initial Data to Production

To ensure that your production environment has the same services and service categories data as your local environment, follow these steps:

### Option 1: Using Fixtures (Data Export/Import)

1. **Export data from your local environment**:
   ```bash
   # Run this command in your local development environment
   python manage.py export_initial_data
   ```
   This will create JSON fixtures in the `fixtures/` directory.

2. **Copy the fixtures to your production server**:
   ```bash
   # Copy fixtures to your server (replace username and server-ip with your values)
   scp -r fixtures/ username@server-ip:/root/healthcare/
   ```

3. **Import data on your production server**:
   ```bash
   # Run this on your production server
   cd /root/healthcare
   docker-compose exec web python manage.py loaddata fixtures/service_categories.json fixtures/services.json
   ```

### Option 2: Using Direct Script (Recommended)

If you're having issues with the management commands, you can use the provided Python script:

1. **Make sure you've pulled the latest code**:
   ```bash
   # On your production server
   cd /root/healthcare
   git pull origin master
   ```

2. **Run the script directly**:
   ```bash
   # On your production server
   cd /root/healthcare
   docker-compose exec web python create_services_script.py
   ```

This script will create a set of default service categories and services if they don't already exist in the database.

## Troubleshooting

### View Logs

```bash
# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart a specific service
docker-compose restart web
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose down
docker-compose up -d
```

## Backup and Restore

### Backup Database

```bash
docker-compose exec db pg_dump -U postgres healthcare_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U postgres healthcare_db < backup.sql
```

## Monitoring

Consider setting up monitoring for your application using Digital Ocean's built-in monitoring tools or third-party services like Prometheus and Grafana.

## Security Best Practices

1. Regularly update your system and dependencies
2. Use strong, unique passwords
3. Implement IP-based access restrictions where appropriate
4. Set up a firewall (UFW)
5. Enable automatic security updates
6. Regularly review logs for suspicious activity

## Scaling

If your application needs to handle more traffic, consider:

1. Upgrading your Digital Ocean droplet
2. Implementing a load balancer
3. Using Digital Ocean's managed database service
