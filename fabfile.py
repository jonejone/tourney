from fabric.api import env, cd, run, local


env.hosts = ['localhost', ]


def flake8():
    local(
        'find . -name "*.py" -print0 | xargs -0 flake8',
        capture=False)


def deploy():
    with cd('/home/jone/tourney/project'):
        run('git pull')
        run('source ~/.virtualenvs/tourney/bin/activate && python manage.py collectstatic --noinput')
        run('sudo /etc/init.d/apache2 restart')
