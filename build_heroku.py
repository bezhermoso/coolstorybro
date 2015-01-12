import os
import ConfigParser

def main():
    config = ConfigParser.RawConfigParser()
    filename = os.path.join(os.path.dirname(__file__), 'heroku.ini')
    config.read(filename)
    config.set('app:main', 'mysql_user', os.environ.get('MYSQL_USER'))
    config.set('app:main', 'mysql_password', os.environ.get('MYSQL_PASSWORD'))
    config.set('app:main', 'mysql_host', os.environ.get('MYSQL_HOST'))
    config.set('app:main', 'mysql_db', os.environ.get('MYSQL_DATABASE'))
    with open(filename, 'w') as conf_file:
        config.write(conf_file)

if __name__ == '__main__':
    main()