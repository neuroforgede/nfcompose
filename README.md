# NF Compose

NF Compose is a (data) integration platform that allows developers to define REST APIs in seconds instead of
minutes. Generated REST APIs are backed by postgres and support automatic consumer notifications on data changes out
of the box.

A Customization Layer based around pluggable engines allows for deep customization behind the same integration framework.

NF Compose is built with multi-tenancy in mind - A single NF Compose instance can serve many different tenants/projects
at the same time.

# Try it out

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