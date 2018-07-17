@Library("N1Pipeline@0.0.5")
import com.n1analytics.git.GitUtils;
import com.n1analytics.git.GitCommit;
import com.n1analytics.n1.docker.N1EngineContainer;
import com.n1analytics.python.PythonVirtualEnvironment;

def isMaster = env.BRANCH_NAME == 'master'
def isDevelop = env.BRANCH_NAME == 'develop'

VENV_DIRECTORY = "env"

GITHUB_TEST_CONTEXT = "jenkins/test"
GITHUB_RELEASE_CONTEXT = "jenkins/test"

def configs = [
    [os: 'linux', pythons: ['python3.4', 'python3.5', 'python3.6'], compilers: ['clang', 'gcc']],
    //[label: 'osx', pythons: ['python3.5'], compilers: ['clang', 'gcc']]
    [os: 'osx', pythons: ['python3.5'], compilers: ['clang']]
]

def PythonVirtualEnvironment prepareVirtualEnvironment(String pythonVersion, clkhashPackageName, compiler, venv_directory = VENV_DIRECTORY) {
  PythonVirtualEnvironment venv = new PythonVirtualEnvironment(this, venv_directory, pythonVersion);
  venv.create();
  venv.runPipCommand("install --upgrade pip coverage setuptools wheel")
  venv.runPipCommand("install --quiet --upgrade ${clkhashPackageName}");
  venv.runPipCommand("install -r requirements.txt");
  String cc = "CC=" + compiler;
  withEnv([cc]) {
    venv.runCommand("setup.py sdist bdist_wheel --universal");
  }
  venv.runPipCommand("install -e .");
  return venv;
}

def build(python_version, compiler, label, release = false) {
  GitUtils.checkoutFromSCM(this)
  Exception testsError = null;
  try {
    clkhashPackageName = "clkhash-*-py2.py3-none-any.whl"
    copyArtifacts(
        projectName: 'clkhash/master',
        fingerprint: true,
        flatten    : true,
        filter     : 'dist/' + clkhashPackageName
    )

    PythonVirtualEnvironment venv = prepareVirtualEnvironment(python_version, clkhashPackageName, compiler)
    try {
      venv.runChosenCommand("pytest --cov=anonlink --junit-xml=testoutput.xml --cov-report=xml:coverage.xml")
      if (release) {
        // This will be the official release
        archiveArtifacts artifacts: "dist/anonlink-*.whl"
        archiveArtifacts artifacts: "dist/anonlink-*.tar.gz"
      }
    } catch (Exception err) {
      testsError = err
    } finally {
      if (!release) {
        junit 'testoutput.xml'
      } else {
        venv.runChosenCommand("coverage xml --omit=\"*/cpp_code/*\" --omit=\"*build_matcher.py*\"")
        cobertura coberturaReportFile: 'coverage.xml'
      }
      if (testsError != null) {
        throw testsError
      }
    }

  } finally {
    try {
      deleteDir()
    } catch (Exception e) {
      echo "Error during 'deleteDir':\n" + e.toString()
    }
  }
}


def builders = [:]
for (config in configs) {
  def os = config["os"]
  def pythons = config["pythons"]
  def compilers = config["compilers"]

  for (_py_version in pythons) {
    for (_compiler in compilers) {

      def py_version = _py_version
      def label = "$os&&$py_version"
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

GitCommit commit;
node() {
  commit = GitUtils.checkoutFromSCM(this);
  commit.setInProgressStatus(GITHUB_TEST_CONTEXT);
}

try {
  parallel builders
} catch (Exception err) {
  node() {
    commit.setFailStatus("Build failed", GITHUB_TEST_CONTEXT);
  }
  throw err
}

node('GPU 1') {
  stage('Release') {
    try {
      commit.setInProgressStatus(GITHUB_RELEASE_CONTEXT);
      build('python3.5', 'gcc', 'GPU 1', true)
      commit.setSuccessStatus(GITHUB_RELEASE_CONTEXT)
    } catch (Exception e) {
      commit.setFailStatus("Release failed", GITHUB_RELEASE_CONTEXT);
      throw e;
    }
  }
}
