import csv
from ofxstatement.parser import StatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, StatementLine

transaction_types = [
    ('CASH', ['Výběr hotovosti z bankomatu']),
    ('DIRECTDEBIT', ['Odeslané inkaso']),
    ('DIRECTDEP', ['Příchozí úhrada', 'Příchozí úhrada SEPA platba',
                   'Vrácení nákupu', 'Zahraniční příchozí úhrada']),
    ('FEE', ['Dotaz na zůstatek v ATM', 'Poplatek', 'Poplatek za tarif', 'Poplatek za výběr',
             'Poplatek za výběr z bankomatu', 'Vedení platební karty', 'Změna parametrů karty']),
    ('INT', ['Odepsaný úrok']),
    ('PAYMENT', ['Mobilní nákup na internetu', 'Mobilní platba na internetu',
                 'Nákup na internetu', 'Nákup na internetu 3D Secure',
                 'Odchozí úhrada', 'Odchozí SEPA úhrada']),
    ('POS', ['Nákup bezkontaktní kartou', 'Nákup u obchodníka', 'Úhrada bezkontaktní kartou']),
    ('REPEATPMT', ['Opakovaná platba', 'Trvalý příkaz']),
    ('SRVCHG', ['Poskytnutí karty-stoplistace', 'Zaslání karty/PIN kurýrem'])
]

class KomercniParser(StatementParser):
    date_format = '%d.%m.%Y'

    def __init__(self, filename):
        self.filename = filename

    def parse_intro(self, reader, statement):
        for row in reader:
            if len(row) == 0:
                continue
            
            id = row[0]
            if id == 'Cislo uctu':
                statement.account_id = row[1]
            elif id == 'Vypis od':
                statement.start_date = self.parse_datetime(row[1])
            elif id == 'Vypis do':
                statement.end_date = self.parse_datetime(row[1])
            elif id == 'Pocatecni zustatek':
                statement.start_balance = self.parse_decimal(row[1])
            elif id == 'Konecny zustatek':
                statement.end_balance = self.parse_decimal(row[1])
            elif id == 'Datum zauctovani':
                return row

    def parse_transactions(self, reader, header, statement):
        date_field = 0
        counter_bank_field = header.index('Protistrana')
        counter_account_field = header.index('Nazev protiuctu')
        amount_field = header.index('Castka')
        currency_field = header.index('Mena')
        trans_id_field = header.index('Identifikace transakce')
        description_field = header.index('Typ transakce')
        message_field = header.index('Popis pro me')
        message_payee_field = header.index('Zprava pro prijemce')

        foreign_payees = []
        for row in reader:
            desc = row[description_field].strip()
            if row[currency_field] != 'CZK':
                if desc != 'Vyrovnávací úhrada':
                    foreign_payees.append(row[counter_account_field])
                continue

            line = StatementLine(
                id = row[trans_id_field],
                date = self.parse_datetime(row[date_field]),
                amount = self.parse_decimal(row[amount_field]))
            if desc == 'Vyrovnávací úhrada':
                line.payee = ', '.join(foreign_payees)
                foreign_payees = []
                line.trntype = 'PAYMENT'
                line.memo = 'payment in foreign currency'
            else:
                line.payee = row[counter_account_field] or row[counter_bank_field]
                line.memo = row[message_field] or row[message_payee_field]
                trntype = next((tt for tt, types in transaction_types if desc in types), None)
                if trntype == None:
                    print(f'warning: transaction type "{desc}" is unknown, mapping to OTHER')
                    trntype = 'OTHER'
                line.trntype = trntype

            statement.lines.append(line)

        if foreign_payees != []:
            print('warning: some foreign payments were not balanced with Czech crowns')
                
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
