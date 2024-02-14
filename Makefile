cython :
	python setup.py build_ext --inplace

clean :
	python setup.py clean --all

test :
	python -m coverage erase
	python -m coverage run --branch --source=./prolothar_process_discovery -m unittest discover -v
	python -m coverage xml -i

check_requirements :
	safety check -r requirements.txt

package :
	python -m build

clean_package :
	rm -R dist build prolothar_process_discovery.egg-info

publish :
	twine upload --skip-existing --verbose dist/*