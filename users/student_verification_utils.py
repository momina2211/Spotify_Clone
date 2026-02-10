"""
Utility functions for student verification.
"""
import re
from typing import Optional, Tuple


# Common educational email domains
EDUCATIONAL_DOMAINS = {
    # Common .edu domains (US)
    '.edu',
    # International educational domains
    '.ac.uk',  # UK academic
    '.ac.za',  # South Africa
    '.ac.jp',  # Japan
    '.ac.in',  # India
    '.ac.au',  # Australia
    '.ac.nz',  # New Zealand
    '.ac.ca',  # Canada
    '.ac.ae',  # UAE
    '.ac.sg',  # Singapore
    '.ac.kr',  # South Korea
    '.ac.cn',  # China
    '.ac.ir',  # Iran
    '.ac.il',  # Israel
    '.ac.th',  # Thailand
    '.ac.id',  # Indonesia
    '.ac.my',  # Malaysia
    '.ac.ph',  # Philippines
    '.ac.bd',  # Bangladesh
    '.ac.lk',  # Sri Lanka
    '.ac.ma',  # Morocco
    '.ac.eg',  # Egypt
    '.ac.ke',  # Kenya
    '.ac.ug',  # Uganda
    '.ac.tz',  # Tanzania
    '.ac.gh',  # Ghana
    '.ac.ng',  # Nigeria
    '.ac.zw',  # Zimbabwe
    '.ac.za',  # South Africa
    '.ac.br',  # Brazil
    '.ac.mx',  # Mexico
    '.ac.ar',  # Argentina
    '.ac.cl',  # Chile
    '.ac.co',  # Colombia
    '.ac.pe',  # Peru
    '.ac.ec',  # Ecuador
    '.ac.ve',  # Venezuela
    '.ac.cr',  # Costa Rica
    '.ac.pa',  # Panama
    '.ac.gt',  # Guatemala
    '.ac.hn',  # Honduras
    '.ac.ni',  # Nicaragua
    '.ac.sv',  # El Salvador
    '.ac.bo',  # Bolivia
    '.ac.py',  # Paraguay
    '.ac.uy',  # Uruguay
    '.ac.do',  # Dominican Republic
    '.ac.cu',  # Cuba
    '.ac.jm',  # Jamaica
    '.ac.tt',  # Trinidad and Tobago
    '.ac.bz',  # Belize
    '.ac.gy',  # Guyana
    '.ac.sr',  # Suriname
    '.ac.fj',  # Fiji
    '.ac.nz',  # New Zealand
    '.ac.pg',  # Papua New Guinea
    '.ac.ws',  # Samoa
    '.ac.to',  # Tonga
    '.ac.vu',  # Vanuatu
    '.ac.sb',  # Solomon Islands
    '.ac.kh',  # Cambodia
    '.ac.la',  # Laos
    '.ac.mm',  # Myanmar
    '.ac.vn',  # Vietnam
    '.ac.kz',  # Kazakhstan
    '.ac.uz',  # Uzbekistan
    '.ac.am',  # Armenia
    '.ac.az',  # Azerbaijan
    '.ac.ge',  # Georgia
    '.ac.by',  # Belarus
    '.ac.md',  # Moldova
    '.ac.ua',  # Ukraine
    '.ac.ru',  # Russia
    '.ac.pl',  # Poland
    '.ac.cz',  # Czech Republic
    '.ac.sk',  # Slovakia
    '.ac.hu',  # Hungary
    '.ac.ro',  # Romania
    '.ac.bg',  # Bulgaria
    '.ac.rs',  # Serbia
    '.ac.hr',  # Croatia
    '.ac.si',  # Slovenia
    '.ac.ba',  # Bosnia and Herzegovina
    '.ac.mk',  # North Macedonia
    '.ac.al',  # Albania
    '.ac.me',  # Montenegro
    '.ac.ee',  # Estonia
    '.ac.lv',  # Latvia
    '.ac.lt',  # Lithuania
    '.ac.fi',  # Finland
    '.ac.se',  # Sweden
    '.ac.no',  # Norway
    '.ac.dk',  # Denmark
    '.ac.is',  # Iceland
    '.ac.ie',  # Ireland
    '.ac.pt',  # Portugal
    '.ac.es',  # Spain
    '.ac.it',  # Italy
    '.ac.gr',  # Greece
    '.ac.cy',  # Cyprus
    '.ac.mt',  # Malta
    '.ac.lu',  # Luxembourg
    '.ac.be',  # Belgium
    '.ac.nl',  # Netherlands
    '.ac.de',  # Germany
    '.ac.at',  # Austria
    '.ac.ch',  # Switzerland
    '.ac.li',  # Liechtenstein
    '.ac.fr',  # France
    '.ac.mc',  # Monaco
    '.ac.ad',  # Andorra
    '.ac.sm',  # San Marino
    '.ac.va',  # Vatican City
    '.ac.tr',  # Turkey
    '.ac.iq',  # Iraq
    '.ac.sa',  # Saudi Arabia
    '.ac.ye',  # Yemen
    '.ac.om',  # Oman
    '.ac.qa',  # Qatar
    '.ac.bh',  # Bahrain
    '.ac.kw',  # Kuwait
    '.ac.jo',  # Jordan
    '.ac.lb',  # Lebanon
    '.ac.sy',  # Syria
    '.ac.ps',  # Palestine
    '.ac.il',  # Israel
    '.ac.cy',  # Cyprus
    '.ac.mt',  # Malta
    '.ac.lu',  # Luxembourg
    '.ac.be',  # Belgium
    '.ac.nl',  # Netherlands
    '.ac.de',  # Germany
    '.ac.at',  # Austria
    '.ac.ch',  # Switzerland
    '.ac.li',  # Liechtenstein
    '.ac.fr',  # France
    '.ac.mc',  # Monaco
    '.ac.ad',  # Andorra
    '.ac.sm',  # San Marino
    '.ac.va',  # Vatican City
    '.ac.tr',  # Turkey
    '.ac.iq',  # Iraq
    '.ac.sa',  # Saudi Arabia
    '.ac.ye',  # Yemen
    '.ac.om',  # Oman
    '.ac.qa',  # Qatar
    '.ac.bh',  # Bahrain
    '.ac.kw',  # Kuwait
    '.ac.jo',  # Jordan
    '.ac.lb',  # Lebanon
    '.ac.sy',  # Syria
    '.ac.ps',  # Palestine
}

# Additional recognized educational keywords in domain names
EDUCATIONAL_KEYWORDS = [
    'university',
    'college',
    'school',
    'edu',
    'academic',
    'institute',
    'univ',
    'polytechnic',
    'academy',
]


def is_educational_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Check if an email address belongs to an educational institution.
    
    Returns:
        Tuple of (is_educational: bool, reason: Optional[str])
    """
    if not email or '@' not in email:
        return False, "Invalid email format"
    
    # Extract domain
    domain = email.lower().split('@')[1]
    
    # Check for plus signs (not allowed for student verification)
    if '+' in email.split('@')[0]:
        return False, "Email addresses with '+' signs are not accepted for student verification"
    
    # Check against known educational domains
    for edu_domain in EDUCATIONAL_DOMAINS:
        if domain.endswith(edu_domain):
            return True, f"Recognized educational domain: {edu_domain}"
    
    # Check for educational keywords in domain
    for keyword in EDUCATIONAL_KEYWORDS:
        if keyword in domain:
            # Additional validation: check if it's likely educational
            # This is a heuristic - may need manual review
            return True, f"Domain contains educational keyword: {keyword} (may require manual verification)"
    
    return False, "Domain not recognized as educational. Please upload documentation instead."


def validate_student_age(date_of_birth) -> Tuple[bool, Optional[str]]:
    """
    Validate that the student is at least 13 years old.
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    from datetime import date
    
    if not date_of_birth:
        return False, "Date of birth is required"
    
    today = date.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )
    
    if age < 13:
        return False, f"Student must be at least 13 years old. Current age: {age}"
    
    return True, None


def extract_ip_address(request) -> Optional[str]:
    """Extract IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def extract_user_agent(request) -> Optional[str]:
    """Extract user agent from request."""
    return request.META.get('HTTP_USER_AGENT', '')
