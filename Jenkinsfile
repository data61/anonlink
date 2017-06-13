void setBuildStatus(String message, String state) {
  step([
    $class: "GitHubCommitStatusSetter",
    statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
  ]);
}

def isMaster = env.BRANCH_NAME == 'master'
def isDevelop = env.BRANCH_NAME == 'develop'

def configs = [
    [label: 'GPU 1', pythons: ['python3.4', 'python3.5', 'python3.6'], compilers: ['clang', 'gcc']],
    [label: 'McNode', pythons: ['python3.5'], compilers: ['clang', 'gcc']]
]

def build(python_version, compiler, label, release=false) {
    try {
        def workspace = pwd();
        echo "${label}"
        echo "workspace directory is ${workspace}"
        env.PATH = "${workspace}/env/bin:/usr/bin:${env.PATH}"

        withEnv(["VENV=${workspace}/env"]) {
        // ${workspace} contains an absolute path to job workspace (not available within a stage)


            sh "test -d ${workspace}/env && rm -rf ${workspace}/env || echo 'no env, skipping cleanup'"

            // The stage below is attempting to get the latest version of our application code.
            // Since this is a multi-branch project the 'checkout scm' command is used. If you're working with a standard
            // pipeline project then you can replace this with the regular 'git url:' pipeline command.
            // The 'checkout scm' command will automatically pull down the code from the appropriate branch that triggered this build.
            checkout scm

            def testsError = null
            try {
                sh """#!/usr/bin/env bash
                    set -xe

                    # Jenkins logs in as a non-interactive shell, so we don't even have /usr/local/bin in PATH
                    export PATH="/usr/local/bin:\${PATH}"
                    printenv

                    rm -fr build
                    ${python_version} -m venv --clear ${VENV}
                    ${VENV}/bin/python ${VENV}/bin/pip install --upgrade pip coverage setuptools wheel

                    ${VENV}/bin/python ${VENV}/bin/pip install -r requirements.txt

                    CC=${compiler} ${VENV}/bin/python setup.py bdist_wheel
                    ${VENV}/bin/python ${VENV}/bin/pip install -e .
                    ${VENV}/bin/python ${VENV}/bin/nosetests \
                        --with-xunit --with-coverage --cover-inclusive \
                        --cover-package=anonlink

                   """

                if(release) {
                    // This will be the official release
                    archiveArtifacts artifacts: "dist/anonlink-*.whl"
                }
            }
            catch(err) {
                testsError = err
                currentBuild.result = 'FAILURE'
                setBuildStatus("Build failed", "FAILURE");
            }
            finally {
                sh '''
                ${VENV}/bin/python ${VENV}/bin/coverage html --omit="*/cpp_code/*" --omit="*build_matcher.py*"
                '''

                if (!release) {
                    junit 'nosetests.xml'
                }

                if (testsError) {
                    throw testsError
                }
            }
        }

    } finally {
        deleteDir()
    }
}


def builders = [:]
for (config in configs) {
    def label = config["label"]
    def pythons = config["pythons"]
    def compilers = config["compilers"]

    for (_py_version in pythons) {
        for (_compiler in compilers) {

            def py_version = _py_version
            def compiler = _compiler

            def combinedName = "${label}-${py_version}-${compiler}"

            builders[combinedName] = {
                node(label) {
                    stage(combinedName) {
                        build(py_version, compiler, label, false)
                    }
                }
            }
        }
    }
}

node {
    checkout scm
    setBuildStatus("Build in progress", "PENDING");
}

parallel builders

node('linux') {

    stage('Release') {
        build('python3.5', 'gcc', 'GPU 1', true)
        setBuildStatus("Tests Passed", "SUCCESS");
    }
}