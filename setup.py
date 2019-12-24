import setuptools
import setuptools.command.develop
import setuptools.command.sdist
import shutil
import subprocess


class BuildStatic(setuptools.Command):
    user_options = []

    def run(self):
        packager = None
        for p in ("yarnpkg", "yarn", "npm"):
            packager = shutil.which(p)
            if packager is not None:
                break

        if packager is None:
            raise Exception(
                "build_static requires yarn or npm to be installed"
            )

        subprocess.check_call([packager, "install"], cwd="js")
        subprocess.check_call([packager, "run", "build"], cwd="js")

    def initialize_options(self):
        ...

    def finalize_options(self):
        ...


class SDist(setuptools.command.sdist.sdist):
    def make_distribution(self):
        self.run_command("build_static")
        return super(SDist, self).make_distribution()


class Develop(setuptools.command.develop.develop):
    def install_for_development(self):
        self.run_command("build_static")
        return super(Develop, self).install_for_development()


setuptools.setup(
    name="pykzee-inspector",
    version="0.1.0",
    description="Web interface for inspecting the Pykzee state",
    url="https://github.com/spacedentist/pykzee-inspector",
    author="Sven Over",
    author_email="sp@cedenti.st",
    license="MIT",
    packages=["pykzee", "pykzee.inspector"],
    install_requires=["aiohttp", "pykzee"],
    package_data={
        "pykzee.inspector": ["resources/index.html", "resources/static/*"]
    },
    cmdclass={"build_static": BuildStatic, "develop": Develop, "sdist": SDist},
)
