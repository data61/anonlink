void setBuildStatus(String message, String state) {
  step([
    $class: "GitHubCommitStatusSetter",
    statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
  ]);
}

def isMaster = env.BRANCH_NAME == 'master'
def isDevelop = env.BRANCH_NAME == 'develop'


node {

    def workspace = pwd();
    echo "workspace directory is ${workspace}"
    env.PATH = "${workspace}/env/bin:/usr/bin:${env.PATH}"


    withEnv(["VENV=${workspace}/env"]) {
        // ${workspace} contains an absolute path to job workspace (not available within a stage)

        stage (name : 'Cleanup') {
            sh "test -d ${workspace}/env && rm -rf ${workspace}/env || echo 'no env, skipping cleanup'"
        }

        stage("Install Python Virtual Enviroment") {
            sh '''
            rm -fr build
            echo "venv directory is ${VENV}"

            python3.5 -m venv --clear ${VENV}
            ${VENV}/bin/python ${VENV}/bin/pip install --upgrade pip coverage setuptools
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
            try {
                sh '''
                    ${VENV}/bin/python ${VENV}/bin/pip install -r requirements.txt
                   '''
               } catch (err) {
                sh 'echo "failed to install requirements"'
               }
        }

        // Build the extension
        stage ("Compile Library") {
            sh '''
                which python3.5
                ${VENV}/bin/python setup.py bdist
                ${VENV}/bin/python ${VENV}/bin/pip install -e .
               '''
        }

        // After all of the dependencies are installed, you can start to run your tests.
        stage ("Run Unit/Integration Tests") {
            def testsError = null
            try {
                sh '''
                    ${VENV}/bin/python ${VENV}/bin/nosetests --with-xunit --with-coverage --cover-inclusive --cover-package=anonlink
                   '''
            }
            catch(err) {
                testsError = err
                currentBuild.result = 'FAILURE'
            }
            finally {
                sh '''
                ${VENV}/bin/python ${VENV}/bin/coverage html --omit="*/cpp_code/*" --omit="*build_matcher.py*"
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
                    ${VENV}/bin/python -m anonlink.cli benchmark
                    deactivate
                   '''
            }
            catch(err) {
                testsError = err
                currentBuild.result = 'FAILURE'
            }
        }
    }



}