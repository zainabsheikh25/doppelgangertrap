"""
decoy.py – Fake mirror system
"""

FAKE_EMPLOYEES = [
    {"id": 1, "name": "Alex Rivera", "role": "Engineer", "salary": "$92,000", "ssn": "XXX-XX-4821"},
    {"id": 2, "name": "Jordan Lee", "role": "Manager", "salary": "$118,000", "ssn": "XXX-XX-7392"},
    {"id": 3, "name": "Sam Patel", "role": "Analyst", "salary": "$78,500", "ssn": "XXX-XX-1947"},
    {"id": 4, "name": "Taylor Kim", "role": "Designer", "salary": "$85,200", "ssn": "XXX-XX-6630"},
]

FAKE_PAYMENTS = [
    {"txn": "TX-98231", "customer": "Acme Corp", "amount": "$14,200", "card": "****-****-****-4412"},
    {"txn": "TX-98245", "customer": "Globex Inc", "amount": "$8,750", "card": "****-****-****-8891"},
]


class DecoyEnvironment:
    def __init__(self, logger):
        self.logger = logger

    def get_employees(self, actor):
        self.logger.log(actor, "VIEWED fake employee records", "employee_records.db", "TRAPPED")
        return FAKE_EMPLOYEES

    def get_payments(self, actor):
        self.logger.log(actor, "VIEWED fake payment data", "customer_payments.db", "TRAPPED")
        return FAKE_PAYMENTS