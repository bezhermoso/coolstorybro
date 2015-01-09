import os

def set(client, jwt):
    file = get_path(client)
    f = open(file, 'w')
    f.write(jwt)
    f.close()
    pass

def get(client):
    file = get_path(client)
    f = open(file, 'r')
    return f.readline()

def delete(client):
    file = get_path(client)
    os.remove(file)
    return True

def get_path(client):
    return os.path.join(os.path.dirname(__file__), '_tokens', client)


class TokenManager(object):
    def set(self, client, secret):
        pass

    def get(self, client):
        pass

    def delete(self, client):
        pass