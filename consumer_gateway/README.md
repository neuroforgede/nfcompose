# Consumer gateway

This contains a simple proxy that serves as a tool to do the actual http calls in a
more sandboxed environment. This is to prevent calls to arbitrary consumer urls
in an environment that can access e.g. redis environments.

Example call via curl:

```
curl -H "x-skipper-proxied-host: github.com" -H "x-skipper-proxied-url: https://github.com/s4ke/" localhost:81
```