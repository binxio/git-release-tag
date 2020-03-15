CURRENT_VERSION=$(git-release-tag show)

dist/git-release-tag-$(CURRENT_VERSION).tag.gz: src/*/* setup.py
	rm -rf dist/*
	pipenv run python setup.py check
	pipenv run python setup.py build
	pipenv run python setup.py sdist

upload-dist: dist/git-release-tag-$(CURRENT_VERSION).tag.gz
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

