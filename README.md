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

In 2025 Komerční banka migrated its online banking services from their previous platform MojeBanka to the new platform KB+.  As part of this migration, their CSV file format changed.  **The current version of this plugin only works with the new KB+ format**.

To download a CSV file from Komerční banka, go to their [online banking site](https://plus.kb.cz) and log in.  CLick on your account to open the transaction listing, click "Statements and confirmations" on the right, then click "Account statement".  Now select a range of dates, then click "Generate statement".  Finally, select the CSV format and press the "Generate statement" button.  You'll see a message "We're preparing the statement", then a message "Document ready".  Click the Download button to download a CSV file.

To convert to an OFX file, run

```
$ ofxstatement convert -t komercni transactions.csv statement.ofx
```
