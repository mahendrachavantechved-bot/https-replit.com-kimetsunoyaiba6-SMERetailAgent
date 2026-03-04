import random, string, json

CITIES   = ["Bengaluru","Mumbai","Delhi","Hyderabad","Chennai","Pune","Ahmedabad","Kolkata"]
INDUSTRIES = ["IT","Retail","Manufacturing","Healthcare","FMCG","Logistics","Education","Textiles"]
PURPOSES = ["Home Loan","Car Loan","Personal Loan","Education Loan","Business Expansion"]
EMP_TYPES = ["Salaried","Self Employed","Contract","Business Owner"]

def _pan():
    return (''.join(random.choices(string.ascii_uppercase,k=5)) +
            ''.join(random.choices(string.digits,k=4)) +
            random.choice(string.ascii_uppercase))

def _gstin(pan):
    return str(random.randint(10,29)) + pan + str(random.randint(1,9)) + 'Z' + random.choice(string.ascii_uppercase+string.digits)

def _mobile():
    return "9" + ''.join(random.choices(string.digits,k=9))

def _email(name):
    return name.lower().replace(" ",".")+random.choice(["@gmail.com","@yahoo.com","@outlook.com"])

def generate_retail_samples(n=200):
    data=[]
    for i in range(n):
        name=f"Retail User {i:04d}"
        pan=_pan()
        data.append({"id":f"R{i:04d}","name":name,"pan":pan,"mobile":_mobile(),
            "email":_email(name),"gender":random.choice(["Male","Female"]),
            "city":random.choice(CITIES),"employment_type":random.choice(EMP_TYPES),
            "loan_amt":random.randint(5,50)*100000,"loan_purpose":random.choice(PURPOSES),
            "cibil_score":random.randint(650,800),"foir_post_loan":round(random.uniform(25,50),2),
            "ltv_ratio":round(random.uniform(60,85),2),"monthly_income":random.randint(30,200)*1000,
            "existing_emi":random.randint(0,15)*1000,"tenure_months":random.choice([12,24,36,48,60,84,120])})
    with open("retail_applicants.json","w") as f: json.dump(data,f,indent=2)
    return data

def generate_sme_samples(n=200):
    data=[]
    for i in range(n):
        name=f"SME Firm {i:04d}"
        pan=_pan()
        data.append({"id":f"S{i:04d}","name":name,"pan":pan,"gstin":_gstin(pan),
            "mobile":_mobile(),"email":_email(name),"city":random.choice(CITIES),
            "industry":random.choice(INDUSTRIES),"loan_amt":random.randint(10,100)*100000,
            "loan_purpose":random.choice(["Working Capital","Machinery","Expansion","Trade Finance"]),
            "cibil_score":random.randint(650,800),"dscr":round(random.uniform(1.2,2.5),2),
            "ltv_ratio":round(random.uniform(55,80),2),"annual_turnover":random.randint(50,500)*100000,
            "vintage_years":random.randint(2,20),"promoter_cibil":random.randint(650,800),
            "gst_compliance":random.choice(["Compliant","Partial","Non-Compliant"])})
    with open("sme_applicants.json","w") as f: json.dump(data,f,indent=2)
    return data

if __name__=="__main__":
    generate_retail_samples()
    generate_sme_samples()
    print("Generated 200 Retail + 200 SME applicants")
    print("Files created: retail_applicants.json & sme_applicants.json")
