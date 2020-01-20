import csv
from ofxstatement.parser import StatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, StatementLine

def index_of(s, t, u):
    try:
        return s.index(t)
    except ValueError:
        return s.index(u)

class KomercniParser(StatementParser):
    date_format = '%d.%m.%Y'

    def __init__(self, filename):
        self.filename = filename

    def guess_type(self, description, amount):
        d = description.lower()
        if 'atm' in d: return 'ATM'
        if 'check' in d: return 'CHECK'
        
        if ('card purchase' in d or
            'Nákup u obchodníka' in d or
            'Nákup bezkontaktní kartou'): return 'POS'
           
        return 'CREDIT' if amount > 0 else 'DEBIT'

    def parse(self):
        statement = Statement(bank_id = 'KOMBCZPP', currency = 'CZK')
        
        with open(self.filename, encoding = 'cp1250') as f:
            next_row_is_end_date = False
            date_field = None
            
            for row in csv.reader(f, delimiter = ';'):
                if len(row) == 0:
                    continue
                
                if next_row_is_end_date:
                    statement.end_date = self.parse_datetime(row[1])
                    next_row_is_end_date = False
                    continue
                
                if date_field is not None:
                    line = StatementLine(id = row[trans_id_field],
                                         date = self.parse_datetime(row[date_field]),
                                         memo = row[description_field],
                                         amount = self.parse_decimal(row[amount_field]))
                    av1 = row[av1_field].strip()
                    if av1 == '' or av1.isnumeric() or av1 == 'AV':
                        line.payee = row[payer_field]
                    else:
                        line.payee = av1
                    line.trntype = self.guess_type(line.memo, line.amount)
                    statement.lines.append(line)
                    continue
                
                id = row[0]
                if id in ('Account number', 'Číslo účtu'):
                    statement.account_id = row[1]
                elif id in ('Statement for period', 'Výpis za období'):
                    statement.start_date = self.parse_datetime(row[1])
                    next_row_is_end_date = True
                elif id in ('Initial balance', 'Počáteční zůstatek'):
                    statement.start_balance = self.parse_decimal(row[1])
                elif id in ('Final balance', 'Konečný zůstatek'):
                    statement.end_balance = self.parse_decimal(row[1])
                elif id in ('Due date', 'Datum splatnosti'):
                    date_field = 0
                    amount_field = index_of(row, 'Amount', 'Částka')
                    trans_id_field = index_of(row, 'Transaction identification',
                                                   'Identifikace transakce')
                    description_field = index_of(row, 'System description', 'Systémový popis')
                    payer_field = index_of(row, 'Message for payer', 'Popis příkazce')
                    av1_field = index_of(row, 'AV field 1', 'AV pole 1')
                    
        return statement

class KomercniPlugin(Plugin):
    'Czech Komerční banka CSV'

    def get_parser(self, filename):
        return KomercniParser(filename)
