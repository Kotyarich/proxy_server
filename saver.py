import sqlite3

requests_number = 2


def get_connection():
    conn = sqlite3.connect("requests.db")
    return conn


def init_db(cursor):
    cursor.execute("CREATE TABLE requests ("
                   "id integer primary key, "
                   "host text, "
                   "port integer, "
                   "request text, "
                   "https boolean)")


def save_request(conn, host, port, request, is_https):
    conn.cursor().execute("INSERT INTO requests(host, port, request, https) VALUES (?, ?, ?, ?)",
                          (host, port, request, is_https))
    conn.commit()


def get_requests(cursor, start_id):
    if start_id > -1:
        sql = "SELECT * FROM requests WHERE id<=? ORDER BY id DESC LIMIT {}".format(requests_number)
        cursor.execute(sql, (start_id,))
    else:
        sql = "SELECT * FROM requests ORDER BY id DESC LIMIT {}".format(requests_number)
        cursor.execute(sql)
    return cursor.fetchall()


def get_request(cursor, req_id):
    sql = "SELECT * FROM requests WHERE id=?"
    cursor.execute(sql, (req_id,))
    return cursor.fetchone()


if __name__ == '__main__':
    init_db(get_connection().cursor())
