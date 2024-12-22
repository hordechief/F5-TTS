## Build image from Dockerfile
```
docker build -t f5tts:v1 .
```

## Built container with f5-tts docker image
```
# example of use original image
docker run -it -p 9203:8890 --name f5-tts  --gpus all -v /home/aurora:/home/aurora -v /home/aurora/.cache/:/root/.cache/ ghcr.io/swivid/f5-tts:main

# use your own model
docker run -it -p 9203:8890 --name f5-tts  --gpus all -v /home/aurora:/home/aurora -v /home/aurora/.cache/:/root/.cache/ f5tts:v1
```

> Note: `/home/aurora:/home/aurora` for data mapping, `/home/aurora/.cache/:/root/.cache/` for cache mapping to save your installation efforts, both are optional

## Launch the application
```
f5-tts_infer-gradio --port 8890 --host 0.0.0.0
```
Change code to update timeout parameter
```
Exception in thread Thread-3 (_do_normal_analytics_request):
Traceback (most recent call last):
  File "/opt/conda/lib/python3.11/site-packages/httpx/_transports/default.py", line 72, in map_httpcore_exceptions
    yield
  File "/opt/conda/lib/python3.11/site-packages/httpx/_transports/default.py", line 236, in handle_request
    resp = self._pool.handle_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/conda/lib/python3.11/site-packages/httpcore/_sync/connection_pool.py", line 216, in handle_request
    raise exc from None
  File "/opt/conda/lib/python3.11/site-packages/httpcore/_sync/connection_pool.py", line 196, in handle_request
    response = connection.handle_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/conda/lib/python3.11/site-packages/httpcore/_sync/http_proxy.py", line 317, in handle_request
    stream = stream.start_tls(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/conda/lib/python3.11/site-packages/httpcore/_sync/http11.py", line 383, in start_tls

To create a public link, set `share=True` in `launch()`.
    return self._stream.start_tls(ssl_context, server_hostname, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/conda/lib/python3.11/site-packages/httpcore/_backends/sync.py", line 152, in start_tls
    with map_exceptions(exc_map):
  File "/opt/conda/lib/python3.11/contextlib.py", line 158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "/opt/conda/lib/python3.11/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectTimeout: _ssl.c:989: The handshake operation timed out
```

Update `timeout` parameter 
``` python
root@af0db69dc1cf:/workspace/F5-TTS# vi /opt/conda/lib/python3.11/site-packages/gradio/analytics.py

def get_local_ip_address() -> str:
    """
    Gets the public IP address or returns the string "No internet connection" if unable
    to obtain it or the string "Analytics disabled" if a user has disabled analytics.
    Does not make a new request if the IP address has already been obtained in the
    same Python session.
    """
    if not analytics_enabled():
        return "Analytics disabled"

    if Context.ip_address is None:
        try:
            ip_address = httpx.get(
                "https://checkip.amazonaws.com/", timeout=30
            ).text.strip()
        except (httpx.ConnectError, httpx.ReadTimeout):
            ip_address = "No internet connection"
        Context.ip_address = ip_address
    else:
        ip_address = Context.ip_address
    return ip_address
```

## Lannch app.py for API

### Preparation

set environment in `Dockerfile`

```
ENV DATA_DIR="/home/aurora/data" # default value: /workspace/F5-TTS/data/tts/
ENV REF_SOUND="hordechief.mp3"
ENV OUTPUT_DIR="/home/aurora/output" # default value: /workspace/F5-TTS/output
ENV PORT=8890
```

> if you want to access the output data out from the docker, you should map the volume and provided a shared space, for data directory, by default, it will load from docker

Change proxy in `Dockerfile` (Optional)
```
ENV http_proxy=http://172.17.0.1:7897/
ENV https_proxy=http://172.17.0.1:7897/
ENV socks5_proxy=172.17.0.1:7897/
ENV no_proxy="localhost,127.0.0.1"
```
### Execute app

```
conda deactivate # if activate virtual environment
cd /workspace/F5-TTS
python app.py
```

### Test URL
```
# infer only
curl -X POST http://localhost:9203/infer -H "Content-Type: application/json" -d '{"input_file": "Select Create Alert on any paper page to activate paper alerts."}'

curl -X POST http://172.16.3.24:9203/infer -H "Content-Type: application/json" -d '{"input_file": "Select Create Alert on any paper page to activate paper alerts."}'

# infer with reference audio 
curl -X POST http://localhost:9203/process -H "Content-Type: application/json" -d '{"input_file": "Select Create Alert on any paper page to activate paper alerts."}'
```

Note: 9103 is the mapping port of 8890, default value: 8890
