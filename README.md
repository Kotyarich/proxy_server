## Proxy server for "Web applications security" technopark course

### Requirements:

- [x] Proxy HTTP requests
- [x] Proxy HTTPS requests
- [x] Ability of repeating old requests

### To generate certificate:

``` bash
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=proxy2 CA"
openssl genrsa -out cert.key 2048
mkdir certs/
```

### Starting

To init data base for saving requests:
```bash
python saver.py
```
To start:
```bash
python repeater.py
```
To start proxy without repeater:
```bash
python proxy.py
```

