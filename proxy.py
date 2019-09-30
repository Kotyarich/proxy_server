#!/usr/bin/python
import os
import socket
import sys
import ssl
import time
from string import Template
from subprocess import Popen, PIPE
from http_parser.pyparser import HttpParser
from _thread import *

import saver


listening_port = 43433
max_conn = 5
buffer_size = 8192
# Paths to certificates
cert_key = 'cert.key'
ca_key = 'ca.key'
ca_cert = 'ca.crt'
cert_dir = 'certs/'


def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('localhost', listening_port))
        s.listen(max_conn)
    except socket.error:
        print("Cant init socket")
        s.close()
        sys.exit(2)

    while True:
        try:
            con, addr = s.accept()
            data = con.recv(buffer_size)
            req = b''
            con.settimeout(0.1)
            while data:
                req += data
                try:
                    data = con.recv(buffer_size)
                except socket.error:
                    break
            start_new_thread(parse_start_string, (con, req))
        except KeyboardInterrupt:
            s.close()
            print("Proxy was shutted down")
            sys.exit(1)


def parse_start_string(con, data):
    p = HttpParser()
    try:
        p.execute(data, len(data))

        url = p.get_url()
        metopd = p.get_method()

        http_pos = url.find('://')
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos+3):]

        port_pos = temp.find(':')
        host_pos = temp.find('/')
        if host_pos == -1:
            host_pos = len(temp)
        if port_pos == -1 or host_pos < port_pos:
            port = 443 if metopd == "CONNECT" else 80
        else:
            port = int((temp[port_pos + 1:])[:host_pos - port_pos - 1])

        host = p.get_headers()['host']
        port_ind = host.find(':')
        if port_ind != -1:
            host = host[:port_ind]
        if metopd == "CONNECT":
            https_proxy(host, port, con)
        else:
            proxy(host, port, con, data)
    except Exception as e:
        # print(e)
        pass


def proxy(host, port, conn, data):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        s.send(data)

        while True:
            reply = s.recv(buffer_size)

            if len(reply) > 0:
                conn.send(reply)
            else:
                break

        s.close()
        conn.close()
        sql_conn = saver.get_connection()
        saver.save_request(sql_conn, host, port, data, 0)
        sql_conn.close()
    except socket.error:
        s.close()
        conn.close()
        sys.exit(1)


def https_proxy(host, port, conn):
    epoch = "%d" % (time.time() * 1000)
    cert_path = "%s/%s.crt" % (cert_dir.rstrip('/'), host)
    # CGenerating config to add subjectAltName (required in modern browsers)
    conf_template = Template("subjectAltName=DNS:${hostname}")
    conf_path = "%s/%s.cnf" % (cert_dir.rstrip('/'), host)
    with open(conf_path, 'w') as fp:
        fp.write(conf_template.substitute(hostname=host))

    # Generating certificate
    p1 = Popen(["openssl", "req", "-new", "-key", cert_key, "-subj", "/CN=%s" % host, "-addext",
                "subjectAltName = DNS:" + host], stdout=PIPE)
    p2 = Popen(
        ["openssl", "x509", "-req", "-extfile", conf_path, "-days", "3650", "-CA", ca_cert, "-CAkey", ca_key,
         "-set_serial", epoch,
         "-out", cert_path], stdin=p1.stdout, stderr=PIPE)
    p2.communicate()
    os.unlink(conf_path)

    # Connecting to server
    tunn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tunn.connect((host, port))
    # Establishing connection with client
    conn.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
    conn_s = ssl.wrap_socket(conn, keyfile=cert_key, certfile=cert_path, server_side=True)
    conn_s.do_handshake()

    request = conn_s.recv(40960)
    # Establishing https connection with server
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s_sock = context.wrap_socket(tunn, server_hostname=host)
    s_sock.send(request)
    # Getting response
    parser = HttpParser()
    resp = b''
    while True:
        data = s_sock.recv(buffer_size)
        if not data:
            break

        received = len(data)
        _ = parser.execute(data, received)
        resp += data

        if parser.is_message_complete():
            break

    conn_s.sendall(resp)
    # Save information about request
    sql_conn = saver.get_connection()
    saver.save_request(sql_conn, host, port, request, 1)
    sql_conn.close()

    s_sock.close()
    conn_s.close()


if __name__ == '__main__':
    start()
