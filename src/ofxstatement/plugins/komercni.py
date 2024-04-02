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

    def parse_intro(self, reader, statement):
        next_row_is_end_date = False

        for row in reader:
            if len(row) == 0:
                continue
            
            if next_row_is_end_date:
                statement.end_date = self.parse_datetime(row[1])
                next_row_is_end_date = False
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
                return row

    def parse_transactions(self, reader, header, statement):
        date_field = 0
        counter_bank_field = index_of(header, 'Counteraccount and bank code', 'Protiúčet a kód banky')
        counter_account_field = index_of(header, 'Counteraccount name', 'Název protiúčtu')
        amount_field = index_of(header, 'Amount', 'Částka')
        trans_id_field = index_of(header, 'Transaction identification',
                                        'Identifikace transakce')
        description_field = index_of(header, 'System description', 'Systémový popis')
        message_field = index_of(header, 'Message for payer', 'Popis příkazce')
        message_payee_field = index_of(header, 'Message for payee', 'Popis pro příjemce')
        av1_field = index_of(header, 'AV field 1', 'AV pole 1')
        av2_field = index_of(header, 'AV field 2', 'AV pole 2')

        for row in reader:
            line = StatementLine(id = row[trans_id_field],
                                 date = self.parse_datetime(row[date_field]),
                                 amount = self.parse_decimal(row[amount_field]))
            desc = row[description_field].strip()
            message = row[message_field]
            av1 = row[av1_field].strip()
            av2 = row[av2_field].strip()
            if desc in ('Ach deposit', 'Incoming payment', 'Transfer credit', 'Příchozí úhrada'):
                line.payee = row[counter_account_field]
                line.memo = message
                line.trntype = 'DEP'
            elif desc in ('Ach withdrawal', 'Odchozí úhrada', 'Outgoing payment'):
                counter = row[counter_account_field]
                line.payee = counter or message
                line.memo = row[message_payee_field]
                line.trntype = 'PAYMENT'
            elif desc in ('ATM cash withdrawal', 'Výběr hotovosti z ATM'):
                line.payee = desc
                line.memo = av1
                line.trntype = 'ATM'
            elif desc in ('ATM cash withdrawal - fee', 'Výběr hotovosti poplatek'):
                line.payee = desc
                line.memo = row[counter_account_field]
                line.trntype = 'FEE'
            elif desc in ('Card purchase', 'Contactless card purchase',
                          'Credit of purchase', 'Dobití mobilního telefonu',
                          'Internet mobile payment', 'Internet purchase 3D Secure',
                          'MO/TO transakce',
                          'Mobilní platba', 'Mobilní platba na internetu',
                          'Nákup bezkontaktní kartou', 'Nákup na internetu',
                          'Nákup na internetu 3D Secure', 'Nákup u obchodníka',
                          'Nákup na tankomatu',
                          'Opakovaná platba', 'Opakovaná platba tokenem',
                          'Purchase on the internet',
                          'Recharge of mobile phone', 'Recurring payment',
                          'Vrácení nákupu'):
                line.payee = av1
                line.memo = av2
                line.trntype = 'POS'
            elif desc in ('Deposit', 'Příchozí úhrada/vklad na účet'):
                line.payee = av1 or message
                line.memo = message
                line.trntype = 'DEP'
            elif desc in ('Debit memo', 'Debit transfer', 'Force pay debit',
                          'Priority 3 check', 'Platba na vrub vašeho účtu'):
                line.payee = message or row[counter_account_field] or row[counter_bank_field]
                line.memo = av1
                line.trntype = 'PAYMENT'
            elif desc in ('Fee', 'Payment card maintenance', 'Poplatek', 'Vedení platební karty'):
                line.payee = av1
                line.memo = av2
                line.trntype = 'FEE'
            else:
                if desc:
                    print(f'warning: unknown transaction type: "{desc}"')
                line.payee = message
                line.memo = row[counter_account_field]
                line.trntype = 'OTHER'
            statement.lines.append(line)
                
    def parse(self):
        statement = Statement(bank_id = 'KOMBCZPP', currency = 'CZK')
        
        with open(self.filename, encoding = 'cp1250') as f:
            reader = csv.reader(f, delimiter = ';')
            header = self.parse_intro(reader, statement)
            self.parse_transactions(reader, header, statement)

        return statement

class KomercniPlugin(Plugin):
    'Czech Komerční banka CSV'

    def get_parser(self, filename):
        return KomercniParser(filename)
