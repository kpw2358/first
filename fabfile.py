'''
로컬 개발 pc에서 원격 서버의 환경부터 ~운용까지 모든 세팅을 진행한다
'''
from fabric.contrib.files import append, exists, sed, put
from fabric.api import local, run, sudo, env
import os
import json


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
print (PROJECT_DIR)
envs = json.load( open( os.path.join(PROJECT_DIR,'deploy.json') ) )
print(envs)
'''
{
    "REPO_URL":"https://github.com/kpw2358/first",
    "PROJECT_NAME":"first",
    "REMOTE_HOST":"ec2-13-209-43-192.ap-northeast-2.compute.amazonaws.com",
    "REMOTE_HOST_SSH":"13.209.43.192",
    "REMOTE_USER" : "ubuntu"
}
'''
REPO_URL            =envs['REPO_URL']
PROJECT_NAME       =envs['PROJECT_NAME']
REMOTE_HOST        =envs['REMOTE_HOST']
REMOTE_HOST_SSH    =envs['REMOTE_HOST_SSH']
REMOTE_USER        =envs['REMOTE_USER']

env.user = REMOTE_USER
env.hosts = [
    REMOTE_HOST_SSH,
]
env.user_ssh_config = True
env.key_filename = 'project.pem' #동일폴더 위치시키기
project_folder = '/home/{}/{}'.format(env.user,PROJECT_NAME)
print (project_folder)

apt_requirements = [
    'curl',
    'git',
    'python3-pip',
    'python3-dev',
    'build-essential',
    'apache2',
    'libapache2-mod-wsgi-py3',
    'python3-setuptools',
    'libssl-dev',
    'libffi-dev'
]
'''
작성이 모두 끝난후
>fab new_initServer
소스가 변경된후
>fab update
'''

def new_initServer():
    _setup()
    update()

def _setup():
    # 리눅스 패키지 업데이트 주소 or 패키지 목록 세팅
    _init_apt()
    # 필요한 패키지 설치
    _install_apt_packages()
    # 가상환경 구축
def _init_apt():
    yn = input('would you want ubuntu linux update? : [y/n]')
    if yn == 'y':#사용자가 업데이트를 원했다면
        #sudo => root 권한으로 실행할때
        #sudo apt-get update
        #sudo apt-get upgrade
        sudo('apt-get update && -y upgrade')
def _install_apt_packages(requires) :
    #설치할 패키지 목록 나열
    reqs = ''
    for req in requires :
        reqs += '' + req
        # reqs => curl git python3-pip ....
    # 수행
    # sudo apt-get install curl
    sudo ('apt-get -y install ' + reqs)
def _making_virtualenv():
    #설치여부확인 => 파일 여부 체크
    if not exists('~/.virtualenvs'):

        #가상환경 폴더
        
        # run 구동 => ubuntu 소유(퍼미션)
        # sudo 구동 => root 소유(퍼미션)
        run ( 'mkdir ~/.virtualenvs' )
        #패키지 설치
        sudo ('pip3 install virtualenv virtualenvwrapper')
        # 환경변수 반영 및 쉘(윈도우의배치) 구동 가상환경 구축
        cmd = '''
            "#python virtualenv global setting
            export WORKON_HOME=~/.virtualenvs
            #python location
            export VIRTUALENVWRAPPER_PYTHON="$(command \which python3)"
            # shell 실행
            source /user/local/bin/virtualenvwrapper.sh"
        '''
        run('echo {} >> ~/.bashrc'.format(cmd) )
def update():
    _git_update()
    _virtualenv_update()
    _virtualhost_make()
    _grant_apache()
    _restart_apache()
def _git_update():
    if exists(project_folder + '/.git'): # 깃트가 존재하면 first폴더로 이동 그리고 저장소로부터 fetch를 해서 최신정보 가져온다
        run('cd %s && git fetch' % (project_folder,))
    else: # 깃트가 존재하지 않으면 저장소로부터 최초로 프로젝트로 받아온다
        run('git clone %s %s' % (REPO_URL, project_folder))
    # 기트의 커밋된 로그를 최신으로 한개 가져온다 그것의 번호를 리턴
    # local : git log -n 1 --format=%H => 232655112331 랜덤숫자
    current_commit = local("git log -n 1 --format=%H", capture=True)
    #first 폴더로 이동 그리고 git reset --hard 232655112331
    #최신 커밋사항으로 소스 반영   중간필요없이 최신 커밋사항으로 소스를 반영하는거임. 최신이 중요!
    run('cd %s && git reset --hard %s' % (project_folder, current_commit))
    #run('cd %s && git reset --hard' % (project_folder, ))
def _virtualenv_update():
    # /home/ubuntu/.virtualenvs/first 라는 가상환경
    virtualenv_folder = project_folder + '/../.virtualenvs/{}'.format(PROJECT_NAME)
    # /home/ubuntu/.virtualenvs/first/bin/pip 가 존재하지 않으면
    if not exists(virtualenv_folder + '/bin/pip'):
        #/home/ubuntu/.virtualenvs로 이동하고 그리고
        # virtualenv firest 가상환경 하나 생성
        run('cd /home/%s/.virtualenvs && virtualenv %s' % (env.user, PROJECT_NAME))

    #상관없이 수행
    #/home/ubuntu/.virtualenvs/first/bin/pip install -r
    run('%s/bin/pip install -r %s/requirements.txt' % (
        virtualenv_folder, project_folder
    ))
def _ufw_allow():
    sudo("ufw allow 'Apache Full'")
    sudo("ufw reload")
def _virtualhost_make():
    script = """'<VirtualHost *:80>
    ServerName {servername}
    <Directory /home/{username}/{project_name}>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    WSGIDaemonProcess {project_name} python-home=/home/{username}/.virtualenvs/{project_name} python-path=/home/{username}/{project_name}
    WSGIProcessGroup {project_name}
    WSGIScriptAlias / /home/{username}/{project_name}/wsgi.py
    
    ErrorLog ${{APACHE_LOG_DIR}}/error.log
    CustomLog ${{APACHE_LOG_DIR}}/access.log combined
    
    </VirtualHost>'""".format(
        username=REMOTE_USER,
        project_name=PROJECT_NAME,
        servername=REMOTE_HOST,
    )
    sudo('echo {} > /etc/apache2/sites-available/{}.conf'.format(script, PROJECT_NAME))
    sudo('a2ensite {}.conf'.format(PROJECT_NAME))
def _grant_apache():
    sudo('chown -R :www-data ~/{}'.format(PROJECT_NAME))
    sudo('chmod -R 775 ~/{}'.format(PROJECT_NAME))
def _restart_apache():
    sudo('service apache2 restart')