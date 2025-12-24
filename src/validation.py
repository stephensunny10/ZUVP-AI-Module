def validate_zuvp_data(extracted_data):
    """Validate extracted ZUVP data and return validation results"""
    # Field mappings - both old and new formats
    required_fields = {
        'Applicant name': 'Jméno žadatele',
        'applicant_name': 'Jméno žadatele',
        'Purpose of use': 'Účel užívání', 
        'purpose_of_use': 'Účel užívání',
        'Location': 'Místo/lokace',
        'location': 'Místo/lokace',
        'specific_location': 'Místo/lokace'
    }
    
    optional_fields = {
        'Company ID (IČO)': 'IČO',
        'company_id': 'IČO',
        'Contact details': 'Kontaktní údaje',
        'contact_details': 'Kontaktní údaje',
        'Duration (dates)': 'Doba užívání',
        'duration': 'Doba užívání',
        'Area in square meters': 'Výměra',
        'area_in_square_meters': 'Výměra'
    }
    
    missing_required = []
    missing_optional = []
    found_data = {}
    
    # Check if data is completely empty or invalid
    if not extracted_data or extracted_data.get('error'):
        return {
            'is_valid': False,
            'is_zuvp_document': False,
            'missing_required': ['Jméno žadatele', 'Účel užívání', 'Místo/lokace'],
            'missing_optional': ['IČO', 'Kontaktní údaje', 'Doba užívání', 'Výměra'],
            'found_data': {},
            'error_message': 'Dokument neobsahuje žádné rozpoznatelné ZUVP údaje.'
        }
    
    # Check for raw response indicating wrong document type
    if 'raw_response' in extracted_data:
        raw_text = extracted_data['raw_response'].lower()
        if 'not a zuvp' in raw_text or 'není zuvp' in raw_text:
            return {
                'is_valid': False,
                'is_zuvp_document': False,
                'missing_required': ['Jméno žadatele', 'Účel užívání', 'Místo/lokace'],
                'missing_optional': ['IČO', 'Kontaktní údaje', 'Doba užívání', 'Výměra'],
                'found_data': {},
                'error_message': 'Nahraný dokument není ZUVP žádost. Nahrajte prosím správný formulář žádosti o zvláštní užívání veřejného prostranství.'
            }
    
    # Check required fields
    required_found = set()
    for field_key, field_name in required_fields.items():
        if field_name in required_found:
            continue  # Skip duplicates
        value = extracted_data.get(field_key)
        if value and (not isinstance(value, str) or value.strip()):
            found_data[field_name] = value
            required_found.add(field_name)
    
    # Check which required fields are missing
    all_required = {'Jméno žadatele', 'Účel užívání', 'Místo/lokace'}
    missing_required = list(all_required - required_found)
    
    # Check optional fields
    optional_found = set()
    for field_key, field_name in optional_fields.items():
        if field_name in optional_found:
            continue  # Skip duplicates
        value = extracted_data.get(field_key)
        if value and (not isinstance(value, str) or value.strip()):
            found_data[field_name] = value
            optional_found.add(field_name)
    
    # Check which optional fields are missing
    all_optional = {'IČO', 'Kontaktní údaje', 'Doba užívání', 'Výměra'}
    missing_optional = list(all_optional - optional_found)
    
    # Determine if document is valid
    is_valid = len(missing_required) == 0
    is_zuvp_document = len(found_data) > 0
    
    error_message = None
    if not is_zuvp_document:
        error_message = 'Dokument neobsahuje rozpoznatelné ZUVP údaje. Zkontrolujte, zda jste nahráli správný formulář.'
    elif not is_valid:
        error_message = f'Chybí povinné údaje: {", ".join(missing_required)}'
    
    return {
        'is_valid': is_valid,
        'is_zuvp_document': is_zuvp_document,
        'missing_required': missing_required,
        'missing_optional': missing_optional,
        'found_data': found_data,
        'error_message': error_message
    }