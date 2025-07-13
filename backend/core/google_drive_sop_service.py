"""
Google Drive Integration for ClubOS
Automatically pulls SOPs, procedures, and documentation from your Google Drive
"""

import os
import json
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
import time
from datetime import datetime, timedelta

class GoogleDriveSOPService:
    """Service to automatically sync SOPs from Google Drive"""
    
    def __init__(self):
        self.service = None
        self.sop_cache = {}
        self.last_sync = None
        self.setup_credentials()
    
    def setup_credentials(self):
        """Setup Google Drive API credentials"""
        try:
            # Load service account credentials from environment or file
            creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            
            if creds_json:
                # From environment variable (recommended for production)
                creds_info = json.loads(creds_json)
                credentials = Credentials.from_service_account_info(
                    creds_info,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            else:
                # From file (for development)
                credentials = Credentials.from_service_account_file(
                    'service_account.json',
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            
            self.service = build('drive', 'v3', credentials=credentials)
            print("✅ Google Drive API connected")
            
        except Exception as e:
            print(f"⚠️  Google Drive API setup failed: {e}")
            print("📋 To enable Google Drive integration:")
            print("1. Create service account at console.cloud.google.com")
            print("2. Download JSON key file")
            print("3. Set GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
            self.service = None
    
    def search_sop_documents(self, folder_id: Optional[str] = None) -> List[Dict]:
        """Search for SOP documents in Google Drive"""
        if not self.service:
            return []
        
        try:
            # Build search query
            query_parts = []
            
            # Look for common SOP file patterns
            sop_patterns = [
                "name contains 'SOP'",
                "name contains 'procedure'", 
                "name contains 'manual'",
                "name contains 'process'",
                "name contains 'instruction'",
                "name contains 'troubleshoot'"
            ]
            
            # File types (Google Docs, PDFs, Word docs)
            file_types = [
                "mimeType='application/vnd.google-apps.document'",
                "mimeType='application/pdf'",
                "mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
            ]
            
            # Combine patterns
            pattern_query = f"({' or '.join(sop_patterns)})"
            type_query = f"({' or '.join(file_types)})"
            
            query = f"{pattern_query} and {type_query} and trashed=false"
            
            # Add folder restriction if specified
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            # Execute search
            results = self.service.files().list(
                q=query,
                pageSize=50,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink, description)"
            ).execute()
            
            documents = results.get('files', [])
            
            print(f"📂 Found {len(documents)} SOP documents in Google Drive")
            return documents
            
        except HttpError as e:
            print(f"❌ Google Drive search error: {e}")
            return []
    
    def extract_document_content(self, document_id: str, mime_type: str) -> str:
        """Extract text content from Google Drive document"""
        if not self.service:
            return ""
        
        try:
            if mime_type == 'application/vnd.google-apps.document':
                # Google Docs - export as plain text
                content = self.service.files().export(
                    fileId=document_id,
                    mimeType='text/plain'
                ).execute()
                
                return content.decode('utf-8')
                
            elif mime_type == 'application/pdf':
                # PDF files - would need additional PDF processing
                print(f"⚠️  PDF processing not implemented for {document_id}")
                return ""
                
            else:
                # Other file types
                print(f"⚠️  Unsupported file type: {mime_type}")
                return ""
                
        except HttpError as e:
            print(f"❌ Error extracting content from {document_id}: {e}")
            return ""
    
    def process_sop_content(self, content: str, document_name: str) -> Dict:
        """Process SOP content into structured data"""
        # Basic processing - extract key information
        processed = {
            "title": document_name,
            "content": content,
            "steps": [],
            "equipment": [],
            "keywords": [],
            "last_updated": datetime.now().isoformat()
        }
        
        # Extract numbered steps
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Look for numbered steps (1. 2. etc.)
            if line and (line[0].isdigit() and '. ' in line):
                processed["steps"].append(line)
            
            # Extract equipment mentions
            equipment_terms = ['trackman', 'projector', 'simulator', 'computer', 'hvac']
            for term in equipment_terms:
                if term.lower() in line.lower() and term not in processed["equipment"]:
                    processed["equipment"].append(term)
            
            # Extract keywords
            keywords = ['emergency', 'maintenance', 'troubleshoot', 'repair', 'replace']
            for keyword in keywords:
                if keyword.lower() in line.lower() and keyword not in processed["keywords"]:
                    processed["keywords"].append(keyword)
        
        return processed
    
    def sync_all_sops(self, folder_id: Optional[str] = None) -> Dict:
        """Sync all SOPs from Google Drive"""
        if not self.service:
            return {"status": "error", "message": "Google Drive not connected"}
        
        start_time = time.time()
        
        # Search for documents
        documents = self.search_sop_documents(folder_id)
        
        synced_sops = {}
        errors = []
        
        for doc in documents:
            try:
                # Extract content
                content = self.extract_document_content(doc['id'], doc['mimeType'])
                
                if content:
                    # Process content
                    processed_sop = self.process_sop_content(content, doc['name'])
                    processed_sop.update({
                        "drive_id": doc['id'],
                        "drive_link": doc.get('webViewLink', ''),
                        "mime_type": doc['mimeType'],
                        "last_modified": doc.get('modifiedTime', '')
                    })
                    
                    synced_sops[doc['id']] = processed_sop
                    print(f"✅ Synced: {doc['name']}")
                
            except Exception as e:
                error_msg = f"Failed to sync {doc['name']}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        # Update cache
        self.sop_cache = synced_sops
        self.last_sync = datetime.now()
        
        sync_time = time.time() - start_time
        
        return {
            "status": "success",
            "synced_count": len(synced_sops),
            "errors": errors,
            "sync_time": f"{sync_time:.2f} seconds",
            "last_sync": self.last_sync.isoformat()
        }
    
    def search_relevant_sops(self, query: str) -> List[Dict]:
        """Search for relevant SOPs based on query"""
        if not self.sop_cache:
            self.sync_all_sops()
        
        relevant_sops = []
        query_lower = query.lower()
        
        for sop_id, sop in self.sop_cache.items():
            relevance_score = 0
            
            # Check title match
            if any(word in sop['title'].lower() for word in query_lower.split()):
                relevance_score += 10
            
            # Check keyword match
            for keyword in sop['keywords']:
                if keyword.lower() in query_lower:
                    relevance_score += 5
            
            # Check equipment match
            for equipment in sop['equipment']:
                if equipment.lower() in query_lower:
                    relevance_score += 8
            
            # Check content match
            if query_lower in sop['content'].lower():
                relevance_score += 3
            
            if relevance_score > 0:
                sop_copy = sop.copy()
                sop_copy['relevance_score'] = relevance_score
                relevant_sops.append(sop_copy)
        
        # Sort by relevance
        relevant_sops.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return relevant_sops[:5]  # Return top 5 most relevant
    
    def get_sop_summary(self, sop_id: str) -> Optional[Dict]:
        """Get summary of a specific SOP"""
        if sop_id not in self.sop_cache:
            return None
        
        sop = self.sop_cache[sop_id]
        
        return {
            "title": sop['title'],
            "step_count": len(sop['steps']),
            "equipment": sop['equipment'],
            "keywords": sop['keywords'],
            "drive_link": sop['drive_link'],
            "last_updated": sop['last_updated']
        }
    
    def should_refresh_cache(self, max_age_hours: int = 6) -> bool:
        """Check if cache should be refreshed"""
        if not self.last_sync:
            return True
        
        age = datetime.now() - self.last_sync
        return age > timedelta(hours=max_age_hours)
    
    def get_cache_status(self) -> Dict:
        """Get current cache status"""
        return {
            "documents_cached": len(self.sop_cache),
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "cache_age_hours": (datetime.now() - self.last_sync).total_seconds() / 3600 if self.last_sync else None,
            "drive_connected": self.service is not None
        }

# Integration with ClubOS Engine
class SOPAwareEngine:
    """Enhanced engine that uses Google Drive SOPs"""
    
    def __init__(self):
        self.drive_service = GoogleDriveSOPService()
        
    async def get_sop_guidance(self, issue_description: str) -> Dict:
        """Get guidance from SOPs for an issue"""
        
        # Search for relevant SOPs
        relevant_sops = self.drive_service.search_relevant_sops(issue_description)
        
        if not relevant_sops:
            return {
                "status": "no_sops_found",
                "message": "No relevant SOPs found in Google Drive",
                "suggestion": "Create SOP document for this type of issue"
            }
        
        # Get the most relevant SOP
        best_sop = relevant_sops[0]
        
        return {
            "status": "sop_found",
            "title": best_sop['title'],
            "steps": best_sop['steps'],
            "equipment": best_sop['equipment'],
            "drive_link": best_sop['drive_link'],
            "relevance_score": best_sop['relevance_score'],
            "last_updated": best_sop['last_updated']
        }
    
    def refresh_sops(self) -> Dict:
        """Manual refresh of SOPs"""
        return self.drive_service.sync_all_sops()
