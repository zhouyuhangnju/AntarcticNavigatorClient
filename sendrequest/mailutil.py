def getemailpsw(no):
    email = ''
    psw = ''
    for idx, line in enumerate(open('../psw.txt', 'r').readlines()):
        line = line.replace('\r\n', '')
        # print idx, line.split()[1]
        if idx == no:
            email = line.split()[1]
        if idx == 5:
            psw = line.split()[1]
    return email, psw


if __name__ == '__main__':
    for i in range(4):
        print getemailpsw(i)

