#!/usr/bin/env python
#coding: utf-8
from __future__ import unicode_literals
from lxml import etree
from collections import defaultdict
import sys, re
import sqlite3

TAG_PREFIX = "{http://www.mediawiki.org/xml/export-0.10/}"

def split_sections(text, n=2):
  a = re.split('\n\s*%s(.*)%s\s*\n'%('='*n,'='*n),'\n'+text)
  if len(a)>2:
    return defaultdict(unicode, zip(a[1::2], [split_sections(t, n+1) or t for t in a[2::2]]))
  return unicode(text)

def extract_dictionary(filename):
    context = etree.iterparse(filename)
    current_thing = defaultdict(str)
    for event, elem in context:
        if event == 'end':
            current_thing[elem.tag.replace(TAG_PREFIX, '')] = elem.text
            if elem.tag == TAG_PREFIX+"page":
                if current_thing['text']:
                    yield current_thing
                    current_thing = defaultdict(str)
                while elem.getparent() is not None:
                    del elem.getparent()[0]

if __name__ == "__main__":
    total = 5255582.
    try:
        filename = sys.argv[1]
    except:
        filename = "enwiktionary-latest-pages-articles.xml"

    con = sqlite3.connect('enwikt.db')
    con.execute('DROP TABLE IF EXISTS word')
    con.execute('DROP TABLE IF EXISTS def') 
    con.execute('DROP TABLE IF EXISTS rel') 
    con.execute('CREATE TABLE word(name VARCHAR(80))')
    con.execute('CREATE TABLE def(word INTEGER, def TEXT)')
    con.execute('CREATE TABLE rel(word INTEGER, def INTEGER, func VARCHAR(10), val VARCHAR(80))')
    con.commit()
    deftr = re.compile('\{\{trans-top\|([^|}]*)')
    deflg = re.compile('\{\{t\+?\|([^|]*)\|([^|}]*)')
    defre = re.compile('# (.*)')
    defln = re.compile('\[\[([^\]]*)\]\]')
    ds = 0
    ts = 0
    for n, d in enumerate(extract_dictionary(filename)):
        sect = split_sections(d['text'])
        if isinstance(sect, unicode) or isinstance(sect['English'], unicode): continue
        c=con.cursor()
        c.execute('INSERT INTO word(name) VALUES (?)',(d['title'],))
        word = c.lastrowid
        print '\r{:.1%}'.format(n/total), ts,
        for name, cont in sect['English'].items():
          if isinstance(cont,unicode) or not cont['Translations'] or not isinstance(cont['Translations'],unicode): continue
          #schema: word, [(meaning, [('lang',[word, ...]),('lang',[word, ...])]), ...]
          meanings = cont['Translations'].split('{{trans-bottom}}')
          for i, txt in enumerate(meanings):
            for defin in deftr.findall(txt): c.execute('INSERT INTO def(word, def) VALUES (?,?)',(word,defin))
            ds += 1
            defid = c.lastrowid
            for lang, trans in deflg.findall(txt):
              if lang in MY_LANGS:
                c.execute('INSERT INTO rel(word, def, func, val) VALUES (?,?,?,?)',(word,defid,lang,trans))
                ts += 1
            
    con.commit()
    con.close()
