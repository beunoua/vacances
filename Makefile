
all: holidays.yaml care.yaml
	python vacances.py --first-care benoist -c comments.txt

2020: holidays_2020.yaml care_2020.yaml
	python vacances.py --care-start 2020-10-26 --first-care benoist -c comments.txt

index.html: holidays_2020.yaml care.yaml
	python vacances.py
