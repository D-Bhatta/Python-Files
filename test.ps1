# Print env info
$_pyver = python --version;
$_pipver = pip --version;
$_pwd = pwd;

echo "Present working directory: $_pwd";
echo "Python version used: $_pyver";
echo "Pip version used: $_pipver";
echo "";

pytest;
mypy;
bandit --ini .bandit;
flake8;
pydocstyle;
