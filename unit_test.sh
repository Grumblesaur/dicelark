export DICELANG_CORE_EDITORS="/home/$USER/.atropos-vars/editors"

source env/bin/activate
cd dicelang/tests
pytest

if [ -z "$1" ]; then
  rm -rf vars/
else
  echo 'variables left in "vars" directory'
fi

