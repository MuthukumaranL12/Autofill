/* global use, db */
// ==========================================================================
// MASTER DATABASE SETUP: medform_db (Updated for 7-Doc Gemini Pipeline)
// ==========================================================================
use('medform_db');

print('[1/6] Resetting and Initializing Collections...');
db.audit_logs.drop();
db.form_requests.drop();
db.form_templates.drop();
db.source_documents.drop();
db.patient_profiles.drop();
db.encryption_keys.drop();
db.users.drop();

function createValidatedCollection(name, schema) {
  print(`Creating collection with schema validator: ${name}`);
  db.createCollection(name, {
    validator: { $jsonSchema: schema },
    validationLevel: 'strict',
    validationAction: 'error',
  });
}

print('[2/6] Applying DPDP & UIDAI Compliant JSON Schema Validators...');

// 1. USERS
createValidatedCollection('users', {
  bsonType: 'object',
  required: ['password_hash', 'phone_hash' , 'role', 'consent_given', 'consent_timestamp', 'is_active', 'created_at', 'updated_at'],
  properties: {
    _id: { bsonType: 'objectId' },
    phone_hash: { bsonType: 'string', description: 'Deterministic HMAC/SHA256 for fast unique login lookup' },
    phone_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 for display/OTP verification' },
    email_hash: { bsonType: 'string' },
    email_enc: { bsonType: 'binData' },
    password_hash: { bsonType: 'string' },
    role: { enum: ['patient', 'staff', 'admin'] },
    consent_given: { bsonType: 'bool' },
    consent_timestamp: { bsonType: 'date' },
    is_active: { bsonType: 'bool' },
    failed_login_attempts: { bsonType: 'number' },
    last_login_at: { bsonType: ['date', 'null'] },
    created_at: { bsonType: 'date' },
    updated_at: { bsonType: 'date' }
  }
});

// 2. ENCRYPTION KEYS
createValidatedCollection('encryption_keys', {
  bsonType: 'object',
  required: ['key_alias', 'algorithm', 'status', 'created_at'],
  properties: {
    _id: { bsonType: 'objectId' },
    key_alias: { bsonType: 'string' },
    algorithm: { enum: ['AES-256-GCM'] },
    wrapped_dek: { bsonType: ['binData', 'null'] },
    kms_reference: { bsonType: ['string', 'null'] },
    status: { enum: ['active', 'rotated', 'revoked'] },
    created_at: { bsonType: 'date' },
    rotated_at: { bsonType: ['date', 'null'] },
    created_by: { bsonType: ['objectId', 'null'] }
  }
});

// 3. PATIENT PROFILES (Updated with all 7 document fields)
createValidatedCollection('patient_profiles', {
  bsonType: 'object',
  required: ['user_id', 'name_enc', 'dek_id', 'created_at', 'updated_at'],
  properties: {
    _id: { bsonType: 'objectId' },
    user_id: { bsonType: 'objectId' },
    // Encrypted PII Fields (Stored as AES-256-GCM BinData)
    name_enc: { bsonType: 'binData',description: 'Encrypted full/original name'},
    email_enc: { bsonType: 'binData' },
    phone_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 for display/OTP verification' },
    first_name_enc: {bsonType: ['binData', 'null'],description: 'Encrypted first/given name'},
    middle_name_enc: {bsonType: ['binData', 'null'],description: 'Encrypted middle name'},
    last_name_enc: {bsonType: ['binData', 'null'],description: 'Encrypted surname/family name'},
    dob_enc: { bsonType: ['binData', 'null'] },


    address_enc: {bsonType: ['binData', 'null'],description: 'Encrypted original complete address'},
    house_number_enc: {bsonType: ['binData', 'null'],description: 'Encrypted house/door/flat number'},
    street_enc: {bsonType: ['binData', 'null'],description: 'Encrypted street/road information'},
    locality_enc: {bsonType: ['binData', 'null'],description: 'Encrypted locality/neighborhood'},
    city_enc: {bsonType: ['binData', 'null'],description: 'Encrypted city/town'},
    state_enc: {bsonType: ['binData', 'null'],description: 'Encrypted state'},
    pincode_enc: {bsonType: ['binData', 'null'],description: 'Encrypted postal PIN code'},
    phone_enc: { bsonType: ['binData', 'null'] },
    guardian_name_enc: { bsonType: ['binData', 'null'], description: "Father/Husband/Relative/Mother/Spouse name" },
    place_of_birth_enc: { bsonType: ['binData', 'null'] },
    insurance_details_enc: { bsonType: ['binData', 'null'], description: "Encrypted JSON payload of health policy details" },

    aadhaar_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 Aadhaar for PDF overlay' },
    pan_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 PAN for PDF overlay' },
    driving_licence_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 DL for PDF overlay' },
    voter_id_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 Voter ID for PDF overlay' },
    passport_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 Passport for PDF overlay' },
    birth_reg_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 Birth Reg for PDF overlay' },
    health_insurance_enc: { bsonType: ['binData', 'null'], description: 'Reversible AES-256 Health Policy for PDF overlay' },
    // Non-sensitive metadata
    gender: { enum: ['MALE', 'FEMALE', 'OTHER', 'M', 'F', 'Other', 'Not specified', null] },
    blood_group: { bsonType: ['string', 'null'] },
    year_of_birth: { bsonType: ['string', 'number', 'null'] },
    nationality: { bsonType: ['string', 'null'] },
    // Tokenized Unique Identifiers (HMAC-SHA256)
    phone_hash: { bsonType: ['string', 'null'] },
    aadhaar_token: { bsonType: ['string', 'null'] },
    pan_token: { bsonType: ['string', 'null'] },
    voter_id_token: { bsonType: ['string', 'null'], description: "Tokenized EPIC Number" },
    passport_token: { bsonType: ['string', 'null'] },
    driving_licence_token: { bsonType: ['string', 'null'] },
    birth_reg_token: { bsonType: ['string', 'null'], description: "Birth Certificate Registration Number Token" },
    health_insurance_token: { bsonType: ['string', 'null'], description: "Policy / Member ID Token" },
    // File references
    signature_s3_key: { bsonType: ['string', 'null'] },
    photo_s3_key: { bsonType: ['string', 'null'] },
    dek_id: { bsonType: 'objectId' },
    created_at: { bsonType: 'date' },
    updated_at: { bsonType: 'date' }
  }
});

// 4. SOURCE DOCUMENTS (Supports all 7 canonical document types from Gemini)
createValidatedCollection('source_documents', {
  bsonType: 'object',
  required: ['user_id', 'profile_id', 'doc_type', 'source', 's3_key_enc', 'ocr_status', 'uploaded_at'],
  properties: {
    _id: { bsonType: 'objectId' },
    user_id: { bsonType: 'objectId' },
    profile_id: { bsonType: 'objectId' },
    doc_type: {
      enum: [
        'aadhaar',
        'pan_card',
        'passport',
        'driving_licence',
        'voter_id',
        'birth_certificate',
        'health_insurance_card',
        'form_scan',
        'other'
      ]
    },
    source: { enum: ['gemini', 'textract', 'manual'] },
    s3_key_enc: { bsonType: 'string' },
    ocr_status: { enum: ['pending', 'processing', 'success', 'failed'] },
    confidence_score: { bsonType: ['number', 'null'] },
    manual_review_required: { bsonType: ['bool', 'null'] },
    manual_verified_by: { bsonType: ['objectId', 'null'] },
    gemini_raw_response: { bsonType: ['object', 'null'] },
    textract_raw_response: { bsonType: ['object', 'null'] },
    extracted_fields_snapshot: { bsonType: ['object', 'null'] },
    uploaded_at: { bsonType: 'date' },
    processed_at: { bsonType: ['date', 'null'] }
  }
});

// 5. FORM TEMPLATES
createValidatedCollection('form_templates', {
  bsonType: 'object',
  required: ['template_name', 'category', 'version', 'is_active', 'page_count', 'field_map', 'created_by', 'created_at', 'updated_at'],
  properties: {
    _id: { bsonType: 'objectId' },
    template_name: { bsonType: 'string' },
    category: { enum: ['government', 'insurance', 'hospital', 'diagnostic_lab'] },
    version: { bsonType: 'string' },
    is_active: { bsonType: 'bool' },
    page_count: { bsonType: 'number' },
    field_map: {
      bsonType: 'array',
      minItems: 1,
      items: {
        bsonType: 'object',
        required: ['field_name', 'page_number', 'x', 'y', 'width', 'height', 'data_key'],
        properties: {
          field_name: { bsonType: 'string' },
          page_number: { bsonType: 'number' },
          x: { bsonType: 'number' },
          y: { bsonType: 'number' },
          width: { bsonType: 'number' },
          height: { bsonType: 'number' },
          font_size: { bsonType: ['number', 'null'] },
          data_key: { bsonType: 'string' },
          field_type: { enum: ['text', 'checkbox', 'signature', 'photo', null] }
        }
      }
    },
    thumbnail_s3_key: { bsonType: ['string', 'null'] },
    created_by: { bsonType: 'objectId' },
    textract_analysis_id: { bsonType: ['objectId', 'null'] },
    created_at: { bsonType: 'date' },
    updated_at: { bsonType: 'date' }
  }
});

// 6. FORM REQUESTS
createValidatedCollection('form_requests', {
  bsonType: 'object',
  required: ['requested_by', 'profile_id', 'template_id', 'status', 'requested_at'],
  properties: {
    _id: { bsonType: 'objectId' },
    requested_by: { bsonType: 'objectId' },
    profile_id: { bsonType: 'objectId' },
    template_id: { bsonType: 'objectId' },
    status: { enum: ['queued', 'processing', 'completed', 'error'] },
    output_s3_key_enc: { bsonType: ['string', 'null'] },
    overlay_log: {
      bsonType: ['array', 'null'],
      items: {
        bsonType: 'object',
        required: ['field_name', 'data_key', 'placed'],
        properties: {
          field_name: { bsonType: 'string' },
          data_key: { bsonType: 'string' },
          placed: { bsonType: 'bool' },
          reason: { bsonType: ['string', 'null'] }
        }
      }
    },
    error_message: { bsonType: ['string', 'null'] },
    output_expires_at: { bsonType: ['date', 'null'] },
    requested_at: { bsonType: 'date' },
    completed_at: { bsonType: ['date', 'null'] }
  }
});

// 7. AUDIT LOGS
createValidatedCollection('audit_logs', {
  bsonType: 'object',
  required: ['actor_id', 'action', 'target_collection', 'target_id', 'ip_address', 'result', 'logged_at'],
  properties: {
    _id: { bsonType: 'objectId' },
    actor_id: { bsonType: 'objectId' },
    action: {
      enum: ['view_profile', 'upload_document', 'ocr_process', 'request_form_fill', 'download_output', 'update_profile', 'login', 'logout', 'key_rotation', 'admin_access']
    },
    target_collection: { bsonType: 'string' },
    target_id: { bsonType: 'objectId' },
    ip_address: { bsonType: 'string' },
    user_agent: { bsonType: ['string', 'null'] },
    result: { enum: ['success', 'denied', 'error'] },
    metadata: { bsonType: ['object', 'null'] },
    logged_at: { bsonType: 'date' }
  }
});

print('[3/6] Setting Up Zero-Knowledge Token & Search Indexes...');
db.users.createIndex({ email_hash: 1 }, { unique: true, sparse: true});
db.users.createIndex({ role: 1 });
db.users.createIndex({ is_active: 1 });
db.users.createIndex({ phone_hash: 1 }, { unique: true });

db.encryption_keys.createIndex({ key_alias: 1 }, { unique: true });
db.encryption_keys.createIndex({ status: 1 });

// Deduplication Sparse Unique Indexes on Tokens
db.patient_profiles.createIndex({ user_id: 1 }, { unique: true });
db.patient_profiles.createIndex({phone_enc:1},{unique:true,sparse:true});
db.patient_profiles.createIndex({email_enc:1},{unique:true,sparse:true});
db.patient_profiles.createIndex({ aadhaar_token: 1 }, { unique: true, sparse: true });
db.patient_profiles.createIndex({ pan_token: 1 }, { unique: true, sparse: true });
db.patient_profiles.createIndex({ voter_id_token: 1 }, { unique: true, sparse: true });
db.patient_profiles.createIndex({ passport_token: 1 }, { unique: true, sparse: true });
db.patient_profiles.createIndex({ driving_licence_token: 1 }, { unique: true, sparse: true });
db.patient_profiles.createIndex({ birth_reg_token: 1 }, { unique: true, sparse: true });
db.patient_profiles.createIndex({ health_insurance_token: 1 }, { unique: true, sparse: true });
db.patient_profiles.createIndex({ phone_hash: 1 });

db.source_documents.createIndex({ user_id: 1, doc_type: 1 });
db.source_documents.createIndex({ ocr_status: 1 });
db.source_documents.createIndex({ manual_review_required: 1 }, { sparse: true });

db.form_templates.createIndex({ template_name: 1, version: 1 }, { unique: true });
db.form_templates.createIndex({ category: 1, is_active: 1 });

db.form_requests.createIndex({ requested_by: 1, requested_at: -1 });
db.form_requests.createIndex({ status: 1, requested_at: 1 });

db.audit_logs.createIndex({ actor_id: 1, logged_at: -1 });
db.audit_logs.createIndex({ target_id: 1, logged_at: -1 });
db.audit_logs.createIndex({ logged_at: 1 }, { expireAfterSeconds: 220752000 }); // 7-year TTL

print('[4/6] Seeding Initial Active Data Encryption Key (DEK)...');
const defaultDekId = new ObjectId();
db.encryption_keys.insertOne({
  _id: defaultDekId,
  key_alias: 'local-pii-dek-v1',
  algorithm: 'AES-256-GCM',
  wrapped_dek: BinData(0, 'u1k23j4k12j34hk123j4hk123412341234='),
  kms_reference: null,
  status: 'active',
  created_at: new Date(),
  rotated_at: null,
  created_by: null
});

print('[SUCCESS] Database initialized with full 7-document support.');