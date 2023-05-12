# Skipper Proxy

This directory contains all the routing we require in order for the skipper server to function properly. See conf.d/90-default.conf for more details, but
basically, this proxy is designed to be put in front of the skipper instance. Any ingress that wants to point to a Skipper instance talks to this proxy
and not directly to the skipper master.

This also handles the proper authentication for Node-RED flows.