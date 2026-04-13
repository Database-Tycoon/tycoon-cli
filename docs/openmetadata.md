# Using OpenMetadata with Tycoon

[OpenMetadata](https://open-metadata.org/) is a unified platform for data discovery, data observability, and data governance. It can be used with Tycoon to provide a centralized view of your data assets.

This document provides a guide on how to set up OpenMetadata and outlines how it can be used with the Tycoon project.

## 1. Installing and Running OpenMetadata

OpenMetadata can be run locally using Docker. The following steps will guide you through the process.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (version 20.10.0 or greater) with at least 6 GiB of memory and 4 vCPUs allocated.
- [Docker Compose](https://docs.docker.com/compose/install/) (version v2.1.1 or greater).

### Procedure

1.  **Create a directory for OpenMetadata:**

    ```bash
    mkdir openmetadata-docker && cd openmetadata-docker
    ```

2.  **Download the Docker Compose file:**

    Download the `docker-compose.yml` file from the [OpenMetadata GitHub releases](https://github.com/open-metadata/OpenMetadata/releases). You can use `curl` to download it:

    ```bash
    # Replace 1.12.4 with the latest release if needed
    curl -sL -o docker-compose.yml https://github.com/open-metadata/OpenMetadata/releases/download/1.12.4-release/docker-compose.yml
    ```

3.  **Start the Docker Compose services:**

    ```bash
    docker compose up --detach
    ```

    This will pull the required Docker images and start the OpenMetadata services in the background.

4.  **Access the OpenMetadata UI:**

    Once the services are up and running, you can access the OpenMetadata UI at [http://localhost:8585](http://localhost:8585).

    The default login credentials are:
    -   **Username:** `admin@open-metadata.org`
    -   **Password:** `admin`

## 2. Integrating Tycoon with OpenMetadata

A direct integration between Tycoon and OpenMetadata is not yet implemented. However, it is possible to build such an integration using the OpenMetadata APIs and Python SDK.

A future integration could involve:

-   **Publishing Tycoon sources as OpenMetadata services:** The data sources defined in `tycoon.yml` could be registered as new services in OpenMetadata.
-   **Publishing dbt models as OpenMetadata tables:** The dbt models in the Tycoon project could be published as tables in OpenMetadata, complete with schema information.
-   **Publishing data lineage:** The lineage between dbt models could be extracted and published to OpenMetadata to provide a complete end-to-end view of the data flow.

This integration would provide a powerful way to discover, govern, and understand the data assets managed by the Tycoon project.
