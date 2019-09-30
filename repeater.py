from proxy import start, saver, buffer_size
from http_parser.pyparser import HttpParser
import socket
import gzip
import ssl
import _thread


def print_requests(last_id):
    sqlite_con = saver.get_connection()
    cursor = sqlite_con.cursor()
    reqs = saver.get_requests(cursor, last_id)
    sqlite_con.close()
    if len(reqs) == 0:
        return -1

    for req in reqs:
        print("{}: host: {}:{}\nRequest:\n{}\n".format(req[0], req[1], req[2], req[3]))

    return reqs[0][0]


def repeat(req_id):
    sqlite_con = saver.get_connection()
    cursor = sqlite_con.cursor()
    _, host, port, request, is_https = saver.get_request(cursor, req_id)
    sqlite_con.close()
    # Connecting to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    if is_https:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        sock = context.wrap_socket(sock, server_hostname=host)
    sock.send(request)

    # Getting response
    parser = HttpParser()
    resp = b''
    while True:
        data = sock.recv(buffer_size)
        if not data:
            break

        received = len(data)
        _ = parser.execute(data, received)
        if parser.is_partial_body():
            resp += parser.recv_body()

        if parser.is_message_complete():
            break
    headers = parser.get_headers()
    # Decode answer
    if headers['CONTENT-ENCODING'] == 'gzip':
        resp = gzip.decompress(resp)
        resp = str(resp, 'utf-8')
    else:
        try:
            resp = resp.decode('utf-8')
        except UnicodeDecodeError:
            print('Body wasn\'t decoded')

    print("{} HTTP/{}.{}".format(parser.get_status_code(), *parser.get_version()))
    for header in headers:
        print('{}: {}'.format(header, headers.get(header)))
    print()
    print(resp)
    print()


def main():
    last_id = -1
    prev_action = 0
    while True:
        if last_id <= 0:
            print("1. Print last {} requests.".format(saver.requests_number))
        else:
            print("1. Print next {} requests;\n2. Print previous {} requests;\n"
                  "3. Repeat request;\n4. Exit.".format(saver.requests_number, saver.requests_number))

        try:
            action = int(input("Enter number: "))
        except ValueError:
            print("Wrong input")
            continue

        if action == 1:
            if last_id > -1:
                last_id += saver.requests_number
            last_id = print_requests(last_id)
            print(last_id)
        elif action == 2:
            last_id -= saver.requests_number
            print_requests(last_id)
        elif action == 3:
            req_id = -1
            while req_id < 0:
                try:
                    req_id = int(input("Enter request number: "))
                except ValueError:
                    print("Wrong input")
                    continue
            repeat(req_id)
        elif action == 4:
            break
        else:
            print("Wrong input")
            continue
        prev_action = action


if __name__ == '__main__':
    _thread.start_new_thread(start, tuple())
    main()
