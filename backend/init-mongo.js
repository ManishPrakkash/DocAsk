// MongoDB initialization script for ClauseWise
db = db.getSiblingDB('clausewise');

// Create collections
db.createCollection('users');
db.createCollection('documents');
db.createCollection('clauses');
db.createCollection('legal_playbooks');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "created_at": 1 });

db.documents.createIndex({ "user_id": 1 });
db.documents.createIndex({ "status": 1 });
db.documents.createIndex({ "created_at": 1 });

db.clauses.createIndex({ "document_id": 1 });
db.clauses.createIndex({ "risk_level": 1 });
db.clauses.createIndex({ "category": 1 });

db.legal_playbooks.createIndex({ "user_id": 1 });
db.legal_playbooks.createIndex({ "is_active": 1 });

print('ClauseWise MongoDB database initialized successfully');
