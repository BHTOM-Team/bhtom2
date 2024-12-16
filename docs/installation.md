# Running Services Locally Using Docker

## Prerequisites

1. **Install Docker**: Ensure Docker is installed on your system.  
2. **Install Docker Compose**: Version > 1.25.0 is required.  
3. **VPN Connection (if required)**: For services requiring access to `wsdb_cache`, ensure you are connected to the VPN or have valid SSH parameters configured in the environment file.  

## Environment Setup

1. **Create Environment Files**:  
   Each service requires a `.env` file for configuration, which should be created in the `docker/dev` directory.  

   - Each service includes an `.env.template` file in the `docker/dev` folder. Copy the content of the template to a new `.env` file and fill in the appropriate values.  
   - Use the same template structure for all services.  

2. **Set Up the `DATA_STORE_PATH`**:  
   In the `.env` file, you will find a parameter called `DATA_STORE_PATH`. This should point to a local folder on your machine. The folder must have the following structure:

   ```text
   DATA_STORE_PATH/
   ├── cache/
   ├── log/
   ├── plots/
   ├── targets/
   ├── cpcsArchiveFile/
   ├── fits/
   ├── kafka/
   ```

   Make sure to create all these subfolders in the directory specified by `DATA_STORE_PATH`.

3. **VPN or SSH Configuration**:  
   For the `cpcs` service, you will need access to the `wsdb_cache` database. To do this:  
   - Connect via VPN to the Cambridge WSDB database.  
   - Alternatively, configure SSH parameters in the `.env` file for the service.  
```

This includes the precise folder structure needed under `DATA_STORE_PATH`. Ensure that your local folder matches this structure for the services to function correctly.
---

## Starting Services Locally

### Step 1: Start the `bhtom2` Service  

The `bhtom2` service must be started first as it initializes the main database.  

1. Navigate to the `docker/dev` directory of the `bhtom2` service:  
   ```bash
   cd bhtom2/docker/dev
   ```  
2. Build and run the `bhtom2` service:  
   ```bash
   docker-compose up -d --build
   ```  

### Step 2: Start Other Services  

Once the `bhtom2` service is running, start the other services in any order:  

#### Upload Service  

1. Navigate to the `docker/dev` directory of the `upload-service`:  
   ```bash
   cd upload-service/docker/dev
   ```  
2. Build and run the service:  
   ```bash
   docker-compose up -d --build
   ```  

#### CPCS Service  

1. Navigate to the `docker/dev` directory of the `cpcs` service:  
   ```bash
   cd cpcs/docker/dev
   ```  
2. Build and run the service:  
   ```bash
   docker-compose up -d --build
   ```  

#### Harvester Service  

1. Navigate to the `docker/dev` directory of the `harvester` service:  
   ```bash
   cd harvester/docker/dev
   ```  
2. Build and run the service:  
   ```bash
   docker-compose up -d --build
   ```  

### Step 3: Verify All Services  

To ensure all services are running correctly, check their logs:  
```bash
docker-compose logs -f
```  
