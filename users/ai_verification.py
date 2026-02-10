"""
AI-powered student verification service.
Uses AI to automatically verify student documents and email addresses.
"""
import os
import re
from typing import Dict, Tuple, Optional
from django.conf import settings

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class StudentVerificationAI:
    """AI service for verifying student documents and information."""
    
    def __init__(self):
        self.openai_client = None
        if OPENAI_AVAILABLE and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            # Support both old and new OpenAI API versions
            try:
                # Try new API format (openai >= 1.0.0)
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                # Fall back to old API format
                openai.api_key = settings.OPENAI_API_KEY
                self.openai_client = openai
    
    def verify_email_domain(self, email: str, school_name: Optional[str] = None) -> Tuple[bool, float, str, list]:
        """
        Verify if an email domain is legitimate for student verification.
        
        Returns:
            Tuple of (is_valid: bool, confidence: float, reason: str, error_messages: list)
        """
        error_messages = []
        
        if not email or '@' not in email:
            error_messages.append("Invalid email format. Please provide a valid email address.")
            return False, 0.0, "Invalid email format", error_messages
        
        domain = email.lower().split('@')[1]
        
        # Check for plus signs (not allowed)
        if '+' in email.split('@')[0]:
            error_messages.append("Email addresses with '+' signs are not accepted for student verification. Please use your primary school email address.")
            return False, 0.0, "Email addresses with '+' signs are not accepted", error_messages
        
        # Check against known educational domains
        from users.student_verification_utils import EDUCATIONAL_DOMAINS, EDUCATIONAL_KEYWORDS
        
        # High confidence for known .edu domains
        for edu_domain in EDUCATIONAL_DOMAINS:
            if domain.endswith(edu_domain):
                return True, 0.95, f"Recognized educational domain: {edu_domain}", []
        
        # Medium confidence for educational keywords
        for keyword in EDUCATIONAL_KEYWORDS:
            if keyword in domain:
                return True, 0.75, f"Domain contains educational keyword: {keyword}", []
        
        # Use AI to verify if domain looks educational
        if self.openai_client and school_name:
            return self._ai_verify_email_domain(email, domain, school_name)
        
        error_messages.append(f"The email domain '{domain}' is not recognized as an educational institution. Please use your school-issued email address or upload a verification document instead.")
        if school_name:
            error_messages.append(f"The email domain does not appear to match the school '{school_name}'. Please verify your email address is correct.")
        
        return False, 0.0, "Domain not recognized as educational", error_messages
    
    def _ai_verify_email_domain(self, email: str, domain: str, school_name: str) -> Tuple[bool, float, str, list]:
        """Use AI to verify if email domain matches school name."""
        error_messages = []
        try:
            prompt = f"""
            Verify if the email domain "{domain}" is likely associated with the educational institution "{school_name}".
            
            Consider:
            1. Common domain patterns for educational institutions
            2. Abbreviations and variations of the school name
            3. Whether the domain structure is typical for educational institutions
            
            Respond in JSON format:
            {{
                "is_valid": true/false,
                "confidence": 0.0-1.0,
                "reason": "explanation",
                "error_message": "specific error if invalid, or null if valid"
            }}
            """
            
            # Use OpenAI client (works with both old and new API versions)
            if hasattr(self.openai_client, 'chat'):
                # New API format (openai >= 1.0.0)
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert at verifying educational email domains. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                response_text = response.choices[0].message.content.strip()
            else:
                # Old API format (openai < 1.0.0)
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert at verifying educational email domains. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                response_text = response.choices[0].message.content.strip()
            
            import json
            ai_result = json.loads(response_text)
            
            is_valid = ai_result.get('is_valid', False)
            confidence = float(ai_result.get('confidence', 0.0))
            reason = ai_result.get('reason', '')
            error_msg = ai_result.get('error_message')
            
            if error_msg:
                error_messages.append(error_msg)
            
            if is_valid:
                return True, confidence, reason, []
            else:
                if not error_messages:
                    error_messages.append(f"The email domain '{domain}' does not appear to match the school '{school_name}'. Please verify your email address is correct or upload a verification document instead.")
                return False, confidence, reason, error_messages
        
        except Exception as e:
            error_messages.append(f"Unable to verify email domain. Please try uploading a verification document instead.")
            return False, 0.0, f"AI verification error: {str(e)}", error_messages
    
    def verify_document(self, document_path: str, document_type: str, 
                       full_name: str, school_name: Optional[str] = None) -> Dict:
        """
        Verify a student document using AI and OCR.
        
        Returns:
            Dict with keys: is_valid, confidence, reason, extracted_info
        """
        result = {
            'is_valid': False,
            'confidence': 0.0,
            'reason': '',
            'extracted_info': {},
            'requires_manual_review': True
        }
        
        # Extract text from document using OCR
        extracted_text = self._extract_text_from_image(document_path)
        
        if not extracted_text:
            result['reason'] = "Could not extract text from document"
            return result
        
        # Use AI to analyze the document
        if self.openai_client:
            return self._ai_analyze_document(extracted_text, document_type, full_name, school_name)
        
        # Fallback: Basic text matching
        return self._basic_document_verification(extracted_text, document_type, full_name, school_name)
    
    def _extract_text_from_image(self, image_path: str) -> Optional[str]:
        """Extract text from image using OCR."""
        if not OCR_AVAILABLE:
            return None
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return None
    
    def _ai_analyze_document(self, extracted_text: str, document_type: str,
                            full_name: str, school_name: Optional[str] = None) -> Dict:
        """Use AI to analyze and verify document content."""
        try:
            prompt = f"""
            Analyze this student verification document and verify its authenticity.
            
            Document Type: {document_type}
            Expected Name: {full_name}
            School Name: {school_name or 'Not provided'}
            
            Document Text:
            {extracted_text[:2000]}  # Limit text length
            
            Verify:
            1. Does the document contain the expected name "{full_name}"? If not, what name is on the document?
            2. Does it show current enrollment or valid dates? Check for expiration dates, enrollment dates, or graduation dates.
            3. Is it a legitimate {document_type}? Does it look authentic?
            4. Does it match the school "{school_name}" if provided? What school name appears on the document?
            
            Respond in JSON format with detailed error messages:
            {{
                "is_valid": true/false,
                "confidence": 0.0-1.0,
                "name_match": true/false,
                "name_on_document": "actual name found on document or null",
                "enrollment_status": "current"/"expired"/"unknown",
                "expiration_date": "date found or null",
                "document_authenticity": "legitimate"/"suspicious"/"unknown",
                "school_match": true/false,
                "school_on_document": "school name found on document or null",
                "errors": ["list of specific error messages if invalid"],
                "warnings": ["list of warnings if any"],
                "reason": "detailed explanation of verification result"
            }}
            
            If invalid, provide specific error messages in the "errors" array explaining exactly what is wrong:
            - "The name on the document does not match. Expected: [name], Found: [name]"
            - "The document appears to be expired. Expiration date: [date]"
            - "The school name on the document does not match. Expected: [school], Found: [school]"
            - "The document does not appear to be a valid {document_type}"
            - "The document appears to be altered or suspicious"
            - etc.
            """
            
            # Use OpenAI client (works with both old and new API versions)
            if hasattr(self.openai_client, 'chat'):
                # New API format (openai >= 1.0.0)
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",  # Use GPT-4 for better analysis
                    messages=[
                        {"role": "system", "content": "You are an expert at verifying student documents. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.2
                )
                response_text = response.choices[0].message.content.strip()
            else:
                # Old API format (openai < 1.0.0)
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-4",  # Use GPT-4 for better analysis
                    messages=[
                        {"role": "system", "content": "You are an expert at verifying student documents. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.2
                )
                response_text = response.choices[0].message.content.strip()
            
            import json
            ai_result = json.loads(response_text)
            
            # Build detailed error message
            error_messages = []
            if not ai_result.get('is_valid', False):
                errors = ai_result.get('errors', [])
                if errors:
                    error_messages = errors
                else:
                    # Fallback error message
                    error_messages = [ai_result.get('reason', 'Document verification failed')]
            
            warnings = ai_result.get('warnings', [])
            
            return {
                'is_valid': ai_result.get('is_valid', False),
                'confidence': float(ai_result.get('confidence', 0.0)),
                'reason': ai_result.get('reason', 'AI analysis completed'),
                'error_messages': error_messages,
                'warnings': warnings,
                'extracted_info': {
                    'name_match': ai_result.get('name_match', False),
                    'name_on_document': ai_result.get('name_on_document'),
                    'enrollment_status': ai_result.get('enrollment_status', 'unknown'),
                    'expiration_date': ai_result.get('expiration_date'),
                    'document_authenticity': ai_result.get('document_authenticity', 'unknown'),
                    'school_match': ai_result.get('school_match', False),
                    'school_on_document': ai_result.get('school_on_document'),
                },
                'requires_manual_review': ai_result.get('confidence', 0.0) < 0.8
            }
        
        except Exception as e:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'reason': f'AI analysis error: {str(e)}',
                'extracted_info': {},
                'requires_manual_review': True
            }
    
    def _basic_document_verification(self, extracted_text: str, document_type: str,
                                    full_name: str, school_name: Optional[str] = None) -> Dict:
        """Basic text matching verification without AI."""
        text_lower = extracted_text.lower()
        name_lower = full_name.lower()
        
        # Check if name appears in document
        name_match = name_lower in text_lower or any(
            part in text_lower for part in name_lower.split() if len(part) > 2
        )
        
        # Check for date patterns (enrollment dates, expiry dates)
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        has_dates = bool(re.search(date_pattern, extracted_text))
        
        # Check for school name if provided
        school_match = False
        if school_name:
            school_match = school_name.lower() in text_lower
        
        # Calculate confidence
        confidence = 0.0
        if name_match:
            confidence += 0.4
        if has_dates:
            confidence += 0.3
        if school_match:
            confidence += 0.3
        
        is_valid = confidence >= 0.6
        
        # Generate error messages
        error_messages = []
        if not is_valid:
            if not name_match:
                error_messages.append(f"The name on the document does not match. Expected: {full_name}")
            if not has_dates:
                error_messages.append("The document does not contain valid dates (enrollment, expiration, or graduation dates)")
            if school_name and not school_match:
                error_messages.append(f"The school name on the document does not match. Expected: {school_name}")
        
        return {
            'is_valid': is_valid,
            'confidence': confidence,
            'reason': f"Basic verification: name_match={name_match}, dates={has_dates}, school_match={school_match}",
            'error_messages': error_messages,
            'warnings': [],
            'extracted_info': {
                'name_match': name_match,
                'has_dates': has_dates,
                'school_match': school_match
            },
            'requires_manual_review': confidence < 0.8
        }
    
    def _validate_dates(self, enrollment_date, graduation_date) -> list:
        """Validate enrollment and graduation dates."""
        errors = []
        from datetime import date
        
        if graduation_date:
            # Check for obviously invalid years (like 0024 instead of 2024)
            if graduation_date.year < 1900 or graduation_date.year > 2100:
                errors.append(
                    f"Invalid graduation year: {graduation_date.year}. "
                    f"Please check the date format (should be YYYY-MM-DD, e.g., 2024-12-31)."
                )
            else:
                today = date.today()
                # Graduation should be in the future (or very recent past)
                if graduation_date.year < today.year - 2:
                    errors.append(
                        f"Graduation date {graduation_date.year} is more than 2 years in the past. "
                        f"If you have already graduated, please contact support."
                    )
                elif graduation_date.year > today.year + 10:
                    errors.append(
                        f"Graduation date {graduation_date.year} is too far in the future. Please check the date."
                    )
        
        if enrollment_date:
            today = date.today()
            # Check for obviously invalid years
            if enrollment_date.year < 1900 or enrollment_date.year > 2100:
                errors.append(
                    f"Invalid enrollment year: {enrollment_date.year}. "
                    f"Please check the date format (should be YYYY-MM-DD)."
                )
            else:
                # Enrollment should not be too far in the past or future
                if enrollment_date.year < today.year - 10:
                    errors.append(
                        f"Enrollment date {enrollment_date.year} is too far in the past. Please check the date."
                    )
                elif enrollment_date.year > today.year + 1:
                    errors.append(
                        f"Enrollment date {enrollment_date.year} is in the future. Please check the date."
                    )
        
        # Check date relationship
        if enrollment_date and graduation_date:
            if graduation_date < enrollment_date:
                errors.append(
                    "Graduation date must be after enrollment date. Please check your dates."
                )
        
        return errors
    
    def _check_all_requirements(self, verification_data: Dict, verification_result: Dict) -> Dict:
        """
        Check if all requirements are fulfilled for immediate approval.
        Both email and document are now required.
        
        Returns:
            Dict with requirements status
        """
        requirements = {
            'age_valid': True,  # Age is validated in serializer
            'email_valid': False,
            'dates_valid': False,
            'document_valid': False,
            'name_match': False,
            'school_match': False,
            'all_met': False
        }
        
        # Check email requirements (REQUIRED)
        email_result = verification_result.get('verification_details', {}).get('email_verification', {})
        if email_result.get('is_valid'):
            requirements['email_valid'] = True
        
        # Check dates are valid
        enrollment_date = verification_data.get('enrollment_date')
        graduation_date = verification_data.get('graduation_date')
        date_errors = self._validate_dates(enrollment_date, graduation_date)
        if not date_errors:
            requirements['dates_valid'] = True
        
        # Check document requirements (REQUIRED)
        doc_result = verification_result.get('verification_details', {}).get('document_verification', {})
        extracted_info = doc_result.get('extracted_info', {})
        
        if doc_result.get('is_valid'):
            requirements['document_valid'] = True
        
        # Name matches
        if extracted_info.get('name_match'):
            requirements['name_match'] = True
        
        # School matches (if provided)
        school_name = verification_data.get('school_name')
        if not school_name or extracted_info.get('school_match', True):
            requirements['school_match'] = True
        
        # All requirements met (BOTH email AND document must be valid)
        requirements['all_met'] = (
            requirements['email_valid'] and
            requirements['document_valid'] and
            requirements['dates_valid'] and
            requirements['name_match'] and
            requirements['school_match'] and
            len(verification_result.get('error_messages', [])) == 0  # No errors
        )
        
        return requirements
    
    def auto_verify_submission(self, verification_data: Dict) -> Dict:
        """
        Automatically verify a student verification submission.
        Both email and document are now REQUIRED for verification.
        
        Args:
            verification_data: Dict containing verification information
        
        Returns:
            Dict with verification result and recommendation
        """
        result = {
            'auto_approved': False,
            'auto_rejected': False,
            'confidence': 0.0,
            'reason': '',
            'error_messages': [],
            'warnings': [],
            'requires_manual_review': True,
            'verification_details': {}
        }
        
        # Both email and document are now required - verify both
        email = verification_data.get('school_email')
        document_path = verification_data.get('document_file')
        school_name = verification_data.get('school_name')
        enrollment_date = verification_data.get('enrollment_date')
        graduation_date = verification_data.get('graduation_date')
        document_type = verification_data.get('document_type')
        full_name_on_document = verification_data.get('full_name_on_document', '')
        
        # Verify email (REQUIRED)
        email_valid = False
        email_confidence = 0.0
        email_reason = ''
        email_errors = []
        
        if email:
            email_valid, email_confidence, email_reason, email_errors = self.verify_email_domain(email, school_name)
            
            # Validate dates
            date_errors = self._validate_dates(enrollment_date, graduation_date)
            if date_errors:
                email_errors.extend(date_errors)
                email_valid = False
                email_confidence = min(email_confidence, 0.5)
        else:
            email_errors.append("School email is required for verification.")
        
        result['verification_details']['email_verification'] = {
            'is_valid': email_valid,
            'confidence': email_confidence,
            'reason': email_reason,
            'error_messages': email_errors
        }
        
        # Verify document (REQUIRED)
        document_valid = False
        document_confidence = 0.0
        document_reason = ''
        document_errors = []
        document_warnings = []
        
        if document_path and hasattr(document_path, 'path'):
            document_result = self.verify_document(
                document_path.path,
                document_type,
                full_name_on_document,
                school_name
            )
            document_valid = document_result['is_valid']
            document_confidence = document_result['confidence']
            document_reason = document_result['reason']
            document_errors = document_result.get('error_messages', [])
            document_warnings = document_result.get('warnings', [])
            result['verification_details']['document_verification'] = document_result
        else:
            document_errors.append("Document file is required for verification.")
        
        # Combine results
        result['error_messages'] = email_errors + document_errors
        result['warnings'] = document_warnings
        result['confidence'] = (email_confidence + document_confidence) / 2 if (email_confidence > 0 and document_confidence > 0) else max(email_confidence, document_confidence)
        
        # Both must be valid for approval
        both_valid = email_valid and document_valid
        has_errors = len(result['error_messages']) > 0
        
        # Check all requirements comprehensively
        all_reqs = self._check_all_requirements(verification_data, result)
        
        if both_valid and all_reqs['all_met'] and not has_errors:
            # Both email and document are valid - immediate approval
            result['auto_approved'] = True
            result['requires_manual_review'] = False
            result['confidence'] = max(result['confidence'], 0.9)  # High confidence when both are valid
            result['reason'] = f"✅ All requirements fulfilled! Both email and document verified successfully. Verification complete."
        elif has_errors or not both_valid:
            # Reject if either email or document is invalid
            result['auto_rejected'] = True
            result['requires_manual_review'] = False
            if result['error_messages']:
                result['reason'] = "; ".join(result['error_messages'])
            else:
                result['reason'] = "Verification failed. Both email and document must be valid."
        else:
            # Edge case - approve but flag for review
            result['auto_approved'] = True
            result['requires_manual_review'] = True
            result['reason'] = f"Auto-approved with review flag: Email and document verified but requires manual review."
        
        return result
