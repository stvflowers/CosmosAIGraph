
New-Item -ItemType Directory -Force -Path .\tmp | out-null
del tmp/*.*

echo 'executing unit tests with code coverage ...'
pytest -v --cov=pysrc/ --cov-report html tests/
