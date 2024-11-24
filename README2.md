
## Update code

因为调试原因，代码进行了共享，需要修改`/workspace/`下的F5-TTS为合适的代码

## Launch the application
```
f5-tts_infer-gradio --port 8889 --host 0.0.0.0
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
Change the reference audio
``` python
ref_file="/home/aurora/data/tts/002.m4a"
```

Change ouput
``` python
file_wave=str(files("f5_tts").joinpath("/home/aurora/output/api_out.wav"))
file_spect=str(files("f5_tts").joinpath("/home/aurora/output/api_out.png"))
output_audio_path = '/home/aurora/output/api_out.wav'
```
### Execute app

```
conda deactivate # if activate virtual environment
cd /workspace/F5-TTS
python app.py
```

### test url
```
# infer only
curl -X POST http://localhost:9103/infer -H "Content-Type: application/json" -d '{"input_file": "Select Create Alert on any paper page to activate paper alerts."}'
curl -X POST http://.1.29:9103/infer -H "Content-Type: application/json" -d '{"input_file": "Select Create Alert on any paper page to activate paper alerts."}'

# infer with reference audio 
curl -X POST http://localhost:9103/process -H "Content-Type: application/json" -d '{"input_file": "/home/aurora/data/tts/002.m4a"}'
```
