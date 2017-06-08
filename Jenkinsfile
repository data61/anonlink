void setBuildStatus(String message, String state) {
  step([
    $class: "GitHubCommitStatusSetter",
    statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
  ]);
}

def isMaster = env.BRANCH_NAME == 'master'
def isDevelop = env.BRANCH_NAME == 'develop'


node("linux") {

    stage (name : 'Test on Linux') {
        def workspace = pwd();
        echo "workspace directory is ${workspace}"
        env.PATH = "${workspace}/env/bin:/usr/bin:${env.PATH}"

        withEnv(["VENV=${workspace}/env"]) {
            // ${workspace} contains an absolute path to job workspace (not available within a stage)

            // clean up
            sh "test -d ${workspace}/env && rm -rf ${workspace}/env || echo 'no env, skipping cleanup'"


            // The stage below is attempting to get the latest version of our application code.
            // Since this is a multi-branch project the 'checkout scm' command is used. If you're working with a standard
            // pipeline project then you can replace this with the regular 'git url:' pipeline command.
            // The 'checkout scm' command will automatically pull down the code from the appropriate branch that triggered this build.
            checkout scm


            // Install Python Virtual Enviroment
            sh '''
                rm -fr build
                echo "venv directory is ${VENV}"
                ls ${VENV}

                python3.5 -m venv --clear ${VENV}
                ${VENV}/bin/python ${VENV}/bin/pip install --upgrade pip coverage setuptools
            '''

            // Install Dependencies
            try {
                sh '''
                    echo "venv directory is ${VENV}"
                    ls ${VENV}
                    ${VENV}/bin/python ${VENV}/bin/pip install -r requirements.txt
                   '''
               } catch (err) {
                sh 'echo "failed to install requirements"'
               }

            // Build the extension
            sh '''
                ${VENV}/bin/python setup.py bdist
                ${VENV}/bin/python ${VENV}/bin/pip install -e .
               '''


            // After all of the dependencies are installed, you can start to run your tests.
            // Run Unit/Integration Tests
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

            // Benchmark
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