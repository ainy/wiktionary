all:ruwiktionary-latest-pages-articles.xml enwiktionary-latest-pages-articles.xml
	python extract.py
	python extract_en.py

ruwiktionary-latest-pages-articles.xml:
	wget https://dumps.wikimedia.org/ruwiktionary/latest/ruwiktionary-latest-pages-articles.xml.bz2
	bunzip2 ruwiktionary-latest-pages-articles.xml.bz2

enwiktionary-latest-pages-articles.xml:
	wget https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2
	bunzip2 enwiktionary-latest-pages-articles.xml.bz2

