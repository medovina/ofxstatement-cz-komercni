ofxstatement-cz-komercni
========================

This is an [ofxstatement](https://github.com/kedder/ofxstatement) plugin that can generate OFX files from CSV files exported by [Komerční banka](https://www.kb.cz/en/), a Czech bank.

To install this plugin, download or clone the sources and run

```
$ python3 setup.py install
```

Or, to install for the current user only:

```
$ python3 setup.py install --user
```

To download a CSV file from Komerční banka, go to their [online banking site](https://www.mojebanka.cz) and log in.  Go to the "List of payments" page and click the link "detailed summary". Choose a date range and click the Display button.  Then click the link 'Save in CSV format' at the bottom of the page.

To convert to an OFX file, run

```
$ ofxstatement convert -t komercni transactions.csv statement.ofx
```

The plugin will work with CSV files that are exported either in English or in Czech.
