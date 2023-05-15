# deploy

This folder contains a sample docker-compose that can be used for integration tests or even
for local development. Note that due to the fact that this takes quite some shortcuts regarding configuration, the setup in [production/docker-compose](../production/docker-compose/) is
generally preferrable.


# playground

To setup a local instance of NF Compose to try out, run `bash local_setup.sh`.

If you want to access the frontend locally, you have to add the line
```
127.0.0.1 nfcomposes3.test.local
```
to your /etc/hosts file