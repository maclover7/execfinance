import glob
import pandas as pd
from PyPDF2 import PdfReader
import re

CONTRIB_REGEX = r'Full Name of Contrib.*\n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(\d+)\n(\d+)\n(\d+)\n'
RECEIPT_REGEX = r'Full Name \n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(.*)\n(\d+)\n(\d+)\n(\d+)\nReceipt Description\n.*\n'
UNITEMIZED_REGEX = r'Unitemized  Contributions Received - \$ 50.00 or Less Per Contributor\nTOTAL for the Reporting Period           \(1\)\n\$\n(.*)\n'

CONTRIBUTORS = {
    "AMALGAMATED TRANSIT UNION COPE": "ATU COPE VOLUNTARY ACCOUNT",
    "IBEW LOCAL UNION NO. 5 PAC": "LOCAL 0005 IBEW PAC",
    "MIDATLANTIC POLITICAL LEAGUE - MALPA": "MID-ATLANTIC LABORERS' POLITICAL LEAGUE",
    "STEAMFITTERS LOCAL UNON #449": "LOCAL 0449 STEAMFITTERS UNION PAC",
    "STEAMFITTERS LOCAL UNION 449 PAC FUND": "LOCAL 0449 STEAMFITTERS UNION PAC",
    "PLUMBERS LOCAL UNION NO. 27 PAC": "LOCAL 0027 PLUMBERS UNION PAC",
    "BRICKLAYERS &AMP; ALLIED CRAFTWORKERS LOCAL 9 PAC": "LOCAL 0009 BRICKLAYERS & ALLIED CRAFTWORKERS PA PAC",
    "PITTSBURGH FIRE FIGHTERS LOCAL NO 1 FIRE PAC ACCOUNT": "PGH FIRE FIGHTERS LOCAL #1 FIRE PAC",
    "TEAMSTERS LOCAL UNION 249 - DRIVE FUND": "LOCAL 0249 TEAMSTERS DRIVE",
    "U.W.U.A. LOCAL 433 PAC": "LOCAL 0433 UWUA (UTILITY WORKERS)",
    "TEAMSTER JOINT COUNCIL 40 PAC": "TEAMSTERS JT COUNCIL 40 PAC",
    "AFSCME COUNCIL 13 POLITICAL &AMP; LEGISLATIVE": "AFSCME COUNCIL 13 POL & LEG ACCT",
    # Laborers
    "LABORERS DISTRICT COUNCIL OF WESTERN PENNSYLVANIA": "WESTERN PENNSYLVANIA LABORERS 2019 PAC",
    "LABORERS' DISTRICT COUNCIL OF WESTERN PENNSYLVANIA": "WESTERN PENNSYLVANIA LABORERS 2019 PAC",
    "WESTERN PA LABORERS UNION PAC": "WESTERN PENNSYLVANIA LABORERS 2019 PAC",
    "WESTERN PENNSYLVANIA LABORERS": "WESTERN PENNSYLVANIA LABORERS 2019 PAC",
    "WESTERN PENNSYLVANIA LABORERS' PAC": "WESTERN PENNSYLVANIA LABORERS 2019 PAC"
}

def flatten(l):
    return [item for sublist in l for item in sublist]

def get_contributions_from_report(filename):
    contributions = process_report(filename)

    df = pd.DataFrame(
        flatten(contributions),
        columns=['name', 'address1', 'city', 'state', 'zipcode', amount, 'month', 'day', 'year'])
    df['name'] = df.name.str.upper()
    df['amount'] = pd.to_numeric(df.amount.str.replace(',', ''))

    return df

def get_top_contributors(name):
    contributions = []
    for file in glob.glob('input/%s_*.pdf' % name.capitalize()):
        contributions.append(flatten(process_report(file)))

    amount_col = 'amount_%s' % name[0:4].lower()
    df = pd.DataFrame(
        flatten(contributions),
        columns=['name', 'address1', 'city', 'state', 'zipcode', amount_col, 'month', 'day', 'year'])

    df['name'] = df.name.str.upper()
    df['name'] = df.name.replace(CONTRIBUTORS)
    df[amount_col] = pd.to_numeric(df[amount_col].str.replace(',', ''))

    df_topcontribs = df.groupby('name')[amount_col].sum().to_frame().reset_index()
    df_sum = df[amount_col].sum()
    df_topcontribs['pct_%s' % name[0:4].lower()] = df_topcontribs[amount_col] / df_sum

    return df_topcontribs

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