#!/usr/bin/env python
#coding: utf-8
from __future__ import print_function, unicode_literals
from lxml import etree
from collections import defaultdict
import sys, re
import sqlite3

TAG_PREFIX = "{http://www.mediawiki.org/xml/export-0.10/}"

def split_sections(text, n=1):
  a = re.split('\n\s*%s (.*) %s\s*\n'%('='*n,'='*n),'\n'+text)
  if len(a)>2:
    return dict(zip(a[1::2], [split_sections(t, n+1) or t for t in a[2::2]]))


def extract_dictionary(filename='ruwiktionary-latest-pages-articles.xml'):
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
    try:
        filename = sys.argv[1]
    except:
        filename = "ruwiktionary-latest-pages-articles.xml"

    con = sqlite3.connect('wiki.db')
    con.execute('DROP TABLE IF EXISTS word')
    con.execute('DROP TABLE IF EXISTS def') 
    con.execute('DROP TABLE IF EXISTS rel') 
    con.execute('CREATE TABLE word(id INTEGER PRIMARY KEY autoincrement, name VARCHAR(80))')
    con.execute('CREATE TABLE def(id INTEGER PRIMARY KEY autoincrement, word INTEGER, def TEXT)')
    con.execute('CREATE TABLE rel(word INTEGER, def INTEGER, func VARCHAR(30), val VARCHAR(80))')
    con.commit()
    defre = re.compile('# (.*)')
    defln = re.compile('\[\[([^\]]*)\]\]')
    for d in extract_dictionary(filename):
      if "# " not in d['text']:
        print('Ignored: '+d['title'])
        continue
      try:
        c=con.cursor()
        c.execute('INSERT INTO word(name) VALUES (?)',(d['title'],))
        word = c.lastrowid
        sections= split_sections(d['text'])['{{-ru-}}']
        if not isinstance(sections, dict):
          sections = [('',split_sections(sections, 3))]
        else:
          sections = sections.items()
        for name, cont in sections:
          #schema: word, [(meaning, [('syn',[synonyms_links, ...]),('ant',[antonyms_links, ...])]), ...]
          rels = ['Синонимы','Антонимы','Гиперонимы','Гипонимы']
          meanings = defre.findall(cont['Семантические свойства']['Значение'])
          for i, defin in enumerate(meanings):
            c.execute('INSERT INTO def(word, def) VALUES (?,?)',(word,defin))
            defid = c.lastrowid
            for rel in rels:
              if rel in cont['Семантические свойства']:
                cache_me = defre.findall(cont['Семантические свойства'][rel]);
                if i not in cache_me: continue
                rel_text = cache_me[i]
                rel_links = defln.findall(rel_text)
                for link in rel_links:
                  c.execute('INSERT INTO rel(word, def, func, val) VALUES (?,?,?,?)',(word,defid,rel,link))
            #todo: translations, related words, clean defs
          con.commit()
      except:
        print('Error: '+d['title'])
        #import traceback
        #traceback.print_exc()
        con.rollback()
        #exit(1)
    con.close()
