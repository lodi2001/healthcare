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

### Option 3: Using Django Shell (Most Reliable)

If you're still having issues, you can create the services directly through the Django shell:

1. **Access the Django shell**:
   ```bash
   # On your production server
   docker-compose exec web python manage.py shell
   ```

2. **Copy and paste this entire code block into the shell**:
   ```python
   from apps.services.models import Service, ServiceCategory

   # Create default service categories
   default_categories = [
       {'name': 'General Medicine', 'description': 'General healthcare services', 'icon': 'fa-stethoscope'},
       {'name': 'Specialized Care', 'description': 'Specialized healthcare services', 'icon': 'fa-heartbeat'},
       {'name': 'Cardiology', 'description': 'Heart and cardiovascular system', 'icon': 'fa-heart'},
       {'name': 'Neurology', 'description': 'Brain, spinal cord, and nervous system', 'icon': 'fa-brain'},
   ]
   
   categories_created = 0
   for cat_data in default_categories:
       cat, created = ServiceCategory.objects.get_or_create(
           name=cat_data['name'],
           defaults={
               'description': cat_data['description'],
               'icon': cat_data.get('icon', '')
           }
       )
       if created:
           categories_created += 1
           print(f"Created service category: {cat.name}")
   
   # Get the General Medicine category for services
   try:
       default_category = ServiceCategory.objects.get(name='General Medicine')
   except ServiceCategory.DoesNotExist:
       default_category = ServiceCategory.objects.first()
   
   if not default_category:
       print("No category found. Creating General Medicine category.")
       default_category = ServiceCategory.objects.create(
           name='General Medicine',
           description='General healthcare services',
           icon='fa-stethoscope'
       )
   
   # Create default services
   default_services = [
       {'name': 'General Consultation', 'description': 'Regular medical consultation', 'price': 150.00, 'duration': 30},
       {'name': 'Follow-up Visit', 'description': 'Follow-up appointment for existing patients', 'price': 100.00, 'duration': 20},
   ]
   
   # Get the Specialized Care category
   try:
       specialized_category = ServiceCategory.objects.get(name='Specialized Care')
   except ServiceCategory.DoesNotExist:
       specialized_category = ServiceCategory.objects.create(
           name='Specialized Care',
           description='Specialized healthcare services',
           icon='fa-heartbeat'
       )
   
   # Add specialized services
   specialized_services = [
       {'name': 'Cardiac Assessment', 'description': 'Comprehensive heart health evaluation', 'price': 300.00, 'duration': 45},
       {'name': 'Diabetes Management', 'description': 'Diabetes care and management', 'price': 200.00, 'duration': 40},
   ]
   
   # Combine all services
   services_to_create = []
   for service in default_services:
       service['category'] = default_category
       services_to_create.append(service)
   
   for service in specialized_services:
       service['category'] = specialized_category
       services_to_create.append(service)
   
   services_created = 0
   for service_data in services_to_create:
       service, created = Service.objects.get_or_create(
           name=service_data['name'],
           defaults={
               'category': service_data['category'],
               'description': service_data['description'],
               'price': service_data['price'],
               'duration_minutes': service_data['duration'],
               'pricing_type': 'fixed'
           }
       )
       if created:
           services_created += 1
           print(f"Created service: {service.name}")
   
   print(f'Created {categories_created} service categories and {services_created} services')
   ```

3. **Press Enter** to execute the code and create the services

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

### Fixture Files Not Found

If you encounter an error like:
```
CommandError: No fixture named 'service_categories' found.
```

This means the fixture files are not in the expected location. Try these solutions:

1. **Check if the fixtures directory exists**:
   ```bash
   ls -la fixtures/
   ```

2. **Create the fixtures directory if it doesn't exist**:
   ```bash
   mkdir -p fixtures
   ```

3. **Manually copy the fixture content**:
   You can create the fixture files manually by copying the content from your local environment.

4. **Use the direct script approach instead (recommended)**:
   ```bash
   # This is the most reliable method
   docker-compose exec web python create_services_script.py
   ```

### Services Not Showing Up After Import

If services are still not showing up in your application after importing:

1. **Check if the services were created in the database**:
   ```bash
   docker-compose exec web python manage.py shell -c "from apps.services.models import Service, ServiceCategory; print(f'Categories: {ServiceCategory.objects.count()}, Services: {Service.objects.count()}')"
   ```

2. **Clear cache if applicable**:
   ```bash
   docker-compose exec web python manage.py clearcache
   ```

3. **Restart the web server**:
   ```bash
   docker-compose restart web
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
