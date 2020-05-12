CLI_APP = whaleAlertLogger
PACKAGE_NAME = whalealert
VENV_NAME = venv
VENV_ACTIVATE = $(VENV_NAME)/bin/activate
PYTHON = $(VENV_NAME)/bin/python3
COVERAGE =  $(VENV_NAME)/bin/coverage3

test: venv
	@. $(VENV_ACTIVATE); $(COVERAGE) run -m unittest discover -s tests
	@. $(VENV_ACTIVATE); $(COVERAGE) report

testRun: install package
	$(CLI_APP) -h
	$(CLI_APP) -w testWorkingDir -g 
	$(CLI_APP) -s
	$(CLI_APP) -s -d
	$(CLI_APP) -s -j
	$(CLI_APP) -s -d -j
	$(CLI_APP) -q
	$(CLI_APP) -v
	$(CLI_APP) -q -m 1
	$(CLI_APP) -q -b bitcoin
	$(CLI_APP) -q -b bitcoin -t BTC
	$(CLI_APP) -q -t ETH
	$(CLI_APP) -w testWorkingDir -x
	rm -f cryptoData.xlsx 
	rm -rf testWorkingDir

package: venv test
	@. $(VENV_ACTIVATE); \
		$(PYTHON) setup.py sdist bdist_wheel

venv: $(VENV_ACTIVATE)

$(VENV_ACTIVATE):
	@test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	@. $(VENV_ACTIVATE); pip3 install -r requirements.txt
	@touch $(VENV_ACTIVATE)

install:
	@pip3 install .

testRelease: test
	@$(PYTHON) -m twine upload --repository-url https://test.pypi.org/legacy/ --skip-existing dist/*

release: test
	@$(PYTHON) -m twine upload --skip-existing dist/*

uninstall: clean
	@pip3 uninstall $(PACKAGE_NAME)

clean:
	@rm -rf $(VENV_NAME)
	@rm -rf *.egg-info
	@rm -rf build/
	@rm -rf dist/
	@rm -rf __pycache__
	@rm -rf **/__pycache__
