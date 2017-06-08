void setBuildStatus(String message, String state) {
  step([
    $class: "GitHubCommitStatusSetter",
    statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
  ]);
}

def isMaster = env.BRANCH_NAME == 'master'
def isDevelop = env.BRANCH_NAME == 'develop'

node {
    // It's often recommended to run a Python project from a virtual environment.
    // This way you can manage all of your dependencies without affecting the rest of your system.

    env.PATH = "${env.WORKSPACE}/env/bin:/usr/bin:${env.PATH}"


    stage("Install Python Virtual Enviroment") {
        sh '''
        rm -fr venv
        rm -fr build
        python3.5 -m venv --clear env
        pip install --upgrade pip coverage setuptools
        '''
    }


    // The stage below is attempting to get the latest version of our application code.
    // Since this is a multi-branch project the 'checkout scm' command is used. If you're working with a standard
    // pipeline project then you can replace this with the regular 'git url:' pipeline command.
    // The 'checkout scm' command will automatically pull down the code from the appropriate branch that triggered this build.
    stage ("Get Latest Code") {
        checkout scm
    }

    // If you're using pip for your dependency management, you should create a requirements file to store a list of all depedencies.
    // In this stage, you should first activate the virtual environment and then run through a pip install of the requirements file.
    stage ("Install Dependencies") {
        sh '''
            pip install -r requirements.txt
           '''
    }

    // Build the extension
    stage ("Compile Library") {
        sh '''
            ${workspace}/env/bin/python setup.py bdist
            ${workspace}/env/bin/pip install -e .
           '''
    }

    // After all of the dependencies are installed, you can start to run your tests.
    stage ("Run Unit/Integration Tests") {
        def testsError = null
        try {
            sh '''
                ${workspace}/env/bin/nosetests --with-xunit --with-coverage --cover-inclusive --cover-package=anonlink
                
               '''
        }
        catch(err) {
            testsError = err
            currentBuild.result = 'FAILURE'
        }
        finally {
            sh '''
            ${workspace}/env/bin/coverage html --omit="*/cpp_code/*" --omit="*build_matcher.py*"
            '''

            junit 'nosetests.xml'

            if (testsError) {
                throw testsError
            }
        }
    }


    stage("Benchmark") {
        try {
            sh '''
                source ${workspace}/env/bin/activate
                python -m anonlink.cli benchmark
                deactivate
               '''
        }
        catch(err) {
            testsError = err
            currentBuild.result = 'FAILURE'
        }
    }

    stage (name : 'Cleanup') {
        sh "test -d ${workspace}/env && rm -rf ${workspace}/env || echo 'no env, skipping cleanup'"
    }


}