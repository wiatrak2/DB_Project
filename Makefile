init:
	python3 dbAPI.py --init $(input)

initCustom:
	python3 dbAPI.py --init --db $(db) $(input)

run:
	python3 dbAPI.py $(input)