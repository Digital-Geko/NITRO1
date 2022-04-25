# We need to import a library to implement SHA256 algorithms, since this is the standard hash for SILA
import hashlib
# We need to import a library to .... ???
import os
# We need to import a library to .... ???
import uuid
# Of course, we need to import the SILA SDK
import silasdk
from src.exceptions import SilaError

# Configure Sila client with values saved in environment variables
# SILA_TIER holds the value to ???
# SILA_PRIVATE_KEY holds the value to ???
# SILA_APP_HANDLE holds the value to ???
sila_app = silasdk.App(os.getenv('SILA_TIER'), os.getenv('SILA_PRIVATE_KEY'), os.getenv('SILA_APP_HANDLE'))

# Since this is the backend, the front end may gather this information and present it to the backend
# Some of these parameters are basic data, but some require clarification
# nickname is the ... ???
# private key is the ... ???
# kyc_attempts is the ... ???
def request_kyc(
        ssn: str,
        first_name: str,
        last_name: str,
        birthdate: str,
        phone: str,
        street_address: str,
        city: str,
        state: str,
        postal_code: str,
        country: str,
        nickname: str,
        private_key: str,
        kyc_attempts: int
):
    """Request KYC verification for individuals."""

    # Get user's information from Sila and the basic parameter to send initially is the user_handle
    payload = {
        'user_handle': nickname
    }

    #Call SILA SDK using a User Entity, and the response is a message that validates the that the user handle exists with its private key
    response_uuid = silasdk.User.get_entity(sila_app, payload, private_key)
    if not response_uuid['success']:
        raise_sila_error(response_uuid)

    # if SILA response is a success, we need to save or update SSN
    # so we will make another SILA SDK call sending the SSN that was sent by the FrontEnd
        
    payload = {
        'user_handle': nickname,
        'identity_alias': 'SSN',
        'identity_value': ssn
    }
    
    # first KYC attempt needs a different treatment from further attempts
    if kyc_attempts <= 1:
        # Save SSN if it's the first time requesting KYC
        response = silasdk.User.add_registration_data(sila_app, silasdk.RegistrationFields.IDENTITY, payload,
                                                      private_key)
        if not response['success']:
            raise_sila_error(response)
    else:
        # Add uuid of the previously saved SSN to the payload
        payload['uuid'] = response_uuid['identities'][0]['uuid']
        # Update SSN if it's not the first time requesting KYC
        response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.IDENTITY, payload,
                                                         private_key)
        if not response['success']:
            raise_sila_error(response)

    # Save or update address
    payload = {
        'user_handle': nickname,
        'street_address_1': street_address,
        'city': city,
        'state': state,
        'postal_code': postal_code,
        'country': country
    }
    if kyc_attempts <= 1:
        # Save address if it's the first time requesting KYC
        response = silasdk.User.add_registration_data(sila_app, silasdk.RegistrationFields.ADDRESS, payload,
                                                      private_key)
        if not response['success']:
            raise_sila_error(response)
    else:
        # Add uuid of the previously saved address to the payload
        payload['uuid'] = response_uuid['addresses'][0]['uuid']
        # Update address if it's not the first time requesting KYC
        response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.ADDRESS, payload,
                                                         private_key)
        if not response['success']:
            raise_sila_error(response)

    # Update full name and birthdate
    payload = {
        'user_handle': nickname,
        'first_name': first_name,
        'last_name': last_name,
        'birthdate': birthdate
    }
    # This information is always updated because is always saved when the user registers in Sila
    response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.ENTITY, payload, private_key)
    if not response['success']:
        raise_sila_error(response)

    # Update phone number
    payload = {
        'user_handle': nickname,
        'phone': phone,
        'uuid': response_uuid['phones'][0]['uuid']
    }
    # This information is always updated because is always saved when the user registers in Sila
    response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.PHONE, payload, private_key)
    if not response['success']:
        raise_sila_error(response)

    payload = {'user_handle': nickname, 'kyc_level': 'DOC_KYC'}
    # After all the user's information is updated in Sila, proceed to request KYC approval under DOC_KYC level
    response = silasdk.User.requestKyc(sila_app, payload, private_key)
    if not response['success']:
        raise_sila_error(response)


def request_kyb(
        ein: str,
        email: str,
        phone: str,
        street_address: str,
        city: str,
        state: str,
        postal_code: str,
        country: str,
        nickname: str,
        private_key: str,
        kyb_attempts: int
):
    """Request KYB verification for business."""

    # Get business's information from Sila
    payload = {
        'user_handle': nickname
    }
    response_uuid = silasdk.User.get_entity(sila_app, payload, private_key)
    if not response_uuid['success']:
        raise_sila_error(response_uuid)

    # Save or update email
    payload = {
        'user_handle': nickname,
        'email': email,
    }
    if kyb_attempts == 1:
        # Save email if it's the first time requesting KYB
        response = silasdk.User.add_registration_data(sila_app, silasdk.RegistrationFields.EMAIL, payload,
                                                      private_key)
    else:
        # Add uuid of the previously saved email to the payload
        payload['uuid'] = response_uuid['emails'][0]['uuid']
        # Update email if it's not the first time requesting KYB
        response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.EMAIL, payload,
                                                         private_key)

    if not response['success']:
        raise_sila_error(response)

    # Save or update phone number
    payload = {
        'user_handle': nickname,
        'phone': phone
    }
    if kyb_attempts == 1:
        # Save phone number if it's the first time requesting KYB
        response = silasdk.User.add_registration_data(sila_app, silasdk.RegistrationFields.PHONE, payload, private_key)
    else:
        # Add uuid of the previously saved phone number to the payload
        payload['uuid'] = response_uuid['phones'][0]['uuid']
        # Update phone number if it's not the first time requesting KYB
        response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.PHONE, payload,
                                                         private_key)

    if not response['success']:
        raise_sila_error(response)

    # Save or update EIN
    payload = {
        'user_handle': nickname,
        'identity_alias': 'EIN',
        'identity_value': ein
    }
    if kyb_attempts == 1:
        # Save EIN if it's the first time requesting KYB
        response = silasdk.User.add_registration_data(sila_app, silasdk.RegistrationFields.IDENTITY, payload,
                                                      private_key)
    else:
        # Add uuid of the previously saved EIN to the payload
        payload['uuid'] = response_uuid['identities'][0]['uuid']
        # Update EIN if it's not the first time requesting KYB
        response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.IDENTITY, payload,
                                                         private_key)

    if not response['success']:
        raise_sila_error(response)

    # Save or update address
    payload = {
        'user_handle': nickname,
        'address_alias': 'default',
        'street_address_1': street_address,
        'city': city,
        'state': state,
        'postal_code': postal_code,
        'country': country
    }
    if kyb_attempts == 1:
        # Save address if it's the first time requesting KYB
        response = silasdk.User.add_registration_data(sila_app, silasdk.RegistrationFields.ADDRESS, payload,
                                                      private_key)
    else:
        # Add uuid of the previously saved address to the payload
        payload['uuid'] = response_uuid['addresses'][0]['uuid']
        # Update address if it's not the first time requesting KYB
        response = silasdk.User.update_registration_data(sila_app, silasdk.RegistrationFields.ADDRESS, payload,
                                                         private_key)

    if not response['success']:
        raise_sila_error(response)

    # After all the business's information is updated in Sila, proceed to request KYB approval
    response = silasdk.User.requestKyc(sila_app, {'user_handle': nickname}, private_key)
    if not response['success']:
        raise_sila_error(response)


def upload_document(
        nickname: str,
        file_contents: bytes,
        mime_type: str,
        document_type: str,
        private_key: str
):
    """Send to Sila complementary documents for KYC/KYB."""

    # Generate a random file name
    file_name = str(uuid.uuid4())
    # Get document identity related to the type
    identity = get_document_identities(document_type)

    payload = {
        'user_handle': nickname,
        'filename': file_name,
        'hash': hashlib.sha256(file_contents).hexdigest(),
        'mime_type': mime_type,
        'document_type': document_type,
        'identity_type': identity
    }

    # Send the document to Sila
    response = silasdk.Documents.uploadDocument(sila_app, payload, file_contents, private_key)
    if not response['success']:
        raise_sila_error(response)


def get_document_identities(document_type):
    """Map Sila's document identities with document types."""

    identities = {
        'tax_1040': 'other',
        'vtl_birth_certificate': 'other',
        'doc_name_change': 'other',
        'vtl_divorce': 'other',
        'id_drivers_permit': 'license',
        'tax_w2': 'other',
        'doc_lease': 'contract',
        'vtl_marriage': 'other',
        'id_military_dependent': 'other',
        'id_military': 'other',
        'doc_mortgage': 'contract',
        'id_nyc_id': 'other',
        'other_doc': 'other',
        'other_id': 'other',
        'id_passport': 'passport',
        'doc_paystub': 'other',
        'doc_green_card': 'other',
        'doc_ssa': 'other',
        'doc_ss_card': 'other',
        'id_state': 'other',
        'id_drivers_license': 'license',
        'tax_1095': 'other',
        'tax_1099': 'other',
        'doc_tuition': 'other',
        'doc_uo_benefits': 'other',
        'id_passport_card': 'passport',
        'doc_utility': 'utility',
        'tax_W4': 'other',

    }
    return identities[document_type]


def raise_sila_error(response):
    """Parse and raise an exception if communication with Sila fails."""

    # Obtain error information
    message = response['validation_details'] if 'validation_details' in response else response['message']
    # Raise an exception with the error's information
    raise SilaError(message)
