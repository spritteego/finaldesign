import requests
from socket import gethostname, gethostbyname


def get_own_socket():
    hostname = gethostname()
    # 获取本机ip
    ip = gethostbyname(hostname)
    return str(ip + ':5000')


localhost = '127.0.0.1:5000'


def init(bootstrap):
    '''
    assume that local node is activated
    '''
    list = []
    list.append(get_own_socket())
    submit_bootstrap = {"nodes": list}
    requests.post(
        "http://{}/nodes/register".format(bootstrap),
        json=submit_bootstrap)
    res = requests.get('http://{}/nodes'.format(bootstrap)).json()
    print("发现邻居节点：\n{}\n加入到本地节点中".format(res['nodes']))
    submit_own = {"nodes": res['nodes']}
    requests.post(
        "http://{}/nodes/register".format(localhost),
        json=submit_own)
    update_nodelist()
    # synchronize()


def get_chain():
    synchronize()
    res = requests.get('http://{}/chain'.format(localhost))
    return res


def update_nodelist():
    res = requests.get('http://{}/nodes'.format(localhost)).json()
    my_nodes = res['nodes']
    newest_nodelist = []
    for my_node in my_nodes:
        try:
            res = requests.get('http://{}/nodes'.format(my_node))
            if res.status_code == 200:
                nodelist = res.json()['nodes']
                for node in nodelist:
                    newest_nodelist.append(node)
        except requests.exceptions.RequestException:
            pass
    data = {'nodes': newest_nodelist}
    requests.post(url='http://{}/nodes/register'.format(localhost), json=data)
# TODO get synchronize function correct in 5.17


def synchronize():
    update_nodelist()
    requests.get('http://{}/resolve'.format(localhost))


def get_mine():
    synchronize()
    res = requests.get(url='http://{}/mine'.format(localhost))
    return res


def post_transaction(data_transaction):
    requests.post(
        url='http://{}/transactions/new'.format(localhost),
        json=data_transaction)


def get_transactions():
    res = requests.get(url='http://{}/transactions'.format(localhost))
    return res
