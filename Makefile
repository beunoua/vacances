
all: 2020

2020: holidays_2020.yaml care.yaml
	python vacances.py --care-start 2020-10-26 --first-care benoist

index.html: holidays_2020.yaml care.yaml
	python vacances.py
