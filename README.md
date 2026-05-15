# NF Compose 🌐

NF Compose is a dynamic data integration platform designed to streamline the development process. It empowers developers to define REST APIs quickly, transitioning from hours to mere seconds. 🚀

## Key Features:

- **Rapid REST API Generation**: APIs are backed by PostgreSQL, ensuring robust and scalable solutions.
- **Real-time Notifications**: Automatic consumer notifications for data updates, keeping users informed on the fly via webhooks. 🔔
- **Customization Layer**: Offers deep customization with pluggable engines, adapting to diverse integration needs.
- **Multi-Tenancy Architecture**: A single instance can efficiently serve multiple tenants or projects, maximizing resource utilization. 🌟

# Showcase 🎥

Discover how NF Compose simplifies REST API setup. Watch our short video demonstrating the ease of going from zero to a fully functional REST API in under 3 minutes!

https://github.com/neuroforgede/nfcompose/assets/719760/fc2d01db-75b7-47ef-ba28-2364034d4051

# Try It Out 🛠️

Explore NF Compose with our public examples repository:

📂 [NF Compose Examples](https://github.com/neuroforgede/nfcompose-examples)

## Getting Started (dev environment):

To start off, clone this repository:

```bash
git clone https://github.com/neuroforgede/nfcompose
```

Switch to the `deploy` folder and setup the playground:

```bash
cd deploy
bash setup_playground.sh
```

You can now access the playground in your browser using the credentials `admin`/`admin`:

![grafik](https://github.com/neuroforgede/nfcompose/assets/719760/d4af576b-bf94-446c-8432-bb35f20aac02)

## Codex In The Dev Container

The `neuroforge_skipper_base_dev` container can now run the Codex CLI directly.
It installs `@openai/codex`, mounts your host `~/.codex` directory into the
container for persistent auth/config, and exposes the full repository at
`/workspace/nfcompose`.

Rebuild the dev environment after pulling these changes:

```bash
bash setup_devenv.sh
```

Then launch Codex inside the running dev container:

```bash
bash run_codex_in_devenv.sh --yolo
```

If you prefer to start an interactive shell first:

```bash
COMPOSE_PROJECT_NAME=$(whoami)_skipper docker compose exec neuroforge_skipper_base_dev bash
cd /workspace/nfcompose
codex --yolo
```

# Use cases

## As a data hub (export)

You develop a customized solution for a customer. Since your solution will have to be integrated into a wider
system landscape, your customer wants you to provide a way to access relevant data via an integration API.

With NF Compose you can provide your customer(s) with a unified approach to data exchange REST APIs without coding
a single line of code. All you have to do is feed the DataSeries with the necessary data and the customer can either
fetch the data when they want (pull based) or they can be notified whenever data changes via Consumers (webhooks).

## As a ingestion layer

Additionally to an export functionality, your customer wants you to have an integration endpoint where they
can send you data that needs to be processed in your core product.

With NF Compose you can provide your customer with a unified data drop off point where they can push the data to.
Then in your app you can use the consumer system with **guaranteed delivery** to consume the data as it comes in.
Alternatively, you can also always use a pull based approach.

## As a customization Engine

If the DataSeries concepts alone are not enough for your needs, you can always use the customization layer of NF Compose
to define custom endpoints that are authenticated and managed by NF Compose. This way you can focus on the
actual business logic and co-locate custom APIs with auto generated REST APIs behind a common login.

The only requirement for an engine is that it is accessible via HTTP by the system. 
Low-Code Tools like Node-RED work very well with NF Compose (in fact the name for the `flow` module comes from this).

# Components
## Skipper

Skipper is the heart of the NF Compose platform and cotnains all REST APIs. Most importantly it exposes APIs for:

- The `dataseries` generated REST API
- The `flow` customization layer
- The `core` REST API for tenant and (super-)user management

## Compose CLI

The Compose CLI allows for access to the DataSeries API. This way you can interact with your integration APIs even
from bash scripts in a simple and common way

## Python SDK

The Compose CLI is built on top of the Python Compose SDK/client library.

# License

NF Compose is released under MPL 2.0. NeuroForge is a registered trademark of NeuroForge GmbH & Co. KG.
