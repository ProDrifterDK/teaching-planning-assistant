#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/prodrifterdk/Documents/projects/teaching-planning-assistant')

from api.db.session import SessionLocal, engine, Base
from api.db.models import ServiceClient, User, PlanningLog, BatchJob
from api.db.apikey_crud import create_service_client, list_service_clients

def main():
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        existing_clients = list_service_clients(db)
        print("Existing clients:")
        for client in existing_clients:
            print(f"  - {client.id}: {client.client_name} (active: {client.is_active})")
        
        print("\nCreating new API key for 'colegio-alas-prod'...")
        
        client, raw_api_key = create_service_client(
            db,
            client_name="colegio-alas-prod",
            permissions=["batch:create", "batch:read", "generate:quiz", "generate:activity", "generate:exam", "generate:reinforcement", "generate:lesson"],
            rate_limit=200,
            webhook_url=None
        )
        
        print(f"\n✅ API Key created successfully!")
        print(f"Client ID: {client.id}")
        print(f"Client Name: {client.client_name}")
        print(f"Permissions: {client.permissions}")
        print(f"Rate Limit: {client.rate_limit}")
        print(f"\n🔑 API KEY (save this - it won't be shown again!):")
        print(f"   {raw_api_key}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.query
    finally:
        db.close()

if __name__ == "__main__":
    main()
