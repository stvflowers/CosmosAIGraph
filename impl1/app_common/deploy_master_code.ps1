# Recreate the python virtual environment and reinstall libs on Windows.
# Chris Joakim, Microsoft

echo 'reformatting the python code with the black tool ...'
black pysrc

echo 'copying the reformatted code to the other sub-projects ...'
ant -f .\deploy_master_code.xml
