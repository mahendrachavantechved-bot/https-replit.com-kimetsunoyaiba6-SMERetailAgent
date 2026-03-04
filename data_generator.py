import random, string

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"]
INDUSTRIES = ["IT", "Retail", "Manufacturing", "Healthcare", "FMCG"]

def _fake_pan():
    return ''.join(random.choices(string.ascii_uppercase, k=5)) + \
           ''.join(random.choices(string.digits, k=4)) + \
           random.choice(string.ascii_uppercase)

def _fake_gstin():
    return str(random.randint(10, 29)) + _fake_pan() + str(random.randint(1, 9)) + 'Z' + \
           random.choice(string.ascii_uppercase + string.digits)

def _fake_mobile():
    return "9" + ''.join(random.choices(string.digits, k=9))

def _fake_email(name):
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com"])
    return f"{name.lower().replace(' ', '.')}@{domain}"

def generate_retail_samples(n=200):
    data = []
    for i in range(n):
        name = f"Retail User {i}"
        data.append({
            "id": f"R{i:04d}",
            "name": name,
            "pan": _fake_pan(),
            "mobile": _fake_mobile(),
            "email": _fake_email(name),
            "city": random.choice(CITIES),
            "employment_type": random.choice(["Salaried", "Self Employed"]),
            "loan_amt": random.randint(5, 50) * 100000,
            "loan_purpose": random.choice(["Home", "Car", "Personal", "Education"]),
            "cibil_score": random.randint(650, 800),
            "foir_post_loan": round(random.uniform(25, 50), 2),
            "ltv_ratio": round(random.uniform(60, 85), 2),
        })
    return data

def generate_sme_samples(n=150):
    data = []
    for i in range(n):
        name = f"SME Firm {i}"
        data.append({
            "id": f"S{i:04d}",
            "name": name,
            "pan": _fake_pan(),
            "gstin": _fake_gstin(),
            "mobile": _fake_mobile(),
            "email": _fake_email(name),
            "city": random.choice(CITIES),
            "industry": random.choice(INDUSTRIES),
            "loan_amt": random.randint(10, 100) * 100000,
            "cibil_score": random.randint(650, 800),
            "dscr": round(random.uniform(1.2, 2.0), 2),
            "ltv_ratio": round(random.uniform(55, 80), 2),
        })
    return data
