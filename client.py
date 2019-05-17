from socket import *
import threading
import sys
import json
import re
import time
import os
import finaldesign.dao as dao
import requests


HOST = '127.0.0.1'
PORT = 8022
BUFSIZE = 1024  # 缓冲区大小  1K
ADDR = (HOST, PORT)
myre = r"^[_a-zA-Z]\w{0,}"
tcpCliSock = socket(AF_INET, SOCK_STREAM)
userAccount = None


def register():
    print("""
    很高兴您将成为校园区块链网络的一员！
    """)
    accout = input('请输入您的账户: ')
    if not re.findall(myre, accout):
        print('账户名非法，请输入合法的字符（[a-z]+[0-9]）!')
        return None
    password1 = input('请输入您的密码: ')
    password2 = input('请再次输入您的密码: ')
    if not (password1 and password1 == password2):
        print('二次输入密码不一致，请重新输入!')
        return None
    global userAccount
    userAccount = accout
    regInfo = [accout, password1, 'register']
    datastr = json.dumps(regInfo)
    tcpCliSock.send(datastr.encode('utf-8'))
    data = tcpCliSock.recv(BUFSIZE)
    data = data.decode('utf-8')
    if data == '0':
        print('注册成功!')
        return True
    elif data == '1':
        print('账户名已存在!')
        return False
    else:
        print('注册异常！')
        return False


def login():
    print("""
    欢迎登录校园区块链通讯系统
    """)
    accout = input('账户: ')
    if not re.findall(myre, accout):
        print('账户名错误!')
        return None
    password = input('密码: ')
    if not password:
        print('密码错误')
        return None
    global userAccount
    userAccount = accout
    loginInfo = [accout, password, 'login']
    datastr = json.dumps(loginInfo)
    tcpCliSock.send(datastr.encode('utf-8'))
    data = tcpCliSock.recv(BUFSIZE)
    data = data.decode('utf-8')
    if data == '0':
        print('登录成功!')
        return True
    else:
        print('登录失败，请重新检查！')
        return False


def addGroup():
    groupname = input('请输入要创建的群组名: ')
    if not re.findall(myre, groupname):
        print('group name illegal!')
        return None
    return groupname


def chat(target):
    while True:
        print('已发送至 {}: '.format(target))
        msg = input()
        if len(msg) > 0 and not msg in 'qQ':
            if 'group' in target:
                optype = 'cg'
            else:
                optype = 'cp'

            dataObj = {
                'type': optype,
                'to': target,
                'msg': msg,
                'froms': userAccount}
            datastr = json.dumps(dataObj)
            tcpCliSock.send(datastr.encode('utf-8'))
            data_transaction = {
                'sender': str(userAccount),
                'recipient': str(target),
                'msg': str(msg)
            }

            dao.post_transaction(data_transaction)
            continue
        elif msg in 'qQ':
            break
        else:
            print('发送数据失败!')


class inputdata(threading.Thread):
    def run(self):

        menu = """
                        (1): 点对点聊天
                        (2): 群组聊天
                        (3): 创建群组
                        (4): 进入群组
                        (5): 远程命令挖矿
                        (6): 启动区块链节点
                        (7): 查看目前区块链
                        (8): 查看聊天记录
                        (9): 退出系统
                        """
        print(menu)
        while True:
            operation = input('请输入数字[1-8]: ')
            if operation in '1':
                target = input('请输入你要聊天的对象: ')
                chat(target)
                continue

            if operation in '2':
                target = input('请输入你要聊天的群组: ')
                chat('group' + target)
                continue

            if operation in '3':
                groupName = addGroup()
                if groupName:
                    data = {'type': 'ag', 'groupName': groupName}
                    dataObj = json.dumps(data)
                    tcpCliSock.send(dataObj.encode('utf-8'))
                continue

            if operation in '4':
                groupname = input('Please input group name fro entering: ')
                if not re.findall(myre, groupname):
                    print('组名不正确!')
                    return None
                data = {'type': 'eg', 'groupName': 'group' + groupname}
                dataObj = json.dumps(data)
                tcpCliSock.send(dataObj.encode('utf-8'))
                continue

            if operation in '5':
                a = dao.get_mine()
                reply = a.json()

                print('已成功挖矿！节点返回数据如下：')
                print('第{}个区块被创建！\nnonce值:{}\n上一个区块哈希：{}\n区块所有消息哈希为：{}'
                      .format(reply["index"], reply["nonce"], reply["previous_hash"], reply["transactions"][0]["recipient"]))
                continue

            if operation in '6':
                # os.popen("python node.py")
                netloc = input('请输入引导节点地址如\'127.0.0.1:5000\'：')
                dao.init(netloc)
                print("初始化节点成功，已添加至节点网络")
                time.sleep(2)
                continue

            if operation in '7':
                a = dao.get_chain()
                chain = a.json()
                print('目前区块链长度为{}'.format(chain["length"]))
                for block in chain["chain"]:
                    print("第{}个区块,创建于{}"
                          .format(block["index"], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(block["timestamp"]))))
                    print("     区块哈希：{}".format(block["previous_hash"]))
                continue

            if operation in '8':
                a = input("请输入要查找记录的对方账号或群组：")
                tx = dao.get_transactions().json()
                for msgdic in tx['transactions']:
                    if msgdic['sender'] == userAccount or msgdic['recipient'] == userAccount:
                        if msgdic['sender'] == userAccount or msgdic['recipient'] == a:
                            print('{}\n{}发送到{}，消息是：\n{}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msgdic["timestamp"])),
                                                                  msgdic['sender'], msgdic['recipient'], msgdic['msg']))
                continue

            if operation in '9':
                tcpCliSock.close()
                sys.exit(1)
            else:
                print('没有该选项，请重新输入!')


class getdata(threading.Thread):
    def run(self):
        while True:
            data = tcpCliSock.recv(BUFSIZE).decode('utf-8')
            if data == '-1':
                print('网络无法连接...')
                continue
            if data == 'ag0':
                print('已创建群组!')
                continue

            if data == 'eg0':
                print('已加入群组!')
                continue

            if data == 'eg1':
                print('加入群组失败!')
                continue

            dataObj = json.loads(data)
            if dataObj['type'] == 'cg':
                print(
                    '从{}(群组： {})收到消息 : {}'.format(
                        dataObj['froms'],
                        dataObj['to'],
                        dataObj['msg']))
            else:
                print('从{}收到消息 : {}'.format(dataObj['froms'], dataObj['msg']))


def main():

    try:
        tcpCliSock.connect(ADDR)
        print('节点初始化成功...')
        while True:
            loginorReg = input('（1）：登录账户\n（2）：注册账户\n请输入：')
            if loginorReg in '1':
                log = login()
                if log:
                    break
            if loginorReg in '2':
                reg = register()
                if reg:
                    break

        myinputd = inputdata()
        mygetdata = getdata()
        myinputd.start()
        mygetdata.start()
        myinputd.join()
        mygetdata.join()

    except Exception:
        print('无法连接至其他节点，正在退出...')
        tcpCliSock.close()
        sys.exit()


if __name__ == '__main__':

    main()
