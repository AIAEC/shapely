pipeline {

  options {
    ansiColor('xterm')
  }

  agent {
    kubernetes {
      yamlFile '.jenkins/builder.yaml'
    }
  }

  parameters {
    string(name: 'PYPI_SERVER_HOST',
          defaultValue: 'pypi.aiacesz.com',
          description: 'The pypi repository host')
  }

  environment {
    PYPI = credentials('pypi-repo-credential')
  }

  stages {
    stage('testing') {
      steps {
        container('python') {
          sh 'apt install -y libgeos-dev'
          sh 'pip install -r requirements-dev.txt'
          sh 'pytest'
        }
      }
    }

    stage('build package') {
      steps {
        container('python') {
          sh 'python setup.py bdist_wheel sdist'
          // sh 'pip install auditwheel'
          // sh 'auditwheel repair $(ls dist/*.whl) -w dist'
        }
      }
    }

    stage('uploading pypi package') {
      steps {
        container('python') {
          sh 'pip install twine'
          sh 'twine upload --repository-url https://$PYPI_SERVER_HOST -u $PYPI_USR -p $PYPI_PSW dist/*'
        }
      }
    }
  }
}
