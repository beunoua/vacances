.PHONY: 2020 2021

all: 2020

2021: 2021/holidays_2021.yaml 2021/care_2021.yaml
	python vacances.py --first-care lydie -c comments.txt --pdf-zoom 1.1 --output-dir $@ $^

2020: 2020/index.html

2020/index.html: 2020/holidays_2020.yaml 2020/care_2020.yaml
	python vacances.py --care-start 2020-10-26 --first-care benoist -c comments.txt --output-dir 2020 $^
