import pathlib

from setuptools import setup, find_packages

main_dir = pathlib.Path(__file__).parent.resolve()
readme_path = main_dir / "README.md"
LONG_DESCRIPTION = readme_path.read_text() if readme_path.exists() else 'LONG DESCRIPTION'


VERSION = '0.1.3'
DESCRIPTION = 'DESCRIPTION'

# Setting up
# print(find_packages())
# exit()
setup(
    name="smartcli",
    version=VERSION,
    author="ProxPxD (Piotr Maliszewski)",
    # author_email="<mail@neuralnine.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    keywords=['python', 'cli', 'parser', 'smart', 'smartcli', 'smartparser'],
    classifiers=[],
    include_package_data=True,
)