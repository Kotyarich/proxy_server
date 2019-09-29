from proxy import start, saver
import _thread


sqlite_con = saver.get_connection()
cursor = sqlite_con.cursor()


def print_requests(last_id):
    reqs = saver.get_requests(cursor, last_id)
    if len(reqs) == 0:
        return -1

    for req in reqs:
        print("{}: host: {}:{}\nRequest:\n{}\n".format(req[0], req[1], req[2], req[3]))

    return reqs[0][0]


def repeat(req_id):
    req = saver.get_request(cursor, req_id)
    print(req)


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
            if prev_action == 2:
                last_id += saver.requests_number
            last_id = print_requests(last_id)
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
