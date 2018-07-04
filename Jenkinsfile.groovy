@Library("N1Pipeline@0.0.5")
import com.n1analytics.git.GitUtils;
import com.n1analytics.git.GitCommit;
import com.n1analytics.n1.docker.N1EngineContainer;
import com.n1analytics.python.PythonVirtualEnvironment;

def isMaster = env.BRANCH_NAME == 'master'
def isDevelop = env.BRANCH_NAME == 'develop'

VENV_DIRECTORY = "env"

GIT_CONTEXT = "jenkins"

def configs = [
    [label: 'GPU 1', pythons: ['python3.4', 'python3.5', 'python3.6'], compilers: ['clang', 'gcc']],
    //[label: 'osx', pythons: ['python3.5'], compilers: ['clang', 'gcc']]
    [label: 'McNode', pythons: ['python3.5', 'python3.6'], compilers: ['clang', 'gcc']]
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
    if (label == 'McNode') {
      // Strip 'python' from the 'pythonX.X' version string
      def pyver = python_version.replace("python", "")

      // 'pyenv versions' returns a list of python versions in x.y.z format
      // with an asterisk in front of the current version. The unspeakable horror
      // below strips leading space and asterisk from each version line, then
      // picks the last x.y.z for which "x.y" matches ${pyver}.
      long_pyver = sh(script: """
          pyenv versions | \\
            sed -e 's/^\\([ *]\\)*//' | \\
            cut -f1 -d' ' | \\
            grep '^${pyver}' | \\
            tail -1
          """, returnStdout: true)

      // Set Python version
      sh(script: "pyenv local ${long_pyver}")

      def chkver = sh(script: "python --version | cut -d' ' -f2", returnStdout: true)
      if ( ! chkver.startsWith(pyver)) {
        throw new Exception("Can't find requested Python version")
      }
    }
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

GitCommit commit;
node() {
  commit = GitUtils.checkoutFromSCM(this);
  commit.setInProgressStatus(GIT_CONTEXT);
}

try {
  parallel builders
} catch (Exception err) {
  node() {
    commit.setFailStatus("Build failed", GIT_CONTEXT);
  }
  throw err
}

node('GPU 1') {
  stage('Release') {
    try {
      build('python3.5', 'gcc', 'GPU 1', true)
      commit.setSuccessStatus(GIT_CONTEXT)
    } catch (Exception e) {
      commit.setFailStatus("Release failed", GIT_CONTEXT);
      throw e;
    }
  }
}
