all: run

run:
	poetry run mitmdump --quiet --flow-detail 0 -s ./hw-capture.py
