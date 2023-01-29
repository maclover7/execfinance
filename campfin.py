import glob
import pandas as pd
from PyPDF2 import PdfReader
import re

CONTRIB_REGEX = r'Full Name of Contrib.*\n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(\d+)\n(\d+)\n(\d+)\n'
RECEIPT_REGEX = r'Full Name \n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(\d+)\n(\d+)\n(\d+)\nReceipt Description\n.*\n'
UNITEMIZED_REGEX = r'Unitemized  Contributions Received - \$ 50.00 or Less Per Contributor\nTOTAL for the Reporting Period           \(1\)\n\$\n(.*)\n'

def flatten(l):
    return [item for sublist in l for item in sublist]

def get_contributions_from_report(filename):
    contributions = process_report(filename)

    df = pd.DataFrame(
        flatten(contributions),
        columns=['name', 'address1', 'city', 'state', 'zipcode', 'amount', 'month', 'day', 'year'])
    df['name'] = df.name.str.upper()
    df['amount'] = pd.to_numeric(df.amount.str.replace(',', ''))

    return df

def get_contributions(name):
    contributions = []
    for file in glob.glob('input/%s_*.pdf' % name.capitalize()):
        contributions.append(flatten(process_report(file)))

    df = pd.DataFrame(
        flatten(contributions),
        columns=['name', 'address1', 'city', 'state', 'zipcode', 'amount', 'month', 'day', 'year'])
    df['name'] = df.name.str.upper()
    df['amount'] = pd.to_numeric(df.amount.str.replace(',', ''))

    return df

def process_report(filename):
    reader = PdfReader(filename)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    unitemized = re.findall(UNITEMIZED_REGEX, text)
    if len(unitemized) == 0:
        unitemized = []
    else:
        unitemized = [(
            'UNITEMIZED',
            '',
            'PITTSBURGH',
            'PA',
            '',
            unitemized[0],
            '',
            '',
            ''
        )]

    return [
        re.findall(CONTRIB_REGEX, text),
        re.findall(RECEIPT_REGEX, text),
        unitemized
    ]