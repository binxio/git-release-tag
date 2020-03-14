

upload-dist:
	pipenv run twine upload dist/*


Pipfile.lock: Pipfile setup.py
	pipenv update -d

clean:
	rm -rf target dist
	pipenv --rm
	find . -name \*.pyc | xargs rm 

test: 
	[ -z "$(ls -1 tests/test*.py 2>/dev/null)" ] || PYTHONPATH=$(PWD)/src pipenv run pytest ./tests/test*.py

fmt:
	black $(find src -name *.py) tests/*.py

