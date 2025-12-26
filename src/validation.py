def validate_zuvp_data(extracted_data):
    """Validate extracted ZUVP data and return validation results"""
    # Field order for consistent display
    field_order = ['Žadatel', 'IČO', 'Kontaktní údaje', 'Účel užívání', 'Místo', 'Doba užívání', 'Plocha']
    
    # Required fields mapping
    required_fields = {
        'applicant_name': 'Žadatel',
        'purpose_of_use': 'Účel užívání', 
        'location': 'Místo',
        'specific_location': 'Místo',
        'duration': 'Doba užívání',
        'area_square_meters': 'Plocha'
    }
    
    # Optional fields mapping
    optional_fields = {
        'company_id': 'IČO',
        'contact_details': 'Kontaktní údaje'
    }
    
    missing_required = []
    missing_optional = []
    found_data = {}
    
    # Always check fields even if there are errors
    if not extracted_data:
        extracted_data = {}
    
    # Check required fields
    required_found = set()
    for field_key, field_name in required_fields.items():
        if field_name in required_found:
            continue
        value = extracted_data.get(field_key)
        # Also check alternative field names
        if not value and field_key == 'area_square_meters':
            value = extracted_data.get('area_sqm') or extracted_data.get('area') or extracted_data.get('area_in_square_meters')
        elif not value and field_key == 'purpose_of_use':
            value = extracted_data.get('purpose')
        elif not value and field_key == 'duration':
            value = extracted_data.get('duration') or extracted_data.get('duration_dates')
        if value and str(value).strip() and str(value).strip().lower() not in ['n/a', 'none', 'null']:
            found_data[field_name] = value
            required_found.add(field_name)
    
    # Check which required fields are missing
    all_required = set(required_fields.values())
    missing_required_set = all_required - required_found
    
    # Check optional fields
    optional_found = set()
    for field_key, field_name in optional_fields.items():
        if field_name in optional_found:
            continue
        value = extracted_data.get(field_key)
        if value and str(value).strip() and str(value).strip().lower() not in ['n/a', 'none', 'null']:
            found_data[field_name] = value
            optional_found.add(field_name)
    
    # Check which optional fields are missing
    all_optional = set(optional_fields.values())
    missing_optional_set = all_optional - optional_found
    
    # Order fields according to specified order
    missing_required = [field for field in field_order if field in missing_required_set]
    missing_optional = [field for field in field_order if field in missing_optional_set]
    
    # Determine validity
    is_valid = len(missing_required) == 0
    is_zuvp_document = len(found_data) > 0
    
    error_message = None
    if not is_zuvp_document:
        error_message = 'Dokument neobsahuje rozpoznatelné ZUVP údaje. Zkontrolujte, zda jste nahráli správný formulář žádosti.'
    elif not is_valid:
        error_message = f'Chybí povinné údaje: {", ".join(missing_required)}. Zkontrolujte dokument a doplňte chybějící informace.'
    elif missing_optional:
        error_message = f'Upozornění - chybí volitelné údaje: {", ".join(missing_optional)}. Dokument lze zpracovat, ale doporučujeme doplnit tyto informace.'
    
    return {
        'is_valid': is_valid,
        'is_zuvp_document': is_zuvp_document,
        'missing_required': missing_required,
        'missing_optional': missing_optional,
        'found_data': found_data,
        'error_message': error_message
    }