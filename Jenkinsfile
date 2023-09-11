pipeline {

  options {
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '13'))
  }

  agent {
    kubernetes {
      yamlFile '.jenkins/builder.yaml'
    }
  }

  environment {
    PYPI = credentials('pypi-repo-credential')
  }

// stages {
//   stage('testing') {
//    steps {
//      container('python') {
//        sh '/opt/python/cp39-cp39/bin/python3 -m pip config set global.index-url https://shoebill:quokka@pypi.aiacesz.com/simple'
//        sh '/opt/python/cp39-cp39/bin/python3 -m pip install -r requirements-test.txt'
//        sh '/opt/python/cp39-cp39/bin/python3 -m pytest -m "not local"'
//      }
//    }
//  }

    stage('build package') {
      steps {
        container('builder') {
          sh './build-customized-wheel.sh'
        }
      }
    }

    stage('uploading pypi package') {
      steps {
        container('python') {
          sh 'pip install twine'
          sh 'twine upload --repository-url https://pypi.aiacesz.com -u $PYPI_USR -p $PYPI_PSW dist/*'
        }
      }
    }
  }
}
